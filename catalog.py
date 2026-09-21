"""Read-only adapters for existing MOD libraries; persistent personal data lives separately."""

from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import time
import contextvars
from contextlib import contextmanager

_transaction = contextvars.ContextVar("catalog_transaction", default=None)

APP = pathlib.Path(__file__).resolve().parent
QUERY_PROJECTION_VERSION = 1


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def read_json(path, default=None):
    path = pathlib.Path(path)
    return (
        json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default
    )


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def refresh_search(db, mod_id):
    """Rebuild search from current MOD and file data, dropping obsolete edits."""
    row = db.execute("SELECT data FROM mods WHERE id=?", (mod_id,)).fetchone()
    if row:
        documents = [row[0]] + [
            r[0] for r in db.execute("SELECT data FROM files WHERE mod_id=?", (mod_id,))
        ]
        db.execute(
            "UPDATE mods SET search=? WHERE id=?",
            (" ".join(documents).casefold(), mod_id),
        )
        refresh_query_projection(db, mod_id)


def refresh_query_projection(db, mod_id):
    """Maintain the SQL-only list/facet/search projection in the caller transaction."""
    row = db.execute("SELECT * FROM mods WHERE id=?", (mod_id,)).fetchone()
    if not row:
        db.execute("DELETE FROM mod_query WHERE mod_id=?", (mod_id,))
        db.execute("DELETE FROM mod_tags WHERE mod_id=?", (mod_id,))
        return
    item = json.loads(row["data"])
    translated = []
    resources = [mod_id] + [
        value[0]
        for value in db.execute("SELECT id FROM files WHERE mod_id=?", (mod_id,))
    ]
    for resource_id in resources:
        sources = source_fields(db, resource_id)
        for value in db.execute(
            "SELECT field,source_hash,text FROM translations WHERE resource_id=?",
            (resource_id,),
        ):
            if value["source_hash"] == digest(sources.get(value["field"], "")):
                translated.append(value["text"])
    search_text = (row["search"] + " " + " ".join(translated)).casefold()
    db.execute(
        """INSERT INTO mod_query(
               mod_id,game,category,author,adult,downloads,updated,endorsements,
               file_count,local_image_count,size_mb,translation_status,search_text,
               algorithm_version
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(mod_id) DO UPDATE SET
               game=excluded.game,category=excluded.category,author=excluded.author,
               adult=excluded.adult,downloads=excluded.downloads,updated=excluded.updated,
               endorsements=excluded.endorsements,file_count=excluded.file_count,
               local_image_count=excluded.local_image_count,size_mb=excluded.size_mb,
               translation_status=excluded.translation_status,
               search_text=excluded.search_text,algorithm_version=excluded.algorithm_version""",
        (
            mod_id,
            row["game"],
            row["category"],
            row["author"],
            row["adult"],
            row["downloads"],
            row["updated"],
            item.get("endorsements", 0),
            item.get("fileCount", 0),
            item.get("localImageCount", 0),
            item.get("sizeMB", 0),
            translation_status(db, item),
            search_text,
            QUERY_PROJECTION_VERSION,
        ),
    )
    db.execute("DELETE FROM mod_tags WHERE mod_id=?", (mod_id,))
    db.executemany(
        "INSERT OR IGNORE INTO mod_tags(mod_id,tag) VALUES(?,?)",
        [(mod_id, tag) for tag in item.get("tags", []) if tag],
    )


def rebuild_query_projections(db):
    ids = [row[0] for row in db.execute("SELECT id FROM mods ORDER BY id")]
    for mod_id in ids:
        refresh_query_projection(db, mod_id)
    db.execute("DELETE FROM mod_query WHERE mod_id NOT IN (SELECT id FROM mods)")
    db.execute("DELETE FROM mod_tags WHERE mod_id NOT IN (SELECT id FROM mods)")
    return len(ids)


class ClosingConnection(sqlite3.Connection):
    """Close the outer context, while supporting nested transaction contexts."""

    def __enter__(self):
        self._depth = getattr(self, "_depth", 0) + 1
        return super().__enter__()

    def __exit__(self, *args):
        try:
            if self._depth == 1:
                return super().__exit__(*args)
        finally:
            self._depth -= 1
            if not self._depth:
                self.close()


class BorrowedConnection:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, *args):
        return False

    def __getattr__(self, key):
        return getattr(self.db, key)


@contextmanager
def atomic(path):
    """Share one outer transaction across legacy and v2 operations and receipts."""
    with connect(path) as db:
        token = _transaction.set((str(pathlib.Path(path).resolve()), db))
        try:
            yield db
        finally:
            _transaction.reset(token)


def connect(path):
    active = _transaction.get()
    if active and active[0] == str(pathlib.Path(path).resolve()):
        return BorrowedConnection(active[1])
    db = sqlite3.connect(path, timeout=30, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.create_function(
        "source_digest", 1, lambda value: digest(str(value or "")), deterministic=True
    )
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA synchronous=FULL")
    return db


def initialize(path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS games(id TEXT PRIMARY KEY,title TEXT,root TEXT,output TEXT,updated REAL);
        CREATE TABLE IF NOT EXISTS mods(id TEXT PRIMARY KEY,game TEXT,nexus_id INTEGER,name TEXT,author TEXT,category TEXT,adult INTEGER,downloads INTEGER,updated INTEGER,search TEXT,data TEXT);
        CREATE INDEX IF NOT EXISTS mods_game ON mods(game);
        CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,mod_id TEXT,nexus_id INTEGER,data TEXT);
        CREATE INDEX IF NOT EXISTS files_mod ON files(mod_id);
        CREATE TABLE IF NOT EXISTS images(id TEXT PRIMARY KEY,mod_id TEXT,ordinal INTEGER,local_path TEXT,remote_url TEXT,caption TEXT,source TEXT);
        CREATE INDEX IF NOT EXISTS images_mod ON images(mod_id,ordinal);
        CREATE TABLE IF NOT EXISTS favorites(mod_id TEXT PRIMARY KEY,created REAL);
        CREATE TABLE IF NOT EXISTS recent(mod_id TEXT PRIMARY KEY,visited REAL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS saved_filters(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,game TEXT,data TEXT NOT NULL,created REAL,updated REAL);
        CREATE TABLE IF NOT EXISTS mod_query(
            mod_id TEXT PRIMARY KEY REFERENCES mods(id) ON DELETE CASCADE,
            game TEXT,category TEXT,author TEXT,adult INTEGER,downloads INTEGER,
            updated INTEGER,endorsements INTEGER,file_count INTEGER,
            local_image_count INTEGER,size_mb REAL,translation_status TEXT,
            search_text TEXT,algorithm_version INTEGER
        );
        CREATE INDEX IF NOT EXISTS mod_query_game ON mod_query(game);
        CREATE INDEX IF NOT EXISTS mod_query_category ON mod_query(category);
        CREATE INDEX IF NOT EXISTS mod_query_author ON mod_query(author);
        CREATE INDEX IF NOT EXISTS mod_query_translation ON mod_query(translation_status);
        CREATE TABLE IF NOT EXISTS mod_tags(
            mod_id TEXT NOT NULL REFERENCES mods(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,PRIMARY KEY(mod_id,tag)
        );
        CREATE INDEX IF NOT EXISTS mod_tags_tag ON mod_tags(tag,mod_id);
        CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,game TEXT,name TEXT,notes TEXT,updated REAL,UNIQUE(game,name));
        CREATE TABLE IF NOT EXISTS selections(profile_id TEXT,file_id TEXT,copy_path TEXT,version TEXT,bytes INTEGER,PRIMARY KEY(profile_id,file_id),FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS translations(resource_id TEXT,field TEXT,source_hash TEXT,text TEXT,model TEXT,imported REAL,PRIMARY KEY(resource_id,field));
        CREATE TABLE IF NOT EXISTS translation_history(id INTEGER PRIMARY KEY,resource_id TEXT,field TEXT,source_hash TEXT,text TEXT,model TEXT,imported REAL);
        CREATE TABLE IF NOT EXISTS translation_tasks(id TEXT PRIMARY KEY,resource_id TEXT,field TEXT,field_hash TEXT,segment_id TEXT,ordinal INTEGER,total INTEGER,source_hash TEXT,source TEXT,protected TEXT,status TEXT,translated TEXT,error TEXT,created REAL);
        CREATE INDEX IF NOT EXISTS task_resource ON translation_tasks(resource_id,field,field_hash);
        CREATE TABLE IF NOT EXISTS previews(id TEXT PRIMARY KEY,payload TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS resource_base(id TEXT PRIMARY KEY,kind TEXT,data TEXT);
        CREATE TABLE IF NOT EXISTS edits(resource_id TEXT PRIMARY KEY,patch TEXT,updated REAL);
        CREATE TABLE IF NOT EXISTS edit_history(id INTEGER PRIMARY KEY,resource_id TEXT,before_patch TEXT,after_patch TEXT,note TEXT,created REAL);
        """)


def setting(db, key, default=None):
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def set_setting(db, key, value):
    db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, dumps(value)))


def resolved_path(db, path):
    """Root changes apply at read time, retaining stable resource and selection identities."""
    mappings = setting(db, "roots", {})
    for old, new in sorted(mappings.items(), key=lambda x: -len(x[0])):
        if path.casefold() == old.casefold() or path.casefold().startswith(
            old.rstrip("\\/").casefold() + "\\"
        ):
            return str(pathlib.Path(new) / path[len(old) :].lstrip("\\/"))
    return path


def file_status(db, path):
    path = resolved_path(db, path)
    p = pathlib.Path(path)
    if not pathlib.Path(p.anchor).exists():
        return {"path": path, "status": "offline", "label": "磁盘不可用"}
    if not p.is_file():
        return {"path": path, "status": "missing", "label": "文件不存在"}
    return {
        "path": path,
        "status": "available",
        "label": "本地可用",
        "actualBytes": p.stat().st_size,
    }


def plain(value):
    import html

    text = html.unescape(str(value or ""))
    text = re.sub(r"\[img\].*?\[/img\]", "", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>|</(?:p|div|li)>", "\n", text, flags=re.I)
    text = re.sub(
        r"<[^>]+>|\[/?(?:b|i|u|size|color|font|center|url|list|quote)[^\]]*\]",
        "",
        text,
        flags=re.I,
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def apply_edits(db, data, kind):
    db.execute(
        "INSERT OR REPLACE INTO resource_base VALUES(?,?,?)",
        (data["id"], kind, dumps(data)),
    )
    row = db.execute(
        "SELECT patch FROM edits WHERE resource_id=?", (data["id"],)
    ).fetchone()
    return dict(data, **json.loads(row[0])) if row else data


def source_configuration():
    """Load a private, local source list without depending on the repo's parent."""
    configured = os.environ.get("LOCAL_MOD_BROWSER_SOURCES", "").strip()
    path = pathlib.Path(configured).expanduser() if configured else APP / "data/sources.json"
    targets = read_json(path, [])
    if isinstance(targets, dict):
        targets = targets.get("games", [])
    if not isinstance(targets, list):
        raise ValueError("sources.json must be an array or an object containing games")
    return path, targets


def load_sources(db):
    config_path, targets = source_configuration()
    for source in targets:
        if not isinstance(source, dict):
            raise ValueError("each source entry must be an object")
        game = dict(source)
        for field in ("key", "title", "root", "outputDir"):
            if not isinstance(game.get(field), str) or not game[field].strip():
                raise ValueError("source entry is missing " + field)
        for field in ("root", "outputDir"):
            value = pathlib.Path(game[field]).expanduser()
            if not value.is_absolute():
                value = (config_path.parent / value).resolve()
            game[field] = str(value)
        p = pathlib.Path(
            resolved_path(
                db, str(pathlib.Path(game["outputDir"]) / "catalog-data.json")
            )
        )
        yield game, read_json(p) if p.is_file() else None

def archive_file_id(path, mod_id):
    """Only evidenced folder identities, never zip(fileIds, paths)."""
    parts = pathlib.PureWindowsPath(path).parts
    for part in reversed(parts[:-1]):
        match = re.fullmatch(r"mod-(\d+)-file-(\d+)", part)
        if not match:
            match = re.fullmatch(r"\d+-(\d+)-(\d+)", part)
        if match and int(match[1]) == mod_id:
            return int(match[2])
    return 0


def evidenced_archive_metadata(db, game):
    """Match archives to a saved Nexus file record only when evidence is unique."""
    metadata_path = (
        pathlib.Path(game["root"]) / "NexusMods_Downloads/Metadata/metadata.json"
    )
    metadata_path = pathlib.Path(resolved_path(db, str(metadata_path)))
    payload = read_json(metadata_path, {})
    if not isinstance(payload, dict):
        return {}
    records = [
        (int(mod["modId"]), file)
        for mod in payload.get("pageMods", [])
        for file in mod.get("files", [])
        if file.get("fileId")
    ]
    required_path = metadata_path.with_name("required_download_plan.json")
    required = read_json(required_path, [])
    if isinstance(required, list):
        records.extend(
            (int(file["modId"]), file) for file in required if file.get("fileId")
        )
    api_cache = read_json(APP / "data" / ("nexus-files-" + game["key"] + ".json"), [])
    if isinstance(api_cache, list):
        records.extend(
            (int(file["modId"]), file)
            for file in api_cache
            if file.get("file_id") or file.get("fileId")
        )
    matches = {}
    for archive in game.get("archives", []):
        if archive.get("fileId"):
            continue
        mod_id = int(archive.get("modId") or 0)
        name = pathlib.PureWindowsPath(archive["path"]).name
        candidates = []
        for candidate_mod, file in records:
            if candidate_mod != mod_id:
                continue
            file_id = int(file.get("fileId") or file.get("file_id"))
            timestamp = int(file.get("date") or file.get("uploaded_timestamp") or 0)
            expected_bytes = int(file.get("size_in_bytes") or 0)
            exact_timestamp = timestamp and re.search(
                rf"-{timestamp}\.(?:zip|7z|rar)$", name, re.I
            )
            explicit_file_id = re.search(
                rf"(?:^|-)({file_id})--|-{mod_id}-{file_id}\.(?:zip|7z|rar)$",
                name,
                re.I,
            )
            exact_size = expected_bytes and expected_bytes == int(
                archive.get("bytes") or 0
            )
            if exact_timestamp or explicit_file_id or exact_size:
                candidates.append(file)
        if len(candidates) == 1:
            file = candidates[0]
            matches[archive["path"].casefold()] = {
                "FileId": int(file.get("fileId") or file.get("file_id")),
                "Name": file.get("name") or file.get("fileName", ""),
                "Version": file.get("version", ""),
                "CategoryName": file.get("category") or file.get("category_name", ""),
                "Description": file.get("description", ""),
                "UploadedTimestamp": file.get("date") or file.get("uploaded_timestamp"),
                "SizeBytes": file.get("size_in_bytes"),
            }
    return matches


def migrate_resource_id(db, old_id, new_id):
    """Preserve personal state when stronger evidence upgrades a local file ID."""
    if old_id == new_id:
        return
    db.execute(
        "INSERT OR IGNORE INTO translations SELECT ?,field,source_hash,text,model,imported "
        "FROM translations WHERE resource_id=?",
        (new_id, old_id),
    )
    db.execute("DELETE FROM translations WHERE resource_id=?", (old_id,))
    db.execute(
        "UPDATE translation_history SET resource_id=? WHERE resource_id=?",
        (new_id, old_id),
    )
    db.execute(
        "UPDATE translation_tasks SET resource_id=? WHERE resource_id=?",
        (new_id, old_id),
    )
    db.execute(
        "INSERT OR IGNORE INTO edits SELECT ?,patch,updated FROM edits WHERE resource_id=?",
        (new_id, old_id),
    )
    db.execute("DELETE FROM edits WHERE resource_id=?", (old_id,))
    db.execute(
        "UPDATE edit_history SET resource_id=? WHERE resource_id=?", (new_id, old_id)
    )
    db.execute(
        "INSERT OR IGNORE INTO selections "
        "SELECT profile_id,?,copy_path,version,bytes FROM selections WHERE file_id=?",
        (new_id, old_id),
    )
    db.execute("DELETE FROM selections WHERE file_id=?", (old_id,))
    db.execute("DELETE FROM resource_base WHERE id=?", (old_id,))


def rebuild(db_path, progress=lambda **kw: None, cancelled=lambda: False):
    started = time.monotonic()
    with connect(db_path) as db:
        metadata = []
        file_meta = {(int(x["ModId"]), int(x["FileId"])): x for x in metadata}
        edges = []
        reqs = {}
        for edge in edges:
            reqs.setdefault(int(edge["ModId"]), []).append(
                {
                    "name": edge["RequiredModName"],
                    "modId": edge.get("RequiredModId"),
                    "kind": "required",
                    "evidence": "Nexus Requirements",
                    "notes": edge.get("Notes", ""),
                    "url": edge.get("Url", ""),
                    "external": edge.get("ExternalRequirement", False),
                }
            )
        # Build in memory; publish as one transaction so cancellation leaves the previous index intact.
        collected, skipped = [], []
        for game, rows in load_sources(db):
            if cancelled():
                raise InterruptedError("已停止，原目录索引保留。")
            if rows is None:
                skipped.append(game["title"])
                continue
            key = game["key"]
            archives = {a["path"].casefold(): a for a in game.get("archives", [])}
            evidenced_files = evidenced_archive_metadata(db, game)
            images_state_name = (
                "all-reference-image-state.json"
                if key == "stellarblade"
                else "reference-image-state.json"
            )
            states = read_json(
                resolved_path(
                    db, str(pathlib.Path(game["outputDir"]) / images_state_name)
                ),
                [],
            )
            by_url = {
                str(s.get("url", "")).casefold(): s for s in states if s.get("ok")
            }
            by_local = {str(s.get("file", "")).casefold(): s for s in states}
            normalized = []
            for index, source in enumerate(rows):
                if cancelled():
                    raise InterruptedError("已停止，原目录索引保留。")
                mid = int(source["modId"])
                paths = source.get("paths", [])
                local_key = digest(
                    "|".join(
                        sorted(
                            p.casefold().replace(game["root"].casefold(), "", 1)
                            for p in paths
                        )
                    )
                )[:24]
                rid = key + (":" + str(mid) if mid > 0 else ":local:" + local_key)
                item = dict(
                    source,
                    id=rid,
                    game=key,
                    gameTitle=game["title"],
                    requirements=reqs.get(mid, []) if key == "stellarblade" else [],
                )
                item["conflictEvidence"] = (
                    "既有本地报告；包含推断，需核实作者说明"
                    if source.get("risk")
                    else "未记录，不代表已确认兼容"
                )
                files = {}
                for path in paths:
                    a = archives.get(path.casefold(), {})
                    local_meta = evidenced_files.get(path.casefold(), {})
                    fid = (
                        archive_file_id(path, mid)
                        if key == "stellarblade"
                        else int(a.get("fileId") or local_meta.get("FileId") or 0)
                    )
                    identity = (
                        str(fid)
                        if fid
                        else "local-"
                        + digest(
                            path.casefold().replace(game["root"].casefold(), "", 1)
                        )[:24]
                    )
                    file_id = rid + ":file:" + identity
                    m = (
                        file_meta.get((mid, fid), {})
                        if key == "stellarblade"
                        else local_meta
                    )
                    p = pathlib.Path(resolved_path(db, path))
                    size = int(
                        m.get("SizeBytes")
                        or a.get("bytes")
                        or (p.stat().st_size if p.is_file() else 0)
                    )
                    f = files.setdefault(
                        file_id,
                        {
                            "id": file_id,
                            "modId": rid,
                            "fileId": fid or None,
                            "name": m.get("Name")
                            or a.get("fileName")
                            or pathlib.PureWindowsPath(path).name,
                            "version": m.get("Version") or "",
                            "category": m.get("CategoryName") or "",
                            "description": plain(m.get("Description")),
                            "uploaded": m.get("UploadedTimestamp"),
                            "bytes": size,
                            "copies": [],
                            "metadataSource": (
                                "Nexus 文件缓存"
                                if key == "stellarblade" and m
                                else "本地 Nexus 元数据"
                                if m
                                else "本地库存"
                            ),
                            "requirements": [],
                            "matched": bool(fid),
                        },
                    )
                    if path not in f["copies"]:
                        f["copies"].append(path)
                images = []
                for n, im in enumerate(source.get("images", [])):
                    src = im.get("src", "")
                    remote = im.get("remoteSrc", "") or (
                        src if src.startswith(("https://", "http://")) else ""
                    )
                    state = (
                        by_url.get(remote.casefold())
                        or by_local.get(src.casefold())
                        or {}
                    )
                    local = (
                        state.get("file")
                        if state.get("ok")
                        else (
                            src
                            if src and not src.startswith(("http://", "https://"))
                            else ""
                        )
                    )
                    lp = str(pathlib.Path(game["outputDir"]) / local) if local else ""
                    images.append(
                        (
                            rid + ":image:" + digest(remote or src)[:20],
                            rid,
                            n,
                            lp,
                            remote,
                            im.get("caption", ""),
                            im.get("source", ""),
                        )
                    )
                item.pop("images", None)
                item["fileCount"] = len(files)
                item["imageCount"] = len(images)
                item["localImageCount"] = sum(bool(im[3]) for im in images)
                item["tags"] = list(dict.fromkeys(source.get("tags", [])))
                search = " ".join(
                    str(v)
                    for v in [
                        mid,
                        source.get("name", ""),
                        source.get("author", ""),
                        source.get("function", ""),
                        source.get("details", ""),
                        source.get("compatibility", ""),
                        source.get("risk", ""),
                        " ".join(item["tags"]),
                        " ".join(
                            f["name"] + " " + f["description"] for f in files.values()
                        ),
                        dumps(item["requirements"]),
                    ]
                ).casefold()
                normalized.append((item, files, images, search))
                if index % 40 == 0:
                    progress(
                        message=f"正在整理 {game['title']} · {index + 1}/{len(rows)}",
                        done=index + 1,
                        total=len(rows),
                    )
            collected.append((game, normalized))
        if cancelled():
            raise InterruptedError("已停止，原目录索引保留。")
        with db:
            migrated = 0
            for game, normalized in collected:
                key = game["key"]
                old_by_copy = {}
                for row in db.execute(
                    "SELECT files.id,files.data FROM files JOIN mods ON files.mod_id=mods.id "
                    "WHERE mods.game=?",
                    (key,),
                ):
                    old = json.loads(row["data"])
                    for copy in old.get("copies", []):
                        old_by_copy[copy.casefold()] = row["id"]
                migrations = {}
                for _item, files, _images, _search in normalized:
                    for new_id, file in files.items():
                        for copy in file.get("copies", []):
                            old_id = old_by_copy.get(copy.casefold())
                            if old_id and old_id != new_id:
                                migrations[old_id] = new_id
                for old_id, new_id in migrations.items():
                    migrate_resource_id(db, old_id, new_id)
                    migrated += 1
                db.execute(
                    "DELETE FROM images WHERE mod_id IN (SELECT id FROM mods WHERE game=?)",
                    (key,),
                )
                db.execute(
                    "DELETE FROM files WHERE mod_id IN (SELECT id FROM mods WHERE game=?)",
                    (key,),
                )
                db.execute("DELETE FROM mods WHERE game=?", (key,))
                db.execute(
                    "INSERT OR REPLACE INTO games VALUES(?,?,?,?,?)",
                    (key, game["title"], game["root"], game["outputDir"], time.time()),
                )
                for item, files, images, search in normalized:
                    item = apply_edits(db, item, "mod")
                    files = {
                        fid: apply_edits(db, f, "file") for fid, f in files.items()
                    }
                    search += (
                        " "
                        + dumps(item).casefold()
                        + " "
                        + dumps(list(files.values())).casefold()
                    )
                    db.execute(
                        "INSERT INTO mods VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            item["id"],
                            key,
                            item["modId"],
                            item["name"],
                            item.get("author", ""),
                            item.get("group", "其他"),
                            int(item.get("adult", False)),
                            item.get("downloads", 0),
                            item.get("updated", 0),
                            search,
                            dumps(item),
                        ),
                    )
                    db.executemany(
                        "INSERT INTO files VALUES(?,?,?,?)",
                        [
                            (f["id"], item["id"], f["fileId"], dumps(f))
                            for f in files.values()
                        ],
                    )
                    db.executemany(
                        "INSERT OR IGNORE INTO images VALUES(?,?,?,?,?,?,?)", images
                    )
            # Imported contributions are durable sources, not disposable index rows.
            from interchange import reapply

            reapply(db)
            rebuild_query_projections(db)
            result = {
                "mods": db.execute("SELECT count(*) FROM mods").fetchone()[0],
                "files": db.execute("SELECT count(*) FROM files").fetchone()[0],
                "images": db.execute("SELECT count(*) FROM images").fetchone()[0],
                "skippedGames": skipped,
                "migratedFileIds": migrated,
                "seconds": round(time.monotonic() - started, 2),
            }
            set_setting(db, "lastIndex", dict(result, at=time.time()))
        return result


def source_fields(db, resource_id):
    row = db.execute("SELECT data FROM mods WHERE id=?", (resource_id,)).fetchone()
    if row:
        data = json.loads(row[0])
        return {
            k: str(data.get(k) or "")
            for k in (
                "name",
                "function",
                "details",
                "compatibility",
                "risk",
                "variantRule",
            )
        }
    row = db.execute("SELECT data FROM files WHERE id=?", (resource_id,)).fetchone()
    if row:
        data = json.loads(row[0])
        return {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
        }
    row = db.execute("SELECT caption FROM images WHERE id=?", (resource_id,)).fetchone()
    return {"caption": row[0]} if row else {}


def translated(db, resource_id):
    fields = source_fields(db, resource_id)
    return {
        r["field"]: r["text"]
        for r in db.execute(
            "SELECT * FROM translations WHERE resource_id=?", (resource_id,)
        )
        if r["source_hash"] == digest(fields.get(r["field"], ""))
    }


def has_english_prose(text):
    """Find natural-language English while ignoring URLs, code and local paths."""
    prose = re.sub(r"https?://\S+", " ", text)
    prose = re.sub(r"`[^`]*`", " ", prose)
    prose = re.sub(r"[A-Za-z]:\\[^\n\r<>\"]+", " ", prose)
    return bool(
        re.search(
            r"(?<![A-Za-z])(?:[A-Za-z][A-Za-z'’.-]*[ \t]+){4,}"
            r"[A-Za-z][A-Za-z'’.-]*(?![A-Za-z])",
            prose,
        )
    )


def needs_translation(text, field=""):
    """Chinese source text is already usable unless English prose remains."""
    if not text.strip():
        return False
    han = len(re.findall(r"[\u3400-\u9fff]", text))
    return han < 2 or has_english_prose(text)


def translation_quality_error(source, translation, field=""):
    """Reject obvious keyword-substitution output without judging normal prose."""
    # Short non-caption fields never enter either rejection rule. In particular,
    # do not scan a large translated body when the current source became short.
    if field != "caption" and len(source) < 500:
        return ""
    source_han = len(re.findall(r"[\u3400-\u9fff]", source))
    source_latin = len(re.findall(r"[A-Za-z]", source))
    translated_han = len(re.findall(r"[\u3400-\u9fff]", translation))
    translated_latin = len(re.findall(r"[A-Za-z]", translation))
    if field == "caption" and source_han == 0 and source_latin >= 6:
        share = translated_han / max(1, translated_han + translated_latin)
        english_connectors = re.search(
            r"\b(?:and|with|of|type|version|fixed|body)\b", translation, re.I
        )
        if share < 0.15 or english_connectors:
            return "图片配文疑似未完整翻译，请提交自然、完整的中文配文"
    if len(source) < 500:
        return ""
    if source_latin < 400 or source_han * 20 > source_latin:
        return ""
    if translated_latin < 400 or translated_han * 3 >= translated_latin:
        return ""
    prose = re.sub(r"https?://\S+", "", translation)
    # Only existence matters. Stop at the first English run instead of allocating
    # every match in a long document; Chinese-heavy text exits before this scan.
    english_run = re.search(
        r"(?<![A-Za-z])(?:[A-Za-z][A-Za-z'’.-]*[ \t]+){7,}"
        r"[A-Za-z][A-Za-z'’.-]*(?![A-Za-z])",
        prose,
    )
    if english_run:
        return "译文疑似仍以英文句法为主，请完整翻译后重新提交"
    return ""


def translation_status(db, item):
    rows = list(
        db.execute(
            "SELECT field,source_hash FROM translations WHERE resource_id=?",
            (item["id"],),
        )
    )
    sources = source_fields(db, item["id"])
    if any(r["source_hash"] != digest(sources.get(r["field"], "")) for r in rows):
        return "stale"
    tasks = [
        task
        for task in db.execute(
            "SELECT field,source,status,translated FROM translation_tasks "
            "WHERE resource_id=?",
            (item["id"],),
        )
        if needs_translation(task["source"], task["field"])
    ]
    if any(
        task["status"] == "review"
        or (
            task["translated"]
            and translation_quality_error(
                task["source"], task["translated"], task["field"]
            )
        )
        for task in tasks
    ):
        return "review"
    needed = {k for k, v in sources.items() if needs_translation(v, k)}
    if not needed or needed.issubset({r["field"] for r in rows}):
        return "complete"
    if rows:
        return "partial"
    if any(task["status"] == "pending" for task in tasks):
        return "pending"
    return "missing"
