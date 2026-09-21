"""CLI + HTTP + real-data reindex checks against an isolated running service."""

import json
import pathlib
import subprocess
import sys
import time
import urllib.request
import urllib.error

APP = pathlib.Path(__file__).resolve().parents[1]
runtime = pathlib.Path(sys.argv[1])
assert runtime.resolve().is_relative_to(APP / "test-results")
info = json.loads(runtime.read_text(encoding="utf-8"))
folder = runtime.parent


def cli(*args, ok=True):
    p = subprocess.run(
        [sys.executable, "ai.py", "--runtime", str(runtime), *args],
        cwd=APP,
        capture_output=True,
        encoding="utf-8",
    )
    result = json.loads(p.stdout)
    assert result["ok"] == ok, (args, result, p.stderr)
    assert p.returncode == (0 if ok else 1), (args, p.returncode)
    return result.get("data", result)


def call(route, payload):
    request = folder / "request.json"
    request.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return cli("call", "POST", route, "--input", str(request))


baseline = cli('status')
games = cli('games')
assert games and all(game['count'] > 0 for game in games)
assert cli("search", "1401", "--game", "stellarblade")["total"] >= 1
assert cli("schema")["schemaVersion"] == 1
cli("show", "missing", ok=False)
export = cli("content-export", "--game", "stellarblade")
output = folder / "catalog-export.jsonl"
if output.exists():
    output = folder / ("catalog-export-" + str(time.time_ns()) + ".jsonl")
cli("download", export["download"], str(output))
assert len(output.read_text(encoding="utf-8").splitlines()) == next(g['count'] for g in games if g['id']=='stellarblade')
assert (
    json.loads(output.read_text(encoding="utf-8").splitlines()[0])["schemaVersion"] == 1
)
resource = cli("resource", "stellarblade:1401")
edit = folder / "edit.json"
edit.write_text(
    json.dumps(
        [
            {
                "resourceId": resource["resourceId"],
                "baseRevision": resource["revision"],
                "patch": {"function": "集成回归保留内容"},
                "note": "test copy only",
            }
        ],
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
preview = cli("edit-preview", str(edit))
assert preview["valid"] == 1
cli("edit-apply", preview["previewId"])
cli("edit-apply", preview["previewId"], ok=False)
for headers in (
    {},
    {"X-Mod-Token": info["token"], "Origin": "https://untrusted.invalid"},
):
    req = urllib.request.Request(
        info["url"] + "/api/favorite", data=b"{}", headers=headers
    )
    try:
        urllib.request.urlopen(req)
        raise AssertionError("unauthorized write accepted")
    except urllib.error.HTTPError as e:
        assert e.code == 403
profiles = cli("profiles")
before = {
    p["id"]: cli("call", "GET", "/api/profile?id=" + p["id"])["items"] for p in profiles
}
job = call("/api/reindex", {})
result = cli("wait", job["id"], "--timeout", "60")
assert result["result"]["mods"] == baseline['mods']
assert cli("resource", "stellarblade:1401")["data"]["function"] == "集成回归保留内容"
for pid, items in before.items():
    assert cli("call", "GET", "/api/profile?id=" + pid)["items"] == items
pilot = call("/api/translations/export", {"pilot": True})
result = cli("wait", pilot["id"], "--timeout", "60")
assert result["done"] == result["total"] == 12
assert 0 < result["result"]["mods"] <= 12
assert result["result"]["segments"] > 0
backup = call("/api/backup", {})
assert pathlib.Path(backup["path"]).is_file()
report = {
    "ok": True,
    "checks": [
        "CLI JSON and exit codes",
        "schema",
        "content JSONL download",
        "preview and single-use apply",
        "unauthorized and cross-origin writes rejected",
        "real reindex preserves edits and exact profiles",
        "12 candidate MOD pilot export with pending segments",
        "online SQLite backup",
    ],
    "pilot": result["result"],
    "profiles": len(profiles),
}
(folder / "integration-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False))
