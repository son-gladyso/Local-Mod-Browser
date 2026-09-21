"""Exercise a real queued translation import, browsing, stop, rollback and resume.

Only synthetic data in test-results is written. No delay or mock is inserted into
the importer. --browser additionally stops the job from the real task-centre UI.
"""

# ruff: noqa: E402 -- standalone acceptance entry point
import argparse
import asyncio
import json
import os
import pathlib
import sys
import threading
import time
import uuid
from http.server import ThreadingHTTPServer

APP = pathlib.Path(__file__).resolve().parents[1]
TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(APP))
import catalog
import content
import server
import translations
from ai import v2_request
from platform_api import Platform
from test_app import seed
from evidence import source_manifest, publish_json
from soak_platform import memory_sample


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    if not 300 <= args.records <= 5000:
        parser.error("records must be between 300 and 5000")
    root = APP / "test-results" / ("import-responsive-" + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    path = root / "catalog.sqlite3"
    seed(path, root)
    results = []
    # Fixture-only registration: every source is small and every field is one segment.
    with catalog.connect(path) as db:
        for i in range(args.records):
            mid = f"stellarblade:{10000 + i}"
            source = f"Synthetic source summary for local acceptance number {i}."
            data = dict(
                id=mid,
                game="stellarblade",
                modId=10000 + i,
                name=f"Fixture {i}",
                gameTitle="剑星",
                author="Fixture",
                group="工具",
                function=source,
                details="",
                requirements=[],
                tags=[],
                fileCount=0,
                imageCount=0,
            )
            catalog.apply_edits(db, data, "mod")
            db.execute(
                "INSERT INTO mods VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    mid,
                    "stellarblade",
                    10000 + i,
                    data["name"],
                    "Fixture",
                    "工具",
                    0,
                    1,
                    1,
                    catalog.dumps(data).casefold(),
                    catalog.dumps(data),
                ),
            )
            tid, sid, hashed = (
                f"fixture-task-{i}",
                f"fixture-segment-{i}",
                catalog.digest(source),
            )
            db.execute(
                "INSERT INTO translation_tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    mid,
                    "function",
                    hashed,
                    sid,
                    0,
                    1,
                    hashed,
                    source,
                    "[]",
                    "pending",
                    "",
                    "",
                    time.time(),
                ),
            )
            results.append(
                dict(
                    taskId=tid,
                    resourceId=mid,
                    field="function",
                    segmentId=sid,
                    sourceHash=hashed,
                    translation=f"隔离测试用途说明，第{i}项。",
                )
            )
    server.DB_PATH, server.STORAGE = path, root
    content.APP = translations.APP = root
    platform = server.PLATFORM = Platform(server)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    info = dict(url=f"http://127.0.0.1:{httpd.server_port}", token=server.TOKEN)
    report = dict(
        ok=False,
        checks=[],
        errors=[],
        records=args.records,
        sourceAtStart=source_manifest(),
        memoryStart=memory_sample(),
    )
    browser = pw = None

    def call(operation, parameters=None):
        response = v2_request(info, operation, parameters or {})
        assert response["ok"], response
        return response["data"]

    def checkpoint(stage, **values):
        publish_json(root / "progress.json", dict(stage=stage, **values))

    async def wait_status(jid, statuses, timeout=420):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = call("jobs.read", dict(id=jid))
            if job["status"] in statuses:
                return job
            if job["status"] in ("blocked", "failed"):
                raise AssertionError(job)
            checkpoint(
                "waiting", status=job["status"], done=job["done"], total=job["total"]
            )
            await asyncio.sleep(0.1)
        raise TimeoutError("Import did not reach " + str(statuses))

    try:
        page = None
        if args.browser:
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            browser = await pw.chromium.launch(
                headless=True,
                executable_path=os.environ.get("LOCAL_MOD_BROWSER_CHROME") or None,
            )
            page = await browser.new_page(viewport=dict(width=1366, height=768))
            page.on("pageerror", lambda e: report["errors"].append(str(e)))
            page.on(
                "console",
                lambda m: (
                    report["errors"].append(m.text) if m.type == "error" else None
                ),
            )
            await page.goto(info["url"])
            await page.locator(".card").first.wait_for()
        preview = call(
            "translations.preview",
            dict(content=json.dumps(results, ensure_ascii=False)),
        )
        assert preview["valid"] == args.records and preview["canApply"]
        job = call(
            "translations.import",
            dict(previewId=preview["previewId"], idempotencyKey="long-import"),
        )
        jid = job["id"]
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            state = call("jobs.read", dict(id=jid))
            if state["done"] >= 10:
                break
            assert state["status"] in ("queued", "running"), state
            await asyncio.sleep(0.05)
        assert state["status"] == "running" and 0 < state["done"] < args.records, state
        timings = {"browse": [], "progress": [], "tasks": []}
        for _ in range(20):
            for name, operation, parameters in [
                ("browse", "mods.search", dict(limit=48)),
                ("progress", "jobs.read", dict(id=jid)),
                ("tasks", "tasks.list", dict(limit=24)),
            ]:
                start = time.perf_counter()
                call(operation, parameters)
                timings[name].append((time.perf_counter() - start) * 1000)
        report["duringImportP95Ms"] = {k: sorted(v)[18] for k, v in timings.items()}
        before_stop = call("jobs.read", dict(id=jid))
        assert before_stop["status"] == "running", (
            "Increase fixture size to sample an active import"
        )
        if page:
            await page.locator('[data-view="browse"]').click()
            await page.locator(".card").first.wait_for()
            await page.locator('[data-view="work"]').click()
            stop = page.locator(f'[data-job-action="cancel"][data-id="{jid}"]')
            await stop.wait_for()
            await page.screenshot(path=str(root / "import-running.png"))
            stop_start = time.perf_counter()
            async with page.expect_response(
                lambda response: response.url.endswith("/api/v2/jobs.control")
                and response.request.method == "POST"
            ) as response_info:
                await stop.click()
            response = await response_info.value
            await response.body()
            stop_ack = time.perf_counter()
            assert response.ok, await response.text()
        else:
            stop_start = time.perf_counter()
            call("jobs.control", dict(id=jid, action="cancel"))
            stop_ack = time.perf_counter()
        stopped = await wait_status(jid, {"cancelled"}, timeout=15)
        stop_exit = time.perf_counter()
        report["stopAckMs"] = (stop_ack - stop_start) * 1000
        report["stopExitMs"] = (stop_exit - stop_start) * 1000
        report["stoppedAfterSegments"] = stopped["done"]
        with catalog.connect(path) as db:
            assert db.execute("SELECT count(*) FROM translations").fetchone()[0] == 0
            assert (
                db.execute(
                    "SELECT count(*) FROM translation_tasks WHERE status='imported'"
                ).fetchone()[0]
                == 0
            )
        assert platform.receipt("job:" + jid) is None
        report["checks"].append(
            "Browse/progress/task reads remain available; stop rolls back the active batch and its receipt"
        )
        checkpoint("resume", stoppedAfter=stopped["done"])
        resumed = call("jobs.control", dict(id=jid, action="resume"))
        assert resumed["id"] == jid
        complete = await wait_status(jid, {"complete"})
        assert complete["result"]["segments"] == args.records
        with catalog.connect(path) as db:
            assert (
                db.execute("SELECT count(*) FROM translations").fetchone()[0]
                == args.records
            )
            assert (
                db.execute("SELECT count(*) FROM translation_history").fetchone()[0]
                == args.records
            )
        replay = call(
            "translations.import",
            dict(previewId=preview["previewId"], idempotencyKey="long-import"),
        )
        assert replay["id"] == jid
        report["checks"].append(
            "Resume keeps the job ID; every field commits once; original submission retries do not enqueue a duplicate"
        )
        report["performancePassed"] = all(
            v <= 300 for v in report["duringImportP95Ms"].values()
        ) and report["stopAckMs"] <= 300 and report["stopExitMs"] <= 2000
        report["ok"] = not report["errors"] and report["performancePassed"]
    except Exception as error:
        report["errors"].append(repr(error))
    finally:
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
        platform.runtime.stop()
        httpd.shutdown()
        httpd.server_close()
        report["memoryEnd"] = memory_sample()
        report["sourceAtEnd"] = source_manifest()
        report["codeUnchanged"] = (
            report["sourceAtStart"]["sha256"] == report["sourceAtEnd"]["sha256"]
        )
        report["ok"] = report["ok"] and report["codeUnchanged"]
        publish_json(root / "report.json", report)
        print(json.dumps(dict(folder=str(root), **report), ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
