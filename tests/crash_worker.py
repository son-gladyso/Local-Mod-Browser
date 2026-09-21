"""Fault injection helper: target must be an isolated platform test directory."""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalog
import server
import content
import translations
from platform_api import Platform

root = pathlib.Path(sys.argv[1]).resolve()
assert root.is_relative_to(catalog.APP / "test-results")
server.DB_PATH = root / "catalog.sqlite3"
server.STORAGE = root
content.APP = root
translations.APP = root
p = Platform(server, start_worker=False)
stage = sys.argv[2]
if stage == "before_commit":
    original = p.write

    def fault(db, *args):
        original(db, *args)
        os._exit(73)

    p.write = fault
    p.invoke(
        "favorite.set",
        dict(id="stellarblade:1401", enabled=True, idempotencyKey="crash-before"),
    )
elif stage == "after_commit":
    p.invoke(
        "profiles.save",
        dict(
            game="stellarblade",
            name="Crash receipt profile",
            idempotencyKey="crash-after",
        ),
    )
    os._exit(74)
elif stage == "artifact_before_receipt":
    original = p.register_artifact

    def fault(*args):
        original(*args)
        os._exit(75)

    p.register_artifact = fault
    p.execute("catalog.export", {"game": "stellarblade"}, "job:crash-artifact")
