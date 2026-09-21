"""Install and verify the locked CPython/SQLite runtime without global changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import urllib.request
import uuid
import zipfile


APP = pathlib.Path(__file__).resolve().parents[1]
LOCK = APP / "runtime-lock.json"
TARGET = APP / ".runtime"
CACHE = APP / "test-results" / "runtime-cache"


def digest(path, algorithm):
    value = hashlib.new(algorithm)
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def fetch(component):
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / component["archive"]
    algorithm = "sha256" if "sha256" in component else "sha3_256"
    expected = component[algorithm]
    if target.is_file() and digest(target, algorithm) == expected:
        return target
    temporary = target.with_suffix(target.suffix + ".download")
    request = urllib.request.Request(
        component["url"], headers={"User-Agent": "local-mod-browser-runtime/1"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
    if digest(temporary, algorithm) != expected:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(component["archive"] + " 校验失败")
    temporary.replace(target)
    return target


def configure_paths(folder):
    path_file = next(folder.glob("python*._pth"))
    lines = [
        line.strip()
        for line in path_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and line.strip() != "#import site"
    ]
    for value in (
        "..",
        "../.venv-mcp/Lib/site-packages",
        "../.venv-mcp/Lib/site-packages/win32",
        "../.venv-mcp/Lib/site-packages/win32/lib",
        "../.venv-mcp/Lib/site-packages/pywin32_system32",
        "import site",
    ):
        if value not in lines:
            lines.append(value)
    path_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify(folder, lock):
    script = r'''
import json, os, pathlib, shutil, sqlite3, sys
from contextlib import closing
root = pathlib.Path.cwd() / "test-results" / ("runtime-self-check-" + str(os.getpid()))
root.mkdir()
source = root / "source.sqlite3"
target = root / "backup.sqlite3"
with closing(sqlite3.connect(source)) as db:
    wal = db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    db.execute("PRAGMA synchronous=FULL")
    synchronous = db.execute("PRAGMA synchronous").fetchone()[0]
    parsed = db.execute("SELECT json_extract('{\"ready\":true}','$.ready')").fetchone()[0]
    db.execute("CREATE TABLE sample(value TEXT)")
    db.execute("INSERT INTO sample VALUES('ok')")
    db.commit()
    with closing(sqlite3.connect(target)) as other:
        db.backup(other)
    db.interrupt()
with closing(sqlite3.connect(target)) as db:
    backup = db.execute("SELECT value FROM sample").fetchone()[0]
shutil.rmtree(root)
print(json.dumps({"python":sys.version.split()[0],"sqlite":sqlite3.sqlite_version,"wal":wal,"synchronous":synchronous,"json":parsed,"backup":backup,"interrupt":hasattr(sqlite3.Connection,"interrupt")}))
'''
    result = subprocess.run(
        [str(folder / "python.exe"), "-c", script],
        cwd=APP,
        capture_output=True,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.decode(errors="replace").strip() or "运行时自检失败"
        )
    output = result.stdout.decode("utf-8")
    report = json.loads(output)
    expected = (lock["python"]["version"], lock["sqlite"]["version"])
    if (report["python"], report["sqlite"]) != expected:
        raise RuntimeError("加载的 Python/SQLite 版本不符：" + output)
    checks = {"wal": "wal", "synchronous": 2, "json": 1, "backup": "ok", "interrupt": True}
    if any(report.get(key) != value for key, value in checks.items()):
        raise RuntimeError("运行时 SQLite 能力自检失败：" + output)
    return report


def install(replace=False):
    if sys.platform != "win32":
        raise RuntimeError("当前锁定包仅支持 Windows x64")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if TARGET.exists() and not replace:
        try:
            return verify(TARGET, lock)
        except Exception:
            raise RuntimeError("已有运行时校验失败；核对后使用 --replace")
    python_zip = fetch(lock["python"])
    sqlite_zip = fetch(lock["sqlite"])
    staging = APP / (".runtime.installing-" + uuid.uuid4().hex)
    previous = APP / (".runtime.previous-" + uuid.uuid4().hex)
    staging.mkdir()
    try:
        with zipfile.ZipFile(python_zip) as archive:
            archive.extractall(staging)
        with zipfile.ZipFile(sqlite_zip) as archive:
            names = {pathlib.PurePosixPath(name).name: name for name in archive.namelist()}
            with archive.open(names["sqlite3.dll"]) as source:
                with (staging / "sqlite3.dll").open("wb") as output:
                    shutil.copyfileobj(source, output)
        configure_paths(staging)
        (staging / "runtime-lock.json").write_text(
            json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        report = verify(staging, lock)
        (staging / "verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        had_previous = TARGET.exists()
        if had_previous:
            TARGET.replace(previous)
        try:
            staging.replace(TARGET)
        except Exception:
            if had_previous and previous.exists() and not TARGET.exists():
                previous.replace(TARGET)
            raise
        if previous.exists():
            shutil.rmtree(previous)
        return report
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps({"ok": True, "data": install(args.replace)}))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1)
