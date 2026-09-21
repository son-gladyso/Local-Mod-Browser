"""Read-only inventory audit. Does not download images or edit catalogue data."""

import json
import pathlib
import sqlite3
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalog

APP = catalog.APP
started = time.monotonic()
db = sqlite3.connect((APP / "data/catalog.sqlite3").as_uri() + "?mode=ro", uri=True)
db.row_factory = sqlite3.Row
try:
    mods = [json.loads(r[0]) for r in db.execute("SELECT data FROM mods")]
    files = [json.loads(r[0]) for r in db.execute("SELECT data FROM files")]
    indexed = {p for f in files for p in f["copies"]}
    source = {
        p
        for game, rows in catalog.load_sources(db)
        for row in rows or []
        for p in row.get("paths", [])
    }
    missing = [
        p for p in indexed if not pathlib.Path(catalog.resolved_path(db, p)).is_file()
    ]
    local_images = {
        r[0] for r in db.execute("SELECT local_path FROM images WHERE local_path<>''")
    }
    existing = sum(
        pathlib.Path(catalog.resolved_path(db, p)).is_file() for p in local_images
    )
    report = {
        "games": [
            dict(r)
            for r in db.execute(
                "SELECT games.id,games.title,(SELECT count(*) FROM mods WHERE mods.game=games.id) mods FROM games"
            )
        ],
        "mods": len(mods),
        "files": len(files),
        "archiveCopies": len(indexed),
        "sourceArchiveCopies": len(source),
        "omittedArchives": sorted(source - indexed),
        "missingArchives": missing,
        "imageRecords": db.execute("SELECT count(*) FROM images").fetchone()[0],
        "uniqueLocalImagePaths": len(local_images),
        "existingLocalImagePaths": existing,
        "unavailableLocalImagePaths": len(local_images) - existing,
        "fullDescription": sum(bool(m.get("details")) for m in mods),
        "unmatchedFileIds": sum(not f.get("fileId") for f in files),
        "seconds": round(time.monotonic() - started, 2),
    }
    (APP / "test-results").mkdir(exist_ok=True)
    (APP / "test-results/inventory-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
finally:
    db.close()
