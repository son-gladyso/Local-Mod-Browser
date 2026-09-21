"""Managed synthetic HTTP service for acceptance scripts; never starts formal data."""

import json
import os
import pathlib
import sys
import threading
import uuid
from contextlib import contextmanager, ExitStack
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalog
import content
import server
import translations
from platform_api import Platform
from test_app import seed


@contextmanager
def isolated_service(label, *, start_worker=True):
    root = catalog.APP / "test-results" / (label + "-" + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    path = root / "catalog.sqlite3"
    mod, archive = seed(path, root)
    with ExitStack() as stack:
        for module, field, value in [
            (server, "DB_PATH", path),
            (server, "STORAGE", root),
            (content, "APP", root),
            (translations, "APP", root),
            (server, "PLATFORM", None),
            (server, "HTTPD", None),
        ]:
            stack.enter_context(patch.object(module, field, value))
        platform = server.PLATFORM = Platform(server, start_worker=start_worker)
        httpd = server.HTTPD = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        info = dict(
            service="local-mod-browser",
            pid=os.getpid(),
            url=f"http://127.0.0.1:{httpd.server_port}",
            token=server.TOKEN,
        )
        runtime = root / "runtime.json"
        runtime.write_text(json.dumps(info), encoding="utf-8")
        try:
            yield SimpleNamespace(
                root=root,
                path=path,
                mod=mod,
                archive=archive,
                platform=platform,
                info=info,
                runtime=runtime,
            )
        finally:
            platform.runtime.stop()
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
