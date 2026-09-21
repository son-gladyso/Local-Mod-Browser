from __future__ import annotations
import argparse
import collections
import json
import mimetypes
import os
import pathlib
import secrets
import sqlite3
import subprocess
import threading
import time
import traceback
import uuid
import sys
from contextlib import closing
from contracts import Problem, OPS, VERSION
from observability import reset_request_id, set_request_id
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse
from catalog import (
    APP,
    connect,
    digest,
    dumps,
    initialize,
    rebuild,
    setting,
    set_setting,
    resolved_path,
    file_status,
    translated,
    translation_status,
)
import translations
import content
from write_scheduler import FairWriteGate

DB_PATH = APP / "data/catalog.sqlite3"
STORAGE = APP
TOKEN = secrets.token_urlsafe(32)
JOBS = {}
JOB_LOCK = threading.Lock()
WRITE_LOCK = FairWriteGate(foreground_ratio=4, background_max_wait=2.0)
SERVICE_NAME = "local-mod-browser"
PLATFORM = None
HTTPD = None


class ApiError(Exception):
    def __init__(self, message, code="invalid_request", status=400):
        super().__init__(message)
        self.code = code
        self.status = status


def required(data, name):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ApiError("缺少有效字段：" + name)
    return value.strip()


def start_job(kind, action):
    with JOB_LOCK:
        if any(j["status"] == "running" for j in JOBS.values()):
            raise ApiError("后台任务正在运行，请等待完成或先停止。", "job_busy", 409)
        jid = uuid.uuid4().hex
        job = {
            "id": jid,
            "kind": kind,
            "status": "running",
            "message": "准备中",
            "done": 0,
            "total": 0,
            "cancel": False,
            "started": time.time(),
        }
        JOBS[jid] = job

    def worker():
        try:
            with WRITE_LOCK:
                result = action(lambda **kw: job.update(kw), lambda: job["cancel"])
            job.update(status="complete", result=result, message="已完成")
        except InterruptedError as e:
            job.update(status="cancelled", message=str(e))
        except Exception as e:
            job.update(status="failed", message=str(e), error=type(e).__name__)
        finally:
            job["finished"] = time.time()

    threading.Thread(target=worker, daemon=True).start()
    return dict(job)


def public_mod(db, item, detail=False, projected_status=None):
    rid = item["id"]
    zh = translated(db, rid)
    favorite = bool(
        db.execute("SELECT 1 FROM favorites WHERE mod_id=?", (rid,)).fetchone()
    )
    image = db.execute(
        "SELECT id FROM images WHERE mod_id=? ORDER BY (local_path<>'') DESC,ordinal LIMIT 1",
        (rid,),
    ).fetchone()
    if not detail:
        keep = (
            "id",
            "game",
            "gameTitle",
            "modId",
            "name",
            "author",
            "group",
            "adult",
            "downloads",
            "endorsements",
            "updated",
            "fileCount",
            "copyCount",
            "imageCount",
            "localImageCount",
            "tags",
            "version",
        )
        output = {k: item.get(k) for k in keep}
        output["summary"] = (
            zh.get("function") or item.get("function") or "作者未提供摘要"
        )[:350]
    else:
        output = dict(item)
    output.update(
        zh=zh if detail else {"name": zh.get("name", "")},
        favorite=favorite,
        translationStatus=projected_status or translation_status(db, item),
        cover=("/api/image/" + image[0]) if image else "",
    )
    if detail:
        output["revision"] = digest(dumps(item))
    return output


def _list_filter(query, key):
    value = query.get(key, [])
    if isinstance(value, str):
        if value.startswith("["):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise ApiError("标签筛选必须是 JSON 数组") from error
        elif value:
            value = [value]
        else:
            value = []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ApiError("标签筛选必须是字符串数组")
    return list(dict.fromkeys(item for item in value if item))


def _filter_sql(query, exclude=()):
    """Build shared catalogue predicates; facets omit their own dimension."""
    exclude = set(exclude)
    params, conditions = [], []
    for field, column in (("game", "game"), ("category", "category"), ("author", "author")):
        if field not in exclude and query.get(field):
            conditions.append("q." + column + "=?")
            params.append(query[field])
    if "adult" not in exclude and query.get("adult") in ("yes", "no"):
        conditions.append("q.adult=?")
        params.append(int(query["adult"] == "yes"))
    if query.get("favorite") in ("1", True):
        conditions.append("q.mod_id IN (SELECT mod_id FROM favorites)")
    if query.get("recent") in ("1", True):
        conditions.append("q.mod_id IN (SELECT mod_id FROM recent)")
    if query.get("variants") in ("1", True):
        conditions.append("q.file_count>1")
    if query.get("localImages") in ("1", True):
        conditions.append("q.local_image_count>0")
    for field, operator in (("updatedFrom", ">="), ("updatedTo", "<=")):
        if query.get(field) not in (None, ""):
            try:
                updated = int(query[field])
            except (TypeError, ValueError) as error:
                raise ApiError("更新时间范围必须是 Unix 秒数") from error
            conditions.append("q.updated" + operator + "?")
            params.append(updated)
    for term in query.get("q", "").casefold().split():
        # instr avoids interpreting user wildcard characters as SQL patterns.
        conditions.append("instr(q.search_text,?)>0")
        params.append(term)
    if "translation" not in exclude and query.get("translation"):
        conditions.append("q.translation_status=?")
        params.append(query["translation"])
    if "tags" not in exclude:
        all_tags = _list_filter(query, "tagsAll")
        if query.get("tag") and query["tag"] not in all_tags:
            all_tags.append(query["tag"])
        for tag in all_tags:
            conditions.append(
                "EXISTS (SELECT 1 FROM mod_tags mt WHERE mt.mod_id=q.mod_id AND mt.tag=?)"
            )
            params.append(tag)
        any_tags = _list_filter(query, "tagsAny")
        if any_tags:
            marks = ",".join("?" for _ in any_tags)
            conditions.append(
                f"EXISTS (SELECT 1 FROM mod_tags mt WHERE mt.mod_id=q.mod_id AND mt.tag IN ({marks}))"
            )
            params.extend(any_tags)
        excluded_tags = _list_filter(query, "tagsExclude")
        if excluded_tags:
            marks = ",".join("?" for _ in excluded_tags)
            conditions.append(
                f"NOT EXISTS (SELECT 1 FROM mod_tags mt WHERE mt.mod_id=q.mod_id AND mt.tag IN ({marks}))"
            )
            params.extend(excluded_tags)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where, params


def list_mods(db, query):
    page = max(1, int(query.get("page", 1)))
    limit = min(96, max(1, int(query.get("limit", 48))))
    order = {
        "downloads": "q.downloads DESC,q.mod_id",
        "updated": "q.updated DESC,q.mod_id",
        "name": "m.name COLLATE NOCASE,q.mod_id",
        "endorsements": "q.endorsements DESC,q.mod_id",
        "files": "q.file_count DESC,q.mod_id",
        "size": "q.size_mb DESC,q.mod_id",
        "recent": "(SELECT visited FROM recent WHERE mod_id=q.mod_id) DESC,q.mod_id",
    }.get(query.get("sort"), "q.downloads DESC,q.mod_id")
    where, params = _filter_sql(query)
    tables = " FROM mod_query q JOIN mods m ON m.id=q.mod_id"
    total = db.execute("SELECT count(*)" + tables + where, params).fetchone()[0]
    rows = db.execute(
        "SELECT m.data,q.translation_status"
        + tables
        + where
        + " ORDER BY "
        + order
        + " LIMIT ? OFFSET ?",
        params + [limit, (page - 1) * limit],
    )
    return {
        "items": [
            public_mod(db, json.loads(row[0]), projected_status=row[1])
            for row in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, (total + limit - 1) // limit),
    }


def facet_counts(db, query):
    result = {}
    for output, dimension, column in (
        ("categories", "category", "q.category"),
        ("authors", "author", "q.author"),
    ):
        where, params = _filter_sql(query, {dimension})
        rows = db.execute(
            f"SELECT {column},count(*) AS total FROM mod_query q{where} "
            f"GROUP BY {column} ORDER BY total DESC,{column} COLLATE NOCASE",
            params,
        )
        result[output] = {row[0]: row[1] for row in rows if row[0]}
    where, params = _filter_sql(query, {"tags"})
    rows = db.execute(
        "SELECT mt.tag,count(*) AS total FROM mod_tags mt "
        "JOIN mod_query q ON q.mod_id=mt.mod_id"
        + where
        + " GROUP BY mt.tag ORDER BY total DESC,mt.tag COLLATE NOCASE",
        params,
    )
    result["tags"] = {row[0]: row[1] for row in rows}
    return result


SAVED_FILTER_FIELDS = {
    "q",
    "category",
    "author",
    "adult",
    "translation",
    "variants",
    "localImages",
    "sort",
    "tagsAll",
    "tagsAny",
    "tagsExclude",
    "updatedFrom",
    "updatedTo",
}


def _public_saved_filter(row):
    value = json.loads(row["data"])
    return dict(value, revision=digest(row["data"]))


def list_saved_filters(db):
    return [
        _public_saved_filter(row)
        for row in db.execute("SELECT * FROM saved_filters ORDER BY name COLLATE NOCASE")
    ]


def save_filter(db, body):
    name = required(body, "name").strip()[:120]
    if not name:
        raise ApiError("筛选名称不能为空")
    game = body.get("game", "")
    if game and not db.execute("SELECT 1 FROM games WHERE id=?", (game,)).fetchone():
        raise ApiError("游戏不存在", "not_found", 404)
    filters = body.get("filters", {})
    if not isinstance(filters, dict):
        raise ApiError("筛选条件必须是对象")
    unknown = set(filters) - SAVED_FILTER_FIELDS
    if unknown:
        raise ApiError("筛选包含未知字段：" + "、".join(sorted(unknown)))
    clean = {key: value for key, value in filters.items() if value not in (None, "", [])}
    for key in ("tagsAll", "tagsAny", "tagsExclude"):
        if key in clean:
            clean[key] = _list_filter(clean, key)
    for key in ("updatedFrom", "updatedTo"):
        if key in clean:
            try:
                clean[key] = int(clean[key])
            except (TypeError, ValueError) as error:
                raise ApiError("更新时间范围必须是 Unix 秒数") from error
    filter_id = body.get("id") or uuid.uuid4().hex
    row = db.execute("SELECT * FROM saved_filters WHERE id=?", (filter_id,)).fetchone()
    now = time.time()
    if row:
        if body.get("revision") != digest(row["data"]):
            raise ApiError("筛选已经变化，请重新读取", "revision_conflict", 409)
        created = row["created"]
    else:
        created = now
    value = dict(
        id=filter_id,
        name=name,
        game=game,
        filters=clean,
        created=created,
        updated=now,
    )
    db.execute(
        "INSERT INTO saved_filters VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,game=excluded.game,data=excluded.data,updated=excluded.updated",
        (filter_id, name, game, dumps(value), created, now),
    )
    return dict(value, revision=digest(dumps(value)))


def delete_filter(db, body):
    row = db.execute(
        "SELECT * FROM saved_filters WHERE id=?", (required(body, "id"),)
    ).fetchone()
    if not row:
        raise ApiError("已保存筛选不存在", "not_found", 404)
    if body.get("revision") != digest(row["data"]):
        raise ApiError("筛选已经变化，请重新读取", "revision_conflict", 409)
    db.execute("DELETE FROM saved_filters WHERE id=?", (row["id"],))
    return {"deleted": True, "id": row["id"]}


def get_detail(db, rid):
    row = db.execute("SELECT data FROM mods WHERE id=?", (rid,)).fetchone()
    if not row:
        raise ApiError("目录中没有这个 MOD", "not_found", 404)
    item = public_mod(db, json.loads(row[0]), True)
    files = []
    for row in db.execute(
        "SELECT data FROM files WHERE mod_id=? ORDER BY nexus_id,id", (rid,)
    ):
        f = json.loads(row[0])
        f["zh"] = translated(db, f["id"])
        f["copies"] = [dict(file_status(db, p), storedPath=p) for p in f["copies"]]
        files.append(f)
    item["files"] = files
    for req in item.get("requirements", []):
        target = item["game"] + ":" + str(req.get("modId"))
        req["resourceId"] = (
            target
            if db.execute("SELECT 1 FROM mods WHERE id=?", (target,)).fetchone()
            else None
        )
        req["availability"] = (
            "已收录，未确认已安装" if req["resourceId"] else "未匹配本地目录"
        )
    return item


def profile_details(db, pid):
    row = db.execute("SELECT * FROM profiles WHERE id=?", (pid,)).fetchone()
    if not row:
        raise ApiError("搭配不存在", "not_found", 404)
    profile = dict(row)
    items = []
    for selection in db.execute(
        "SELECT * FROM selections WHERE profile_id=? ORDER BY file_id", (pid,)
    ):
        file_row = db.execute(
            "SELECT data FROM files WHERE id=?", (selection["file_id"],)
        ).fetchone()
        f = (
            json.loads(file_row[0])
            if file_row
            else {
                "id": selection["file_id"],
                "name": "目录中已不存在的文件",
                "copies": [],
            }
        )
        mod = db.execute(
            "SELECT data FROM mods WHERE id=?", (f.get("modId", ""),)
        ).fetchone()
        m = json.loads(mod[0]) if mod else {}
        status = file_status(db, selection["copy_path"])
        changed = bool(
            file_row
            and (
                selection["version"] != f.get("version", "")
                or selection["bytes"] != f.get("bytes", 0)
            )
        )
        items.append(
            {
                "fileId": f["id"],
                "nexusFileId": f.get("fileId"),
                "modId": f.get("modId"),
                "modName": m.get("name", ""),
                "name": f["name"],
                "version": selection["version"],
                "bytes": selection["bytes"],
                "storedPath": selection["copy_path"],
                "fileStatus": status,
                "changed": changed
                or (
                    status.get("actualBytes", selection["bytes"]) != selection["bytes"]
                ),
                "orphan": not bool(file_row),
                "requirements": m.get("requirements", []) + f.get("requirements", []),
                "risk": m.get("risk", ""),
                "source": m.get("nexus", ""),
                "copies": f.get("copies", []),
            }
        )
    profile["items"] = items
    counts = collections.Counter(i["modId"] for i in items)
    warnings = [
        {
            "kind": "multipleFiles",
            "modId": mid,
            "message": "同一 MOD 选了多个文件，请核实变体和可选组件能否共用。",
        }
        for mid, n in counts.items()
        if n > 1
    ]
    selected_mods = set(counts)
    for i in items:
        for req in i["requirements"]:
            target = profile["game"] + ":" + str(req.get("modId"))
            if req.get("kind", "unknown") == "required" and target not in selected_mods:
                warnings.append(
                    {
                        "kind": "dependency",
                        "message": f"{i['modName']} 的前置未在本搭配中：{req['name']}（可能已单独安装，请核实）",
                    }
                )
    profile["warnings"] = warnings
    return profile


def export_profile(db, pid, format):
    p = profile_details(db, pid)
    payload = {
        "schemaVersion": 1,
        "format": "local-mod-selection",
        "created": time.time(),
        "game": p["game"],
        "profile": {"id": p["id"], "name": p["name"], "notes": p["notes"]},
        "files": p["items"],
        "warnings": p["warnings"],
        "installationPerformed": False,
        "compatibility": "中立文件清单，尚未适配 GMM 原生格式",
    }
    if format == "txt":
        blocks = [
            f"{p['name']} · {p['game']}\n{p['notes']}\n仅列出已选择的具体文件；未执行安装。"
        ]
        for i in p["items"]:
            blocks.append(
                f"{i['modName']}\n  文件：{i['name']} | FileId {i['nexusFileId']} | 版本 {i['version'] or '待补充'}\n  路径：{i['fileStatus']['path']}\n  状态：{i['fileStatus']['label']}\n  来源：{i['source']}\n  前置：{'; '.join(r['name'] for r in i['requirements']) or '未记录，需核对作者说明'}\n  风险：{i['risk'] or '未记录'}"
            )
        blocks.extend("提示：" + w["message"] for w in p["warnings"])
        content = "\n\n".join(blocks)
    else:
        content = json.dumps(payload, ensure_ascii=False, indent=2)
    name = (
        "selection-"
        + pid
        + "-"
        + uuid.uuid4().hex[:8]
        + (".txt" if format == "txt" else ".json")
    )
    (STORAGE / "exports").mkdir(exist_ok=True)
    temporary = (STORAGE / "exports" / name).with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8-sig" if format == "txt" else "utf-8")
    temporary.replace(STORAGE / "exports" / name)
    return {"download": "/api/download/" + name, "manifest": payload}


API_DOC = {
    "version": 1,
    "platform": {
        "version": VERSION,
        "capabilities": "/api/v2/capabilities",
        "openapi": "/api/v2/openapi",
        "cli": "python ai.py capabilities",
    },
    "service": SERVICE_NAME,
    "read": [
        "GET /api/schema",
        "GET /api/facets?game=GAME",
        "GET /api/resource?id=RESOURCE_ID",
        "GET /api/content/history?id=RESOURCE_ID",
        "GET /api/health",
        "GET /api/games",
        "GET /api/mods?q=&game=&category=&tag=&author=&sort=downloads|endorsements|updated|name|files|size|recent&adult=yes|no&translation=missing|pending|partial|complete|review|stale&favorite=1&variants=1&localImages=1&page=1&limit=48",
        "GET /api/mod?id=RESOURCE_ID",
        "GET /api/images?id=RESOURCE_ID&page=1",
        "GET /api/profiles?game=GAME",
        "GET /api/profile?id=PROFILE_ID",
        "GET /api/translations",
        "GET /api/jobs",
        "GET /api/settings",
        "GET /api/saved-filters",
    ],
    "write": {
        "/api/backup": {},
        "/api/content/export": {"game": "optional game ID"},
        "/api/content/preview": {
            "records": [
                {
                    "resourceId": "ID",
                    "baseRevision": "revision",
                    "patch": {"function": "text"},
                    "note": "reason",
                }
            ]
        },
        "/api/content/apply": {"previewId": "preview ID"},
        "/api/profile/preview": {"manifest": "local-mod-selection object"},
        "/api/profile/import": {"previewId": "preview ID", "name": "new profile name"},
        "/api/favorite": {"id": "resource ID", "enabled": True},
        "/api/recent": {"id": "resource ID"},
        "/api/profile/save": {
            "id": "optional",
            "game": "game ID",
            "name": "name",
            "notes": "text",
        },
        "/api/profile/copy": {"id": "profile ID", "name": "new name"},
        "/api/profile/delete": {"id": "profile ID"},
        "/api/profile/select": {
            "profileId": "profile ID",
            "fileId": "file resource ID",
            "copyPath": "exact stored path",
            "selected": True,
        },
        "/api/profile/export": {"id": "profile ID", "format": "json|txt"},
        "/api/translations/export": {
            "pilot": True,
            "game": "optional game ID",
            "modId": "optional resource ID",
        },
        "/api/translations/preview": {"content": "results.jsonl text"},
        "/api/translations/import": {"previewId": "server preview ID"},
        "/api/reindex": {},
        "/api/images/check": {},
        "/api/jobs/cancel": {"id": "job ID"},
        "/api/settings": {"key": "view", "value": {}},
        "/api/saved-filters/save": {"name": "筛选名称", "game": "GAME", "filters": {}},
        "/api/saved-filters/delete": {"id": "筛选 ID", "revision": "当前版本"},
        "/api/roots": {"old": "registered root", "new": "existing replacement root"},
        "/api/reveal": {"fileId": "file resource ID", "copyPath": "exact stored path"},
    },
    "auth": "Same-origin UI gets token from /api/bootstrap. Local CLI reads data/runtime.json; POST uses X-Mod-Token. Never expose the token in shared logs.",
    "response": {"ok": True, "data": "result"},
    "error": {
        "ok": False,
        "error": {"code": "stable code", "message": "readable explanation"},
    },
}


def get_api(path, query):
    if path.startswith("/api/v2/"):
        name = path.removeprefix("/api/v2/")
        spec = OPS.get(name)
        if not spec:
            raise Problem("not_found", "能力不存在", status=404)
        converted = dict(query)
        for key, value in query.items():
            schema = spec["inputSchema"]["properties"].get(key, {})
            if schema.get("type") in ("integer", "boolean", "array", "object"):
                try:
                    converted[key] = (
                        json.loads(value) if isinstance(value, str) else value
                    )
                except ValueError as error:
                    raise Problem(
                        "invalid_parameter", "参数必须是有效 JSON", field=key
                    ) from error
        return PLATFORM.invoke(name, converted, method="GET")
    with connect(DB_PATH) as db:
        if path == "/api/health":
            return {
                "service": SERVICE_NAME,
                "version": 1,
                "contractVersion": VERSION if PLATFORM else None,
                "pythonVersion": sys.version.split()[0],
                "sqliteVersion": sqlite3.sqlite_version,
                "pid": os.getpid(),
                "database": str(DB_PATH.resolve()),
                "mods": db.execute("SELECT count(*) FROM mods").fetchone()[0],
                "index": setting(db, "lastIndex", {}),
                "busy": PLATFORM.runtime.busy()
                if PLATFORM
                else any(j["status"] == "running" for j in JOBS.values()),
            }
        if path == "/api/schema":
            return json.loads((APP / "schemas.json").read_text(encoding="utf-8"))
        if path == "/api/bootstrap":
            return {
                "token": TOKEN,
                "title": "本地 MOD 浏览器",
                "lastIndex": setting(db, "lastIndex", {}),
                "view": setting(db, "view", {}),
            }
        if path == "/api/docs":
            return dict(
                API_DOC,
                editorialFields=content.EDIT_FIELDS,
                interchange={
                    "read": "GET /api/resource?id=RESOURCE_ID",
                    "history": "GET /api/content/history?id=RESOURCE_ID",
                    "export": "POST /api/content/export {game: optional}",
                    "preview": "POST /api/content/preview {records:[{resourceId,baseRevision,patch,note}]}",
                    "apply": "POST /api/content/apply {previewId}",
                    "profilePreview": "POST /api/profile/preview {manifest}",
                    "profileImport": "POST /api/profile/import {previewId,name}",
                },
            )
        if path == "/api/resource":
            return content.read_resource(db, required(query, "id"))
        if path == "/api/content/history":
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM edit_history WHERE resource_id=? ORDER BY id DESC LIMIT 100",
                    (required(query, "id"),),
                )
            ]
        if path == "/api/settings":
            return {
                "view": setting(db, "view", {}),
                "roots": setting(db, "roots", {}),
                "lastIndex": setting(db, "lastIndex", {}),
            }
        if path == "/api/saved-filters":
            return list_saved_filters(db)
        if path == "/api/games":
            games = [
                dict(r)
                for r in db.execute(
                    "SELECT games.*, (SELECT count(*) FROM mods WHERE game=games.id) count FROM games ORDER BY CASE WHEN id='stellarblade' THEN 0 ELSE 1 END,title"
                )
            ]
            for g in games:
                g["available"] = pathlib.Path(resolved_path(db, g["root"])).exists()
            return games
        if path == "/api/facets":
            return facet_counts(db, query)
        if path == "/api/mods":
            return list_mods(db, query)
        if path == "/api/mod":
            return get_detail(db, required(query, "id"))
        if path == "/api/images":
            rid = required(query, "id")
            page = max(1, int(query.get("page", 1)))
            rows = db.execute(
                "SELECT * FROM images WHERE mod_id=? ORDER BY ordinal LIMIT 24 OFFSET ?",
                (rid, (page - 1) * 24),
            )
            return {
                "items": [
                    dict(r, src="/api/image/" + r["id"], zh=translated(db, r["id"]))
                    for r in rows
                ],
                "total": db.execute(
                    "SELECT count(*) FROM images WHERE mod_id=?", (rid,)
                ).fetchone()[0],
                "page": page,
            }
        if path == "/api/profiles":
            return [
                dict(r)
                for r in db.execute(
                    "SELECT profiles.*,(SELECT count(*) FROM selections WHERE profile_id=profiles.id) count FROM profiles WHERE (?='' OR game=?) ORDER BY updated DESC",
                    (query.get("game", ""), query.get("game", "")),
                )
            ]
        if path == "/api/profile":
            return profile_details(db, required(query, "id"))
        if path == "/api/jobs":
            if PLATFORM:
                return PLATFORM.runtime.listing("jobs", {"limit": 96})["items"]
            return list(JOBS.values())[-10:]
        if path == "/api/translations":
            counts = collections.Counter()
            issues = []
            for row in db.execute("SELECT data FROM mods"):
                m = json.loads(row[0])
                status = translation_status(db, m)
                counts[status] += 1
                if status in ("review", "stale"):
                    issues.append({"id": m["id"], "name": m["name"], "status": status})
            errors = [
                dict(r)
                for r in db.execute(
                    "SELECT id,resource_id,field,error FROM translation_tasks WHERE status='review' LIMIT 100"
                )
            ]
            packages = [
                {"name": p.name, "download": "/api/download/" + p.name}
                for p in sorted((STORAGE / "exports").glob("Gemini*.zip"), reverse=True)
            ]
            return {
                "counts": counts,
                "issues": issues,
                "errors": errors,
                "packages": packages,
                "model": translations.MODEL,
            }
    raise ApiError("接口不存在", "not_found", 404)


def check_images(progress, cancelled):
    with connect(DB_PATH) as db:
        rows = list(db.execute("SELECT id,local_path FROM images"))
        missing = []
        checked = 0
        for r in rows:
            if cancelled():
                raise InterruptedError("图片检查已停止。")
            if (
                r["local_path"]
                and not pathlib.Path(resolved_path(db, r["local_path"])).is_file()
            ):
                missing.append(r["id"])
            checked += 1
            if checked % 100 == 0:
                progress(
                    message=f"检查图片 {checked}/{len(rows)}",
                    done=checked,
                    total=len(rows),
                )
        report = {
            "checked": checked,
            "missing": len(missing),
            "missingIds": missing,
            "at": time.time(),
        }
        set_setting(db, "imageCheck", report)
        return report


def post_api(path, body):
    if path.startswith("/api/v2/"):
        return PLATFORM.invoke(path.removeprefix("/api/v2/"), body, method="POST")
    if PLATFORM:
        jobs = {
            "/api/reindex": "maintenance.index",
            "/api/images/check": "maintenance.images",
            "/api/translations/export": "translations.export",
            "/api/translations/import": "translations.import",
        }
        if path in jobs:
            return PLATFORM.invoke(jobs[path], body)
        if path == "/api/translations/preview":
            return PLATFORM.invoke(
                "translations.preview", dict(body, allowPartial=True)
            )
        if path == "/api/jobs/cancel":
            return PLATFORM.invoke(
                "jobs.control", {"id": required(body, "id"), "action": "cancel"}
            )
    if path == "/api/reindex":
        return start_job("index", lambda p, c: rebuild(DB_PATH, p, c))
    if path == "/api/images/check":
        return start_job("images", check_images)
    if path == "/api/translations/export":
        return start_job(
            "translation-export",
            lambda p, c: translations.export_package(DB_PATH, body, p, c),
        )
    if path == "/api/translations/import":
        pid = required(body, "previewId")
        return start_job(
            "translation-import",
            lambda p, c: translations.apply_import(DB_PATH, pid, p, c),
        )
    if path == "/api/jobs/cancel":
        job = JOBS.get(required(body, "id"))
        if not job:
            raise ApiError("任务不存在", "not_found", 404)
        job["cancel"] = True
        return job
    with WRITE_LOCK, connect(DB_PATH) as db:
        if path == "/api/content/export":
            return content.export_content(db, body.get("game", ""))
        if path == "/api/content/preview":
            return content.preview_edits(db, body.get("records"))
        if path == "/api/content/apply":
            return content.apply_preview(db, required(body, "previewId"))
        if path == "/api/profile/preview":
            return content.preview_profile(db, body.get("manifest"))
        if path == "/api/profile/import":
            return content.import_profile(
                db, required(body, "previewId"), required(body, "name")
            )
        if path in ("/api/favorite", "/api/recent"):
            rid = required(body, "id")
            if not db.execute("SELECT 1 FROM mods WHERE id=?", (rid,)).fetchone():
                raise ApiError("MOD 不存在", "not_found", 404)
            if path.endswith("favorite"):
                if body.get("enabled"):
                    db.execute(
                        "INSERT OR REPLACE INTO favorites VALUES(?,?)",
                        (rid, time.time()),
                    )
                else:
                    db.execute("DELETE FROM favorites WHERE mod_id=?", (rid,))
            else:
                db.execute(
                    "INSERT OR REPLACE INTO recent VALUES(?,?)", (rid, time.time())
                )
            return {"id": rid}
        if path == "/api/settings":
            key = required(body, "key")
            if key not in ("view", "language"):
                raise ApiError("不支持的设置项")
            set_setting(db, key, body.get("value"))
            return {"saved": True}
        if path == "/api/saved-filters/save":
            return save_filter(db, body)
        if path == "/api/saved-filters/delete":
            return delete_filter(db, body)
        if path == "/api/roots":
            old, new = required(body, "old"), required(body, "new")
            if not db.execute("SELECT 1 FROM games WHERE root=?", (old,)).fetchone():
                raise ApiError("只允许重定位已登记的游戏资料根目录")
            if not pathlib.Path(new).is_absolute() or not pathlib.Path(new).is_dir():
                raise ApiError("新目录不存在或不是绝对路径")
            mappings = setting(db, "roots", {})
            mappings[old] = new
            set_setting(db, "roots", mappings)
            return {"saved": True, "old": old, "new": new}
        if path == "/api/profile/save":
            pid = body.get("id") or uuid.uuid4().hex
            game = required(body, "game")
            name = required(body, "name")[:120]
            if not db.execute("SELECT 1 FROM games WHERE id=?", (game,)).fetchone():
                raise ApiError("游戏不存在")
            old = db.execute("SELECT game FROM profiles WHERE id=?", (pid,)).fetchone()
            if old and old[0] != game:
                raise ApiError("不能更改现有搭配所属游戏")
            db.execute(
                "INSERT INTO profiles VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,notes=excluded.notes,updated=excluded.updated",
                (pid, game, name, str(body.get("notes", ""))[:10000], time.time()),
            )
            return {"id": pid}
        if path == "/api/profile/delete":
            db.execute("DELETE FROM profiles WHERE id=?", (required(body, "id"),))
            return {"deleted": True}
        if path == "/api/profile/copy":
            old = profile_details(db, required(body, "id"))
            pid = uuid.uuid4().hex
            db.execute(
                "INSERT INTO profiles VALUES(?,?,?,?,?)",
                (
                    pid,
                    old["game"],
                    required(body, "name")[:120],
                    old["notes"],
                    time.time(),
                ),
            )
            db.execute(
                "INSERT INTO selections SELECT ?,file_id,copy_path,version,bytes FROM selections WHERE profile_id=?",
                (pid, old["id"]),
            )
            return {"id": pid}
        if path == "/api/profile/select":
            pid, fid = required(body, "profileId"), required(body, "fileId")
            p = db.execute("SELECT game FROM profiles WHERE id=?", (pid,)).fetchone()
            if not p:
                raise ApiError("搭配不存在")
            if body.get("selected") is False:
                db.execute(
                    "DELETE FROM selections WHERE profile_id=? AND file_id=?",
                    (pid, fid),
                )
            else:
                row = db.execute(
                    "SELECT files.data,mods.game FROM files JOIN mods ON files.mod_id=mods.id WHERE files.id=?",
                    (fid,),
                ).fetchone()
                if not row or row[1] != p[0]:
                    raise ApiError("该文件不属于此游戏搭配")
                f = json.loads(row[0])
                copy = required(body, "copyPath")
                if copy not in f["copies"]:
                    raise ApiError("选择的副本不在文件清单内")
                db.execute(
                    "INSERT OR REPLACE INTO selections VALUES(?,?,?,?,?)",
                    (pid, fid, copy, f.get("version", ""), f.get("bytes", 0)),
                )
            db.execute("UPDATE profiles SET updated=? WHERE id=?", (time.time(), pid))
            return {"selected": body.get("selected") is not False}
        if path == "/api/profile/export":
            return export_profile(db, required(body, "id"), body.get("format", "json"))
        if path == "/api/reveal":
            row = db.execute(
                "SELECT data FROM files WHERE id=?", (required(body, "fileId"),)
            ).fetchone()
            copy = required(body, "copyPath")
            if not row or copy not in json.loads(row[0])["copies"]:
                raise ApiError("未登记的文件路径")
            status = file_status(db, copy)
            if status["status"] != "available":
                raise ApiError(status["label"], "file_unavailable")
            subprocess.Popen(["explorer.exe", "/select,", status["path"]])
            return {"opened": True}
        if path == "/api/translations/preview":
            return translations.preview_import(DB_PATH, required(body, "content"))
        if path == "/api/backup":
            folder = STORAGE / "backups"
            folder.mkdir(exist_ok=True)
            target = folder / (
                time.strftime("personal-%Y%m%d-%H%M%S-")
                + uuid.uuid4().hex[:6]
                + ".sqlite3"
            )
            with closing(sqlite3.connect(target)) as dest:
                db.backup(dest)
            return {"path": str(target)}
    raise ApiError("接口不存在", "not_found", 404)


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalModBrowser/1"

    def log_message(self, fmt, *args):
        pass

    def reply(
        self,
        status,
        data,
        content_type="application/json; charset=utf-8",
        *,
        cache_control=None,
    ):
        serialize_started = time.monotonic()
        raw = dumps(data).encode("utf-8") if isinstance(data, (dict, list)) else data
        if PLATFORM:
            PLATFORM.metrics.observe(
                "http", "result_serialization", time.monotonic() - serialize_started
            )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Request-ID", getattr(self, "request_id", ""))
        cache = (
            "private,max-age=3600" if content_type.startswith("image/") else "no-store"
        )
        self.send_header("Cache-Control", cache_control or cache)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        try:
            self.end_headers()
            self.wfile.write(raw)
        except ConnectionError:
            pass

    def authorized_host(self):
        host = self.headers.get("Host", "")
        return host in (
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        )

    def do_GET(self):
        self.request_id = uuid.uuid4().hex
        request_token = set_request_id(self.request_id)
        try:
            parse_started = time.monotonic()
            if not self.authorized_host():
                raise ApiError("只接受本机访问", "host_denied", 403)
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
            if PLATFORM:
                PLATFORM.metrics.observe(
                    "http", "request_parsing", time.monotonic() - parse_started
                )
            if path.startswith("/api/image/"):
                with connect(DB_PATH) as db:
                    row = db.execute(
                        "SELECT local_path FROM images WHERE id=?",
                        (path[len("/api/image/") :],),
                    ).fetchone()
                    p = (
                        pathlib.Path(resolved_path(db, row[0]))
                        if row and row[0]
                        else None
                    )
                    if (
                        p
                        and p.is_file()
                        and p.suffix.lower()
                        in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
                    ):
                        self.reply(
                            200,
                            p.read_bytes(),
                            mimetypes.guess_type(str(p))[0]
                            or "application/octet-stream",
                        )
                        return
                    if row and query.get("placeholder") == "1":
                        # Presentation opt-in only: raw image API callers still
                        # receive a meaningful 404 for an unavailable source.
                        placeholder = (
                            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">'
                            '<rect width="640" height="400" fill="#191d24"/>'
                            '<g fill="none" stroke="#68788c" stroke-width="3">'
                            '<rect x="288" y="116" width="64" height="54" rx="6"/>'
                            '<path d="m294 161 17-19 12 12 10-10 14 17"/></g>'
                            '<g fill="#a0a9b8" font-family="sans-serif" text-anchor="middle">'
                            '<text x="320" y="218" font-size="23">图片暂不可用</text>'
                            '<text x="320" y="253" font-size="18">尚未缓存，或资料盘已离线</text></g></svg>'
                        ).encode("utf-8")
                        self.reply(
                            200, placeholder, "image/svg+xml", cache_control="no-store"
                        )
                        return
                    raise ApiError("图片尚未下载或路径不可用", "image_unavailable", 404)
            if path.startswith("/api/download/"):
                name = path[len("/api/download/") :]
                if pathlib.Path(name).name != name or "/" in name or "\\" in name:
                    raise ApiError("无效下载路径")
                p = STORAGE / "exports" / name
                if not p.is_file():
                    raise ApiError("导出文件不存在", "not_found", 404)
                self.reply(200, p.read_bytes(), "application/octet-stream")
                return
            if path.startswith("/api/"):
                self.reply(200, {"ok": True, "data": get_api(path, query)})
                return
            files = {
                "/": "index.html",
                "/app.js": "app.js",
                "/editor.js": "editor.js",
                "/work.js": "work.js",
                "/work.css": "work.css",
                "/style.css": "style.css",
                "/tag-translations.json": "tag-translations.json",
            }
            if path not in files:
                raise ApiError("页面不存在", "not_found", 404)
            p = APP / "static" / files[path]
            self.reply(
                200,
                p.read_bytes(),
                {
                    ".html": "text/html; charset=utf-8",
                    ".js": "text/javascript; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".json": "application/json; charset=utf-8",
                }[p.suffix],
            )
        except Exception as e:
            self.error(e)
        finally:
            reset_request_id(request_token)

    def do_POST(self):
        self.request_id = uuid.uuid4().hex
        request_token = set_request_id(self.request_id)
        try:
            parse_started = time.monotonic()
            if not self.authorized_host() or self.headers.get("X-Mod-Token") != TOKEN:
                raise ApiError("本地会话校验失败", "unauthorized", 403)
            origin = self.headers.get("Origin")
            if origin and origin not in (
                f"http://127.0.0.1:{self.server.server_port}",
                f"http://localhost:{self.server.server_port}",
            ):
                raise ApiError("拒绝跨站修改", "origin_denied", 403)
            length = int(self.headers.get("Content-Length", "0"))
            if length > 32 * 1024 * 1024:
                raise ApiError("单次导入不能超过 32 MiB", "too_large", 413)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ApiError("请求必须是 JSON 对象")
            if PLATFORM:
                PLATFORM.metrics.observe(
                    "http", "request_parsing", time.monotonic() - parse_started
                )
            self.reply(
                200, {"ok": True, "data": post_api(urlparse(self.path).path, body)}
            )
        except Exception as e:
            self.error(e)
        finally:
            reset_request_id(request_token)

    def error(self, e):
        if isinstance(e, ConnectionError):
            return  # Browser navigation can cancel an in-flight local request.
        if isinstance(e, Problem):
            self.reply(e.status, {"ok": False, "error": e.payload()})
            return
        if isinstance(e, sqlite3.IntegrityError):
            e = ApiError(
                "同一游戏下已有这个搭配名称，请换一个名称。", "name_conflict", 409
            )
        status = (
            e.status
            if isinstance(e, ApiError)
            else 400
            if isinstance(e, (ValueError, KeyError))
            else 500
        )
        if status == 500:
            try:
                folder = STORAGE / "diagnostics"
                folder.mkdir(exist_ok=True)
                with (folder / "errors.jsonl").open("a", encoding="utf-8") as log:
                    log.write(
                        json.dumps(
                            {
                                "at": time.time(),
                                "requestId": getattr(self, "request_id", ""),
                                "type": type(e).__name__,
                                "traceback": traceback.format_exc(),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except OSError:
                pass
        self.reply(
            status,
            {
                "ok": False,
                "error": {
                    "code": e.code
                    if isinstance(e, ApiError)
                    else "invalid_data"
                    if status == 400
                    else "internal_error",
                    "message": (
                        "内部错误；请使用请求 ID 查看本机诊断日志。"
                        if status == 500
                        else str(e)
                    ),
                },
            },
        )


def main():
    global DB_PATH, STORAGE, PLATFORM, HTTPD
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--no-auto-index", action="store_true")
    parser.add_argument("--runtime", default=str(APP / "data/runtime.json"))
    args = parser.parse_args()
    DB_PATH = pathlib.Path(args.db)
    from runtime_support import ensure_pinned_process

    ensure_pinned_process(
        required=DB_PATH.resolve() == (APP / "data/catalog.sqlite3").resolve()
    )
    storage = DB_PATH.resolve().parent
    from lifecycle_lock import directory_lock
    from restore_platform import recover_interrupted

    # The service owns this OS lock from recovery inspection until every
    # database connection and worker has stopped.  Offline restore contends
    # for the same byte-range lock.
    with directory_lock(storage, purpose="service"):
        recover_interrupted(storage, lock_held=True)
        initialize(DB_PATH)
        if DB_PATH.resolve() != (APP / "data/catalog.sqlite3").resolve():
            STORAGE = storage
            content.APP = STORAGE
            translations.APP = STORAGE
        from platform_api import Platform

        PLATFORM = Platform(sys.modules[__name__])
        httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
        HTTPD = httpd
        runtime = {
            "service": SERVICE_NAME,
            "pid": os.getpid(),
            "url": f"http://127.0.0.1:{httpd.server_port}",
            "token": TOKEN,
            "pythonVersion": sys.version.split()[0],
            "sqliteVersion": sqlite3.sqlite_version,
        }
        target = pathlib.Path(args.runtime)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".tmp")
        temp.write_text(dumps(runtime), encoding="utf-8")
        temp.replace(target)
        with connect(DB_PATH) as db:
            empty = not db.execute("SELECT 1 FROM mods LIMIT 1").fetchone()
        if empty and not args.no_auto_index:
            start_job("index", lambda p, c: rebuild(DB_PATH, p, c))
        print(runtime["url"], flush=True)
        try:
            httpd.serve_forever()
        finally:
            PLATFORM.runtime.stop()
            httpd.server_close()


if __name__ == "__main__":
    main()
