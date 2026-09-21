"""Double-click launcher: single service, no terminal window, standard-library only."""

from __future__ import annotations
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
import webbrowser

APP = pathlib.Path(__file__).resolve().parent


def running():
    try:
        info = json.loads((APP / "data/runtime.json").read_text(encoding="utf-8"))
        if not info["url"].startswith("http://127.0.0.1:"):
            return None
        with urllib.request.urlopen(info["url"] + "/api/health", timeout=1) as response:
            data = json.load(response)
        health = data.get("data", {})
        if health.get("service") != "local-mod-browser":
            return None
        from runtime_support import PYTHON_VERSION, SQLITE_VERSION

        if (health.get("pythonVersion"), health.get("sqliteVersion")) != (
            PYTHON_VERSION,
            SQLITE_VERSION,
        ):
            raise RuntimeError(
                "已运行的旧服务未使用固定运行时；请先关闭旧服务再重试。"
            )
        return info
    except (OSError, ValueError, KeyError):
        return None


def start(open_browser=True):
    from runtime_support import ensure_pinned_process

    ensure_pinned_process(required=True)
    folder = APP / "data"
    folder.mkdir(exist_ok=True)
    lock = (folder / "launcher.lock").open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            lock.seek(0)
            lock.write(b"0")
            lock.flush()
            lock.seek(0)
            for attempt in range(100):
                try:
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("另一个启动程序尚未完成，请稍后重试。")
        info = running()
        if not info:
            # Resolve a paired restore before either database is opened.
            from restore_platform import recover_interrupted

            recover_interrupted(folder)
            executable = pathlib.Path(sys.executable)
            pythonw = executable.with_name("pythonw.exe")
            if os.name == "nt" and pythonw.exists():
                executable = pythonw
            with (folder / "server.log").open("ab") as log:
                subprocess.Popen(
                    [str(executable), str(APP / "server.py")],
                    cwd=APP,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            for _ in range(150):
                info = running()
                if info:
                    break
                time.sleep(0.1)
            if not info:
                raise RuntimeError("服务未能启动，请检查 data/server.log。")
        if open_browser:
            webbrowser.open(info["url"])
        return info
    finally:
        lock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        value = start(not args.no_browser)
        if sys.stdout:
            print(value["url"])
    except Exception as error:
        if sys.stderr:
            print(str(error), file=sys.stderr)
        if os.name == "nt" and not args.no_browser:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, str(error), "本地 MOD 浏览器", 0x10)
        sys.exit(1)
