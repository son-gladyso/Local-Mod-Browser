"""Small, dependency-free evidence helpers for reproducible local acceptance."""

import hashlib
import json
import pathlib
import platform
import sys

APP = pathlib.Path(__file__).resolve().parents[1]


def source_manifest():
    paths = (
        list(APP.glob("*.py"))
        + list((APP / "tests").glob("*.py"))
        + list((APP / "tests").glob("*.cjs"))
        + list((APP / "tools").glob("*.py"))
        + [
            p
            for p in (APP / "static").iterdir()
            if p.suffix in (".js", ".css", ".html", ".json")
        ]
        + list(APP.glob("requirements*.txt"))
        + [
            APP / "schemas.json",
            APP / "workflows.json",
            APP / "runtime-lock.json",
            APP / ".runtime" / "runtime-lock.json",
            APP / ".runtime" / "python.exe",
            APP / ".runtime" / "python313.dll",
            APP / ".runtime" / "sqlite3.dll",
        ]
    )
    files = {
        p.relative_to(APP).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
        if p.is_file()
    }
    return dict(
        files=files,
        sha256=hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        python=sys.version,
        platform=platform.platform(),
    )


def publish_json(path, data):
    path = pathlib.Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
