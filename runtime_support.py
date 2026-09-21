"""Selection and verification of the project-local Windows runtime."""

from __future__ import annotations

import os
import pathlib
import platform
import sqlite3
import sys


APP = pathlib.Path(__file__).resolve().parent
RUNTIME = APP / ".runtime"
PYTHON_VERSION = "3.13.15"
SQLITE_VERSION = "3.53.4"


def executable():
    return RUNTIME / ("python.exe" if os.name == "nt" else "python")


def verify_loaded():
    actual_python = platform.python_version()
    actual_sqlite = sqlite3.sqlite_version
    actual_bits = platform.architecture()[0]
    if (actual_python, actual_sqlite, actual_bits) != (
        PYTHON_VERSION,
        SQLITE_VERSION,
        "64bit",
    ):
        raise RuntimeError(
            "运行时版本不符："
            f"Python {actual_python} / SQLite {actual_sqlite} / {actual_bits}；"
            f"要求 Python {PYTHON_VERSION} / SQLite {SQLITE_VERSION} / 64bit。"
        )
    return {
        "python": actual_python,
        "sqlite": actual_sqlite,
        "architecture": actual_bits,
        "executable": str(pathlib.Path(sys.executable).resolve()),
    }


def ensure_pinned_process(*, required):
    """Re-exec through the pinned interpreter, or fail for a formal entrypoint."""
    pinned = executable()
    if pinned.is_file():
        if pathlib.Path(sys.executable).resolve() != pinned.resolve():
            os.execv(str(pinned), [str(pinned), *sys.argv])
        return verify_loaded()
    if required:
        raise RuntimeError(
            "缺少项目专用运行时；请先运行 "
            "python tools/bootstrap_runtime.py"
        )
    return None
