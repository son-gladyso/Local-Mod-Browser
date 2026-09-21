"""Small in-process latency registry with privacy-safe diagnostic snapshots."""

from __future__ import annotations

import contextvars
import json
import math
import os
import pathlib
import threading
import time
from collections import defaultdict, deque


REQUEST_ID = contextvars.ContextVar("request_id", default="")


def set_request_id(value: str):
    return REQUEST_ID.set(value)


def reset_request_id(token) -> None:
    REQUEST_ID.reset(token)


def request_id() -> str:
    return REQUEST_ID.get()


class Metrics:
    """Aggregate monotonic durations; never retain request bodies or paths."""

    def __init__(
        self,
        log_path: pathlib.Path | None = None,
        *,
        maximum=20000,
        maximum_log_bytes=5 * 1024 * 1024,
    ):
        self.log_path = pathlib.Path(log_path) if log_path else None
        self.maximum = maximum
        self.maximum_log_bytes = maximum_log_bytes
        self.lock = threading.Lock()
        self.samples = deque(maxlen=self.maximum)
        self.recent = deque(maxlen=100)
        self.last_flush = time.monotonic()
        self.flush_running = False

    def observe(self, operation: str, phase: str, seconds: float, **dimensions) -> None:
        now = time.time()
        milliseconds = max(0.0, seconds * 1000)
        safe_dimensions = {
            key: value
            for key, value in dimensions.items()
            if isinstance(value, (str, int, float, bool))
        }
        with self.lock:
            self.samples.append(
                (now, operation, phase, milliseconds, safe_dimensions)
            )
            self.recent.append(
                {
                    "requestId": request_id(),
                    "operation": operation,
                    "phase": phase,
                    "milliseconds": round(milliseconds, 3),
                    "at": now,
                    **safe_dimensions,
                }
            )
            due = (
                time.monotonic() - self.last_flush >= 60 and not self.flush_running
            )
            if due:
                self.last_flush = time.monotonic()
                self.flush_running = True
        if due:
            threading.Thread(target=self._flush_worker, daemon=True).start()

    @staticmethod
    def percentile(values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = max(0, math.ceil(percentile * len(ordered)) - 1)
        return round(ordered[index], 3)

    def snapshot(self, window_seconds=300, *, include_recent=True) -> dict:
        cutoff = time.time() - window_seconds
        with self.lock:
            samples = [sample for sample in self.samples if sample[0] >= cutoff]
            recent = list(self.recent) if include_recent else []
        grouped = defaultdict(list)
        results = defaultdict(lambda: defaultdict(list))
        for _at, operation, phase, value, dimensions in samples:
            grouped[(operation, phase)].append(value)
            if dimensions.get("result"):
                results[(operation, phase)][dimensions["result"]].append(value)
        operations = {}
        for (operation, phase), values in grouped.items():
            if not values:
                continue
            summary = {
                "samples": len(values),
                "p50Ms": self.percentile(values, 0.50),
                "p95Ms": self.percentile(values, 0.95),
                "p99Ms": self.percentile(values, 0.99),
                "maxMs": round(max(values), 3),
            }
            if results[(operation, phase)]:
                summary["byResult"] = {
                    result: {
                        "samples": len(group),
                        "p50Ms": self.percentile(group, 0.50),
                        "p95Ms": self.percentile(group, 0.95),
                        "p99Ms": self.percentile(group, 0.99),
                    }
                    for result, group in results[(operation, phase)].items()
                }
                failures = sum(
                    len(group)
                    for result, group in results[(operation, phase)].items()
                    if result not in ("success", "idempotent_replay")
                )
                summary["errorRate"] = round(failures / len(values), 6)
            operations.setdefault(operation, {})[phase] = summary
        return {
            "windowSeconds": window_seconds,
            "generatedAt": time.time(),
            "operations": operations,
            "recent": recent,
        }

    def _flush_worker(self):
        try:
            self.flush()
        finally:
            with self.lock:
                self.flush_running = False

    def flush(self) -> None:
        if not self.log_path:
            return
        payload = self.snapshot(300, include_recent=False)
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if (
                self.log_path.exists()
                and self.log_path.stat().st_size >= self.maximum_log_bytes
            ):
                for index in range(2, 0, -1):
                    source = self.log_path.with_suffix(
                        self.log_path.suffix + f".{index}"
                    )
                    target = self.log_path.with_suffix(
                        self.log_path.suffix + f".{index + 1}"
                    )
                    if source.exists():
                        os.replace(source, target)
                os.replace(
                    self.log_path,
                    self.log_path.with_suffix(self.log_path.suffix + ".1"),
                )
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            # Diagnostics must never make a business operation fail.
            return
