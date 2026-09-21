"""Three HTTP clients exercise >1,000 collaboration operations on a fixture DB.

Lease expiry is injected only into this script's isolated runtime database.
Everything else, including conflict/cancel checks, goes through the public API.
"""

# ruff: noqa: E402 -- standalone script adds the project import root

import argparse
import collections
import concurrent.futures
import json
import pathlib
import sys
import threading
import time
import uuid
from http.server import ThreadingHTTPServer

APP = pathlib.Path(__file__).resolve().parents[1]
TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(APP))
import content
import server
import translations
from ai import v2_request
from platform_api import Platform
from test_app import seed
from soak_platform import memory_sample
from evidence import source_manifest, publish_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=30)
    args = parser.parse_args()
    root = APP / "test-results" / ("collaboration-" + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    path = root / "catalog.sqlite3"
    mod, _ = seed(path, root)
    server.DB_PATH, server.STORAGE = path, root
    content.APP = translations.APP = root
    platform = server.PLATFORM = Platform(server)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    info = dict(url=f"http://127.0.0.1:{httpd.server_port}", token=server.TOKEN)
    barrier = threading.Barrier(3, timeout=45)
    lock = threading.Lock()
    counts = collections.Counter()
    durations = []
    errors = []
    winners = collections.Counter()
    initial_memory = memory_sample()
    started = time.monotonic()
    source_start = source_manifest()

    def call(name, params, expected=None):
        t = time.perf_counter()
        response = v2_request(info, name, params)
        with lock:
            counts[name] += 1
            durations.append((time.perf_counter() - t) * 1000)
        if expected:
            assert not response["ok"] and response["error"]["code"] == expected, (
                response
            )
            with lock:
                counts["expected:" + expected] += 1
            return response
        assert response["ok"], response
        return response["data"]

    def client(number):
        try:
            for round_no in range(args.rounds):
                identity = f"{number}-{round_no}"
                task = call(
                    "tasks.create",
                    dict(
                        title="HTTP 协作 " + identity,
                        goal="隔离库并发资料整理",
                        scope=dict(
                            game="stellarblade",
                            resources=[mod["id"]],
                            fields=["function"],
                            operations=["content.preview", "content.apply"],
                        ),
                        acceptance=[dict(kind="receipts")],
                        idempotencyKey="create-" + identity,
                    ),
                )
                lease = call(
                    "tasks.claim", dict(id=task["id"], owner="client-" + str(number))
                )["lease"]
                call(
                    "tasks.claim",
                    dict(id=task["id"], owner="contender"),
                    "task_unavailable",
                )
                call("tasks.renew", dict(lease=lease))
                resource = call("resources.read", dict(ids=[mod["id"]]))["items"][0]
                barrier.wait()  # All clients must edit the same source revision.
                preview = call(
                    "content.preview",
                    dict(
                        lease=lease,
                        records=[
                            dict(
                                resourceId=mod["id"],
                                baseRevision=resource["revision"],
                                patch=dict(function="并发资料整理 " + identity),
                                note="synthetic HTTP acceptance",
                            )
                        ],
                    ),
                )
                barrier.wait()
                request = dict(
                    lease=lease,
                    previewId=preview["previewId"],
                    idempotencyKey="apply-" + identity,
                )
                response = v2_request(info, "content.apply", request)
                with lock:
                    counts["content.apply"] += 1
                if response["ok"]:
                    with lock:
                        winners[round_no] += 1
                    replay = call("content.apply", request)
                    assert replay == response["data"]
                    call(
                        "content.apply",
                        dict(request, previewId="different"),
                        "idempotency_conflict",
                    )
                else:
                    assert response["error"]["code"] == "revision_conflict", response
                    with lock:
                        counts["expected:revision_conflict"] += 1
                call(
                    "tasks.checkpoint",
                    dict(lease=lease, checkpoint=dict(round=round_no)),
                )
                # Deterministically simulate five minutes offline without delaying every round.
                with platform.runtime.gate, platform.runtime.db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    expired = platform.runtime.read("tasks", task["id"], db)
                    expired["expires"] = time.time() - 1
                    platform.runtime.save(db, "tasks", expired)
                replacement = call(
                    "tasks.claim", dict(id=task["id"], owner="replacement")
                )["lease"]
                assert replacement["generation"] > lease["generation"]
                call(
                    "tasks.checkpoint",
                    dict(lease=lease, checkpoint={}),
                    "lease_expired",
                )
                call("tasks.context", dict(id=task["id"]))
                call("tasks.control", dict(id=task["id"], action="cancel"))
                call("tasks.renew", dict(lease=replacement), "lease_expired")
                call(
                    "tasks.claim",
                    dict(id=task["id"], owner="after-cancel"),
                    "task_unavailable",
                )
                barrier.wait()  # No next-round writes until all conflicts are checked.
                if number == 0:
                    with lock:
                        publish_json(
                            root / "progress.json",
                            dict(
                                round=round_no + 1,
                                rounds=args.rounds,
                                counts=dict(counts),
                                errors=errors,
                            ),
                        )
        except Exception as error:
            with lock:
                errors.append(dict(client=number, error=repr(error)))
            barrier.abort()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(client, range(3)))
        total = sum(
            value for key, value in counts.items() if not key.startswith("expected:")
        )
        assert not errors, errors
        assert len(winners) == args.rounds and set(winners.values()) == {1}, dict(
            winners
        )
        assert counts["expected:revision_conflict"] == args.rounds * 2
        assert total >= 1000, total
        ok = True
    except Exception as error:
        errors.append(dict(error=repr(error)))
        ok = False
    finally:
        httpd.shutdown()
        httpd.server_close()
        platform.runtime.stop()
    report = dict(
        ok=ok,
        clients=3,
        rounds=args.rounds,
        operations=total,
        counts=dict(counts),
        oneWinnerPerRound=dict(winners),
        errors=errors,
        elapsedSeconds=time.monotonic() - started,
        requestP95Ms=sorted(durations)[int(len(durations) * 0.95)]
        if durations
        else None,
        memoryStart=initial_memory,
        memoryEnd=memory_sample(),
        scope="synthetic fixture; expiry injected only in isolated runtime",
        sourceAtStart=source_start,
        sourceAtEnd=source_manifest(),
    )
    report["codeUnchanged"] = (
        report["sourceAtStart"]["sha256"] == report["sourceAtEnd"]["sha256"]
    )
    report["ok"] = report["ok"] and report["codeUnchanged"]
    publish_json(root / "report.json", report)
    print(json.dumps(dict(folder=str(root), **report), ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
