"""Isolated platform contracts, fencing, receipts and interchange regression."""

import concurrent.futures
import copy
import json
import pathlib
import sqlite3
import sys
import time
import unittest
import uuid
import subprocess
import threading
from contextlib import closing, contextmanager
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalog
import server
import content
import interchange
import translations
import workflows
from contracts import OPS, Problem, openapi
from platform_api import Platform, pack
from test_app import seed


class PlatformTest(unittest.TestCase):
    def setUp(self):
        self.root = catalog.APP / "test-results" / ("platform-" + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.path = self.root / "catalog.sqlite3"
        self.mod, self.archive = seed(self.path, self.root)
        self.patches = [
            patch.object(server, "DB_PATH", self.path),
            patch.object(server, "STORAGE", self.root),
            patch.object(content, "APP", self.root),
            patch.object(translations, "APP", self.root),
            patch.object(server, "PLATFORM", None),
        ]
        for p in self.patches:
            p.start()
        self.p = Platform(server, start_worker=False)

    def tearDown(self):
        self.p.runtime.stop()
        for p in reversed(self.patches):
            p.stop()

    def invoke(self, operation, **args):
        return self.p.invoke(operation, args)

    def copy_valid_pair(self, destination):
        destination.mkdir(parents=True, exist_ok=True)
        with catalog.connect(self.path) as source:
            with closing(sqlite3.connect(destination / "catalog.sqlite3")) as target:
                source.backup(target)
        with self.p.runtime.db() as source:
            with closing(
                sqlite3.connect(destination / "work-runtime.sqlite3")
            ) as target:
                source.backup(target)
        return {
            name: (destination / name).read_bytes()
            for name in ("catalog.sqlite3", "work-runtime.sqlite3")
        }

    def test_contract_search_text_cursor(self):
        self.assertEqual(set(openapi()["paths"]), {x["path"] for x in OPS.values()})
        with self.assertRaises(Problem) as caught:
            self.invoke("mods.search", typo=True)
        self.assertEqual(caught.exception.code, "unknown_parameter")
        self.assertEqual(self.invoke("mods.search", tag="框架")["total"], 1)
        r = self.invoke(
            "resources.read", ids=[self.mod["id"]], fields=["details"], budget=2000
        )
        self.assertEqual(r["items"][0]["deferred"][0]["field"], "details")
        text = ""
        offset = 0
        revision = None
        while True:
            args = dict(id=self.mod["id"], field="details", offset=offset, budget=2000)
            if revision:
                args["revision"] = revision
            data = self.invoke("resources.text", **args)
            text += data["text"]
            revision = data["revision"]
            offset = data["nextOffset"]
            if offset is None:
                break
        self.assertEqual(text, self.mod["details"])

    def test_runtime_events_are_ordered_cursor_pages_and_support_tail(self):
        jobs = [
            self.invoke("catalog.export", game="stellarblade") for _ in range(3)
        ]
        first = self.invoke("events.read", after=0, limit=2, kind="jobs")
        self.assertEqual(len(first["items"]), 2)
        self.assertTrue(first["hasMore"])
        self.assertEqual(
            [item["seq"] for item in first["items"]],
            sorted(item["seq"] for item in first["items"]),
        )
        second = self.invoke(
            "events.read", after=first["nextAfter"], limit=2, kind="jobs"
        )
        self.assertTrue(
            all(item["seq"] > first["nextAfter"] for item in second["items"])
        )
        tail = self.invoke("events.read", limit=2, kind="jobs", tail=True)
        self.assertEqual([item["id"] for item in tail["items"]], [j["id"] for j in jobs[-2:]])
        self.assertEqual(tail["nextAfter"], tail["items"][-1]["seq"])

    def test_runtime_keeps_full_sync_wal_anchor_until_stop(self):
        self.assertIsNotNone(self.p.runtime._anchor)
        with self.p.runtime.db() as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            self.assertEqual(db.execute("PRAGMA synchronous").fetchone()[0], 2)
        self.p.runtime.stop()
        self.assertIsNone(self.p.runtime._anchor)

    def test_five_allowlisted_workflows_and_content_edit_execution(self):
        definitions = self.invoke("workflows.list")
        self.assertEqual(definitions["total"], 5)
        self.assertEqual(
            set(workflows.DEFINITIONS), {item["id"] for item in definitions["items"]}
        )
        self.assertTrue(
            all(
                step["operation"] in OPS
                for definition in definitions["items"]
                for step in definition["steps"]
            )
        )
        resource = self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]
        run = self.invoke(
            "workflows.start",
            id="content-edit",
            inputs={
                "read": {"ids": [self.mod["id"]], "fields": ["function"]},
                "records": [
                    {
                        "resourceId": self.mod["id"],
                        "baseRevision": resource["revision"],
                        "patch": {"function": "流程提交摘要"},
                        "note": "隔离流程验收",
                    }
                ],
                "commitMode": "atomic",
            },
            idempotencyKey="workflow-content-fixture",
        )
        for step in range(3):
            run = self.invoke(
                "workflows.resume",
                runId=run["id"],
                external={},
                idempotencyKey=f"workflow-resume-{step}",
            )
        self.assertEqual(run["status"], "complete")
        self.assertEqual(
            self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]["data"][
                "function"
            ],
            "流程提交摘要",
        )
        replay = self.invoke(
            "workflows.resume",
            runId=run["id"],
            external={},
            idempotencyKey="workflow-resume-2",
        )
        self.assertEqual(replay, run)

    def test_runtime_receipt_can_be_verified_by_operation_and_hash(self):
        key = "runtime-receipt-fixture"
        created = self.invoke(
            "tasks.create",
            title="回执核对",
            goal="验证运行库回执",
            scope={"operations": ["favorite.set"]},
            acceptance=[{"kind": "receipts", "minimum": 1}],
            idempotencyKey=key,
        )
        receipt = self.p.invoke(
            "receipts.read", {"key": key, "operation": "tasks.create"}
        )
        self.assertTrue(receipt["found"])
        self.assertEqual(receipt["domain"], "runtime")
        self.assertEqual(receipt["operation"], "tasks.create")
        self.assertEqual(receipt["result"]["id"], created["id"])
        with self.assertRaises(Problem) as caught:
            self.p.invoke("receipts.read", {"key": key, "operation": "tasks.claim"})
        self.assertEqual(caught.exception.code, "idempotency_conflict")

    def test_batched_workflow_waits_for_the_real_job_terminal_state(self):
        run = workflows.new_run(
            "content-edit",
            {
                "read": {"ids": [self.mod["id"]]},
                "records": [{"resourceId": self.mod["id"], "patch": {}}],
                "commitMode": "batched",
            },
            "workflow-batched-wait",
        )
        calls = []

        def invoke(operation, _arguments):
            calls.append(operation)
            if operation == "resources.read":
                return {"items": []}
            if operation == "content.preview":
                return {"previewId": "preview-fixture"}
            if operation == "content.apply":
                return {"id": "job-fixture", "status": "queued"}
            states = ["running", "complete"]
            return {"id": "job-fixture", "status": states[calls.count("jobs.read") - 1]}

        run = workflows.advance(run, {}, invoke)
        run = workflows.advance(run, {}, invoke)
        run = workflows.advance(run, {}, invoke)
        self.assertEqual(run["status"], "waiting_job")
        self.assertEqual(run["step"], 2)
        run = workflows.advance(run, {}, invoke)
        self.assertEqual(run["status"], "waiting_job")
        run = workflows.advance(run, {}, invoke)
        self.assertEqual(run["status"], "complete")
        self.assertEqual(calls.count("content.apply"), 1)

    def test_workflow_replays_the_exact_checkpointed_request_after_lost_response(self):
        run = workflows.new_run(
            "profile-build",
            {
                "search": {"game": "stellarblade"},
                "fileIds": ["file-one"],
                "profile": {"game": "stellarblade", "name": "fixture"},
                "selections": [
                    {"fileId": "file-one", "copyPath": "copy-one", "selected": True}
                ],
                "format": "json",
            },
            "workflow-request-journal",
        )
        saved = []
        selection_requests = []
        profile_reads = []

        def invoke(operation, arguments):
            if operation == "mods.search":
                return {"items": []}
            if operation == "files.compare":
                return {"items": []}
            if operation == "profiles.save":
                return {"id": "profile-one"}
            if operation == "profiles.read":
                profile_reads.append(True)
                return {
                    "id": "profile-one",
                    "revision": "revision-old" if len(profile_reads) == 1 else "revision-new",
                }
            if operation == "profiles.select":
                selection_requests.append(copy.deepcopy(arguments))
                if len(selection_requests) == 1:
                    raise ConnectionError("response lost after commit")
                return {"selected": True, "receiptId": arguments["idempotencyKey"]}
            raise AssertionError(operation)

        for _ in range(3):
            run = workflows.advance(run, {}, invoke)
        with self.assertRaises(ConnectionError):
            workflows.advance(
                run,
                {},
                invoke,
                checkpoint=lambda value: saved.append(copy.deepcopy(value)),
            )
        recovered = saved[-1]
        self.assertIn("pendingRequest", recovered)
        workflows.advance(recovered, {}, invoke)
        self.assertEqual(selection_requests[0], selection_requests[1])
        self.assertEqual(len(profile_reads), 1)

    def test_workflow_status_listing_and_run_version_cas(self):
        run = self.invoke(
            "workflows.start",
            id="content-edit",
            inputs={
                "read": {"ids": [self.mod["id"]]},
                "records": [],
                "commitMode": "atomic",
            },
            idempotencyKey="workflow-version-fixture",
        )
        self.assertEqual(run["runVersion"], 1)
        status = self.invoke("workflows.status", runId=run["id"])
        self.assertEqual(status["runVersion"], 1)
        listed = self.invoke("workflows.runs", page=1, limit=48)
        self.assertIn(run["id"], {item["id"] for item in listed["items"]})
        advanced = self.invoke(
            "workflows.resume",
            runId=run["id"],
            external={},
            expectedRunVersion=1,
            idempotencyKey="workflow-version-resume-one",
        )
        self.assertGreater(advanced["runVersion"], 1)
        with self.assertRaises(Problem) as caught:
            self.invoke(
                "workflows.resume",
                runId=run["id"],
                external={},
                expectedRunVersion=1,
                idempotencyKey="workflow-version-resume-stale",
            )
        self.assertEqual(caught.exception.code, "revision_conflict")

    def test_metrics_report_phases_without_business_payloads(self):
        self.invoke("mods.search", game="stellarblade", limit=1)
        report = self.invoke("maintenance.metrics", windowSeconds=60)
        self.assertGreaterEqual(
            report["operations"]["mods.search"]["total"]["samples"], 1
        )
        self.assertIn("business", report["operations"]["mods.search"])
        recent = [
            event for event in report["recent"] if event["operation"] == "mods.search"
        ]
        self.assertTrue(recent)
        self.assertTrue(all(event["requestId"] for event in recent))
        serialized = catalog.dumps(report)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn(self.mod["details"], serialized)

    def edit(self, text="整理后的中文摘要", key="apply-1", lease=None):
        with catalog.connect(self.path) as db:
            r = content.read_resource(db, self.mod["id"])
        args = dict(
            records=[
                dict(
                    resourceId=self.mod["id"],
                    baseRevision=r["revision"],
                    patch={"function": text},
                )
            ]
        )
        if lease:
            args["lease"] = lease
        preview = self.invoke("content.preview", **args)
        request = dict(previewId=preview["previewId"], idempotencyKey=key)
        if lease:
            request["lease"] = lease
        return self.invoke("content.apply", **request), request

    def test_receipt_replay_undo_conflict(self):
        result, request = self.edit()
        self.assertEqual(self.invoke("content.apply", **request), result)
        with self.assertRaises(Problem):
            self.invoke(
                "content.apply", previewId="different", idempotencyKey="apply-1"
            )
        self.edit("后续变更", key="apply-2")
        with self.assertRaises(Problem) as caught:
            self.invoke("batches.undo", id=result["batchId"])
        self.assertEqual(caught.exception.code, "revision_conflict")

    def test_committed_receipt_replay_does_not_join_write_queue(self):
        request = dict(
            id=self.mod["id"],
            enabled=True,
            idempotencyKey="favorite-replay-without-write-lock",
        )
        result = self.invoke("favorite.set", **request)

        class RejectingGate:
            def acquire(self, *args, **kwargs):
                raise AssertionError("committed receipt replay acquired the write gate")

            def release(self):
                raise AssertionError("unacquired write gate was released")

        with patch.object(server, "WRITE_LOCK", RejectingGate()):
            self.assertEqual(self.invoke("favorite.set", **request), result)
            with self.assertRaises(Problem) as caught:
                self.invoke(
                    "favorite.set",
                    id=self.mod["id"],
                    enabled=False,
                    idempotencyKey=request["idempotencyKey"],
                )
        self.assertEqual(caught.exception.code, "idempotency_conflict")

    def test_undo_restores_source(self):
        result, _ = self.edit()
        self.invoke("batches.undo", id=result["batchId"])
        self.assertEqual(
            self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]["data"][
                "function"
            ],
            self.mod["function"],
        )

    def task(self):
        return self.invoke(
            "tasks.create",
            title="补全摘要",
            goal="补充有来源的摘要",
            scope=dict(
                game="stellarblade",
                resources=[self.mod["id"]],
                fields=["function"],
                operations=["content.preview", "content.apply"],
            ),
            acceptance=[
                dict(
                    kind="resource_fields",
                    resourceId=self.mod["id"],
                    fields=["function"],
                )
            ],
        )

    def test_parallel_claim_and_fencing(self):
        task = self.task()

        def claim(i):
            try:
                return self.invoke("tasks.claim", id=task["id"], owner=str(i))
            except Problem:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            winners = [x for x in pool.map(claim, range(3)) if x]
        self.assertEqual(len(winners), 1)
        lease = winners[0]["lease"]
        result, _ = self.edit(lease=lease)
        completed = self.invoke(
            "tasks.complete", lease=lease, results=[result["receiptId"]]
        )
        self.assertEqual(completed["status"], "complete")
        with self.assertRaises(Problem):
            self.invoke("tasks.renew", lease=lease)

    def test_expired_and_paused_cannot_submit(self):
        task = self.task()
        lease = self.invoke("tasks.claim", id=task["id"], owner="agent-a")["lease"]
        self.invoke("tasks.control", id=task["id"], action="pause")
        with self.assertRaises(Problem):
            self.edit(lease=lease)
        self.invoke("tasks.control", id=task["id"], action="resume")
        new = self.invoke("tasks.claim", id=task["id"], owner="agent-b")["lease"]
        self.assertGreater(new["generation"], lease["generation"])
        with self.assertRaises(Problem):
            self.invoke("tasks.checkpoint", lease=lease, checkpoint={})
        self.invoke("tasks.checkpoint", lease=new, checkpoint={"next": "read_resource"})

    def test_scope_and_completion(self):
        task = self.task()
        lease = self.invoke("tasks.claim", id=task["id"], owner="agent")["lease"]
        with self.assertRaises(Problem):
            self.invoke("favorite.set", id=self.mod["id"], enabled=True, lease=lease)
        with self.assertRaises(Problem):
            self.invoke("tasks.complete", lease=lease, results=["not-a-receipt"])

    def package(self):
        return dict(
            format="local-mod-catalog",
            schemaVersion=2,
            records=[
                dict(
                    kind="mod",
                    alias="author-new-999",
                    source=dict(
                        kind="author", reference="https://example.test/mods/999"
                    ),
                    data=dict(
                        game="stellarblade",
                        modId=999,
                        name="New sourced MOD",
                        function="来源摘要",
                        details="来源正文",
                    ),
                ),
                dict(
                    kind="file",
                    alias="author-file-12",
                    source=dict(
                        kind="author", reference="https://example.test/files/12"
                    ),
                    data=dict(
                        game="stellarblade",
                        modId="stellarblade:999",
                        fileId=12,
                        name="Main",
                        version="1.0",
                        copies=[self.archive],
                    ),
                ),
            ],
        )

    def many_mod_package(self, count=55):
        return dict(
            format="local-mod-catalog",
            schemaVersion=2,
            records=[
                dict(
                    kind="mod",
                    alias=f"batch-mod-{number}",
                    source=dict(
                        kind="author",
                        reference=f"https://example.test/mods/{2000 + number}",
                    ),
                    data=dict(
                        game="stellarblade",
                        modId=2000 + number,
                        name=f"Batch MOD {number}",
                        function="批次验收",
                        details="来源正文",
                    ),
                )
                for number in range(count)
            ],
        )

    def test_batched_catalog_commit_persists_receipts_and_resumes(self):
        preview = self.invoke("catalog.preview", package=self.many_mod_package())
        stopped = False

        def progress(**values):
            nonlocal stopped
            if values.get("done") == 1:
                stopped = True

        arguments = dict(previewId=preview["previewId"], commitMode="batched")
        with self.assertRaises(InterruptedError):
            self.p.execute_batched(
                "catalog.apply",
                arguments,
                "job:resume-fixture",
                progress,
                lambda: stopped,
            )
        first = self.p.runtime.job_batches(dict(id="resume-fixture", page=1, limit=10))
        self.assertEqual(
            [item["status"] for item in first["items"]], ["committed", "pending"]
        )
        # The immutable business plan, rather than the expiring preview, is the
        # source of truth for continuation.
        with catalog.connect(self.path) as db:
            db.execute("DELETE FROM v2_previews WHERE id=?", (preview["previewId"],))
            committed = db.execute(
                "SELECT count(*) FROM execution_batches WHERE plan_id=?",
                ("resume-fixture",),
            ).fetchone()[0]
        self.assertEqual(committed, 1)
        result = self.p.execute_batched(
            "catalog.apply",
            arguments,
            "job:resume-fixture",
            lambda **_values: None,
            lambda: False,
        )
        self.assertEqual(result["committedBatches"], 2)
        batches = self.p.runtime.job_batches(
            dict(id="resume-fixture", page=1, limit=10)
        )
        self.assertEqual(
            [item["status"] for item in batches["items"]],
            ["committed", "committed"],
        )
        self.assertEqual(len({item["receiptId"] for item in batches["items"]}), 2)
        self.assertEqual(self.p.receipt("job:resume-fixture"), result)
        self.assertEqual(self.invoke("mods.search", q="Batch MOD")["total"], 55)

    def test_batched_mode_queues_and_publishes_aggregate_receipt(self):
        preview = self.invoke("catalog.preview", package=self.many_mod_package())
        self.p.runtime.start(self.p.execute_job, self.p.receipt)
        job = self.invoke(
            "catalog.apply",
            previewId=preview["previewId"],
            commitMode="batched",
            idempotencyKey="queued-batch-fixture",
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            current = self.invoke("jobs.read", id=job["id"])
            if current["status"] not in ("queued", "running"):
                break
            time.sleep(0.02)
        self.assertEqual(current["status"], "complete", current)
        batches = self.invoke("jobs.batches", id=job["id"], page=1, limit=10)
        self.assertEqual(batches["total"], 2)
        self.assertTrue(all(item["status"] == "committed" for item in batches["items"]))
        receipt = self.invoke("receipts.read", key="job:" + job["id"])
        self.assertTrue(receipt["found"])
        self.assertEqual(receipt["result"], current["result"])

    def test_batched_translation_publishes_only_after_all_segments_commit(self):
        package = translations.export_package(self.path, {"modId": self.mod["id"]})
        tasks = []
        for source in pathlib.Path(package["path"]).glob("tasks-*.jsonl"):
            tasks.extend(
                json.loads(line)
                for line in source.read_text(encoding="utf-8").splitlines()
            )
        tasks = [task for task in tasks if task["field"] == "details"]
        self.assertGreater(len(tasks), 1)
        results = [
            {
                key: task[key]
                for key in (
                    "taskId",
                    "resourceId",
                    "field",
                    "segmentId",
                    "sourceHash",
                )
            }
            | {
                "translation": "这是完整的分批中文测试译文。"
                + " ".join(task["protectedTokens"])
            }
            for task in tasks
        ]
        preview = self.invoke("translations.preview", content=json.dumps(results))
        result = self.p.execute_batched(
            "translations.import",
            dict(previewId=preview["previewId"], commitMode="batched"),
            "job:translation-batch-fixture",
            lambda **_values: None,
            lambda: False,
        )
        self.assertEqual(result["committedBatches"], 1)
        batches = self.p.runtime.job_batches(
            dict(id="translation-batch-fixture", page=1, limit=10)
        )
        self.assertEqual(batches["items"][0]["units"], len(tasks))
        self.assertEqual(batches["items"][0]["recordIndexes"], list(range(len(tasks))))
        with catalog.connect(self.path) as db:
            self.assertIn("details", catalog.translated(db, self.mod["id"]))

    def test_long_translation_crosses_batch_boundary_before_atomic_publish(self):
        resource = self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]
        long_details = (
            "This complete source sentence explains installation details and "
            "compatibility requirements for the local acceptance fixture. " * 2400
        )
        preview = self.invoke(
            "content.preview",
            records=[
                dict(
                    resourceId=self.mod["id"],
                    baseRevision=resource["revision"],
                    patch={"details": long_details},
                    note="long-field batch boundary fixture",
                )
            ],
        )
        self.invoke(
            "content.apply",
            previewId=preview["previewId"],
            idempotencyKey="long-field-source",
        )
        package = translations.export_package(
            self.path, {"modId": self.mod["id"], "force": True}
        )
        tasks = []
        for source in pathlib.Path(package["path"]).glob("tasks-*.jsonl"):
            tasks.extend(
                json.loads(line)
                for line in source.read_text(encoding="utf-8").splitlines()
            )
        tasks = [task for task in tasks if task["field"] == "details"]
        self.assertGreater(len(tasks), 50)
        results = [
            {
                key: task[key]
                for key in (
                    "taskId",
                    "resourceId",
                    "field",
                    "segmentId",
                    "sourceHash",
                )
            }
            | {"translation": "这是完整中文译文，用于验证分段保存和全文原子发布。"}
            for task in tasks
        ]
        preview = self.invoke("translations.preview", content=json.dumps(results))
        stopped = False

        def progress(**values):
            nonlocal stopped
            if values.get("done") == 1:
                stopped = True

        arguments = dict(previewId=preview["previewId"], commitMode="batched")
        with self.assertRaises(InterruptedError):
            self.p.execute_batched(
                "translations.import",
                arguments,
                "job:long-translation",
                progress,
                lambda: stopped,
            )
        batches = self.p.runtime.job_batches(
            dict(id="long-translation", page=1, limit=10)
        )
        self.assertGreaterEqual(batches["total"], 2)
        self.assertEqual(batches["items"][0]["units"], 50)
        with catalog.connect(self.path) as db:
            self.assertNotIn("details", catalog.translated(db, self.mod["id"]))
        result = self.p.execute_batched(
            "translations.import",
            arguments,
            "job:long-translation",
            lambda **_values: None,
            lambda: False,
        )
        self.assertEqual(result["committedBatches"], batches["total"])
        with catalog.connect(self.path) as db:
            self.assertIn("details", catalog.translated(db, self.mod["id"]))

    def test_single_oversized_record_is_its_own_batch(self):
        records = [{"payload": "x" * (513 * 1024)}, {"payload": "small"}]
        batches = self.p._partition_units(records, [[0], [1]])
        self.assertEqual([batch["indexes"] for batch in batches], [[0], [1]])
        self.assertEqual([batch["unitCount"] for batch in batches], [1, 1])

    def test_catalog_roundtrip_persistence_duplicate_undo(self):
        preview = self.invoke("catalog.preview", package=self.package())
        self.assertFalse(preview["errors"])
        self.invoke("catalog.apply", previewId=preview["previewId"])
        self.assertEqual(self.invoke("mods.search", q="New sourced")["total"], 1)
        duplicate = self.invoke("catalog.preview", package=self.package())
        self.assertTrue(all(r["status"] == "duplicate" for r in duplicate["changes"]))
        with catalog.connect(self.path) as db:
            db.execute("DELETE FROM files WHERE mod_id='stellarblade:999'")
            db.execute("DELETE FROM mods WHERE id='stellarblade:999'")
            interchange.reapply(db)
            self.assertIsNotNone(
                db.execute("SELECT id FROM mods WHERE id='stellarblade:999'").fetchone()
            )

    def test_invalid_paths_partial_requires_explicit_choice(self):
        package = self.package()
        package["records"][1]["data"]["copies"] = ["C:\\outside\\secret.zip"]
        preview = self.invoke("catalog.preview", package=package)
        self.assertEqual(len(preview["errors"]), 1)
        with self.assertRaises(Problem):
            self.invoke("catalog.apply", previewId=preview["previewId"])
        preview = self.invoke("catalog.preview", package=package, allowPartial=True)
        self.invoke("catalog.apply", previewId=preview["previewId"])
        self.assertEqual(self.invoke("mods.search", q="New sourced")["total"], 1)

    def test_recovery_after_commit_before_job_ack(self):
        job = self.invoke(
            "catalog.export", game="stellarblade", idempotencyKey="export-key"
        )
        with self.p.runtime.db() as db:
            row = self.p.runtime.read("jobs", job["id"], db)
            row["status"] = "running"
            self.p.runtime.save(db, "jobs", row)
        result = self.p.execute("catalog.export", row["input"], "job:" + job["id"])
        self.p.runtime.start(self.p.execute, self.p.receipt)
        recovered = self.invoke("jobs.read", id=job["id"])
        self.assertEqual(recovered["status"], "complete")
        self.assertEqual(recovered["result"], result)
        self.assertEqual(
            self.invoke(
                "catalog.export", game="stellarblade", idempotencyKey="export-key"
            )["id"],
            job["id"],
        )

    def test_transaction_rolls_back_with_receipt(self):
        with patch.object(self.p, "write", side_effect=self.broken_write):
            with self.assertRaises(Problem):
                self.invoke(
                    "favorite.set",
                    id=self.mod["id"],
                    enabled=True,
                    idempotencyKey="failed",
                )
        with catalog.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM favorites").fetchone()[0], 0
            )
            self.assertEqual(
                db.execute("SELECT count(*) FROM operation_receipts").fetchone()[0], 0
            )

    def test_actual_process_crashes(self):
        helper = pathlib.Path(__file__).with_name("crash_worker.py")
        for stage, code in [
            ("before_commit", 73),
            ("after_commit", 74),
            ("artifact_before_receipt", 75),
        ]:
            result = subprocess.run(
                [sys.executable, str(helper), str(self.root), stage],
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(
                result.returncode, code, result.stderr.decode(errors="replace")
            )
        with catalog.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM favorites").fetchone()[0], 0
            )
            self.assertEqual(
                db.execute("SELECT count(*) FROM profiles").fetchone()[0], 1
            )
            self.assertEqual(
                db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 0
            )
        self.invoke(
            "profiles.save",
            game="stellarblade",
            name="Crash receipt profile",
            idempotencyKey="crash-after",
        )
        with catalog.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM profiles").fetchone()[0], 1
            )
        result = self.p.execute(
            "catalog.export", {"game": "stellarblade"}, "job:crash-artifact"
        )
        self.assertTrue(result["artifact"]["sha256"])

    def test_pair_backup_and_restore(self):
        from restore_platform import restore

        result = self.p.execute("maintenance.backup", {}, "test-backup")
        destination = self.root / "restored"
        destination.mkdir()
        preview = restore(result["path"], destination)
        self.assertTrue(preview["requiresConfirmation"])
        restored = restore(result["path"], destination, True)
        with catalog.connect(destination / "catalog.sqlite3") as db:
            self.assertEqual(db.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(db.execute("SELECT count(*) FROM mods").fetchone()[0], 1)
        self.assertTrue(pathlib.Path(restored["rollback"]).is_dir())

    def test_restore_second_file_failure_does_not_leave_half_a_pair(self):
        from restore_platform import restore

        result = self.p.execute("maintenance.backup", {}, "restore-failure-backup")
        destination = self.root / "restore-failure"
        destination.mkdir()
        original_replace = pathlib.Path.replace

        def fail_runtime(path, target):
            if pathlib.Path(target).name == "work-runtime.sqlite3":
                raise OSError("fixture disk error on second publication")
            return original_replace(path, target)

        with patch.object(pathlib.Path, "replace", fail_runtime):
            with self.assertRaises(OSError):
                restore(result["path"], destination, True)
        self.assertFalse((destination / "catalog.sqlite3").exists())
        self.assertFalse((destination / "work-runtime.sqlite3").exists())

    def test_restore_preparation_failure_preserves_both_existing_databases(self):
        import shutil
        from restore_platform import restore

        result = self.p.execute("maintenance.backup", {}, "restore-prepare-backup")
        original_copy = shutil.copy2
        for failure in ("save_first", "stage_first", "save_second", "stage_second"):
            with self.subTest(failure=failure):
                destination = self.root / failure
                originals = self.copy_valid_pair(destination)

                def fail_copy(source, target):
                    target = pathlib.Path(target)
                    saving = target.parent.name == "old"
                    second = target.name.startswith("work-runtime")
                    stage = ("save_" if saving else "stage_") + (
                        "second" if second else "first"
                    )
                    if stage == failure:
                        target.write_bytes(b"partial copy")
                        raise OSError("fixture partial copy during " + failure)
                    return original_copy(source, target)

                with patch("restore_platform.shutil.copy2", side_effect=fail_copy):
                    with self.assertRaises(OSError):
                        restore(result["path"], destination, True)
                for name, data in originals.items():
                    self.assertEqual((destination / name).read_bytes(), data)
                self.assertFalse(list(destination.glob("*.restore-tmp")))

    def test_restore_publication_failure_restores_existing_pair(self):
        from restore_platform import restore

        result = self.p.execute("maintenance.backup", {}, "restore-existing-backup")
        destination = self.root / "restore-existing"
        originals = self.copy_valid_pair(destination)
        original_replace = pathlib.Path.replace
        failed = False

        def fail_runtime(path, target):
            nonlocal failed
            if pathlib.Path(target).name == "work-runtime.sqlite3" and not failed:
                failed = True
                raise OSError("fixture failure publishing second database")
            return original_replace(path, target)

        with patch.object(pathlib.Path, "replace", fail_runtime):
            with self.assertRaises(OSError):
                restore(result["path"], destination, True)
        for name, data in originals.items():
            self.assertEqual((destination / name).read_bytes(), data)
        self.assertFalse(list(destination.glob("*.restore-tmp")))

    def test_restore_journal_recovers_forced_exit_between_pair_replacements(self):
        from restore_platform import journal_state, recover_interrupted, restore

        result = self.p.execute("maintenance.backup", {}, "restore-crash-backup")
        destination = self.root / "restore-crash"
        originals = self.copy_valid_pair(destination)
        original_replace = pathlib.Path.replace

        def terminate_on_runtime(path, target):
            if pathlib.Path(target).name == "work-runtime.sqlite3":
                raise SystemExit("forced process termination")
            return original_replace(path, target)

        with patch.object(pathlib.Path, "replace", terminate_on_runtime):
            with self.assertRaises(SystemExit):
                restore(result["path"], destination, True)
        journal = journal_state(destination)
        self.assertEqual(journal["state"], "PUBLISHING")
        recovered = recover_interrupted(destination)
        self.assertEqual(recovered["status"], "rolled_back")
        for name, data in originals.items():
            self.assertEqual((destination / name).read_bytes(), data)
        self.assertFalse(list(destination.glob("*.restore-tmp")))

    def test_restore_journal_recovers_forced_exit_while_preparing(self):
        import shutil
        from restore_platform import journal_state, recover_interrupted, restore

        result = self.p.execute("maintenance.backup", {}, "restore-prepare-crash")
        destination = self.root / "restore-prepare-crash"
        originals = self.copy_valid_pair(destination)
        original_copy = shutil.copy2

        def terminate_during_stage(source, target):
            target = pathlib.Path(target)
            if target.parent.name == "new" and target.name == "catalog.sqlite3":
                target.write_bytes(b"incomplete staged copy")
                raise SystemExit("forced process termination while preparing")
            return original_copy(source, target)

        with patch("restore_platform.shutil.copy2", side_effect=terminate_during_stage):
            with self.assertRaises(SystemExit):
                restore(result["path"], destination, True)
        journal = journal_state(destination)
        self.assertEqual(journal["state"], "PREPARING")
        recovered = recover_interrupted(destination)
        self.assertEqual(recovered["status"], "rolled_back")
        for name, data in originals.items():
            self.assertEqual((destination / name).read_bytes(), data)
        self.assertFalse(list(destination.glob("*.restore-tmp")))

    def test_restore_committed_state_rebuilds_the_new_pair(self):
        import restore_platform

        result = self.p.execute("maintenance.backup", {}, "restore-commit-crash")
        destination = self.root / "restore-commit-crash"
        self.copy_valid_pair(destination)
        original_set_state = restore_platform._set_state

        def terminate_before_complete(journal, run, state, action):
            if state == "COMPLETE":
                raise SystemExit("forced termination after durable commit")
            return original_set_state(journal, run, state, action)

        with patch.object(
            restore_platform, "_set_state", side_effect=terminate_before_complete
        ):
            with self.assertRaises(SystemExit):
                restore_platform.restore(result["path"], destination, True)
        self.assertEqual(restore_platform.journal_state(destination)["state"], "COMMITTED")
        (destination / "catalog.sqlite3").write_bytes(b"incomplete later copy")
        recovered = restore_platform.recover_interrupted(destination)
        self.assertEqual(recovered["status"], "complete")
        expected = restore_platform.validate_pair(result["path"])["files"]
        restore_platform.validate_pair(destination, expected)
        self.assertEqual(restore_platform.journal_state(destination)["state"], "COMPLETE")

    def test_restore_journal_is_delete_full_and_service_lock_is_exclusive(self):
        from lifecycle_lock import LifecycleLockBusy
        from restore_platform import JOURNAL, restore

        result = self.p.execute("maintenance.backup", {}, "restore-lock-fixture")
        destination = self.root / "restore-lock-fixture"
        restore(result["path"], destination, True)
        with closing(sqlite3.connect(destination / JOURNAL)) as journal:
            self.assertEqual(journal.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            self.assertEqual(journal.execute("PRAGMA synchronous").fetchone()[0], 2)

        lock_script = (
            "import pathlib,sys; "
            "from lifecycle_lock import DirectoryLock; "
            "lock=DirectoryLock(pathlib.Path(sys.argv[1])); lock.acquire(); "
            "print('locked',flush=True); sys.stdin.read(); lock.release()"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", lock_script, str(destination)],
            cwd=pathlib.Path(__file__).resolve().parents[1],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(LifecycleLockBusy):
                restore(result["path"], destination, True)
        finally:
            process.stdin.close()
            process.wait(5)
        error = process.stderr.read()
        process.stdout.close()
        process.stderr.close()
        self.assertEqual(process.returncode, 0, error)

    def test_local_alias_identity_and_reference_prevents_undo(self):
        package = self.package()
        package["records"][0]["data"].pop("modId")
        package["records"][1]["data"].pop("fileId")
        package["records"][1]["data"].pop("modId")
        package["records"][1]["data"]["parentAlias"] = "author-new-999"
        package["records"].reverse()
        preview = self.invoke("catalog.preview", package=package)
        self.assertFalse(preview["errors"])
        applied = self.invoke("catalog.apply", previewId=preview["previewId"])
        mid = next(c["resourceId"] for c in preview["changes"] if c["kind"] == "mod")
        fid = next(c["resourceId"] for c in preview["changes"] if c["kind"] == "file")
        self.assertIn(":local:", mid)
        again = self.invoke("catalog.preview", package=package)
        self.assertEqual({c["resourceId"] for c in again["changes"]}, {mid, fid})
        profile = self.invoke("profiles.save", game="stellarblade", name="引用检查")
        revision = self.invoke("profiles.read", id=profile["id"])["revision"]
        self.invoke(
            "profiles.select",
            profileId=profile["id"],
            fileId=fid,
            copyPath=self.archive,
            selected=True,
            revision=revision,
        )
        with self.assertRaises(Problem) as caught:
            self.invoke("batches.undo", id=applied["batchId"])
        self.assertEqual(caught.exception.code, "resource_referenced")

    def test_database_migration_is_atomic(self):
        with catalog.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 5)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_doctor_is_lightweight_and_integrity_check_is_separate(self):
        result = self.invoke("doctor")
        self.assertEqual(result["databaseCheck"], "readable")
        self.assertEqual(result["integrityCheck"]["status"], "not_checked")
        verified = self.p.execute("maintenance.verify", {}, "verify-test")
        self.assertEqual(verified["databaseCheck"], "ok")
        with self.assertRaises(InterruptedError):
            self.p.execute(
                "maintenance.verify", {}, "verify-cancelled", cancelled=lambda: True
            )
        self.assertIsNone(self.p.receipt("verify-cancelled"))

    def test_files_list_exposes_all_pages_and_budget_continuation(self):
        first = self.invoke("files.list", id=self.mod["id"], limit=1)
        self.assertEqual(first["total"], 2)
        self.assertEqual(first["nextPage"], 2)
        second = self.invoke("files.list", id=self.mod["id"], limit=1, page=2)
        self.assertIsNone(second["nextPage"])
        self.assertNotEqual(
            first["items"][0]["resourceId"], second["items"][0]["resourceId"]
        )
        small = self.invoke("files.list", id=self.mod["id"], budget=2000)
        found = list(small["items"])
        if small.get("continuation"):
            next_read = small["continuation"]
            found.extend(
                self.invoke(next_read["operation"], **next_read["arguments"])["items"]
            )
        self.assertEqual(len(found), 2)

    def test_reapply_ignores_counts_edits_and_image_storage_shape(self):
        package = self.package()
        package["records"].append(
            dict(
                kind="image",
                alias="preview-image",
                source=dict(kind="author", reference="https://example.test/screenshot"),
                data=dict(
                    game="stellarblade",
                    modId="stellarblade:999",
                    remote_url="https://example.test/image.png",
                    caption="Author caption",
                ),
            )
        )
        preview = self.invoke("catalog.preview", package=package)
        self.assertFalse(preview["errors"])
        self.invoke("catalog.apply", previewId=preview["previewId"])
        resource = self.invoke("resources.read", ids=["stellarblade:999"])["items"][0]
        edit = self.invoke(
            "content.preview",
            records=[
                dict(
                    resourceId=resource["resourceId"],
                    baseRevision=resource["revision"],
                    patch={"function": "人工整理的摘要"},
                )
            ],
        )
        self.invoke("content.apply", previewId=edit["previewId"])
        with catalog.connect(self.path) as db:
            for _ in range(2):
                interchange.reapply(db)
            self.assertEqual(
                db.execute("SELECT count(*) FROM import_conflicts").fetchone()[0], 0
            )
            resource = content.read_resource(db, "stellarblade:999")["data"]
            self.assertEqual(resource["function"], "人工整理的摘要")
            self.assertEqual(resource["fileCount"], 1)
            self.assertEqual(resource["imageCount"], 1)
        again = self.invoke("catalog.preview", package=package)
        image = next(x for x in again["changes"] if x["kind"] == "image")
        self.assertEqual(image["status"], "duplicate")

    def test_scope_checks_stored_batch_and_profile_preview(self):
        changed, _ = self.edit()
        task = self.invoke(
            "tasks.create",
            title="限定资源",
            goal="不得修改其他 MOD",
            scope=dict(
                game="stellarblade",
                resources=["stellarblade:999"],
                operations=["batches.undo", "profiles.import"],
            ),
            acceptance=[dict(kind="receipts", minimum=1)],
        )
        lease = self.invoke("tasks.claim", id=task["id"], owner="test")["lease"]
        with self.assertRaises(Problem) as caught:
            self.invoke("batches.undo", id=changed["batchId"], lease=lease)
        self.assertEqual(caught.exception.code, "scope_denied")
        manifest = dict(
            format="local-mod-selection",
            schemaVersion=1,
            game="stellarblade",
            files=[
                dict(
                    fileId=self.mod["id"] + ":file:1",
                    storedPath=self.archive,
                    version="1.2.3",
                    bytes=7,
                )
            ],
        )
        preview = self.invoke("profiles.preview", manifest=manifest)
        with self.assertRaises(Problem) as caught:
            self.invoke(
                "profiles.import",
                previewId=preview["previewId"],
                name="拒绝越界",
                lease=lease,
            )
        self.assertEqual(caught.exception.code, "scope_denied")
        with catalog.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM profiles").fetchone()[0], 0
            )

    def test_catalog_translation_fields_and_preview_ownership_are_scoped(self):
        resource = self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]
        package = dict(
            format="local-mod-catalog",
            schemaVersion=2,
            records=[
                dict(
                    kind="mod",
                    alias="scoped-translation",
                    resourceId=self.mod["id"],
                    baseRevision=resource["revision"],
                    source=dict(kind="curated", reference="fixture translation source"),
                    data=dict(game="stellarblade", modId=1401, name=self.mod["name"]),
                    translations=[
                        dict(
                            field="function",
                            text="有来源的中文摘要",
                            source_hash=catalog.digest(self.mod["function"]),
                        )
                    ],
                )
            ],
        )
        # Normalize the existing source first, so this package changes only a
        # translation (not empty defaults newly added to the synthetic fixture).
        original_translations = package["records"][0].pop("translations")
        baseline = self.invoke("catalog.preview", package=package)
        self.invoke("catalog.apply", previewId=baseline["previewId"])
        package["records"][0]["baseRevision"] = self.invoke(
            "resources.read", ids=[self.mod["id"]]
        )["items"][0]["revision"]
        package["records"][0]["translations"] = original_translations
        leases = []
        for field in ("details", "function", "function"):
            task = self.invoke(
                "tasks.create",
                title="限定译文字段",
                goal="只提交授权字段",
                scope=dict(
                    game="stellarblade",
                    resources=[self.mod["id"]],
                    fields=[field],
                    operations=["catalog.preview", "catalog.apply"],
                ),
                acceptance=[dict(kind="receipts", minimum=1)],
            )
            leases.append(
                self.invoke("tasks.claim", id=task["id"], owner=field)["lease"]
            )
        preview = self.invoke("catalog.preview", package=package)
        self.assertTrue(preview["canApply"], preview)
        with self.assertRaises(Problem) as caught:
            self.invoke(
                "catalog.apply", previewId=preview["previewId"], lease=leases[0]
            )
        self.assertEqual(caught.exception.code, "scope_denied")
        # Use the full game scope for preview: its raw source payload includes
        # the identity name in addition to the single translated field.
        task = self.invoke(
            "tasks.create",
            title="有归属的预览",
            goal="保留所属任务",
            scope=dict(
                game="stellarblade", operations=["catalog.preview", "catalog.apply"]
            ),
            acceptance=[dict(kind="receipts", minimum=1)],
        )
        owner = self.invoke("tasks.claim", id=task["id"], owner="owner")["lease"]
        owned = self.invoke("catalog.preview", package=package, lease=owner)
        with self.assertRaises(Problem) as caught:
            self.invoke("catalog.apply", previewId=owned["previewId"], lease=leases[2])
        self.assertEqual(caught.exception.code, "scope_denied")
        self.invoke("catalog.apply", previewId=preview["previewId"], lease=leases[1])
        with catalog.connect(self.path) as db:
            self.assertEqual(
                catalog.translated(db, self.mod["id"])["function"], "有来源的中文摘要"
            )

    def test_runtime_pagination_and_busy_beyond_first_page(self):
        with self.p.runtime.db() as db:
            for number in range(120):
                item = dict(
                    id=str(number),
                    kind="test",
                    status="running" if number == 0 else "complete",
                )
                self.p.runtime.save(db, "jobs", item)
        self.assertTrue(self.p.runtime.busy())
        page = self.invoke("jobs.list", status="complete", page=2, limit=10)
        self.assertEqual(page["total"], 119)
        self.assertEqual(
            [j["id"] for j in page["items"]], [str(n) for n in range(109, 99, -1)]
        )
        active = self.invoke("jobs.list", status="running")
        self.assertEqual(active["total"], 1)
        self.assertEqual(active["items"][0]["id"], "0")

    def test_stop_at_commit_gate_rolls_back_business_and_receipt(self):
        stopped = False

        @contextmanager
        def stop_at_gate():
            nonlocal stopped
            stopped = True
            yield

        with patch.object(self.p.runtime, "gate", stop_at_gate()):
            with self.assertRaises(InterruptedError):
                self.p.execute(
                    "favorite.set",
                    dict(id=self.mod["id"], enabled=True),
                    "stopped-at-commit",
                    cancelled=lambda: stopped,
                )
        self.assertIsNone(self.p.receipt("stopped-at-commit"))
        with catalog.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM favorites").fetchone()[0], 0
            )

    def test_favorite_changes_invalidate_search_cursor(self):
        self.invoke("favorite.set", id=self.mod["id"], enabled=True)
        args = dict(favorite=True, limit=1)
        first = self.invoke("mods.search", **args)
        # A one-item fixture has no natural next page; encode its next-page cursor.
        import json

        identity = catalog.digest(
            json.dumps(dict(favorite="1", limit=1), sort_keys=True, ensure_ascii=False)
        )
        cursor = pack(
            dict(version=first["catalogRevision"], query=identity, page=2, offset=0)
        )
        self.invoke("favorite.set", id=self.mod["id"], enabled=False)
        with self.assertRaises(Problem) as caught:
            self.invoke("mods.search", cursor=cursor, **args)
        self.assertEqual(caught.exception.code, "cursor_stale")

    def test_nested_parent_stop_resume_fences_existing_descendant_lease(self):
        parent = self.task()
        child = self.invoke(
            "tasks.create",
            title="子任务",
            goal="分工",
            parentId=parent["id"],
            scope=parent["scope"],
            acceptance=parent["acceptance"],
        )
        grandchild = self.invoke(
            "tasks.create",
            title="孙任务",
            goal="分工",
            parentId=child["id"],
            scope=parent["scope"],
            acceptance=parent["acceptance"],
        )
        lease = self.invoke("tasks.claim", id=grandchild["id"], owner="old")["lease"]
        self.invoke("tasks.control", id=parent["id"], action="pause")
        with self.assertRaises(Problem):
            self.edit(lease=lease)
        self.invoke("tasks.control", id=parent["id"], action="resume")
        with self.assertRaises(Problem) as caught:
            self.edit(lease=lease)
        self.assertEqual(caught.exception.code, "lease_expired")
        self.invoke("tasks.control", id=grandchild["id"], action="resume")
        fresh = self.invoke("tasks.claim", id=grandchild["id"], owner="new")["lease"]
        self.edit(lease=fresh)

    def test_completion_requires_unique_actual_results(self):
        task = self.invoke(
            "tasks.create",
            title="两次整理",
            goal="两次实际提交",
            scope=dict(
                operations=["content.preview", "content.apply", "catalog.export"]
            ),
            acceptance=[dict(kind="receipts", minimum=2)],
        )
        lease = self.invoke("tasks.claim", id=task["id"], owner="agent")["lease"]
        exported = self.p.execute("catalog.export", dict(lease=lease), "export-only")
        with self.assertRaises(Problem):
            self.invoke(
                "tasks.complete",
                lease=lease,
                results=[exported["receiptId"], exported["artifact"]["id"]],
            )
        first, _ = self.edit(lease=lease)
        with self.assertRaises(Problem):
            self.invoke(
                "tasks.complete",
                lease=lease,
                results=[first["receiptId"], first["receiptId"]],
            )
        second, _ = self.edit("第二次有来源整理", key="second-actual", lease=lease)
        complete = self.invoke(
            "tasks.complete",
            lease=lease,
            results=[first["receiptId"], second["receiptId"]],
        )
        self.assertEqual(complete["status"], "complete")

    def test_handoff_recovers_receipts_without_checkpoint(self):
        task = self.task()
        lease = self.invoke("tasks.claim", id=task["id"], owner="disconnected")["lease"]
        applied, _ = self.edit(lease=lease)
        context = self.invoke("tasks.context", id=task["id"])
        self.assertEqual(context["checkpoint"], {})
        self.assertTrue(context["resources"][0]["revision"])
        receipts = context["completedResults"]
        self.assertEqual(receipts["total"], 2)
        actual = [r for r in receipts["items"] if r["completionEvidence"]]
        self.assertEqual([r["receiptId"] for r in actual], [applied["receiptId"]])
        first = self.invoke("tasks.results", id=task["id"], limit=1)
        second = self.invoke(
            "tasks.results", id=task["id"], page=first["nextPage"], limit=1
        )
        self.assertNotEqual(
            first["items"][0]["receiptId"], second["items"][0]["receiptId"]
        )

    def test_partial_content_retains_failed_indices_and_batches_only_valid_records(
        self,
    ):
        current = self.invoke("resources.read", ids=[self.mod["id"]])["items"][0]
        preview = self.invoke(
            "content.preview",
            allowPartial=True,
            records=[
                {},
                dict(
                    resourceId=self.mod["id"],
                    baseRevision=current["revision"],
                    patch=dict(function="合格资料"),
                ),
                dict(
                    resourceId="missing",
                    baseRevision="old",
                    patch=dict(function="拒绝资料"),
                ),
            ],
        )
        self.assertTrue(preview["canApply"])
        self.assertEqual([e["index"] for e in preview["errors"]], [0, 2])
        result = self.invoke("content.apply", previewId=preview["previewId"])
        batch = self.invoke("batches.read", id=result["batchId"])
        self.assertEqual([r["resourceId"] for r in batch["items"]], [self.mod["id"]])
        history = self.invoke("history.list", limit=1)
        self.assertEqual(history["total"], 1)

    def test_acceptance_rejects_unknown_or_incomplete_conditions(self):
        for condition in [
            dict(kind="receipts", minumum=2),
            dict(kind="resource_fields"),
        ]:
            with self.assertRaises(Problem):
                self.invoke(
                    "tasks.create",
                    title="错误条件",
                    goal="不能创建",
                    scope=dict(operations=["content.apply"]),
                    acceptance=[condition],
                )

    def test_parent_completion_accepts_only_its_completed_children(self):
        parent = self.invoke(
            "tasks.create",
            title="父任务",
            goal="分工完成",
            scope=dict(operations=["content.preview", "content.apply"]),
            acceptance=[dict(kind="children_complete")],
        )
        parent_lease = self.invoke("tasks.claim", id=parent["id"], owner="coordinator")[
            "lease"
        ]
        child = self.invoke(
            "tasks.create",
            title="子任务",
            goal="整理",
            parentId=parent["id"],
            scope=parent["scope"],
            acceptance=[dict(kind="receipts")],
        )
        with self.assertRaises(Problem):
            self.invoke("tasks.complete", lease=parent_lease, results=[child["id"]])
        lease = self.invoke("tasks.claim", id=child["id"], owner="worker")["lease"]
        result, _ = self.edit(lease=lease)
        self.invoke("tasks.complete", lease=lease, results=[result["receiptId"]])
        self.assertEqual(
            self.invoke("tasks.complete", lease=parent_lease, results=[child["id"]])[
                "status"
            ],
            "complete",
        )

    def test_cancel_during_transient_failure_does_not_retry(self):
        started, release, finished = (
            threading.Event(),
            threading.Event(),
            threading.Event(),
        )
        calls = []

        def execute(*args):
            calls.append(args)
            started.set()
            release.wait(5)
            raise TimeoutError("temporary fixture failure")

        job = self.invoke("catalog.export", game="stellarblade")
        self.p.runtime.start(execute, lambda key: None)
        self.assertTrue(started.wait(5))
        self.invoke("jobs.control", id=job["id"], action="cancel")
        release.set()
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            current = self.invoke("jobs.read", id=job["id"])
            if current["status"] == "cancelled":
                finished.set()
                break
            time.sleep(0.02)
        self.assertTrue(finished.is_set(), current)
        self.assertEqual(len(calls), 1)

    def test_restart_respects_stop_requested_before_process_exit(self):
        job = self.invoke("catalog.export", game="stellarblade")
        with self.p.runtime.db() as db:
            current = self.p.runtime.read("jobs", job["id"], db)
            current.update(status="running", cancel=True)
            self.p.runtime.save(db, "jobs", current)
        execute = unittest.mock.Mock()
        self.p.runtime.start(execute, lambda key: None)
        self.assertEqual(self.invoke("jobs.read", id=job["id"])["status"], "cancelled")
        execute.assert_not_called()

    def broken_write(self, db, *args):
        db.execute("INSERT INTO favorites VALUES(?,?)", (self.mod["id"], time.time()))
        raise ValueError("fault before receipt")


if __name__ == "__main__":
    unittest.main()
