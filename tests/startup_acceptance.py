"""Measure process startup against an existing index in a disposable copy."""

import json
import pathlib
import sqlite3
import subprocess
import sys
import time
import urllib.request
import uuid
from contextlib import closing

TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
from evidence import APP, publish_json, source_manifest


def main():
    root = APP / "test-results" / ("startup-" + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    # Online backup reads the source; tests never start a service on formal data.
    source = (APP / "data/catalog.sqlite3").as_uri() + "?mode=ro"
    with closing(sqlite3.connect(source, uri=True)) as db:
        with closing(sqlite3.connect(root / "catalog.sqlite3")) as target:
            db.backup(target)
    report = dict(sourceAtStart=source_manifest(), samples=[], errors=[])
    # First start includes first-time platform migration and its backup. It is
    # recorded separately from the <=5s existing-index restart requirement.
    for stage in ("migration", "existing_index_1", "existing_index_2"):
        runtime = root / (stage + "-runtime.json")
        with (root / (stage + ".log")).open("wb") as log:
            started = time.perf_counter()
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(APP / "server.py"),
                    "--db",
                    str(root / "catalog.sqlite3"),
                    "--runtime",
                    str(runtime),
                    "--no-auto-index",
                ],
                cwd=APP,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Service exited during " + stage)
                    try:
                        info = json.loads(runtime.read_text(encoding="utf-8"))
                        with urllib.request.urlopen(
                            info["url"] + "/api/health", timeout=1
                        ) as response:
                            assert json.load(response)["ok"]
                        break
                    except (OSError, ValueError):
                        if time.perf_counter() - started > 45:
                            raise TimeoutError("Service startup timed out")
                        time.sleep(0.05)
                elapsed = time.perf_counter() - started
                report["samples"].append(dict(stage=stage, seconds=elapsed))
                request = urllib.request.Request(
                    info["url"] + "/api/v2/service.stop",
                    data=b'{"confirm":true}',
                    headers={
                        "Content-Type": "application/json",
                        "X-Mod-Token": info["token"],
                    },
                )
                with urllib.request.urlopen(request, timeout=10) as response:
                    assert json.load(response)["ok"]
                process.wait(timeout=15)
            except Exception as error:
                report["errors"].append(str(error))
                break
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
    report["sourceAtEnd"] = source_manifest()
    report["ok"] = (
        not report["errors"]
        and len(report["samples"]) == 3
        and all(s["seconds"] <= 5 for s in report["samples"][1:])
        and report["sourceAtStart"]["sha256"] == report["sourceAtEnd"]["sha256"]
    )
    publish_json(root / "report.json", report)
    print(json.dumps(dict(folder=str(root), **report), ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
