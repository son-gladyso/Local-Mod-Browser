"""Versioned editorial and profile interchange shared by the human UI and AI CLI."""

from __future__ import annotations
import json
import time
import uuid
from catalog import APP, digest, dumps, refresh_search

EDIT_FIELDS = {
    "mod": {
        "name": "string",
        "function": "string",
        "details": "string",
        "compatibility": "string",
        "risk": "string",
        "variantRule": "string",
        "group": "string",
        "tags": "string[]",
        "requirements": "requirement[]",
    },
    "file": {
        "name": "string",
        "description": "string",
        "version": "string",
        "category": "string",
        "requirements": "requirement[]",
    },
}


def read_resource(db, rid):
    for table, kind in (("mods", "mod"), ("files", "file")):
        row = db.execute(f"SELECT data FROM {table} WHERE id=?", (rid,)).fetchone()
        if row:
            data = json.loads(row[0])
            patch = db.execute(
                "SELECT patch FROM edits WHERE resource_id=?", (rid,)
            ).fetchone()
            return {
                "resourceId": rid,
                "kind": kind,
                "revision": digest(dumps(data)),
                "data": data,
                "patch": json.loads(patch[0]) if patch else {},
                "editableFields": EDIT_FIELDS[kind],
            }
    raise ValueError("资源不存在：" + rid)


def validate_edit(db, record):
    if not isinstance(record, dict):
        raise ValueError("编辑记录必须是 JSON 对象")
    rid = record.get("resourceId", "")
    if not isinstance(rid, str) or not rid:
        raise ValueError("resourceId 必须是非空字符串")
    current = read_resource(db, rid)
    if record.get("baseRevision") != current["revision"]:
        raise ValueError("资料已变化，请重新读取 revision 后编辑")
    patch = record.get("patch")
    if not isinstance(patch, dict) or not patch:
        raise ValueError("patch 不能为空，清除覆盖请将字段设为 null")
    for key, value in patch.items():
        kind = EDIT_FIELDS[current["kind"]].get(key)
        if not kind:
            raise ValueError("不允许修改身份、路径或未知字段：" + key)
        if value is None:
            continue
        if kind == "string" and (not isinstance(value, str) or len(value) > 1000000):
            raise ValueError(key + " 必须是文本且不能超过 100 万字符")
        if kind == "string[]" and (
            not isinstance(value, list)
            or len(value) > 100
            or any(not isinstance(x, str) for x in value)
        ):
            raise ValueError(key + " 必须是字符串数组，最多 100 项")
        if kind == "requirement[]":
            if not isinstance(value, list) or any(
                not isinstance(r, dict)
                or not r.get("name")
                or r.get("kind") not in ("required", "optional", "unknown")
                or not r.get("evidence")
                for r in value
            ):
                raise ValueError(
                    "依赖须填写 name、kind(required/optional/unknown)、evidence；不明确时使用 unknown"
                )
            for requirement in value:
                if any(
                    not isinstance(requirement.get(k, ""), str)
                    for k in ("name", "evidence", "notes", "url")
                ):
                    raise ValueError("依赖名称、来源、备注和链接必须是文本")
    return current


def preview_edits(db, records):
    if not isinstance(records, list) or len(records) > 5000:
        raise ValueError("records 必须是数组，每次最多 5000 项")
    valid, invalid, seen = [], [], set()
    for index, record in enumerate(records):
        try:
            current = validate_edit(db, record)
            if current["resourceId"] in seen:
                raise ValueError("同一批内资源重复，请合并 patch")
            seen.add(current["resourceId"])
            valid.append(record)
        except ValueError as e:
            invalid.append(
                {
                    "index": index,
                    "resourceId": record.get("resourceId")
                    if isinstance(record, dict)
                    else None,
                    "error": str(e),
                }
            )
    token = uuid.uuid4().hex
    db.execute(
        "INSERT INTO previews VALUES(?,?,?)",
        (token, dumps({"kind": "edits", "records": valid}), time.time()),
    )
    return {
        "previewId": token,
        "valid": len(valid),
        "errors": invalid,
        "changes": [
            {
                "resourceId": r["resourceId"],
                "fields": list(r["patch"]),
                "note": r.get("note", ""),
            }
            for r in valid
        ],
    }


def apply_preview(db, preview_id):
    row = db.execute(
        "SELECT payload FROM previews WHERE id=?", (preview_id,)
    ).fetchone()
    payload = json.loads(row[0]) if row else {}
    if payload.get("kind") != "edits":
        raise ValueError("编辑预览不存在或类型不匹配")
    for record in payload["records"]:
        validate_edit(db, record)
    affected = set()
    for record in payload["records"]:
        current = read_resource(db, record["resourceId"])
        rid = current["resourceId"]
        patch = dict(current["patch"])
        for key, value in record["patch"].items():
            if value is None:
                patch.pop(key, None)
            else:
                patch[key] = value
        base_row = db.execute(
            "SELECT data FROM resource_base WHERE id=?", (rid,)
        ).fetchone()
        if not base_row:
            raise ValueError("缺少原文快照，请先重建索引")
        data = dict(json.loads(base_row[0]), **patch)
        db.execute(
            "INSERT OR REPLACE INTO edits VALUES(?,?,?)",
            (rid, dumps(patch), time.time()),
        )
        db.execute(
            "INSERT INTO edit_history(resource_id,before_patch,after_patch,note,created) VALUES(?,?,?,?,?)",
            (
                rid,
                dumps(current["patch"]),
                dumps(patch),
                str(record.get("note", "人工或 AI 整理")),
                time.time(),
            ),
        )
        if current["kind"] == "mod":
            db.execute(
                "UPDATE mods SET data=?,name=?,category=? WHERE id=?",
                (dumps(data), data["name"], data.get("group", "其他"), rid),
            )
            affected.add(rid)
        else:
            db.execute("UPDATE files SET data=? WHERE id=?", (dumps(data), rid))
            affected.add(data["modId"])
    for rid in affected:
        refresh_search(db, rid)
    db.execute("DELETE FROM previews WHERE id=?", (preview_id,))
    return {"updated": len(payload["records"])}


def export_content(db, game=""):
    if game and not db.execute("SELECT 1 FROM games WHERE id=?", (game,)).fetchone():
        raise ValueError("游戏不存在")
    records = []
    for row in db.execute(
        "SELECT id FROM mods WHERE (?='' OR game=?) ORDER BY id", (game, game)
    ):
        mod = read_resource(db, row[0])
        mod["schemaVersion"] = 1
        mod["translations"] = [
            dict(r)
            for r in db.execute(
                "SELECT field,source_hash,text,model FROM translations WHERE resource_id=?",
                (row[0],),
            )
        ]
        mod["files"] = [
            read_resource(db, r[0])
            for r in db.execute(
                "SELECT id FROM files WHERE mod_id=? ORDER BY id", (row[0],)
            )
        ]
        for file in mod["files"]:
            file["translations"] = [
                dict(r)
                for r in db.execute(
                    "SELECT field,source_hash,text,model FROM translations WHERE resource_id=?",
                    (file["resourceId"],),
                )
            ]
        records.append(mod)
    name = "catalog-content-" + (game or "all") + "-" + uuid.uuid4().hex[:8] + ".jsonl"
    (APP / "exports").mkdir(exist_ok=True)
    (APP / "exports" / name).write_text(
        "\n".join(dumps(r) for r in records), encoding="utf-8"
    )
    return {
        "schemaVersion": 1,
        "records": len(records),
        "download": "/api/download/" + name,
    }


def preview_profile(db, manifest):
    if (
        not isinstance(manifest, dict)
        or manifest.get("schemaVersion") != 1
        or manifest.get("format") != "local-mod-selection"
    ):
        raise ValueError("需要 schemaVersion=1 的 local-mod-selection 清单")
    game = manifest.get("game")
    if not db.execute("SELECT 1 FROM games WHERE id=?", (game,)).fetchone():
        raise ValueError("清单游戏尚未登记")
    if not isinstance(manifest.get("files"), list) or len(manifest["files"]) > 10000:
        raise ValueError("files 必须是数组，最多 10000 项")
    if not isinstance(manifest.get("profile", {}), dict):
        raise ValueError("profile 必须是对象")
    files, errors, seen = [], [], set()
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            errors.append({"fileId": None, "error": "文件记录必须是对象"})
            continue
        rid = item.get("fileId")
        row = db.execute(
            "SELECT files.data,mods.game FROM files JOIN mods ON mods.id=files.mod_id WHERE files.id=?",
            (rid,),
        ).fetchone()
        if not row or row[1] != game:
            errors.append({"fileId": rid, "error": "文件不存在或游戏不匹配"})
            continue
        f = json.loads(row[0])
        path = item.get("storedPath")
        if (
            path not in f["copies"]
            or item.get("version", "") != f.get("version", "")
            or item.get("bytes") != f.get("bytes")
        ):
            errors.append(
                {"fileId": rid, "error": "副本或版本与当前目录不同，需重新选择"}
            )
            continue
        if rid in seen:
            errors.append({"fileId": rid, "error": "重复文件"})
            continue
        seen.add(rid)
        files.append(
            {
                "fileId": rid,
                "path": path,
                "version": f.get("version", ""),
                "bytes": f.get("bytes", 0),
            }
        )
    token = uuid.uuid4().hex
    payload = {
        "kind": "profile",
        "game": game,
        "name": manifest.get("profile", {}).get("name", "导入搭配"),
        "notes": manifest.get("profile", {}).get("notes", ""),
        "files": files,
    }
    db.execute(
        "INSERT INTO previews VALUES(?,?,?)", (token, dumps(payload), time.time())
    )
    return {
        "previewId": token,
        "valid": len(files),
        "errors": errors,
        "game": game,
        "suggestedName": payload["name"] + "（导入）",
    }


def import_profile(db, preview_id, name):
    row = db.execute(
        "SELECT payload FROM previews WHERE id=?", (preview_id,)
    ).fetchone()
    p = json.loads(row[0]) if row else {}
    if p.get("kind") != "profile":
        raise ValueError("搭配导入预览不存在")
    for i in p["files"]:
        row = db.execute("SELECT data FROM files WHERE id=?", (i["fileId"],)).fetchone()
        f = json.loads(row[0]) if row else {}
        if (
            i["path"] not in f.get("copies", [])
            or i["version"] != f.get("version")
            or i["bytes"] != f.get("bytes")
        ):
            raise ValueError("预览之后目录已变化，请重新导入")
    pid = uuid.uuid4().hex
    db.execute(
        "INSERT INTO profiles VALUES(?,?,?,?,?)",
        (pid, p["game"], name, p["notes"], time.time()),
    )
    db.executemany(
        "INSERT INTO selections VALUES(?,?,?,?,?)",
        [(pid, i["fileId"], i["path"], i["version"], i["bytes"]) for i in p["files"]],
    )
    db.execute("DELETE FROM previews WHERE id=?", (preview_id,))
    return {"id": pid, "count": len(p["files"])}
