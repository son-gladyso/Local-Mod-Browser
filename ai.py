"""Stable JSON CLI for any local AI agent. Run `python ai.py tour` first."""

from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from launcher import start, APP
from contracts import OPS
from platform_client import shared_client


def main():
    from runtime_support import ensure_pinned_process

    ensure_pinned_process(
        required="--runtime" not in sys.argv and "--url" not in sys.argv
    )
    parser = argparse.ArgumentParser(
        description="本地 MOD 浏览器 AI 入口；标准输出仅输出 JSON"
    )
    parser.add_argument("--output", help="将完整响应保存为 UTF-8 JSON 文件")
    parser.add_argument("--url", help="连接指定本机测试服务，配合 --runtime 使用")
    parser.add_argument("--runtime", help="自定义 runtime.json，不启动正式服务")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("tour")
    sub.add_parser("status")
    sub.add_parser("schema")
    sub.add_parser("games")
    sub.add_parser("profiles")
    sub.add_parser("docs")
    wait = sub.add_parser("wait")
    wait.add_argument("id")
    wait.add_argument("--timeout", type=float, default=60)
    download = sub.add_parser("download")
    download.add_argument("path")
    download.add_argument("destination")
    for name in ("edit-preview", "profile-preview", "translation-preview"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", help="UTF-8 JSON/JSONL 文件")
    for name in ("edit-apply", "translation-apply"):
        cmd = sub.add_parser(name)
        cmd.add_argument("preview_id")
    export = sub.add_parser("content-export")
    export.add_argument("--game", default="")
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--game", default="")
    search.add_argument("--page", type=int, default=1)
    for field, schema in OPS["mods.search"]["inputSchema"]["properties"].items():
        if field in ("q", "game", "page"):
            continue
        search.add_argument(
            "--" + field,
            type=int
            if schema.get("type") == "integer"
            else json.loads
            if schema.get("type") in ("array", "boolean")
            else str,
        )
    capability_parser = sub.add_parser("capabilities")
    capability_parser.add_argument("--operation")
    capability_parser.add_argument("--group")
    sub.add_parser("doctor")
    sub.add_parser("openapi")
    invoke = sub.add_parser(
        "invoke", help="按能力名调用 v2，参数来自 UTF-8 JSON 或 stdin"
    )
    invoke.add_argument("operation", choices=list(OPS))
    invoke.add_argument("--input", default="-")
    # Dotted commands are generated from the same registry used by HTTP and MCP.
    for name, spec in OPS.items():
        if "." not in name:
            continue
        cmd = sub.add_parser(name, help=spec["description"])
        cmd.add_argument("--input", help="JSON 文件或 -（stdin）；可与命令参数合并")
        for field, schema in spec["inputSchema"]["properties"].items():
            cmd.add_argument(
                "--" + field,
                type=int
                if schema.get("type") == "integer"
                else json.loads
                if schema.get("type") in ("array", "object", "boolean")
                else str,
            )
    show = sub.add_parser("show")
    show.add_argument("id")
    resource = sub.add_parser("resource")
    resource.add_argument("id")
    call = sub.add_parser("call")
    call.add_argument("method", choices=["GET", "POST"])
    call.add_argument("path")
    call.add_argument("--input", help="UTF-8 JSON request file; '-' reads stdin")
    args = parser.parse_args()
    if args.command == "tour":
        return {
            "ok": True,
            "data": {
                "project": "本地 MOD 浏览器",
                "startHere": str(APP / "AI入口.md"),
                "humanGuide": str(APP / "使用说明.md"),
                "architecture": str(APP / "ARCHITECTURE.md"),
                "contract": str(APP / "schemas.json"),
                "commands": [
                    "python ai.py status",
                    "python ai.py search CNS --game stellarblade",
                    "python ai.py show stellarblade:1401",
                    "python ai.py resource stellarblade:1401",
                    "python ai.py schema",
                    "python ai.py call POST /api/content/preview --input edits.json",
                ],
                "codeMap": {
                    "catalog.py": "读取现有缓存，统一身份，SQLite 和索引",
                    "server.py": "本机 HTTP API，搭配管理，后台任务",
                    "content.py": "可追溯资料修改、批量预览提交、搭配导入",
                    "translations.py": "Gemini 任务、分段、校验、翻译历史",
                    "static/app.js": "中文人类界面",
                    "launcher.py": "单服务启动",
                    "tests/test_app.py": "核心契约与真实数据验收",
                },
                "rules": [
                    "查询不需要修改数据库",
                    "修改内容先读取 revision，再 preview/apply",
                    "不得直接改源目录或原压缩包",
                    "翻译用 tasks.jsonl 身份字段回传",
                    "安装尚未接入 GMM",
                ],
            },
        }
    info = (
        json.loads(pathlib.Path(args.runtime).read_text(encoding="utf-8"))
        if args.runtime
        else start(False)
    )
    if args.url:
        info["url"] = args.url
    if args.command in OPS or args.command == "invoke":
        name = args.operation if args.command == "invoke" else args.command
        supplied = getattr(args, "input", None)
        parameters = (
            json.loads(
                sys.stdin.read()
                if supplied == "-"
                else pathlib.Path(supplied).read_text(encoding="utf-8-sig")
            )
            if supplied
            else {}
        )
        for field in OPS[name]["inputSchema"]["properties"]:
            value = getattr(args, field, None)
            if value is not None:
                parameters[field] = value
        return v2_request(info, name, parameters)
    if args.command == "search":
        parameters = {
            field: getattr(args, field)
            for field in OPS["mods.search"]["inputSchema"]["properties"]
            if getattr(args, field, None) is not None
        }
        parameters["q"] = args.query
        return v2_request(info, "mods.search", parameters)
    parsed = urllib.parse.urlparse(info["url"])
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
    ):
        raise ValueError("只允许连接 127.0.0.1 本机服务")
    routes = {
        "status": "/api/health",
        "schema": "/api/docs",
        "show": "/api/mod?id=" + urllib.parse.quote(getattr(args, "id", "")),
        "resource": "/api/resource?id=" + urllib.parse.quote(getattr(args, "id", "")),
        "search": "/api/mods?"
        + urllib.parse.urlencode(
            {
                "q": getattr(args, "query", ""),
                "game": getattr(args, "game", ""),
                "page": getattr(args, "page", 1),
            }
        ),
    }
    routes.update(
        games="/api/games",
        profiles="/api/profiles",
        docs="/api/docs",
        schema="/api/schema",
    )
    body = None
    if args.command.endswith("-preview"):
        raw = pathlib.Path(args.input).read_text(encoding="utf-8-sig")
        if args.command == "translation-preview":
            path, body = "/api/translations/preview", {"content": raw}
        elif args.command == "profile-preview":
            path, body = "/api/profile/preview", {"manifest": json.loads(raw)}
        else:
            try:
                records = json.loads(raw)
            except json.JSONDecodeError:
                records = [
                    json.loads(line) for line in raw.splitlines() if line.strip()
                ]
            if isinstance(records, dict):
                records = records.get("records", [records])
            path, body = "/api/content/preview", {"records": records}
    elif args.command.endswith("-apply"):
        path = (
            "/api/content/apply"
            if args.command == "edit-apply"
            else "/api/translations/import"
        )
        body = {"previewId": args.preview_id}
    elif args.command == "content-export":
        path, body = "/api/content/export", {"game": args.game}
    elif args.command == "wait":
        deadline = time.monotonic() + args.timeout
        while True:
            with urllib.request.urlopen(
                info["url"] + "/api/jobs", timeout=10
            ) as response:
                jobs = json.load(response)["data"]
            job = next((j for j in jobs if j["id"] == args.id), None)
            if not job:
                raise ValueError("任务不存在（服务重启后任务记录不保留）")
            if job["status"] not in ("running", "queued"):
                result = {"ok": job["status"] == "complete", "data": job}
                if not result["ok"]:
                    result["error"] = {
                        "code": "job_" + job["status"],
                        "message": job["message"],
                    }
                return result
            if time.monotonic() >= deadline:
                return {
                    "ok": False,
                    "error": {
                        "code": "wait_timeout",
                        "message": "任务仍在运行，可再次 wait",
                    },
                    "data": job,
                }
            time.sleep(0.2)
    else:
        path = (
            args.path if args.command in ("call", "download") else routes[args.command]
        )
    if not path.startswith("/api/") or path.startswith("//"):
        raise ValueError("只允许 /api/ 路径")
    if args.command == "download":
        if not path.startswith("/api/download/"):
            raise ValueError("只允许下载应用 exports 中的文件")
        with urllib.request.urlopen(
            info["url"] + urllib.parse.quote(path, safe="/:%"), timeout=120
        ) as response:
            raw = response.read()
        target = pathlib.Path(args.destination)
        with target.open("xb") as output:
            output.write(raw)
        return {"ok": True, "data": {"path": str(target.resolve()), "bytes": len(raw)}}
    method = (
        args.method if args.command == "call" else "POST" if body is not None else "GET"
    )
    payload = None
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    elif method == "POST":
        raw = (
            sys.stdin.read()
            if args.input == "-"
            else pathlib.Path(args.input).read_text(encoding="utf-8-sig")
            if args.input
            else "{}"
        )
        payload = json.dumps(json.loads(raw), ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        info["url"] + path,
        data=payload,
        method=method,
        headers={"Content-Type": "application/json", "X-Mod-Token": info["token"]},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return json.load(error)


def v2_request(info, name, parameters):
    return shared_client(info).request(name, parameters)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = main()
    except Exception as error:
        result = {"ok": False, "error": {"code": "cli_error", "message": str(error)}}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    # --output is global and deliberately precedes the command.
    if "--output" in sys.argv:
        try:
            destination = pathlib.Path(sys.argv[sys.argv.index("--output") + 1])
            destination.write_text(output + "\n", encoding="utf-8")
        except (OSError, IndexError) as error:
            result = {
                "ok": False,
                "error": {"code": "output_error", "message": str(error)},
            }
            output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    sys.exit(0 if result.get("ok") else 1)
