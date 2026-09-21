"""Regression tests use synthetic data in temporary databases, never personal data."""

import json
import os
import pathlib
import sys
import uuid
import shutil
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalog
import content
import server
import translations
from contracts import VERSION


def seed(path, folder):
    catalog.initialize(path)
    archive = folder / "sample.zip"
    archive.write_bytes(b"archive")
    with catalog.connect(path) as db:
        db.execute(
            "INSERT INTO games VALUES(?,?,?,?,?)",
            ("stellarblade", "剑星", str(folder), str(folder), 1),
        )
        m = dict(
            id="stellarblade:1401",
            game="stellarblade",
            gameTitle="剑星",
            modId=1401,
            name="Test MOD",
            author="Author",
            group="工具",
            tags=["框架"],
            downloads=10,
            function="Sample summary",
            details="Install sample.pak v1.2.3\n\n" + "Full paragraph. " * 800,
            requirements=[],
            fileCount=2,
            imageCount=0,
            localImageCount=0,
            paths=[str(archive)],
        )
        catalog.apply_edits(db, m, "mod")
        db.execute(
            "INSERT INTO mods VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                m["id"],
                m["game"],
                1401,
                m["name"],
                m["author"],
                m["group"],
                0,
                10,
                1,
                "",
                catalog.dumps(m),
            ),
        )
        for n in (1, 2):
            f = dict(
                id=f"stellarblade:1401:file:{n}",
                modId=m["id"],
                fileId=n,
                name=f"Variant {n}",
                description="unique_file_needle" if n == 1 else "Other choice",
                version="1.2.3",
                category="Main",
                bytes=7,
                copies=[str(archive)],
                requirements=[],
            )
            catalog.apply_edits(db, f, "file")
            db.execute(
                "INSERT INTO files VALUES(?,?,?,?)",
                (f["id"], m["id"], n, catalog.dumps(f)),
            )
        catalog.refresh_search(db, m["id"])
    return m, str(archive)


class AppTest(unittest.TestCase):
    def setUp(self):
        test_root = pathlib.Path(__file__).resolve().parents[1] / "test-results"
        test_root.mkdir(exist_ok=True)
        self.root = test_root / ("unit-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.path = self.root / "test.sqlite3"
        self.mod, self.archive = seed(self.path, self.root)
        self.patches = [
            patch.object(server, "DB_PATH", self.path),
            patch.object(server, "STORAGE", self.root),
            patch.object(content, "APP", self.root),
            patch.object(translations, "APP", self.root),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        assert self.root.resolve().is_relative_to(
            pathlib.Path(__file__).resolve().parents[1] / "test-results"
        )
        shutil.rmtree(self.root)

    def edit(self, rid, patch_data):
        with catalog.connect(self.path) as db:
            r = content.read_resource(db, rid)
            p = content.preview_edits(
                db, [dict(resourceId=rid, baseRevision=r["revision"], patch=patch_data)]
            )
            self.assertFalse(p["errors"])
            return content.apply_preview(db, p["previewId"])

    def test_search_preserves_files_and_drops_obsolete_edits(self):
        self.edit(self.mod["id"], {"function": "new_summary"})
        self.assertEqual(
            server.get_api("/api/mods", {"q": "unique_file_needle"})["total"], 1
        )
        self.edit(
            "stellarblade:1401:file:1", {"description": "replacement_file_needle"}
        )
        self.assertEqual(
            server.get_api("/api/mods", {"q": "unique_file_needle"})["total"], 0
        )
        self.assertEqual(
            server.get_api("/api/mods", {"q": "replacement_file_needle"})["total"], 1
        )
        self.edit("stellarblade:1401:file:1", {"description": None})
        self.assertEqual(
            server.get_api("/api/mods", {"q": "unique_file_needle"})["total"], 1
        )

    def test_stale_preview_rejected_without_partial_write(self):
        with catalog.connect(self.path) as db:
            r = content.read_resource(db, self.mod["id"])
            p = content.preview_edits(
                db,
                [
                    dict(
                        resourceId=r["resourceId"],
                        baseRevision=r["revision"],
                        patch={"function": "obsolete"},
                    )
                ],
            )
        self.edit(self.mod["id"], {"function": "winner"})
        with catalog.connect(self.path) as db:
            with self.assertRaises(ValueError):
                content.apply_preview(db, p["previewId"])
            self.assertEqual(
                content.read_resource(db, self.mod["id"])["data"]["function"], "winner"
            )

    def test_edit_validation_and_history(self):
        with catalog.connect(self.path) as db:
            r = content.read_resource(db, self.mod["id"])
            records = [
                {
                    "resourceId": r["resourceId"],
                    "baseRevision": r["revision"],
                    "patch": {"paths": ["bad"]},
                }
            ]
            p = content.preview_edits(db, records + [None])
            self.assertEqual(len(p["errors"]), 2)
        self.edit(self.mod["id"], {"function": "edited"})
        self.assertEqual(
            len(server.get_api("/api/content/history", {"id": self.mod["id"]})), 1
        )

    def test_profile_exact_roundtrip_and_duplicate_copy(self):
        pid = server.post_api(
            "/api/profile/save", {"game": "stellarblade", "name": "Profile"}
        )["id"]
        data = {
            "profileId": pid,
            "fileId": "stellarblade:1401:file:1",
            "copyPath": self.archive,
        }
        server.post_api("/api/profile/select", data)
        server.post_api("/api/profile/select", data)
        exported = server.post_api("/api/profile/export", {"id": pid})["manifest"]
        self.assertEqual(len(exported["files"]), 1)
        self.assertEqual(exported["files"][0]["nexusFileId"], 1)
        p = server.post_api("/api/profile/preview", {"manifest": exported})
        self.assertFalse(p["errors"])
        imported = server.post_api(
            "/api/profile/import", {"previewId": p["previewId"], "name": "Roundtrip"}
        )
        self.assertEqual(
            server.get_api("/api/profile", {"id": imported["id"]})["items"][0][
                "storedPath"
            ],
            self.archive,
        )
        exported["files"][0]["version"] = "wrong"
        self.assertEqual(
            len(
                server.post_api("/api/profile/preview", {"manifest": exported})[
                    "errors"
                ]
            ),
            1,
        )

    def test_optional_dependency_is_not_required_warning(self):
        self.edit(
            "stellarblade:1401:file:1",
            {
                "requirements": [
                    {
                        "name": "Optional",
                        "kind": "optional",
                        "evidence": "author",
                        "modId": 5,
                    }
                ]
            },
        )
        pid = server.post_api(
            "/api/profile/save", {"game": "stellarblade", "name": "Optional"}
        )["id"]
        server.post_api(
            "/api/profile/select",
            {
                "profileId": pid,
                "fileId": "stellarblade:1401:file:1",
                "copyPath": self.archive,
            },
        )
        self.assertEqual(server.get_api("/api/profile", {"id": pid})["warnings"], [])

    def test_reindex_preserves_personal_data_and_edits(self):
        self.edit(self.mod["id"], {"function": "keep_me"})
        server.post_api("/api/favorite", {"id": self.mod["id"], "enabled": True})
        pid = server.post_api(
            "/api/profile/save", {"game": "stellarblade", "name": "Keep"}
        )["id"]
        server.post_api(
            "/api/profile/select",
            {
                "profileId": pid,
                "fileId": "stellarblade:1401:file:1",
                "copyPath": self.archive,
            },
        )
        game = {
            "key": "stellarblade",
            "title": "剑星",
            "root": str(self.root),
            "outputDir": str(self.root),
        }
        with (
            patch.object(
                catalog, "load_sources", return_value=iter([(game, [self.mod])])
            ),
            patch.object(catalog, "read_json", return_value=[]),
        ):
            catalog.rebuild(self.path)
        self.assertTrue(server.get_api("/api/mod", {"id": self.mod["id"]})["favorite"])
        self.assertEqual(
            server.get_api("/api/resource", {"id": self.mod["id"]})["data"]["function"],
            "keep_me",
        )
        self.assertEqual(len(server.get_api("/api/profile", {"id": pid})["items"]), 1)

    def test_reindex_upgrades_evidenced_file_id_and_preserves_state(self):
        game_root = self.root / "game"
        metadata = game_root / "NexusMods_Downloads" / "Metadata"
        metadata.mkdir(parents=True)
        archive = game_root / "Choice-77-1-0-1234567890.zip"
        archive.write_bytes(b"archive")
        game = {
            "key": "samplegame",
            "title": "Sample Game",
            "root": str(game_root),
            "outputDir": str(game_root),
            "archives": [
                {
                    "modId": 77,
                    "fileId": 0,
                    "fileName": archive.name,
                    "path": str(archive),
                }
            ],
        }
        mod = dict(
            id="unused",
            modId=77,
            name="Choice",
            author="Author",
            group="工具",
            tags=[],
            downloads=0,
            function="Summary",
            details="Details",
            requirements=[],
            paths=[str(archive)],
        )
        with patch.object(catalog, "load_sources", return_value=iter([(game, [mod])])):
            catalog.rebuild(self.path)
        with catalog.connect(self.path) as db:
            old_id = db.execute(
                "SELECT id FROM files WHERE mod_id='samplegame:77'"
            ).fetchone()[0]
            db.execute(
                "INSERT INTO translations VALUES(?,?,?,?,?,?)",
                (old_id, "name", catalog.digest(archive.name), "选项", "test", 1),
            )
            db.execute(
                "INSERT INTO edits VALUES(?,?,?)",
                (old_id, catalog.dumps({"description": "keep_edit"}), 1),
            )
            db.execute(
                "INSERT INTO profiles VALUES(?,?,?,?,?)",
                ("evidence-profile", "samplegame", "Evidence", "", 1),
            )
            db.execute(
                "INSERT INTO selections VALUES(?,?,?,?,?)",
                ("evidence-profile", old_id, str(archive), "", len(b"archive")),
            )
        (metadata / "metadata.json").write_text(
            json.dumps(
                {
                    "pageMods": [
                        {
                            "modId": 77,
                            "files": [
                                {
                                    "fileId": 456,
                                    "name": "Choice",
                                    "version": "1.0",
                                    "category": "MAIN",
                                    "description": "Author description",
                                    "date": 1234567890,
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        with patch.object(catalog, "load_sources", return_value=iter([(game, [mod])])):
            result = catalog.rebuild(self.path)
        new_id = "samplegame:77:file:456"
        self.assertEqual(result["migratedFileIds"], 1)
        with catalog.connect(self.path) as db:
            file = json.loads(
                db.execute("SELECT data FROM files WHERE id=?", (new_id,)).fetchone()[0]
            )
            self.assertEqual(file["fileId"], 456)
            self.assertEqual(file["version"], "1.0")
            self.assertEqual(file["description"], "keep_edit")
            self.assertEqual(
                db.execute(
                    "SELECT file_id FROM selections WHERE profile_id='evidence-profile'"
                ).fetchone()[0],
                new_id,
            )
            self.assertEqual(
                db.execute(
                    "SELECT text FROM translations WHERE resource_id=?", (new_id,)
                ).fetchone()[0],
                "选项",
            )

    def tasks(self):
        package = translations.export_package(self.path, {"modId": self.mod["id"]})
        tasks = []
        for p in pathlib.Path(package["path"]).glob("tasks-*.jsonl"):
            tasks.extend(
                json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()
            )
        return tasks

    def result(self, t):
        return {
            k: t[k]
            for k in ("taskId", "resourceId", "field", "segmentId", "sourceHash")
        } | {"translation": "这是完整的中文测试译文。" + " ".join(t["protectedTokens"])}

    def test_translation_partial_complete_duplicate_and_bad_identity(self):
        tasks = [t for t in self.tasks() if t["field"] == "details"]
        self.assertGreater(len(tasks), 1)
        first = translations.preview_import(
            self.path, json.dumps(self.result(tasks[0]))
        )
        self.assertEqual(len(first["partial"]), 1)
        translations.apply_import(self.path, first["previewId"])
        with catalog.connect(self.path) as db:
            self.assertNotIn("details", catalog.translated(db, self.mod["id"]))
        rest = translations.preview_import(
            self.path, json.dumps([self.result(t) for t in tasks[1:]])
        )
        translations.apply_import(self.path, rest["previewId"])
        with catalog.connect(self.path) as db:
            self.assertEqual(
                catalog.translated(db, self.mod["id"])["details"],
                "".join(self.result(t)["translation"] for t in tasks),
            )
        duplicate = translations.preview_import(
            self.path, json.dumps([self.result(t) for t in tasks])
        )
        self.assertEqual(duplicate["duplicates"], len(tasks))
        bad = self.result(tasks[0])
        bad["resourceId"] = "wrong"
        self.assertEqual(
            len(translations.preview_import(self.path, json.dumps(bad))["errors"]), 1
        )

    def test_translation_rejects_long_english_keyword_substitution(self):
        self.assertFalse(
            catalog.needs_translation(
                "同一 MOD 有多个文件时，请按作者说明选择需要的变体。",
                "variantRule",
            )
        )
        self.assertTrue(
            catalog.needs_translation(
                "作者提示：This complete English sentence still needs to be translated.",
                "risk",
            )
        )
        self.assertTrue(catalog.needs_translation("ArchiveXL", "name"))
        t = next(
            t
            for t in self.tasks()
            if t["field"] == "details" and len(t["source"]) > 500
        )
        bad = self.result(t)
        bad["translation"] = (
            "This is an obviously untranslated English sentence with many words "
            "still in the original language. " * 60
        ) + " ".join(t["protectedTokens"])
        preview = translations.preview_import(self.path, json.dumps(bad))
        self.assertIn("英文句法", preview["errors"][0]["error"])

        bilingual_source = ("English release note. 中文发布说明。" * 80).strip()
        self.assertEqual(
            catalog.translation_quality_error(bilingual_source, bilingual_source), ""
        )
        self.assertIn(
            "图片配文",
            catalog.translation_quality_error(
                "Orin's Armor with Orin's Mask",
                "Orin's 护甲 with Orin's 面具",
                "caption",
            ),
        )
        self.assertEqual(
            catalog.translation_quality_error(
                "Sky Ace Stockings", "天空王牌长筒袜（Sky Ace Stockings）", "caption"
            ),
            "",
        )

    def test_translation_protected_paths_and_stale_source(self):
        t = next(
            t for t in self.tasks() if t["field"] == "details" and t["ordinal"] == 0
        )
        r = self.result(t)
        r["translation"] = r["translation"].replace("sample.pak", "wrong.pak")
        self.assertIn(
            "关键内容",
            translations.preview_import(self.path, json.dumps(r))["errors"][0]["error"],
        )
        self.edit(self.mod["id"], {"details": "Source changed"})
        self.assertIn(
            "原文已更新",
            translations.preview_import(self.path, json.dumps(self.result(t)))[
                "errors"
            ][0]["error"],
        )

    def test_cancellation_rolls_back_index(self):
        with self.assertRaises(InterruptedError):
            catalog.rebuild(self.path, cancelled=lambda: True)
        self.assertEqual(server.get_api("/api/health", {})["mods"], 1)

    def test_contract_version_is_consistent_across_legacy_metadata(self):
        platform = SimpleNamespace(runtime=SimpleNamespace(busy=lambda: False))
        with patch.object(server, "PLATFORM", platform):
            health = server.get_api("/api/health", {})
        docs = server.get_api("/api/docs", {})
        schema = server.get_api("/api/schema", {})
        self.assertEqual(health["contractVersion"], VERSION)
        self.assertEqual(docs["platform"]["version"], VERSION)
        self.assertEqual(schema["x-platformContract"]["version"], VERSION)

    def test_source_configuration_is_explicit_and_resolves_relative_paths(self):
        config = self.root / "sources.json"
        config.write_text(
            json.dumps(
                [
                    {
                        "key": "demo",
                        "title": "Demo Game",
                        "root": "library",
                        "outputDir": "catalog",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with patch.dict(os.environ, {"LOCAL_MOD_BROWSER_SOURCES": str(config)}):
            path, targets = catalog.source_configuration()
            with patch.object(catalog, "source_configuration", return_value=(path, targets)):
                with catalog.connect(self.path) as db:
                    game, rows = next(catalog.load_sources(db))
        self.assertEqual(path, config)
        self.assertEqual(game["root"], str((self.root / "library").resolve()))
        self.assertEqual(game["outputDir"], str((self.root / "catalog").resolve()))
        self.assertIsNone(rows)

    def test_file_translation_search_excludes_stale_text(self):
        fid = "stellarblade:1401:file:1"
        with catalog.connect(self.path) as db:
            source = catalog.source_fields(db, fid)["description"]
            db.execute(
                "INSERT INTO translations VALUES(?,?,?,?,?,?)",
                (fid, "description", catalog.digest(source), "中文文件词条", "test", 1),
            )
            catalog.refresh_query_projection(db, self.mod["id"])
        self.assertEqual(server.get_api("/api/mods", {"q": "中文文件词条"})["total"], 1)
        self.edit(fid, {"description": "changed"})
        self.assertEqual(server.get_api("/api/mods", {"q": "中文文件词条"})["total"], 0)

    def test_pagination_and_schema(self):
        second = dict(
            self.mod,
            id="stellarblade:1402",
            modId=1402,
            name="Zebra MOD",
            author="Other Author",
            group="外观",
            tags=["框架", "服装"],
            downloads=100,
            endorsements=50,
            updated=2,
            fileCount=0,
            paths=[],
        )
        with catalog.connect(self.path) as db:
            catalog.apply_edits(db, second, "mod")
            db.execute(
                "INSERT INTO mods VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    second["id"],
                    second["game"],
                    second["modId"],
                    second["name"],
                    second["author"],
                    second["group"],
                    0,
                    second["downloads"],
                    second["updated"],
                    "",
                    catalog.dumps(second),
                ),
            )
            catalog.refresh_search(db, second["id"])
        page = server.get_api(
            "/api/mods", {"limit": "1", "tag": "框架", "sort": "downloads"}
        )
        self.assertEqual(len(page["items"]), 1)
        self.assertEqual(page["total"], 2)
        self.assertEqual(page["items"][0]["id"], second["id"])
        by_name = server.get_api(
            "/api/mods", {"tag": "框架", "sort": "name", "limit": "48"}
        )
        self.assertEqual(
            [item["id"] for item in by_name["items"]],
            [self.mod["id"], second["id"]],
        )
        self.assertEqual(server.get_api("/api/mods", {"tag": "不存在"})["total"], 0)
        self.assertEqual(
            server.get_api(
                "/api/mods", {"tagsAll": ["框架", "服装"]}
            )["items"][0]["id"],
            second["id"],
        )
        self.assertEqual(
            server.get_api(
                "/api/mods", {"tagsAny": ["服装", "不存在"]}
            )["total"],
            1,
        )
        self.assertEqual(
            server.get_api("/api/mods", {"tagsExclude": ["服装"]})["total"],
            1,
        )
        self.assertEqual(
            server.get_api("/api/facets", {"game": "stellarblade"})["tags"]["框架"],
            2,
        )
        contextual = server.get_api(
            "/api/facets", {"game": "stellarblade", "tagsAll": ["服装"]}
        )
        self.assertEqual(contextual["categories"], {"外观": 1})
        self.assertEqual(contextual["authors"], {"Other Author": 1})
        self.assertEqual(contextual["tags"], {"框架": 2, "服装": 1})
        schema = json.loads(
            (pathlib.Path(__file__).resolve().parents[1] / "schemas.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("editRecord", schema["$defs"])

    def test_named_filters_are_versioned_and_separate(self):
        saved = server.post_api(
            "/api/saved-filters/save",
            {
                "name": "服装筛选",
                "game": "stellarblade",
                "filters": {"tagsAll": ["服装"], "sort": "updated"},
            },
        )
        self.assertEqual(
            server.get_api("/api/saved-filters", {})[0]["revision"],
            saved["revision"],
        )
        with self.assertRaises(server.ApiError) as caught:
            server.post_api(
                "/api/saved-filters/save", dict(saved, name="过期更新", revision="old")
            )
        self.assertEqual(caught.exception.code, "revision_conflict")
        deleted = server.post_api(
            "/api/saved-filters/delete",
            {"id": saved["id"], "revision": saved["revision"]},
        )
        self.assertTrue(deleted["deleted"])
        self.assertEqual(server.get_api("/api/saved-filters", {}), [])

    def test_browser_disconnect_does_not_send_second_response(self):
        from unittest.mock import Mock

        handler = object.__new__(server.Handler)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock(side_effect=ConnectionAbortedError())
        handler.reply(200, {"ok": True})
        self.assertEqual(handler.send_response.call_count, 1)
        handler.send_header.assert_any_call("Cache-Control", "no-store")

    def test_internal_error_hides_details_and_writes_local_diagnostics(self):
        from unittest.mock import Mock

        handler = object.__new__(server.Handler)
        handler.request_id = "public-safe-request"
        handler.reply = Mock()
        secret = "private-path-" + str(self.root)
        handler.error(RuntimeError(secret))
        status, payload = handler.reply.call_args.args
        self.assertEqual(status, 500)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertEqual(payload["error"]["code"], "internal_error")
        diagnostic = self.root / "diagnostics/errors.jsonl"
        self.assertTrue(diagnostic.is_file())
        self.assertIn("public-safe-request", diagnostic.read_text(encoding="utf-8"))

    def test_unavailable_image_placeholder_is_explicit_and_not_cached(self):
        from unittest.mock import Mock

        rid = self.mod["id"] + ":image:offline"
        with catalog.connect(self.path) as db:
            db.execute(
                "INSERT INTO images VALUES(?,?,?,?,?,?,?)",
                (
                    rid,
                    self.mod["id"],
                    0,
                    "",
                    "https://example.test/image.png",
                    "",
                    "fixture",
                ),
            )
        handler = object.__new__(server.Handler)
        handler.authorized_host = lambda: True
        handler.reply = Mock()
        handler.path = "/api/image/" + rid
        handler.do_GET()
        self.assertEqual(handler.reply.call_args.args[0], 404)

        self.assertEqual(
            handler.reply.call_args.args[1]["error"]["code"], "image_unavailable"
        )
        handler.path += "?placeholder=1"
        handler.do_GET()
        self.assertEqual(handler.reply.call_args.args[0], 200)
        self.assertEqual(handler.reply.call_args.args[2], "image/svg+xml")
        self.assertEqual(handler.reply.call_args.kwargs["cache_control"], "no-store")
        self.assertIn("资料盘已离线", handler.reply.call_args.args[1].decode())
        handler.path = "/api/image/unknown?placeholder=1"
        handler.do_GET()
        self.assertEqual(handler.reply.call_args.args[0], 404)

    def test_translation_quality_skips_unnecessary_prose_scan(self):
        source = "Original English source text with installation instructions. " * 100
        translated = "完整准确的中文说明。" * 100 + " ArchiveXL " * 100
        with patch.object(
            catalog.re, "search", side_effect=AssertionError("unnecessary scan")
        ):
            self.assertEqual(
                catalog.translation_quality_error(source, translated, "details"), ""
            )
        english = "This is a sentence that still needs a full translation. " * 100
        self.assertIn(
            "英文句法", catalog.translation_quality_error(source, english, "details")
        )
        self.assertIn(
            "图片配文",
            catalog.translation_quality_error(
                "Body version", "Body version", "caption"
            ),
        )


if __name__ == "__main__":
    unittest.main()
