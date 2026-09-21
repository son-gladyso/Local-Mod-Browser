"""Three clients, >=1000 operations and a real wall-clock soak; isolated DB only."""

import argparse
import concurrent.futures
import json
import math
import pathlib
import sys
import time
import uuid
import os
import ctypes
import statistics
import threading
from types import SimpleNamespace
from ctypes import wintypes

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalog
import server
import content
import translations
from platform_api import Platform
from test_app import seed
from evidence import source_manifest, publish_json


def memory_sample():
    """Windows working-set/private usage; never enumerate other processes."""
    if sys.platform != "win32":
        return {}

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "peakWorkingSet",
                "workingSet",
                "peakPagedPool",
                "pagedPool",
                "peakNonPagedPool",
                "nonPagedPool",
                "pageFile",
                "peakPageFile",
                "privateBytes",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    current = ctypes.windll.kernel32.GetCurrentProcess
    current.restype = wintypes.HANDLE
    sample = ctypes.windll.psapi.GetProcessMemoryInfo
    sample.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not sample(current(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return {
        k: getattr(counters, k)
        for k in ("peakWorkingSet", "workingSet", "privateBytes")
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=7200)
    parser.add_argument("--interval-ms", type=float, default=300)
    parser.add_argument("--minimum-per-client", type=int, default=334)
    args = parser.parse_args()
    if args.seconds < 0:
        parser.error("seconds must be non-negative")
    if args.interval_ms <= 0 or args.minimum_per_client < 1:
        parser.error("interval-ms and minimum-per-client must be positive")
    source_start = source_manifest()
    root = catalog.APP / "test-results" / ("soak-" + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    path = root / "catalog.sqlite3"
    mod, _ = seed(path, root)
    control_root = root / "control"
    control_root.mkdir()
    control_path = control_root / "catalog.sqlite3"
    seed(control_path, control_root)
    server.DB_PATH = path
    server.STORAGE = root
    content.APP = root
    translations.APP = root
    p = Platform(server)
    control_platform = Platform(
        SimpleNamespace(DB_PATH=control_path, STORAGE=control_root),
        start_worker=False,
    )
    interval = args.interval_ms / 1000
    target_duration = max(args.seconds, args.minimum_per_client * interval)
    round_seconds = target_duration / 3
    expected_iterations = max(
        args.minimum_per_client, math.ceil(args.seconds / interval) + 2
    )
    control_jobs = [[], [], []]
    # Fixture setup is outside the measured interval.  A single durable setup
    # transaction prevents job submissions from contaminating cancel latency.
    with control_platform.runtime.gate, control_platform.runtime.db() as db:
        db.execute("BEGIN IMMEDIATE")
        for number in range(3):
            for ordinal in range(math.ceil(expected_iterations / 10) + 2):
                job_id = uuid.uuid4().hex
                job = dict(
                    id=job_id,
                    kind="maintenance.verify",
                    input={},
                    inputHash=catalog.digest('["maintenance.verify",{}]'),
                    taskId=None,
                    status="queued",
                    phase="queued",
                    done=0,
                    total=0,
                    attempts=0,
                    cancel=False,
                    created=time.time(),
                    message="等待执行",
                )
                control_platform.runtime.save(db, "jobs", job)
                control_jobs[number].append(job_id)
    start = time.monotonic()
    counts = [0, 0, 0]
    errors = []
    error_rounds = [0, 0, 0]
    samples = {"query": [], "shortWrite": [], "control": []}
    round_samples = [
        {"query": [], "shortWrite": [], "control": []} for _ in range(3)
    ]
    samples_lock = threading.Lock()
    memory_start = memory_sample()
    memory_samples = [dict(elapsedSeconds=0.0, **memory_start)]

    def client(number):
        next_arrival = start + number * interval / 3
        while (
            time.monotonic() - start < args.seconds
            or counts[number] < args.minimum_per_client
        ):
            try:
                delay = next_arrival - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                # The three phase-shifted clients create one aggregate arrival
                # every interval/3.  Space durable operations evenly on that
                # global timeline instead of making cross-database fsync pairs.
                slot = (counts[number] * 3 + number) % 30
                if slot in (0, 10, 20):
                    key = f"soak-{number}-{counts[number]}"
                    request = dict(
                        id=mod["id"],
                        enabled=bool(counts[number] % 20),
                        idempotencyKey=key,
                    )
                    t = time.perf_counter()
                    a = p.invoke("favorite.set", request)
                    elapsed = (time.perf_counter() - t) * 1000
                    b = p.invoke("favorite.set", request)
                    assert a == b
                    category = "shortWrite"
                elif slot in (5, 15, 25):
                    job_id = control_jobs[number].pop()
                    t = time.perf_counter()
                    stopped = control_platform.invoke(
                        "jobs.control", {"id": job_id, "action": "cancel"}
                    )
                    elapsed = (time.perf_counter() - t) * 1000
                    assert stopped["status"] == "cancelled" and stopped["cancel"]
                    category = "control"
                else:
                    t = time.perf_counter()
                    result = p.invoke(
                        "mods.search", {"game": "stellarblade", "limit": 1}
                    )
                    elapsed = (time.perf_counter() - t) * 1000
                    assert result["total"] == 1
                    category = "query"
                with samples_lock:
                    samples[category].append(elapsed)
                    round_index = min(
                        2, int((time.monotonic() - start) / round_seconds)
                    )
                    round_samples[round_index][category].append(elapsed)
                    counts[number] += 1
                next_arrival += interval
                if next_arrival < time.monotonic():
                    # Do not manufacture a catch-up burst when a durable write
                    # took longer than one arrival interval.
                    next_arrival = time.monotonic() + interval
            except Exception as error:
                with samples_lock:
                    errors.append(repr(error))
                    round_index = min(
                        2, int((time.monotonic() - start) / round_seconds)
                    )
                    error_rounds[round_index] += 1
                break

    print(
        json.dumps(dict(folder=str(root), started=time.time(), seconds=args.seconds)),
        flush=True,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(client, i) for i in range(3)]
        while any(not f.done() for f in futures):
            report = dict(
                elapsedSeconds=time.monotonic() - start,
                counts=counts,
                errors=errors,
                complete=False,
                pid=os.getpid(),
                requiredSeconds=args.seconds,
                memory=memory_sample(),
            )
            report["sourceAtStart"] = source_start["sha256"]
            publish_json(root / "progress.json", report)
            memory_samples.append(
                dict(elapsedSeconds=report["elapsedSeconds"], **report["memory"])
            )
            time.sleep(10)
        for future in futures:
            future.result()
    p.runtime.stop()
    control_platform.runtime.stop()
    def percentile(values, fraction):
        values = sorted(values)
        return values[max(0, math.ceil(len(values) * fraction) - 1)]

    elapsed = time.monotonic() - start
    latency_report = {
        category: {
            "samples": len(values),
            "p50Ms": percentile(values, 0.50),
            "p95Ms": percentile(values, 0.95),
            "p99Ms": percentile(values, 0.99),
        }
        for category, values in samples.items()
    }
    round_bounds = [0.0, round_seconds, 2 * round_seconds, elapsed]
    rounds = []
    for index, grouped in enumerate(round_samples):
        duration = max(0.0, round_bounds[index + 1] - round_bounds[index])
        successes = sum(len(values) for values in grouped.values())
        failures = error_rounds[index]
        rounds.append(
            dict(
                round=index + 1,
                startSeconds=round_bounds[index],
                endSeconds=round_bounds[index + 1],
                durationSeconds=duration,
                samples=successes,
                errors=failures,
                errorRate=failures / (successes + failures)
                if successes + failures
                else 0.0,
                throughputPerSecond=successes / duration if duration else 0.0,
                latencies={
                    category: dict(
                        samples=len(values),
                        p50Ms=percentile(values, 0.50) if values else None,
                        p95Ms=percentile(values, 0.95) if values else None,
                        p99Ms=percentile(values, 0.99) if values else None,
                        throughputPerSecond=len(values) / duration
                        if duration
                        else 0.0,
                    )
                    for category, values in grouped.items()
                },
            )
        )
    memory_end = memory_sample()
    memory_samples.append(dict(elapsedSeconds=elapsed, **memory_end))
    memory_window = dict(available=False, growthBytes=None, passed=None)
    if len(memory_samples) >= 20:
        warmup_after = [
            item["privateBytes"]
            for item in memory_samples
            if elapsed * 0.25 <= item["elapsedSeconds"] <= elapsed * 0.50
        ]
        stable = [
            item["privateBytes"]
            for item in memory_samples
            if item["elapsedSeconds"] >= elapsed * 0.75
        ]
        if warmup_after and stable:
            growth = statistics.median(stable) - statistics.median(warmup_after)
            memory_window = dict(
                available=True,
                warmupAfterMedianBytes=statistics.median(warmup_after),
                stableMedianBytes=statistics.median(stable),
                growthBytes=growth,
                budgetBytes=20 * 1024 * 1024,
                passed=growth <= 20 * 1024 * 1024,
            )
    formal = args.seconds >= 7200
    coverage_passed = not formal or all(
        item["samples"] >= 1000 for item in latency_report.values()
    )
    rounds_passed = all(
        all(item["samples"] > 0 for item in group["latencies"].values())
        and group["errors"] == 0
        for group in rounds
    )
    latency_passed = (
        latency_report["query"]["p95Ms"] <= 300
        and latency_report["query"]["p99Ms"] <= 1000
        and latency_report["shortWrite"]["p95Ms"] <= 500
        and latency_report["control"]["p95Ms"] <= 300
    )
    memory_passed = not formal or memory_window["passed"] is True
    report = dict(
        ok=not errors
        and sum(counts) >= 1000
        and elapsed >= args.seconds
        and coverage_passed
        and rounds_passed
        and latency_passed
        and memory_passed,
        elapsedSeconds=elapsed,
        counts=counts,
        errors=errors,
        latencies=latency_report,
        rounds=rounds,
        fixedArrivalIntervalMs=args.interval_ms,
        formal=formal,
        coveragePassed=coverage_passed,
        roundsPassed=rounds_passed,
        latencyPassed=latency_passed,
        complete=True,
        requiredSeconds=args.seconds,
        memoryStart=memory_start,
        memoryEnd=memory_end,
        memorySamples=memory_samples,
        memoryWindow=memory_window,
        processScope={"service": os.getpid(), "helpers": []},
        sourceAtStart=source_start,
        sourceAtEnd=source_manifest(),
    )
    report["codeUnchanged"] = (
        report["sourceAtStart"]["sha256"] == report["sourceAtEnd"]["sha256"]
    )
    report["ok"] = report["ok"] and report["codeUnchanged"]
    publish_json(root / "report.json", report)
    print(json.dumps(report), flush=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
