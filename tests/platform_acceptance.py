"""Real HTTP / CLI / stdio MCP and Playwright acceptance on a disposable service."""

import argparse
import asyncio
import json
import pathlib
import subprocess
import sys
import time
import uuid
import os

APP = pathlib.Path(__file__).resolve().parents[1]
TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(APP))
from contracts import OPS  # noqa: E402 -- script sets the project import root
from evidence import source_manifest, publish_json  # noqa: E402


class Harness:
    def __init__(self, runtime):
        self.runtime = pathlib.Path(runtime).resolve()
        assert self.runtime.is_relative_to(APP / "test-results")
        self.info = json.loads(self.runtime.read_text(encoding="utf-8"))
        self.root = self.runtime.parent
        self.report = {"checks": [], "errors": [], "sourceAtStart": source_manifest()}

    def call(self, name, args=None):
        from ai import v2_request
        from jsonschema import Draft202012Validator
        from contracts import response_schema

        result = v2_request(self.info, name, args or {})
        Draft202012Validator(response_schema(OPS[name])).validate(result)
        assert result["ok"], result
        return result["data"]

    async def mcp(self):
        from mcp import Client, StdioServerParameters

        params = StdioServerParameters(
            command=sys.executable,
            args=[str(APP / "mcp_adapter.py"), "--runtime", str(self.runtime)],
            cwd=str(self.root),
        )
        async with Client(params) as client:
            tools = await client.list_tools()
            values = tools.tools if hasattr(tools, "tools") else tools
            assert len(values) == len(OPS), (len(values), len(OPS))
            from contracts import response_schema

            by_name = {tool.name: tool for tool in values}
            for name, spec in OPS.items():
                tool = by_name[name.replace(".", "_")]
                assert tool.input_schema == spec["inputSchema"]
                assert tool.output_schema == response_schema(spec)
            resources = await client.list_resources()
            resource_values = (
                resources.resources if hasattr(resources, "resources") else resources
            )
            resource_uris = {str(resource.uri) for resource in resource_values}
            assert resource_uris == {"mod-browser://start", "mod-browser://workflows"}
            workflow_resource = await client.read_resource("mod-browser://workflows")
            workflow_text = workflow_resource.contents[0].text
            assert len(json.loads(workflow_text)["workflows"]) == 5
            result = await client.call_tool(
                "mods_search", {"game": "stellarblade", "limit": 3, "sort": "updated"}
            )
            structured = getattr(result, "structured_content", None) or getattr(
                result, "structuredContent", None
            )
            assert structured and structured["ok"], result
            expected = self.call(
                "mods.search", {"game": "stellarblade", "limit": 3, "sort": "updated"}
            )
            assert structured["data"] == expected
            # Replay one write across all three transports, including stdin JSON.
            request = dict(
                game="stellarblade",
                name="三入口一致-" + uuid.uuid4().hex[:8],
                idempotencyKey="three-transports-" + uuid.uuid4().hex,
            )
            expected = self.call("profiles.save", request)
            cli = subprocess.run(
                [
                    sys.executable,
                    str(APP / "ai.py"),
                    "--runtime",
                    str(self.runtime),
                    "invoke",
                    "profiles.save",
                    "--input",
                    "-",
                ],
                input=json.dumps(request, ensure_ascii=False),
                encoding="utf-8",
                capture_output=True,
                env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                cwd=self.root,
            )
            assert cli.returncode == 0 and json.loads(cli.stdout)["data"] == expected, (
                cli.stdout,
                cli.stderr,
            )
            replay = await client.call_tool("profiles_save", request)
            assert replay.structured_content["data"] == expected
            from ai import v2_request

            for operation, invalid in [
                ("resources.read", {"ids": ["missing"]}),
                ("mods.search", {"typo": True}),
            ]:
                http_error = v2_request(self.info, operation, invalid)
                mcp_error = await client.call_tool(operation.replace(".", "_"), invalid)
                assert mcp_error.structured_content == http_error, (
                    mcp_error,
                    http_error,
                )
        self.report["checks"].append(
            "HTTP / MCP identical search; stdio tool discovery; entry and workflow resources"
        )
        self.report["checks"].append(
            "HTTP / CLI stdin / MCP identical idempotent write; MCP unknown-parameter and missing-resource errors; host cwd independence"
        )

    def cli(self):
        p = subprocess.run(
            [
                sys.executable,
                str(APP / "ai.py"),
                "--runtime",
                str(self.runtime),
                "mods.search",
                "--game",
                "stellarblade",
                "--limit",
                "3",
                "--sort",
                "updated",
            ],
            capture_output=True,
            encoding="utf-8",
            cwd=APP,
        )
        assert p.returncode == 0, (p.stdout, p.stderr)
        assert json.loads(p.stdout)["data"] == self.call(
            "mods.search", {"game": "stellarblade", "limit": 3, "sort": "updated"}
        )
        p = subprocess.run(
            [
                sys.executable,
                str(APP / "ai.py"),
                "--runtime",
                str(self.runtime),
                "resources.read",
                "--ids",
                '["missing"]',
            ],
            capture_output=True,
            encoding="utf-8",
            cwd=APP,
        )
        assert p.returncode == 1 and not json.loads(p.stdout)["ok"]
        self.report["checks"].append(
            "HTTP / CLI identical search and structured failure"
        )

    def perf(self):
        latencies = []
        for _ in range(30):
            t = time.perf_counter()
            self.call("mods.search", {"game": "stellarblade", "limit": 48})
            latencies.append((time.perf_counter() - t) * 1000)
        latencies.sort()
        self.report["searchP95Ms"] = latencies[28]
        assert latencies[28] <= 300, latencies
        latencies = []
        for _ in range(30):
            t = time.perf_counter()
            self.call("jobs.list", {"limit": 24})
            latencies.append((time.perf_counter() - t) * 1000)
        latencies.sort()
        self.report["jobsP95Ms"] = latencies[28]
        assert latencies[28] <= 300
        t = time.perf_counter()
        doctor = self.call("doctor")
        self.report["doctorMs"] = (time.perf_counter() - t) * 1000
        assert doctor["databaseCheck"] == "readable"
        assert self.report["doctorMs"] <= 300
        for name, parameters in [
            ("tasks.list", {"limit": 24}),
            ("mods.search", {"limit": 48}),
            ("mods.search", {"game": "stellarblade", "q": "CNS", "limit": 10}),
        ]:
            timings = []
            self.call(name, parameters)
            for _ in range(20):
                t = time.perf_counter()
                self.call(name, parameters)
                timings.append((time.perf_counter() - t) * 1000)
            key = name + ":" + json.dumps(parameters, sort_keys=True)
            self.report.setdefault("additionalP95Ms", {})[key] = sorted(timings)[18]
            assert sorted(timings)[18] <= 300, (key, timings)

    async def browser(self):
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                executable_path=os.environ.get("LOCAL_MOD_BROWSER_CHROME") or None,
            )
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})
            errors = []
            handled_errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def console_message(message):
                if message.type == "error":
                    target = (
                        handled_errors if "验收模拟连接中断" in message.text else errors
                    )
                    target.append(message.text)

            page.on("console", console_message)
            await page.goto(self.info["url"])
            await page.locator('[data-game="stellarblade"]').wait_for()
            await page.locator('[data-view="browse"]').click()
            await page.locator(".card").first.wait_for()
            await page.locator('[data-view="work"]').click()
            await page.locator("#workNew").wait_for()
            await page.locator("#workNew").click()
            name = "验收任务-" + "长中文名称" * 12 + uuid.uuid4().hex[:8]
            await page.locator('#dialogFields [name="title"]').fill(name)
            await page.locator('#dialogFields [name="goal"]').fill(
                "仅隔离库：补充作者有来源的摘要"
            )
            await page.locator('#dialogForm [type="submit"]').click()
            panel = page.locator(".work-list .panel").filter(has_text=name)
            await panel.wait_for()
            await panel.locator('[data-task-action="pause"]').click()
            await panel.locator('[data-task-action="resume"]').click()
            await panel.locator("[data-context]").click()
            await page.locator("#workContext").wait_for(state="visible")
            # Refresh (including the periodic task refresh) must retain the open
            # handoff panel, with its copy/download controls still usable.
            await page.locator("#workRefresh").click()
            await page.locator("#workContext").wait_for(state="visible")
            assert name in await page.locator("#workContext").inner_text()
            await page.locator('[data-work-tab="connect"]').click()
            await page.locator("#copyMcpConfig").wait_for()
            await page.context.grant_permissions(["clipboard-read", "clipboard-write"])
            await page.locator("#copyMcpConfig").click()
            copied = await page.evaluate("navigator.clipboard.readText()")
            assert self.info["token"] not in copied and json.loads(copied)["mcpServers"]
            await page.screenshot(path=str(self.root / "platform-connect-1920.png"))
            await page.locator('[data-work-tab="exchange"]').click()
            await page.locator("#workImportFile").wait_for()
            resource = self.call(
                "resources.read",
                {"ids": ["stellarblade:1401"], "fields": ["name", "function"]},
            )["items"][0]
            edits = [
                {
                    "resourceId": resource["resourceId"],
                    "baseRevision": resource["revision"],
                    "patch": {"function": "隔离浏览器验收：有来源的摘要整理"},
                    "note": "browser acceptance",
                }
            ]
            fixture = self.root / "ui-edits.json"
            fixture.write_text(json.dumps(edits, ensure_ascii=False), encoding="utf-8")
            await page.locator("#workImportType").select_option("content")
            rejected = self.root / "ui-rejected.json"
            rejected.write_text(
                json.dumps([dict(edits[0], baseRevision="stale-fixture")]),
                encoding="utf-8",
            )
            await page.locator("#workImportFile").set_input_files(str(rejected))
            await page.locator("#workApply").wait_for()
            assert not await page.locator("#workApply").is_enabled()
            async with page.expect_download() as downloading:
                await page.locator("#workDownloadErrors").click()
            downloaded = await downloading.value
            retry_file = self.root / "ui-retry-records.json"
            await downloaded.save_as(str(retry_file))
            assert (
                json.loads(retry_file.read_text(encoding="utf-8"))[0]["resourceId"]
                == resource["resourceId"]
            )
            await page.locator("#workImportFile").set_input_files(str(fixture))
            await page.locator("#workApply:not([disabled])").wait_for()
            assert await page.locator("#workApply").is_enabled()
            before_jobs = {
                item["id"] for item in self.call("jobs.list", {"limit": 96})["items"]
            }
            await page.locator("#workApply").click()
            await page.locator("#workNew").wait_for()
            submitted_job = None
            for _ in range(300):
                candidates = [
                    item
                    for item in self.call("jobs.list", {"limit": 96})["items"]
                    if item["id"] not in before_jobs
                ]
                if candidates:
                    submitted_job = self.call("jobs.read", {"id": candidates[0]["id"]})
                    if submitted_job["status"] in {
                        "complete",
                        "failed",
                        "blocked",
                        "cancelled",
                    }:
                        break
                await asyncio.sleep(0.1)
            assert submitted_job and submitted_job["status"] == "complete", submitted_job
            latest_batch = self.call("history.list", {"page": 1, "limit": 24})["items"][0]
            await page.locator('[data-work-tab="history"]').click()
            undo = page.locator(f'[data-undo-batch="{latest_batch["id"]}"]')
            await undo.wait_for()
            await undo.click()
            panel = page.locator(
                f'[data-batch-details="{latest_batch["id"]}"]'
            ).locator("xpath=ancestor::article[1]")
            await (
                panel.locator(".badge")
                .filter(has_text="已撤销")
                .first.wait_for()
            )
            for width, height in [(1920, 1080), (1366, 768), (390, 844)]:
                await page.set_viewport_size({"width": width, "height": height})
                await page.locator('[data-work-tab="tasks"]').click()
                await page.locator("#workNew").wait_for()
                overflow = await page.evaluate(
                    "document.documentElement.scrollWidth>window.innerWidth"
                )
                assert not overflow, (width, "horizontal overflow")
                await page.screenshot(
                    path=str(self.root / f"platform-tasks-{width}.png")
                )
                await page.keyboard.press("/")
                assert await page.locator("#search").evaluate(
                    "(e)=>e===document.activeElement"
                )
                await page.locator('[data-work-tab="connect"]').focus()
                await page.keyboard.press("Enter")
                await page.locator("#copyMcpConfig").wait_for()
                # Recover a handled API failure via the visible retry button.
                await page.locator('[data-work-tab="tasks"]').click()

                async def fail_once(route):
                    await route.fulfill(
                        status=200,
                        content_type="application/json",
                        body=json.dumps(
                            dict(
                                ok=False,
                                error=dict(
                                    code="fixture_offline", message="验收模拟连接中断"
                                ),
                            ),
                            ensure_ascii=False,
                        ),
                    )

                await page.route("**/api/v2/doctor", fail_once, times=1)
                await page.locator('[data-work-tab="connect"]').click()
                await page.locator("#workRetry").wait_for()
                await page.locator("#workRetry").click()
                await page.locator("#copyMcpConfig").wait_for()
            assert not errors, errors
            assert len(handled_errors) == 3, handled_errors
            await browser.close()
        self.report["checks"].append(
            "Playwright: create/pause/resume/handoff/import/undo, keyboard, 1920/1366/390 without overflow or console errors"
        )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime")
    parser.add_argument("--skip-browser", action="store_true")
    parser.add_argument("--only", choices=("transports", "performance", "browser"))
    args = parser.parse_args()
    h = Harness(args.runtime)
    try:
        if args.only in (None, "transports"):
            h.cli()
            await h.mcp()
        if args.only in (None, "performance"):
            h.perf()
        if args.only in (None, "browser") and not args.skip_browser:
            await h.browser()
        h.report["ok"] = True
    except Exception as error:
        h.report["ok"] = False
        h.report["errors"].append(repr(error))
        raise
    finally:
        h.report["sourceAtEnd"] = source_manifest()
        h.report["codeUnchanged"] = (
            h.report["sourceAtStart"]["sha256"] == h.report["sourceAtEnd"]["sha256"]
        )
        h.report["ok"] = h.report["ok"] and h.report["codeUnchanged"]
        h.report["scope"] = args.only or (
            "transports+performance" if args.skip_browser else "full"
        )
        filename = (
            "platform-" + args.only + "-report.json"
            if args.only
            else "platform-report.json"
        )
        publish_json(h.root / filename, h.report)
        print(json.dumps(h.report, ensure_ascii=False))
    return 0 if h.report["ok"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
