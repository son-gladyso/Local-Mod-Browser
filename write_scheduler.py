"""Re-entrant FIFO foreground/background write gate with bounded starvation."""

from __future__ import annotations

import collections
import threading
import time


class FairWriteGate:
    """Admit FIFO writers with a four-foreground to one-background policy."""

    def __init__(self, foreground_ratio=4, background_max_wait=2.0):
        self.foreground_ratio = foreground_ratio
        self.background_max_wait = background_max_wait
        self.condition = threading.Condition()
        self.owner = None
        self.depth = 0
        self.foreground = collections.deque()
        self.background = collections.deque()
        self.foreground_streak = 0
        self.last_grant_background = False
        self.sequence = 0

    @property
    def foreground_waiters(self):
        return len(self.foreground)

    @property
    def background_waiters(self):
        return len(self.background)

    def _background_due(self, now=None):
        if not self.background:
            return False
        now = time.monotonic() if now is None else now
        return self.foreground_streak >= self.foreground_ratio or (
            now - self.background[0][1] >= self.background_max_wait
        )

    def _selected_queue(self, now):
        # An aged background head may jump ahead once, but cannot turn a busy
        # background queue into a run of consecutive batches while an
        # interactive write is waiting.
        if self.foreground and self.last_grant_background:
            return self.foreground
        if self._background_due(now):
            return self.background
        if self.foreground:
            return self.foreground
        return self.background

    def acquire(self, blocking=True, timeout=-1, *, background=False):
        identity = threading.get_ident()
        with self.condition:
            if self.owner == identity:
                self.depth += 1
                return True
            if not blocking:
                timeout = 0
            deadline = (
                None if timeout is None or timeout < 0 else time.monotonic() + timeout
            )
            self.sequence += 1
            waiter = (self.sequence, time.monotonic(), identity)
            queue = self.background if background else self.foreground
            queue.append(waiter)
            try:
                while True:
                    now = time.monotonic()
                    selected = self._selected_queue(now)
                    if self.owner is None and selected and selected[0] is waiter:
                        queue.popleft()
                        self.owner = identity
                        self.depth = 1
                        if background:
                            self.foreground_streak = 0
                        else:
                            self.foreground_streak += 1
                        self.last_grant_background = background
                        return True
                    if deadline is not None:
                        remaining = deadline - now
                        if remaining <= 0:
                            queue.remove(waiter)
                            self.condition.notify_all()
                            return False
                    else:
                        remaining = None
                    self.condition.wait(remaining)
            except BaseException:
                if waiter in queue:
                    queue.remove(waiter)
                    self.condition.notify_all()
                raise

    def release(self):
        identity = threading.get_ident()
        with self.condition:
            if self.owner != identity:
                raise RuntimeError("cannot release an unowned write gate")
            self.depth -= 1
            if not self.depth:
                self.owner = None
                self.condition.notify_all()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_args):
        self.release()
