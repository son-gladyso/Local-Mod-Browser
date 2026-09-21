"""Prepare a disposable real-data copy. Only test-results/ is written."""

import pathlib
import sqlite3
import uuid
import argparse
import json
from contextlib import closing

APP = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--preserve-content",
    action="store_true",
    help="保留译文、覆盖与路径映射，验收真实导入后的性能",
)
args = parser.parse_args()
folder = APP / "test-results" / ("browser-" + uuid.uuid4().hex[:10])
folder.mkdir(parents=True)
with closing(
    sqlite3.connect((APP / "data/catalog.sqlite3").as_uri() + "?mode=ro", uri=True)
) as source:
    with closing(sqlite3.connect(folder / "catalog.sqlite3")) as target:
        source.backup(target)
        tables = (
            "favorites",
            "recent",
            "settings",
            "profiles",
            "selections",
            "translations",
            "translation_history",
            "translation_tasks",
            "previews",
            "edits",
            "edit_history",
        )
        if args.preserve_content:
            tables = ("favorites", "recent", "profiles", "selections", "previews")
        for table in tables:
            target.execute("DELETE FROM " + table)
        target.commit()
        baseline = {
            table: target.execute("SELECT count(*) FROM " + table).fetchone()[0]
            for table in ("games", "mods", "files", "images", "translations", "edits")
        }
(folder / "fixture-baseline.json").write_text(
    json.dumps(dict(preserveContent=args.preserve_content, counts=baseline)),
    encoding="utf-8",
)
(APP / "test-results/browser-folder.txt").write_text(str(folder), encoding="utf-8")
print(str(folder))
