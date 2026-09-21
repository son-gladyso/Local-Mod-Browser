import pathlib
import sys
import time
import urllib.error
import unittest
from unittest.mock import patch


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from contracts import Problem, VERSION
from fixture_service import isolated_service
from platform_client import PlatformClient, TaskSession


class PlatformClientTests(unittest.TestCase):
    def test_lost_write_response_reuses_one_generated_idempotency_key(self):
        client = PlatformClient(
            {"url": "http://127.0.0.1:1", "token": "fixture"}, attempts=2
        )
        sends = []

        def response(operation, parameters):
            if operation == "capabilities":
                return {"ok": True, "data": {"version": VERSION}}
            if operation == "receipts.read":
                return {"ok": True, "data": {"found": False}}
            sends.append(dict(parameters))
            if len(sends) == 1:
                raise urllib.error.URLError("response lost")
            return {"ok": True, "data": {"id": "created-once"}}

        with patch.object(client, "_request_once", side_effect=response), patch(
            "platform_client.time.sleep"
        ):
            result = client.request(
                "tasks.create",
                {
                    "title": "fixture",
                    "goal": "prove retry identity",
                    "scope": {"operations": ["favorite.set"]},
                    "acceptance": [{"kind": "receipts", "minimum": 1}],
                },
            )
        self.assertTrue(result["ok"])
        self.assertEqual(len(sends), 2)
        self.assertTrue(sends[0]["idempotencyKey"].startswith("client:"))
        self.assertEqual(sends[0], sends[1])

    def test_contract_major_version_is_checked_before_business_call(self):
        client = PlatformClient({"url": "http://127.0.0.1:1", "token": "fixture"})
        with patch.object(
            client,
            "_request_once",
            return_value={"ok": True, "data": {"version": "3.0.0"}},
        ) as request:
            with self.assertRaises(Problem) as caught:
                client.call("games.list")
        self.assertEqual(caught.exception.code, "contract_version_mismatch")
        request.assert_called_once_with("capabilities", {})

    def test_discovery_task_session_checkpoint_and_external_wait(self):
        with isolated_service("platform-client") as fixture:
            client = PlatformClient(fixture.info)
            self.assertEqual(client.call("capabilities")["version"], VERSION)
            task = client.call(
                "tasks.create",
                {
                    "title": "客户端会话",
                    "goal": "验证续租安全窗口",
                    "scope": {"operations": ["favorite.set"]},
                    "acceptance": [{"kind": "receipts", "minimum": 1}],
                },
            )
            session = TaskSession.claim(
                client, task["id"], "client-fixture", renew_seconds=3600
            )
            try:
                checkpointed = session.checkpoint(
                    "read", input_value={"resource": fixture.mod["id"]}, batch=0
                )
                self.assertEqual(checkpointed["checkpoint"]["step"], "read")
                self.assertEqual(len(checkpointed["checkpoint"]["inputHash"]), 64)
                session.failure = ConnectionError("fixture renewal failure")
                session.expires = time.time() + 5
                # Reads remain useful for diagnosis inside the write safety window.
                self.assertEqual(
                    session.call("resources.read", {"ids": [fixture.mod["id"]]})[
                        "items"
                    ][0]["resourceId"],
                    fixture.mod["id"],
                )
                with self.assertRaises(Problem) as caught:
                    session.call(
                        "favorite.set",
                        {"id": fixture.mod["id"], "enabled": True},
                    )
                self.assertEqual(caught.exception.code, "lease_renewal_failed")
                session.failure = None
                session.expires = time.time() + 300
                waiting = session.wait_external("等待外部翻译包")
                self.assertEqual(waiting["status"], "waiting_external")
                self.assertTrue(session.closed.is_set())
            finally:
                session.close()


if __name__ == "__main__":
    unittest.main()
