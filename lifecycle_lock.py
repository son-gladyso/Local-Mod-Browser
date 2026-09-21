"""Cross-process lock protecting one catalog/runtime database directory."""

from __future__ import annotations

import contextlib
import os
import pathlib
import time


class LifecycleLockBusy(RuntimeError):
    pass


class DirectoryLock:
    def __init__(self, folder, *, timeout=0, purpose="operation"):
        self.folder = pathlib.Path(folder).resolve()
        self.timeout = timeout
        self.purpose = purpose
        self.stream = None

    def acquire(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / "platform-lifecycle.lock"
        self.stream = path.open("a+b")
        self.stream.seek(0, os.SEEK_END)
        if self.stream.tell() == 0:
            self.stream.write(b"0")
            self.stream.flush()
        deadline = None if self.timeout is None else time.monotonic() + self.timeout
        while True:
            try:
                self.stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError as error:
                if deadline is not None and time.monotonic() >= deadline:
                    self.stream.close()
                    self.stream = None
                    raise LifecycleLockBusy(
                        f"数据目录正在被其他服务或恢复工具使用：{self.folder}"
                    ) from error
                time.sleep(0.05)

    def release(self):
        if not self.stream:
            return
        try:
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        finally:
            self.stream.close()
            self.stream = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *_args):
        self.release()


@contextlib.contextmanager
def directory_lock(folder, *, timeout=0, purpose="operation"):
    lock = DirectoryLock(folder, timeout=timeout, purpose=purpose)
    with lock:
        yield lock
