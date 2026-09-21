"""Durable work ownership and job queue. No catalogue connection is held here."""

from __future__ import annotations
import json
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from contracts import Problem, OPS
from catalog import dumps, digest


class Runtime:
    def __init__(self, path, metrics=None):
        self.path = path
        self.metrics = metrics
        self.gate = threading.RLock()
        self.wake = threading.Event()
        self.stopping = threading.Event()
        self.thread = None
        self._anchor = None
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts(key TEXT PRIMARY KEY,hash TEXT,result TEXT,created REAL);
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,id TEXT,data TEXT,created REAL);
                CREATE TABLE IF NOT EXISTS job_batches(
                    job_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY(job_id,ordinal)
                );
                CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS tasks_status ON tasks(json_extract(data,'$.status'));
                CREATE INDEX IF NOT EXISTS jobs_status ON jobs(json_extract(data,'$.status'));
                CREATE INDEX IF NOT EXISTS job_batches_status ON job_batches(job_id,json_extract(data,'$.status'));
                CREATE INDEX IF NOT EXISTS workflow_runs_status ON workflow_runs(json_extract(data,'$.status'));
                PRAGMA user_version=3;
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(receipts)")}
            if "operation" not in columns:
                db.execute("ALTER TABLE receipts ADD COLUMN operation TEXT")
            db.execute(
                "DELETE FROM events WHERE created<?", (time.time() - 90 * 86400,)
            )
        # Keep one connection for the runtime lifetime.  Without it, every
        # request closes SQLite's last WAL connection and can inherit an
        # avoidable final checkpoint before the persisted response is sent.
        self._anchor = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        self._anchor.execute("PRAGMA journal_mode=WAL")
        self._anchor.execute("PRAGMA synchronous=FULL")

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def read(self, table, rid, db=None):
        if db is None:
            with self.db() as connection:
                return self.read(table, rid, connection)
        row = db.execute(f"SELECT data FROM {table} WHERE id=?", (rid,)).fetchone()
        if not row:
            raise Problem("not_found", "任务或作业不存在", status=404, id=rid)
        return json.loads(row[0])

    @staticmethod
    def public(item):
        return {k: v for k, v in item.items() if k not in ("tokenHash", "input")}

    def save(self, db, table, item):
        item["updated"] = time.time()
        db.execute(
            f"INSERT OR REPLACE INTO {table} VALUES(?,?)", (item["id"], dumps(item))
        )
        db.execute(
            "INSERT INTO events(kind,id,data,created) VALUES(?,?,?,?)",
            (table, item["id"], dumps({"status": item["status"]}), time.time()),
        )

    def listing(self, table, args):
        if table not in ("tasks", "jobs"):
            raise ValueError("Unsupported runtime collection")
        limit, page = args.get("limit", 48), args.get("page", 1)
        where = " WHERE json_extract(data,'$.status')=?" if args.get("status") else ""
        parameters = (args["status"],) if where else ()
        with self.db() as db:
            # Count and page share a read snapshot; decode only the requested page.
            db.execute("BEGIN")
            total = db.execute(
                f"SELECT count(*) FROM {table}{where}", parameters
            ).fetchone()[0]
            values = [
                self.public(json.loads(r[0]))
                for r in db.execute(
                    f"SELECT data FROM {table}{where} ORDER BY rowid DESC LIMIT ? OFFSET ?",
                    (*parameters, limit, (page - 1) * limit),
                )
            ]
        return dict(
            items=values,
            total=total,
            page=page,
        )

    def events(self, args):
        limit = args.get("limit", 96)
        after = args.get("after", 0)
        kind = args.get("kind")
        where = " WHERE seq>?"
        values = [after]
        if kind:
            where += " AND kind=?"
            values.append(kind)
        with self.db() as db:
            if args.get("tail"):
                tail_where = " WHERE kind=?" if kind else ""
                tail_values = [kind] if kind else []
                rows = list(
                    db.execute(
                        "SELECT seq,kind,id,data,created FROM events"
                        + tail_where
                        + " ORDER BY seq DESC LIMIT ?",
                        (*tail_values, limit),
                    )
                )[::-1]
            else:
                rows = list(
                    db.execute(
                        "SELECT seq,kind,id,data,created FROM events"
                        + where
                        + " ORDER BY seq LIMIT ?",
                        (*values, limit + 1),
                    )
                )
        has_more = len(rows) > limit
        rows = rows[:limit]
        items = [
            dict(
                seq=row["seq"],
                kind=row["kind"],
                id=row["id"],
                created=row["created"],
                **json.loads(row["data"]),
            )
            for row in rows
        ]
        return dict(
            items=items,
            nextAfter=items[-1]["seq"] if items else after,
            hasMore=has_more,
        )

    def busy(self):
        with self.db() as db:
            return (
                db.execute(
                    "SELECT 1 FROM jobs WHERE json_extract(data,'$.status') IN ('running','queued') LIMIT 1"
                ).fetchone()
                is not None
            )

    def ensure_job_batches(self, job_id, batches, operation_version):
        """Persist deterministic batch boundaries before the first commit."""
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = list(
                db.execute(
                    "SELECT ordinal,data FROM job_batches WHERE job_id=? ORDER BY ordinal",
                    (job_id,),
                )
            )
            if existing:
                values = [json.loads(row["data"]) for row in existing]
                if len(values) != len(batches) or any(
                    value["inputHash"] != batch["inputHash"]
                    for value, batch in zip(values, batches)
                ):
                    raise Problem(
                        "batch_plan_conflict",
                        "持久批次边界与当前输入不一致",
                        status=409,
                        next_action="inspect_batches",
                    )
                return values
            now = time.time()
            values = []
            for ordinal, batch in enumerate(batches):
                value = dict(
                    batch,
                    jobId=job_id,
                    ordinal=ordinal,
                    operationVersion=operation_version,
                    status="pending",
                    receiptId=None,
                    result=None,
                    error=None,
                    created=now,
                    updated=now,
                )
                db.execute(
                    "INSERT INTO job_batches VALUES(?,?,?)",
                    (job_id, ordinal, dumps(value)),
                )
                values.append(value)
            return values

    def update_job_batch(self, job_id, ordinal, **updates):
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT data FROM job_batches WHERE job_id=? AND ordinal=?",
                (job_id, ordinal),
            ).fetchone()
            if not row:
                raise Problem("not_found", "作业批次不存在", status=404)
            value = json.loads(row[0])
            value.update(updates, updated=time.time())
            db.execute(
                "UPDATE job_batches SET data=? WHERE job_id=? AND ordinal=?",
                (dumps(value), job_id, ordinal),
            )
            return value

    def job_batches(self, args):
        page, limit = args.get("page", 1), args.get("limit", 48)
        conditions, values = ["job_id=?"], [args["id"]]
        if args.get("status"):
            conditions.append("json_extract(data,'$.status')=?")
            values.append(args["status"])
        where = " AND ".join(conditions)
        with self.db() as db:
            total = db.execute(
                f"SELECT count(*) FROM job_batches WHERE {where}", values
            ).fetchone()[0]
            rows = db.execute(
                f"SELECT data FROM job_batches WHERE {where} ORDER BY ordinal LIMIT ? OFFSET ?",
                (*values, limit, (page - 1) * limit),
            )
            return dict(
                items=[json.loads(row[0]) for row in rows],
                total=total,
                page=page,
            )

    def workflow_read(self, run_id, db=None):
        if db is None:
            with self.db() as connection:
                return self.workflow_read(run_id, connection)
        row = db.execute(
            "SELECT data FROM workflow_runs WHERE id=?", (run_id,)
        ).fetchone()
        if not row:
            raise Problem("not_found", "流程运行不存在", status=404)
        return json.loads(row[0])

    def workflow_save(self, run):
        run["updated"] = time.time()
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT OR REPLACE INTO workflow_runs VALUES(?,?)",
                (run["id"], dumps(run)),
            )

    def workflow_checkpoint(self, run, execution_token):
        run["updated"] = time.time()
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            current = self.workflow_read(run["id"], db)
            if current.get("executionToken") != execution_token:
                raise Problem(
                    "workflow_execution_lost",
                    "流程执行权已经变化",
                    status=409,
                )
            db.execute(
                "UPDATE workflow_runs SET data=? WHERE id=?",
                (dumps(run), run["id"]),
            )

    def workflow_list(self, args):
        from workflows import public_run

        page, limit = args.get("page", 1), args.get("limit", 48)
        with self.db() as db:
            where = (
                " WHERE json_extract(data,'$.status')=?" if args.get("status") else ""
            )
            values = (args["status"],) if where else ()
            total = db.execute(
                "SELECT count(*) FROM workflow_runs" + where, values
            ).fetchone()[0]
            rows = db.execute(
                "SELECT data FROM workflow_runs"
                + where
                + " ORDER BY rowid DESC LIMIT ? OFFSET ?",
                (*values, limit, (page - 1) * limit),
            )
            return dict(
                items=[public_run(json.loads(row[0])) for row in rows],
                total=total,
                page=page,
            )

    def verify_lease(self, lease, db=None):
        if not lease:
            raise Problem("lease_required", "需要任务租约", next_action="claim_task")
        task = self.read("tasks", lease["taskId"], db)
        if (
            task["status"] != "running"
            or task["expires"] <= time.time()
            or task.get("owner") != lease["owner"]
            or task["generation"] != lease["generation"]
            or not secrets.compare_digest(
                task.get("tokenHash", ""), digest(lease["token"])
            )
        ):
            raise Problem(
                "lease_expired",
                "租约已过期、任务暂停或已被接续",
                status=409,
                next_action="claim_task",
                taskId=task["id"],
            )
        self.verify_ancestors(task, db)
        return task

    def verify_ancestors(self, task, db=None, *, claiming=False):
        generations = {}
        parent_id = task.get("parentId")
        while parent_id:
            parent = self.read("tasks", parent_id, db)
            if parent["status"] in ("paused", "cancelled", "complete"):
                raise Problem("task_stopped", "上级任务已停止", status=409)
            generations[parent_id] = parent["generation"]
            parent_id = parent.get("parentId")
        if not claiming and task.get("ancestorGenerations", generations) != generations:
            raise Problem(
                "lease_expired",
                "上级任务已停止或接续，请重新领取子任务",
                status=409,
                next_action="claim_task",
                taskId=task["id"],
            )
        return generations

    def mutate(self, name, args, checks=None):
        key = args.get("idempotencyKey")
        canonical_args = {k: v for k, v in args.items() if k != "idempotencyKey"}
        fingerprint = digest(
            json.dumps([name, canonical_args], sort_keys=True, ensure_ascii=False)
        )
        legacy_fingerprint = digest(
            json.dumps([name, args], sort_keys=True, ensure_ascii=False)
        )
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if key:
                row = db.execute(
                    "SELECT hash,result,operation FROM receipts WHERE key=?", (key,)
                ).fetchone()
                if row:
                    if row["hash"] not in (fingerprint, legacy_fingerprint) or (
                        row["operation"] and row["operation"] != name
                    ):
                        raise Problem(
                            "idempotency_conflict",
                            "同一幂等键不能用于不同内容",
                            status=409,
                        )
                    result = json.loads(row["result"])
                    result["_metricsReceiptReplay"] = True
                    return result
            result = self._mutate(db, name, args, checks)
            if key:
                db.execute(
                    "INSERT INTO receipts(key,hash,result,created,operation) VALUES(?,?,?,?,?)",
                    (key, fingerprint, dumps(result), time.time(), name),
                )
            return result

    def receipt(self, key):
        with self.db() as db:
            row = db.execute(
                "SELECT hash,result,operation FROM receipts WHERE key=?", (key,)
            ).fetchone()
        if not row:
            return None
        return {
            "payloadHash": row["hash"],
            "operation": row["operation"],
            "result": json.loads(row["result"]),
        }

    def _mutate(self, db, name, args, checks):
        if name == "tasks.create":
            scope = args["scope"]
            if not scope["operations"] or any(
                x not in OPS or OPS[x]["destructive"] for x in scope["operations"]
            ):
                raise Problem("invalid_scope", "范围必须列出有效的非破坏性操作")
            if not args["acceptance"]:
                raise Problem("acceptance_required", "至少指定一个可验证完成条件")
            for condition in args["acceptance"]:
                if condition.get("kind") not in (
                    "resource_fields",
                    "translations_complete",
                    "profile_files",
                    "receipts",
                    "children_complete",
                ):
                    raise Problem(
                        "invalid_acceptance",
                        "不支持的完成条件",
                        allowed=[
                            "resource_fields",
                            "translations_complete",
                            "profile_files",
                            "receipts",
                            "children_complete",
                        ],
                    )
                required = {
                    "resource_fields": ("resourceId", "fields"),
                    "translations_complete": ("resourceId",),
                    "profile_files": ("profileId", "fileIds"),
                }.get(condition["kind"], ())
                if any(field not in condition for field in required) or (
                    condition["kind"] == "resource_fields"
                    and not condition.get("fields")
                ):
                    raise Problem(
                        "invalid_acceptance",
                        "完成条件缺少资源或字段",
                        required=list(required),
                    )
            if args.get("parentId"):
                parent = self.read("tasks", args["parentId"], db)
                self.verify_ancestors({"parentId": parent["id"]}, db, claiming=True)
                for field in ("game", "resources", "fields", "operations"):
                    expected = parent["scope"].get(field)
                    actual = scope.get(field)
                    if expected and (
                        not actual
                        or (
                            isinstance(expected, list)
                            and not set(actual) <= set(expected)
                        )
                        or (isinstance(expected, str) and actual != expected)
                    ):
                        raise Problem("scope_expansion", "子任务不能扩大父任务范围")
            task = dict(
                id=uuid.uuid4().hex,
                title=args["title"],
                goal=args["goal"],
                scope=scope,
                acceptance=args["acceptance"],
                resources=args.get("resources", scope.get("resources", [])),
                parentId=args.get("parentId"),
                status="pending",
                generation=0,
                expires=0,
                owner="",
                checkpoint={},
                artifacts=[],
                results=[],
                created=time.time(),
            )
            self.save(db, "tasks", task)
            return self.public(task)
        if name.startswith("tasks."):
            lease = args.get("lease")
            task = self.read("tasks", args.get("id") or (lease or {}).get("taskId"), db)
            if name == "tasks.claim":
                ancestors = self.verify_ancestors(task, db, claiming=True)
                if task["status"] not in ("pending", "running") or (
                    task["status"] == "running" and task["expires"] > time.time()
                ):
                    raise Problem(
                        "task_unavailable",
                        "任务已领取或需要先恢复",
                        status=409,
                        next_action="inspect_task",
                    )
                token = secrets.token_urlsafe(24)
                task.update(
                    owner=args["owner"],
                    tokenHash=digest(token),
                    generation=task["generation"] + 1,
                    expires=time.time() + 300,
                    status="running",
                    ancestorGenerations=ancestors,
                )
                self.save(db, "tasks", task)
                return dict(
                    task=self.public(task),
                    lease=dict(
                        taskId=task["id"],
                        owner=args["owner"],
                        generation=task["generation"],
                        token=token,
                    ),
                )
            if name == "tasks.control":
                if lease and lease.get("taskId") != task["id"]:
                    raise Problem(
                        "scope_denied", "不能使用其他任务的租约改变本任务", status=403
                    )
                if task["status"] == "complete":
                    raise Problem(
                        "task_complete", "已完成任务不能重新改变状态", status=409
                    )
                if args["action"] in ("wait", "block"):
                    self.verify_lease(lease, db)
                task.update(
                    status={
                        "pause": "paused",
                        "cancel": "cancelled",
                        "resume": "pending",
                        "wait": "waiting_external",
                        "block": "blocked",
                    }[args["action"]],
                    reason=args.get("reason", ""),
                    expires=0,
                    generation=task["generation"] + 1,
                )
            else:
                self.verify_lease(lease, db)
                if name == "tasks.renew":
                    task["expires"] = time.time() + 300
                elif name == "tasks.checkpoint":
                    if len(dumps(args["checkpoint"])) > 8000:
                        raise Problem(
                            "checkpoint_too_large",
                            "检查点最多 8000 字符；长资料请使用成果引用",
                        )
                    task["checkpoint"] = args["checkpoint"]
                    task["artifacts"] = list(
                        dict.fromkeys(task["artifacts"] + args.get("artifacts", []))
                    )
                elif name == "tasks.complete":
                    if not args["results"]:
                        raise Problem("results_required", "必须提供成果或提交回执")
                    failures = checks(task, args["results"])
                    if failures:
                        raise Problem(
                            "acceptance_failed",
                            "任务尚未满足完成条件",
                            next_action="finish_remaining",
                            failures=failures,
                        )
                    task.update(status="complete", results=args["results"], expires=0)
            self.save(db, "tasks", task)
            return self.public(task)
        if name == "jobs.control":
            job = self.read("jobs", args["id"], db)
            if args["action"] == "cancel":
                if job["status"] not in ("complete", "failed", "cancelled"):
                    job["cancel"] = True
                    if job["status"] != "running":
                        job["status"] = "cancelled"
            else:
                if job["status"] not in (
                    "blocked",
                    "failed",
                    "cancelled",
                    "interrupted",
                ):
                    raise Problem("job_not_resumable", "当前作业不能恢复")
                if job.get("taskId"):
                    task = self.verify_lease(args.get("lease"), db)
                    if task["id"] != job["taskId"]:
                        raise Problem(
                            "scope_denied",
                            "新租约不属于该作业的任务",
                            status=403,
                        )
                    if job["kind"] not in task["scope"]["operations"]:
                        raise Problem(
                            "scope_denied",
                            "新租约不覆盖该作业的剩余操作",
                            status=403,
                        )
                    job["input"]["lease"] = args["lease"]
                job.update(status="queued", cancel=False, error=None, attempts=0)
            self.save(db, "jobs", job)
            self.wake.set()
            return self.public(job)
        # Queue submissions are idempotent in this same runtime transaction.
        job = dict(
            id=uuid.uuid4().hex,
            kind=name,
            input=args,
            inputHash=digest(
                json.dumps([name, args], sort_keys=True, ensure_ascii=False)
            ),
            taskId=args.get("lease", {}).get("taskId"),
            status="queued",
            phase="queued",
            done=0,
            total=0,
            attempts=0,
            cancel=False,
            created=time.time(),
            message="等待执行",
        )
        self.save(db, "jobs", job)
        self.wake.set()
        return self.public(job)

    def start(self, execute, receipt):
        if self.thread:
            return
        # Business receipts decide whether a worker died before or after commit.
        with self.gate, self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in db.execute("SELECT data FROM jobs").fetchall():
                job = json.loads(row[0])
                if job["status"] == "running":
                    result = receipt("job:" + job["id"])
                    if result is not None:
                        job.update(
                            status="complete", result=result, message="已核对提交回执"
                        )
                    else:
                        job.update(
                            status="cancelled" if job["cancel"] else "queued",
                            message="已停止"
                            if job["cancel"]
                            else "上次执行中断，准备恢复",
                        )
                    self.save(db, "jobs", job)

        def worker():
            while not self.stopping.is_set():
                with self.gate, self.db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    row = db.execute(
                        "SELECT data FROM jobs WHERE json_extract(data,'$.status')='queued' ORDER BY rowid LIMIT 1"
                    ).fetchone()
                    if row:
                        job = json.loads(row[0])
                        if self.metrics:
                            self.metrics.observe(
                                job["kind"],
                                "queue_age",
                                max(0.0, time.time() - job["created"]),
                            )
                        job.update(
                            status="running",
                            attempts=job["attempts"] + 1,
                            phase="executing",
                            message="执行中",
                        )
                        self.save(db, "jobs", job)
                if not row:
                    self.wake.wait(0.5)
                    self.wake.clear()
                    continue

                def cancelled():
                    if self.stopping.is_set():
                        return True
                    with self.db() as db:
                        current = self.read("jobs", job["id"], db)
                        if current["cancel"]:
                            return True
                        if current.get("taskId"):
                            try:
                                self.verify_lease(current["input"].get("lease"), db)
                            except Problem:
                                return True
                    return False

                last_progress = [0.0, ""]

                def progress(**kw):
                    now = time.monotonic()
                    phase = kw.get("phase", "")
                    terminal = kw.get("done") == kw.get("total") and kw.get("total")
                    if (
                        not terminal
                        and phase == last_progress[1]
                        and now - last_progress[0] < 1
                    ):
                        return
                    last_progress[:] = [now, phase]
                    with self.gate, self.db() as db:
                        db.execute("BEGIN IMMEDIATE")
                        current = self.read("jobs", job["id"], db)
                        current.update(kw)
                        self.save(db, "jobs", current)

                try:
                    if cancelled():
                        raise InterruptedError("已停止")
                    result = execute(
                        job["kind"],
                        job["input"],
                        "job:" + job["id"],
                        progress,
                        cancelled,
                    )
                    updates = dict(
                        status="complete",
                        phase="complete",
                        result=result,
                        message="已完成",
                    )
                except InterruptedError as error:
                    updates = dict(
                        status="interrupted" if self.stopping.is_set() else "cancelled",
                        message=str(error),
                    )
                except Exception as error:
                    transient = isinstance(error, (TimeoutError, ConnectionError)) or (
                        isinstance(error, sqlite3.OperationalError)
                        and "locked" in str(error)
                    )
                    payload = (
                        error.payload()
                        if isinstance(error, Problem)
                        else dict(
                            code="temporary_error" if transient else "operation_failed",
                            message=str(error),
                            retryable=transient,
                            nextAction="resume" if transient else "inspect_input",
                        )
                    )
                    updates = dict(
                        status="queued"
                        if transient and job["attempts"] < 3
                        else "blocked",
                        error=payload,
                        message=str(error),
                    )
                    if transient:
                        self.stopping.wait(min(job["attempts"], 3))
                with self.gate, self.db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    current = self.read("jobs", job["id"], db)
                    if current["cancel"] and updates["status"] == "queued":
                        updates.update(status="cancelled", message="已停止，不再重试")
                    current.update(updates)
                    self.save(db, "jobs", current)

        self.thread = threading.Thread(
            target=worker, name="durable-mod-worker", daemon=True
        )
        self.thread.start()

    def stop(self):
        self.stopping.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=5)
        if self._anchor is not None:
            self._anchor.close()
            self._anchor = None
