"""Source-backed catalogue interchange, registered paths and reversible batches."""

from __future__ import annotations
import json
import pathlib
import time
import uuid
from catalog import (
    dumps,
    digest,
    apply_edits,
    refresh_search,
    rebuild_query_projections,
    QUERY_PROJECTION_VERSION,
    resolved_path,
    translation_quality_error,
)
from contracts import Problem


def migrate(db):
    db.executescript("""
        BEGIN IMMEDIATE;
        CREATE TABLE IF NOT EXISTS operation_receipts(key TEXT PRIMARY KEY,hash TEXT,result TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS import_sources(id TEXT PRIMARY KEY,kind TEXT,data TEXT,base TEXT,source TEXT,alias TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS import_conflicts(id TEXT PRIMARY KEY,data TEXT);
        CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,data TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,data TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS issue_reports(game TEXT PRIMARY KEY,data TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS saved_filters(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,game TEXT,data TEXT NOT NULL,created REAL,updated REAL);
        CREATE TABLE IF NOT EXISTS changes(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,resource_id TEXT,action TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS v2_previews(id TEXT PRIMARY KEY,data TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS execution_plans(id TEXT PRIMARY KEY,operation TEXT NOT NULL,input_hash TEXT NOT NULL,data TEXT NOT NULL,created REAL);
        CREATE TABLE IF NOT EXISTS execution_batches(plan_id TEXT NOT NULL,ordinal INTEGER NOT NULL,data TEXT NOT NULL,created REAL,PRIMARY KEY(plan_id,ordinal));
        CREATE INDEX IF NOT EXISTS receipt_task ON operation_receipts(json_extract(result,'$.taskId'));
    """)
    for table, identity, kind in [
        ("mods", "id", "mod"),
        ("files", "id", "file"),
        ("images", "id", "image"),
        ("translations", "resource_id", "translation"),
        ("translation_tasks", "resource_id", "translation_task"),
        ("favorites", "mod_id", "favorite"),
        ("recent", "mod_id", "recent"),
        ("profiles", "id", "profile"),
        ("selections", "profile_id", "selection"),
    ]:
        for verb in ("INSERT", "UPDATE", "DELETE"):
            ref = "OLD" if verb == "DELETE" else "NEW"
            db.execute(f"""CREATE TRIGGER IF NOT EXISTS change_{table}_{verb} AFTER {verb} ON {table}
                           BEGIN INSERT INTO changes(kind,resource_id,action,created)
                           VALUES('{kind}',{ref}.{identity},'{verb.lower()}',unixepoch()); END""")
    missing = db.execute(
        "SELECT count(*) FROM mods WHERE id NOT IN (SELECT mod_id FROM mod_query)"
    ).fetchone()[0]
    stale = db.execute(
        "SELECT count(*) FROM mod_query WHERE algorithm_version<>?",
        (QUERY_PROJECTION_VERSION,),
    ).fetchone()[0]
    if missing or stale:
        rebuild_query_projections(db)
    db.execute("PRAGMA user_version=5")


def registered_path(db, game, path):
    row = db.execute("SELECT root FROM games WHERE id=?", (game,)).fetchone()
    if not row:
        raise Problem(
            "game_unregistered", "游戏尚未登记", next_action="register_game", game=game
        )
    original = pathlib.Path(row[0]).resolve()
    mapped = pathlib.Path(resolved_path(db, row[0])).resolve()
    candidate = pathlib.Path(path)
    if not candidate.is_absolute() or not any(
        candidate.resolve().is_relative_to(root) for root in (original, mapped)
    ):
        raise Problem(
            "root_unregistered",
            "路径必须位于该游戏登记根目录内",
            next_action="register_root",
            path=path,
        )
    return str(candidate)


def snapshot(db, rid):
    result = {}
    for table, key in [
        ("mods", "id"),
        ("files", "id"),
        ("images", "id"),
        ("resource_base", "id"),
        ("edits", "resource_id"),
        ("import_sources", "id"),
        ("translations", "resource_id"),
        ("translation_tasks", "resource_id"),
    ]:
        result[table] = [
            dict(r) for r in db.execute(f"SELECT * FROM {table} WHERE {key}=?", (rid,))
        ]
    return result


def snapshot_hash(value):
    # Tasks may get new pending exports without changing imported content; keep them
    # in the fingerprint so undo cannot silently erase subsequent work.
    return digest(dumps(value))


def save_batch(db, before, note):
    bid = uuid.uuid4().hex
    after = {rid: snapshot_hash(snapshot(db, rid)) for rid in before}
    after_data = {rid: snapshot(db, rid) for rid in before}
    data = dict(
        id=bid,
        note=note,
        before=before,
        after=after,
        afterData=after_data,
        status="applied",
        resources=list(before),
    )
    db.execute("INSERT INTO batches VALUES(?,?,?)", (bid, dumps(data), time.time()))
    return bid


def undo(db, bid):
    row = db.execute("SELECT data FROM batches WHERE id=?", (bid,)).fetchone()
    if not row:
        raise Problem("not_found", "批次不存在", status=404)
    batch = json.loads(row[0])
    if batch["status"] != "applied":
        raise Problem("batch_already_undone", "批次已撤销", status=409)
    for rid, expected in batch["after"].items():
        if snapshot_hash(snapshot(db, rid)) != expected:
            raise Problem(
                "revision_conflict",
                "批次之后资料已经变化，不能覆盖",
                status=409,
                next_action="review_diff",
                resourceId=rid,
            )
        previous = batch["before"][rid]
        if (
            not previous["files"]
            and db.execute(
                "SELECT 1 FROM selections WHERE file_id=?", (rid,)
            ).fetchone()
        ):
            raise Problem(
                "resource_referenced",
                "新文件已有搭配引用，请先处理引用",
                status=409,
                resourceId=rid,
            )
        if not previous["mods"]:
            for table, key in [
                ("favorites", "mod_id"),
                ("recent", "mod_id"),
                ("files", "mod_id"),
                ("images", "mod_id"),
            ]:
                refs = db.execute(
                    f"SELECT * FROM {table} WHERE {key}=?", (rid,)
                ).fetchall()
                if refs and (
                    table in ("favorites", "recent")
                    or any(r["id"] not in batch["before"] for r in refs)
                ):
                    raise Problem(
                        "resource_referenced",
                        "新 MOD 已有引用，请先处理引用",
                        status=409,
                        resourceId=rid,
                    )
    for rid, previous in batch["before"].items():
        for table, rows in previous.items():
            key = (
                "resource_id"
                if table in ("edits", "translations", "translation_tasks")
                else "id"
            )
            db.execute(f"DELETE FROM {table} WHERE {key}=?", (rid,))
            for item in rows:
                db.execute(
                    f"INSERT INTO {table} ({','.join(item)}) VALUES({','.join('?' for _ in item)})",
                    tuple(item.values()),
                )
    for rid in batch["before"]:
        refresh_search(db, rid)
        f = db.execute("SELECT mod_id FROM files WHERE id=?", (rid,)).fetchone()
        if f:
            refresh_search(db, f[0])
    batch["status"] = "undone"
    db.execute("UPDATE batches SET data=? WHERE id=?", (dumps(batch), bid))
    return dict(batchId=bid, undone=len(batch["before"]))


def put(db, kind, data):
    rid = data["id"]
    if kind == "mod":
        data = apply_edits(db, data, "mod")
        db.execute(
            "INSERT OR REPLACE INTO mods VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid,
                data["game"],
                data.get("modId"),
                data["name"],
                data.get("author", ""),
                data.get("group", "其他"),
                int(data.get("adult", False)),
                data.get("downloads", 0),
                data.get("updated", 0),
                "",
                dumps(data),
            ),
        )
        refresh_search(db, rid)
    elif kind == "file":
        data = apply_edits(db, data, "file")
        db.execute(
            "INSERT OR REPLACE INTO files VALUES(?,?,?,?)",
            (rid, data["modId"], data.get("fileId"), dumps(data)),
        )
        refresh_search(db, data["modId"])
    elif kind == "image":
        db.execute(
            "INSERT OR REPLACE INTO images VALUES(?,?,?,?,?,?,?)",
            (
                rid,
                data["modId"],
                data.get("ordinal", 0),
                data.get("local_path", ""),
                data.get("remote_url", ""),
                data.get("caption", ""),
                data["source"],
            ),
        )


def refresh_counts(db, mids):
    for mid in mids:
        row = db.execute("SELECT data FROM mods WHERE id=?", (mid,)).fetchone()
        if not row:
            continue
        data = json.loads(row[0])
        data["fileCount"] = db.execute(
            "SELECT count(*) FROM files WHERE mod_id=?", (mid,)
        ).fetchone()[0]
        data["imageCount"] = db.execute(
            "SELECT count(*) FROM images WHERE mod_id=?", (mid,)
        ).fetchone()[0]
        data["localImageCount"] = db.execute(
            "SELECT count(*) FROM images WHERE mod_id=? AND local_path<>''", (mid,)
        ).fetchone()[0]
        db.execute("UPDATE mods SET data=? WHERE id=?", (dumps(data), mid))
        refresh_search(db, mid)


def preview(db, package, allow_partial=False):
    if (
        package.get("format") != "local-mod-catalog"
        or package.get("schemaVersion") != 2
        or not isinstance(package.get("records"), list)
    ):
        raise Problem(
            "invalid_manifest",
            "需要 local-mod-catalog、schemaVersion=2 和 records 数组",
        )
    if len(package["records"]) > 5000:
        raise Problem("too_many_records", "每批最多 5000 条")
    valid, errors, seen, planned = [], [], set(), {}
    # Parents must precede files; no array-position identity matching.
    ordered = sorted(
        enumerate(package["records"]),
        key=lambda pair: (
            0 if isinstance(pair[1], dict) and pair[1].get("kind") == "mod" else 1
        ),
    )
    aliases = {}
    for index, raw in ordered:
        try:
            if not isinstance(raw, dict):
                raise Problem("invalid_record", "记录必须是 JSON 对象")
            kind = raw.get("kind")
            if kind not in ("mod", "file", "image"):
                raise Problem("invalid_kind", "kind 必须是 mod/file/image")
            source = raw.get("source")
            if (
                not isinstance(source, dict)
                or not source.get("reference")
                or source.get("kind") not in ("author", "curated", "inferred")
            ):
                raise Problem("source_required", "每条资料须有来源 kind 和 reference")
            data = dict(raw.get("data", {}))
            game = data.get("game")
            game_row = db.execute("SELECT * FROM games WHERE id=?", (game,)).fetchone()
            if not game_row:
                raise Problem(
                    "game_unregistered", "游戏未登记", next_action="register_game"
                )
            alias = raw.get("alias")
            if not alias:
                raise Problem("alias_required", "每条记录需要稳定的来源 alias")
            alias = game + ":" + kind + ":" + alias
            known = db.execute(
                "SELECT id FROM import_sources WHERE alias=?", (alias,)
            ).fetchone()
            rid = raw.get("resourceId") or (known[0] if known else None)
            if kind == "mod":
                canonical = (
                    game + ":" + str(data["modId"])
                    if isinstance(data.get("modId"), int) and data["modId"] > 0
                    else None
                )
                rid = rid or canonical or game + ":local:" + uuid.uuid4().hex
                if canonical and canonical != rid:
                    raise Problem("identity_conflict", "ModId 与资源身份不一致")
                defaults = dict(
                    name="",
                    author="",
                    function="",
                    details="",
                    requirements=[],
                    tags=[],
                    group="其他",
                    version="",
                    fileCount=0,
                    imageCount=0,
                    localImageCount=0,
                    paths=[],
                    gameTitle=game_row["title"],
                    modId=None,
                )
                for path in data.get("paths", []):
                    registered_path(db, game, path)
            else:
                if data.get("parentAlias"):
                    parent_alias = game + ":mod:" + data.pop("parentAlias")
                    mapped = db.execute(
                        "SELECT id FROM import_sources WHERE alias=?", (parent_alias,)
                    ).fetchone()
                    data["modId"] = aliases.get(parent_alias) or (
                        mapped[0] if mapped else None
                    )
                mid = data.get("modId")
                parent = planned.get(mid)
                if not parent:
                    row = db.execute(
                        "SELECT data FROM mods WHERE id=?", (mid,)
                    ).fetchone()
                    parent = json.loads(row[0]) if row else None
                if not parent or parent["game"] != game:
                    raise Problem(
                        "parent_unmatched",
                        "父 MOD 未匹配；请先导入父条目",
                        next_action="match_parent",
                    )
                if kind == "file":
                    canonical = (
                        mid + ":file:" + str(data["fileId"])
                        if isinstance(data.get("fileId"), int) and data["fileId"] > 0
                        else None
                    )
                    rid = rid or canonical or mid + ":file:local:" + uuid.uuid4().hex
                    if canonical and canonical != rid:
                        raise Problem("identity_conflict", "FileId 与资源身份不一致")
                    defaults = dict(
                        name="",
                        description="",
                        version="",
                        category="",
                        bytes=0,
                        copies=[],
                        requirements=[],
                        fileId=None,
                    )
                    for path in data.get("copies", []):
                        registered_path(db, game, path)
                else:
                    rid = rid or mid + ":image:" + uuid.uuid4().hex
                    defaults = dict(local_path="", remote_url="", caption="", ordinal=0)
                    if data.get("local_path"):
                        registered_path(db, game, data["local_path"])
                    data["source"] = source["reference"]
            if not rid.startswith(game + ":") or rid in seen:
                raise Problem("identity_conflict", "身份游戏不匹配或批次内重复")
            seen.add(rid)
            current = snapshot(db, rid)
            table = {"mod": "mods", "file": "files", "image": "images"}[kind]
            old_rows = current[table]
            old = (
                (
                    json.loads(old_rows[0]["data"])
                    if kind != "image"
                    else dict(old_rows[0])
                )
                if old_rows
                else None
            )
            if old and raw.get("baseRevision") != digest(dumps(old)):
                comparable = dict(old)
                if kind == "image":
                    comparable["modId"] = comparable.pop("mod_id")
                if all(
                    comparable.get(k) == v
                    for k, v in data.items()
                    if k not in ("game", "id")
                ) and not raw.get("translations"):
                    valid.append(
                        dict(
                            kind=kind,
                            id=rid,
                            status="duplicate",
                            data=old,
                            source=source,
                            alias=alias,
                            beforeHash=snapshot_hash(current),
                        )
                    )
                    continue
                raise Problem(
                    "revision_conflict",
                    "现有资料需要当前 baseRevision，不能静默覆盖",
                    status=409,
                    next_action="read_resource",
                    resourceId=rid,
                )
            normalized = dict(defaults, **(old or {}))
            if kind == "file" and old:
                data["copies"] = list(
                    dict.fromkeys(old.get("copies", []) + data.get("copies", []))
                )
            normalized.update(data, id=rid)
            for field in (
                "name",
                "author",
                "function",
                "details",
                "description",
                "version",
                "category",
                "group",
                "caption",
                "remote_url",
                "local_path",
            ):
                if field in normalized and (
                    not isinstance(normalized[field], str)
                    or len(normalized[field]) > 1000000
                ):
                    raise Problem("invalid_field", "文本字段无效", field=field)
            if "requirements" in normalized:
                requirements = normalized["requirements"]
                if not isinstance(requirements, list) or any(
                    not isinstance(r, dict)
                    or not r.get("name")
                    or r.get("kind") not in ("required", "optional", "unknown")
                    or not r.get("evidence")
                    for r in requirements
                ):
                    raise Problem(
                        "invalid_requirements", "依赖必须注明名称、类型和依据"
                    )
            if "tags" in normalized and (
                not isinstance(normalized["tags"], list)
                or len(normalized["tags"]) > 100
                or any(not isinstance(t, str) for t in normalized["tags"])
            ):
                raise Problem("invalid_tags", "标签必须是最多100项的文本数组")
            if kind != "image" and not normalized.get("name"):
                raise Problem("name_required", "名称不能为空")
            if kind == "file" and not normalized.get("fileId"):
                normalized["identityStatus"] = "unmatched"
            planned[rid] = normalized
            aliases[alias] = rid
            imported_translations = raw.get("translations", [])
            if not isinstance(imported_translations, list):
                raise Problem("invalid_translations", "translations 必须是数组")
            for translated_record in imported_translations:
                field = translated_record.get("field")
                original = normalized.get(field, "")
                if (
                    not field
                    or not isinstance(original, str)
                    or not isinstance(translated_record.get("text"), str)
                ):
                    raise Problem("invalid_translation", "译文须有有效字段和文本")
                if translated_record.get("source_hash") == digest(original):
                    from translations import protected_tokens

                    missing = [
                        t
                        for t in protected_tokens(original)
                        if t not in translated_record["text"]
                    ]
                    quality = translation_quality_error(
                        original, translated_record["text"], field
                    )
                    if missing or quality:
                        raise Problem(
                            "translation_invalid",
                            quality or "关键标识被改写",
                            missing=missing,
                        )
            valid.append(
                dict(
                    kind=kind,
                    id=rid,
                    status="update" if old else "new",
                    data=normalized,
                    source=source,
                    alias=alias,
                    beforeHash=snapshot_hash(current),
                    base=old,
                    translations=imported_translations,
                )
            )
        except (Problem, ValueError, TypeError, KeyError) as e:
            errors.append(
                dict(
                    index=index,
                    resourceId=raw.get("resourceId") if isinstance(raw, dict) else None,
                    error=e.payload()
                    if isinstance(e, Problem)
                    else {"code": "invalid_data", "message": str(e)},
                )
            )
    pid = uuid.uuid4().hex
    payload = dict(
        kind="catalog", records=valid, errors=errors, allowPartial=allow_partial
    )
    db.execute(
        "INSERT INTO v2_previews VALUES(?,?,?)", (pid, dumps(payload), time.time())
    )
    return dict(
        previewId=pid,
        valid=len(valid),
        errors=errors,
        canApply=bool(valid) and (not errors or allow_partial),
        changes=[
            dict(
                resourceId=r["id"],
                kind=r["kind"],
                status=r["status"],
                before=r.get("base"),
                after=r["data"],
            )
            for r in valid
        ],
    )


def apply(db, pid):
    row = db.execute("SELECT data FROM v2_previews WHERE id=?", (pid,)).fetchone()
    payload = json.loads(row[0]) if row else {}
    if payload.get("kind") != "catalog":
        raise Problem("preview_expired", "资料预览不存在", next_action="preview_again")
    if payload["errors"] and not payload["allowPartial"]:
        raise Problem("preview_has_errors", "预览有错误；修正或明确选择仅导入合格项")
    before, mids = {}, set()
    for r in payload["records"]:
        if snapshot_hash(snapshot(db, r["id"])) != r["beforeHash"]:
            raise Problem(
                "revision_conflict",
                "预览之后资料已变化",
                status=409,
                next_action="preview_again",
                resourceId=r["id"],
            )
    for r in payload["records"]:
        if r["status"] == "duplicate":
            continue
        before[r["id"]] = snapshot(db, r["id"])
        if r["kind"] != "mod":
            mid = r["data"]["modId"]
            before.setdefault(mid, snapshot(db, mid))
            mids.add(mid)
        put(db, r["kind"], r["data"])
        db.execute(
            "INSERT OR REPLACE INTO import_sources VALUES(?,?,?,?,?,?)",
            (
                r["id"],
                r["kind"],
                dumps(r["data"]),
                dumps(r.get("base")),
                dumps(r["source"]),
                r["alias"],
            ),
        )
        for translated_record in r.get("translations", []):
            values = (
                r["id"],
                translated_record["field"],
                translated_record.get("source_hash", ""),
                translated_record["text"],
                translated_record.get("model", "来源资料包"),
                time.time(),
            )
            db.execute(
                "INSERT INTO translation_history(resource_id,field,source_hash,text,model,imported) VALUES(?,?,?,?,?,?)",
                values,
            )
            # Keep stale provenance in history, never publish it as a current translation.
            if translated_record.get("source_hash") == digest(
                r["data"].get(translated_record["field"], "")
            ):
                db.execute(
                    "INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?,?)", values
                )
    refresh_counts(db, mids)
    bid = save_batch(db, before, "资料包导入")
    db.execute("DELETE FROM v2_previews WHERE id=?", (pid,))
    return dict(batchId=bid, updated=len(before), remaining=payload["errors"])


def reapply(db):
    if not db.execute(
        "SELECT 1 FROM sqlite_master WHERE name='import_sources'"
    ).fetchone():
        return
    mids = set()
    for row in db.execute(
        "SELECT * FROM import_sources ORDER BY CASE kind WHEN 'mod' THEN 0 WHEN 'file' THEN 1 ELSE 2 END"
    ).fetchall():
        wanted = json.loads(row["data"])
        base = json.loads(row["base"])
        table = {"mod": "mods", "file": "files", "image": "images"}[row["kind"]]
        existing = db.execute(
            f"SELECT * FROM {table} WHERE id=?", (row["id"],)
        ).fetchone()
        current = (
            (json.loads(existing["data"]) if row["kind"] != "image" else dict(existing))
            if existing
            else None
        )
        # Compare source data, not effective values containing user edits. Counts
        # are derived from child rows and are never evidence of a source conflict.
        if current and row["kind"] != "image":
            source_row = db.execute(
                "SELECT data FROM resource_base WHERE id=?", (row["id"],)
            ).fetchone()
            if source_row:
                current = json.loads(source_row[0])
        elif current:
            current["modId"] = current.pop("mod_id")
            current["game"] = wanted.get("game")
        derived = (
            {"fileCount", "imageCount", "localImageCount"}
            if row["kind"] == "mod"
            else set()
        )
        if base and row["kind"] == "image" and "mod_id" in base:
            base = dict(base, modId=base["mod_id"], game=wanted.get("game"))
            base.pop("mod_id")
        if current and base:
            changes = {
                k: v for k, v in wanted.items() if k not in derived and base.get(k) != v
            }
            conflicts = [
                k for k in changes if current.get(k) not in (base.get(k), wanted.get(k))
            ]
            if conflicts:
                db.execute(
                    "INSERT OR REPLACE INTO import_conflicts VALUES(?,?)",
                    (
                        row["id"],
                        dumps(
                            dict(
                                resourceId=row["id"],
                                fields=conflicts,
                                source=json.loads(row["source"]),
                            )
                        ),
                    ),
                )
                continue
            wanted = dict(current, **changes)
        elif current and any(
            current.get(k) != wanted.get(k)
            for k in (current.keys() | wanted.keys()) - derived
        ):
            # Existing source now contains an imported new identity: surface collision.
            db.execute(
                "INSERT OR REPLACE INTO import_conflicts VALUES(?,?)",
                (
                    row["id"],
                    dumps(
                        {
                            "resourceId": row["id"],
                            "reason": "来源出现同身份条目，请核对",
                        }
                    ),
                ),
            )
            continue
        db.execute("DELETE FROM import_conflicts WHERE id=?", (row["id"],))
        put(db, row["kind"], wanted)
        mids.add(wanted["id"] if row["kind"] == "mod" else wanted["modId"])
    refresh_counts(db, mids)
