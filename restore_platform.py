"""Offline paired restore with an SQLite crash-resumable journal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import time
import uuid
from contextlib import closing

from contracts import VERSION
from lifecycle_lock import directory_lock


APP = pathlib.Path(__file__).resolve().parent
FILES = ("catalog.sqlite3", "work-runtime.sqlite3")
JOURNAL = "restore-journal.sqlite3"


def sha256(path):
    value = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def database_info(path):
    path = pathlib.Path(path)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        check = db.execute("PRAGMA quick_check").fetchone()[0]
        if check != "ok":
            raise ValueError("数据库损坏：" + path.name)
        return {
            "sha256": sha256(path),
            "userVersion": db.execute("PRAGMA user_version").fetchone()[0],
        }


def validate_pair(folder, expected=None):
    folder = pathlib.Path(folder)
    present = [(folder / name).exists() for name in FILES]
    if any(present) and not all(present):
        raise ValueError("数据库配对不完整；catalog 与 work-runtime 必须同时存在")
    if not any(present):
        return {"empty": True, "files": {}}
    files = {name: database_info(folder / name) for name in FILES}
    if expected:
        for name in FILES:
            wanted = (
                expected[name]["sha256"]
                if isinstance(expected[name], dict)
                else expected[name]
            )
            if files[name]["sha256"] != wanted:
                raise ValueError("数据库配对哈希不符：" + name)
    return {"empty": False, "files": files}


def _journal(path):
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS restore_runs(
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            data TEXT NOT NULL,
            created REAL NOT NULL,
            updated REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS restore_events(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            state TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            created REAL NOT NULL
        );
        PRAGMA user_version=1;
        """
    )
    return db


def _event(journal_path, run, action, target=None):
    now = time.time()
    run["updated"] = now
    with closing(_journal(journal_path)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO restore_runs VALUES(?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state,data=excluded.data,updated=excluded.updated",
                (
                    run["id"],
                    run["state"],
                    json.dumps(run, ensure_ascii=False),
                    run["created"],
                    now,
                ),
            )
            db.execute(
                "INSERT INTO restore_events(run_id,state,action,target,created) VALUES(?,?,?,?,?)",
                (run["id"], run["state"], action, target, now),
            )


def _set_state(journal_path, run, state, action):
    run["state"] = state
    run[state.lower() + "At"] = time.time()
    _event(journal_path, run, action)


def journal_state(destination):
    path = pathlib.Path(destination) / JOURNAL
    if not path.exists():
        return None
    with closing(_journal(path)) as db:
        row = db.execute(
            "SELECT data FROM restore_runs ORDER BY updated DESC LIMIT 1"
        ).fetchone()
    return json.loads(row[0]) if row else None


def _active_run(journal_path):
    if not journal_path.exists():
        return None
    with closing(_journal(journal_path)) as db:
        row = db.execute(
            "SELECT data FROM restore_runs WHERE state NOT IN ('COMPLETE','ROLLED_BACK') "
            "ORDER BY updated DESC LIMIT 1"
        ).fetchone()
    return json.loads(row[0]) if row else None


def _flush_file(path):
    with pathlib.Path(path).open("r+b") as stream:
        os.fsync(stream.fileno())


def _copy_durable(source, target):
    target = pathlib.Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    _flush_file(target)


def _cleanup_publish_temps(destination):
    for name in FILES:
        (destination / (name + ".restore-tmp")).unlink(missing_ok=True)


def _publish_pair(destination, source, expected, empty, journal_path, run, action):
    destination = pathlib.Path(destination)
    source = pathlib.Path(source)
    for name in FILES:
        target = destination / name
        _event(journal_path, run, action + "_INTENT", name)
        if empty:
            target.unlink(missing_ok=True)
        else:
            staged = source / name
            if not staged.is_file() or sha256(staged) != expected[name]["sha256"]:
                raise RuntimeError("不可变配对副本缺失或哈希不符：" + name)
            temporary = destination / (name + ".restore-tmp")
            _copy_durable(staged, temporary)
            temporary.replace(target)
        _event(journal_path, run, action + "_COMPLETE", name)


def _block(journal_path, run, error):
    run["state"] = "BLOCKED"
    run["blockedReason"] = str(error)
    _event(journal_path, run, "RECOVERY_BLOCKED")


def _recover_locked(destination):
    destination = pathlib.Path(destination).resolve()
    journal_path = destination / JOURNAL
    run = _active_run(journal_path)
    if not run:
        return {"status": "none"}
    if run["state"] == "BLOCKED":
        raise RuntimeError(
            "恢复日志处于 BLOCKED；保持服务停止并人工核对："
            + str(journal_path)
        )
    stage = pathlib.Path(run["stage"])
    try:
        if run["state"] == "COMMITTED":
            _publish_pair(
                destination,
                stage / "new",
                run["newPair"]["files"],
                False,
                journal_path,
                run,
                "REBUILD_NEW",
            )
            validate_pair(destination, run["newPair"]["files"])
            _cleanup_publish_temps(destination)
            _set_state(journal_path, run, "COMPLETE", "RECOVERY_COMPLETE")
            return {"status": "complete", "journal": str(journal_path)}

        if run["state"] == "PREPARING":
            # No live target replacement is allowed before PREPARED is durable.
            old = run["oldPair"]
            validate_pair(destination, None if old["empty"] else old["files"])
        else:
            _set_state(journal_path, run, "ROLLING_BACK", "ROLLBACK_STARTED")
            old = run["oldPair"]
            _publish_pair(
                destination,
                stage / "old",
                old["files"],
                old["empty"],
                journal_path,
                run,
                "REBUILD_OLD",
            )
            validate_pair(destination, None if old["empty"] else old["files"])
        _cleanup_publish_temps(destination)
        _set_state(journal_path, run, "ROLLED_BACK", "ROLLBACK_COMPLETE")
        return {"status": "rolled_back", "journal": str(journal_path)}
    except Exception as error:
        _block(journal_path, run, error)
        raise RuntimeError(
            "无法确定恢复后的配对数据库；已进入 BLOCKED：" + str(error)
        ) from error


def recover_interrupted(destination, *, lock_held=False):
    """Resolve an interrupted restore before either business database opens."""
    destination = pathlib.Path(destination).resolve()
    if lock_held:
        return _recover_locked(destination)
    with directory_lock(destination, purpose="restore-recovery"):
        return _recover_locked(destination)


def _restore_locked(backup, destination):
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "local-mod-backup" or manifest.get("schemaVersion") != 2:
        raise ValueError("不是平台 v2 配套备份")
    expected = {name: {"sha256": manifest["files"].get(name)} for name in FILES}
    new_pair = validate_pair(backup, expected)
    _recover_locked(destination)
    for name in FILES:
        for suffix in ("-wal", "-shm"):
            sidecar = destination / (name + suffix)
            if sidecar.exists():
                raise ValueError(
                    "目标仍有数据库运行文件，请先正常关闭对应服务：" + sidecar.name
                )
    old_pair = validate_pair(destination)
    restore_id = uuid.uuid4().hex
    stage = destination / ("restore-" + restore_id)
    (stage / "old").mkdir(parents=True)
    (stage / "new").mkdir()
    journal_path = destination / JOURNAL
    run = dict(
        id=restore_id,
        state="PREPARING",
        codeVersion=VERSION,
        backup=str(backup),
        destination=str(destination),
        stage=str(stage),
        oldPair=old_pair,
        newPair=new_pair,
        created=time.time(),
    )
    _event(journal_path, run, "PREPARATION_STARTED")
    try:
        if not old_pair["empty"]:
            for name in FILES:
                _copy_durable(destination / name, stage / "old" / name)
            validate_pair(stage / "old", old_pair["files"])
        for name in FILES:
            _copy_durable(backup / name, stage / "new" / name)
        validate_pair(stage / "new", new_pair["files"])
        _set_state(journal_path, run, "PREPARED", "PAIR_COPIES_DURABLE")
        _set_state(journal_path, run, "PUBLISHING", "PUBLICATION_STARTED")
        _publish_pair(
            destination,
            stage / "new",
            new_pair["files"],
            False,
            journal_path,
            run,
            "PUBLISH_NEW",
        )
        validate_pair(destination, new_pair["files"])
        _set_state(journal_path, run, "COMMITTED", "NEW_PAIR_COMMITTED")
        _set_state(journal_path, run, "COMPLETE", "RESTORE_COMPLETE")
    except Exception:
        _recover_locked(destination)
        raise
    _cleanup_publish_temps(destination)
    return {
        "restored": dict(
            backup=str(backup), destination=str(destination), files=list(FILES)
        ),
        "rollback": str(stage / "old"),
        "stagedNew": str(stage / "new"),
        "journal": str(journal_path),
    }


def restore(backup, destination, confirm=False):
    backup = pathlib.Path(backup).resolve()
    destination = pathlib.Path(destination).resolve()
    if destination != (APP / "data").resolve() and not destination.is_relative_to(
        (APP / "test-results").resolve()
    ):
        raise ValueError("只允许恢复正式 data 或隔离测试目录")
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "local-mod-backup" or manifest.get("schemaVersion") != 2:
        raise ValueError("不是平台 v2 配套备份")
    expected = {name: {"sha256": manifest["files"].get(name)} for name in FILES}
    new_pair = validate_pair(backup, expected)
    plan = dict(backup=str(backup), destination=str(destination), files=list(FILES))
    if not confirm:
        return dict(preview=plan, requiresConfirmation=True, verified=new_pair)
    destination.mkdir(parents=True, exist_ok=True)
    with directory_lock(destination, purpose="restore"):
        return _restore_locked(backup, destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup")
    parser.add_argument("--destination", default=str(APP / "data"))
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    try:
        from runtime_support import ensure_pinned_process

        ensure_pinned_process(
            required=pathlib.Path(args.destination).resolve() == (APP / "data").resolve()
        )
        print(
            json.dumps(
                dict(ok=True, data=restore(args.backup, args.destination, args.confirm)),
                ensure_ascii=False,
            )
        )
    except Exception as error:
        print(json.dumps(dict(ok=False, error=str(error)), ensure_ascii=False))
        sys.exit(1)
