"""Shared standard-library client and lease session for CLI and MCP."""

from __future__ import annotations

import hashlib
import json
import pathlib
import threading
import time
import random
import urllib.error
import urllib.parse
import urllib.request
import uuid

from contracts import OPS, VERSION, Problem
from launcher import start


TRANSIENT_CODES = {"temporary_error", "database_locked", "service_unavailable"}
_CLIENTS = {}
_CLIENTS_LOCK = threading.Lock()


class PlatformClient:
    def __init__(self, info, *, attempts=3, timeout=120, total_timeout=150):
        self.info = dict(info)
        self.attempts = attempts
        self.timeout = timeout
        self.total_timeout = total_timeout
        self._verified = False
        parsed = urllib.parse.urlparse(self.info["url"])
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.username
            or parsed.password
        ):
            raise ValueError("只允许连接 127.0.0.1 本机服务")

    @classmethod
    def connect(cls, runtime=None):
        info = (
            json.loads(pathlib.Path(runtime).read_text(encoding="utf-8"))
            if runtime
            else start(False)
        )
        client = cls(info)
        client.ensure_compatible()
        return client

    def ensure_compatible(self):
        if self._verified:
            return self
        discovered = self.call("capabilities")
        if discovered["version"].split(".", 1)[0] != VERSION.split(".", 1)[0]:
            raise Problem(
                "contract_version_mismatch",
                "客户端与服务契约主版本不兼容",
                next_action="update_client_or_service",
                client=VERSION,
                service=discovered["version"],
            )
        self._verified = True
        return self

    def _request_once(self, name, parameters):
        spec = OPS[name]
        parameters = dict(parameters)
        timeout = parameters.pop("__client_timeout__", self.timeout)
        path = self.info["url"] + spec["path"]
        payload = None
        if spec["write"]:
            payload = json.dumps(parameters, ensure_ascii=False).encode("utf-8")
        elif parameters:
            path += "?" + urllib.parse.urlencode(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if not isinstance(value, str)
                    else value
                    for key, value in parameters.items()
                }
            )
        request = urllib.request.Request(
            path,
            data=payload,
            method=spec["method"],
            headers={
                "Content-Type": "application/json",
                "X-Mod-Token": self.info["token"],
                "X-Request-ID": uuid.uuid4().hex,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            return json.load(error)

    def request(self, name, parameters=None):
        if name not in OPS:
            raise Problem("not_found", "能力不存在", status=404, operation=name)
        if name != "capabilities":
            self.ensure_compatible()
        parameters = dict(parameters or {})
        if OPS[name]["write"]:
            # The key is created once, before the first send, and the exact request is
            # reused for every retry.  A lost response can therefore never turn a
            # retry into a second logical write.
            parameters.setdefault("idempotencyKey", "client:" + uuid.uuid4().hex)
        payload_hash = hashlib.sha256(
            json.dumps(
                [name, {k: v for k, v in parameters.items() if k != "idempotencyKey"}],
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        deadline = time.monotonic() + self.total_timeout
        last_error = None
        for attempt in range(self.attempts):
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                request_parameters = dict(parameters)
                if remaining < self.timeout:
                    request_parameters["__client_timeout__"] = remaining
                result = self._request_once(name, request_parameters)
                error = result.get("error", {})
                transient = (
                    error.get("retryable") or error.get("code") in TRANSIENT_CODES
                )
                if not transient or attempt + 1 >= self.attempts:
                    return result
                last_error = Problem(
                    error.get("code", "temporary_error"),
                    error.get("message", "临时错误"),
                    retryable=True,
                    details=error.get("details", {}),
                )
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                last_error = error
                key = parameters.get("idempotencyKey")
                if OPS[name]["write"] and key and name != "receipts.read":
                    try:
                        receipt = self._request_once(
                            "receipts.read",
                            {
                                "key": key,
                                "operation": name,
                                "payloadHash": payload_hash,
                                "__client_timeout__": min(
                                    self.timeout, max(0.1, deadline - time.monotonic())
                                ),
                            },
                        )
                        if receipt.get("ok") and receipt["data"].get("found"):
                            return {"ok": True, "data": receipt["data"]["result"]}
                    except (urllib.error.URLError, TimeoutError, ConnectionError):
                        pass
            if attempt + 1 >= self.attempts or time.monotonic() >= deadline:
                break
            delay = random.uniform(0, 0.25 * (2**attempt))
            time.sleep(min(delay, max(0, deadline - time.monotonic())))
        return {
            "ok": False,
            "error": {
                "code": "connection_failed",
                "message": str(last_error),
                "retryable": True,
                "nextAction": "check_service_then_retry_same_request",
            },
        }

    def call(self, name, parameters=None):
        response = self.request(name, parameters)
        if not response.get("ok"):
            error = response.get("error", {})
            raise Problem(
                error.get("code", "request_failed"),
                error.get("message", "请求失败"),
                retryable=error.get("retryable", False),
                next_action=error.get("nextAction", "inspect_error"),
                **error.get("details", {}),
            )
        return response["data"]


class TaskSession:
    """Lease renewal, safe-window fencing, checkpoints and external waiting."""

    def __init__(self, client, lease, task, *, renew_seconds=60, safe_seconds=30):
        self.client = client
        self.lease = lease
        self.task = task
        self.renew_seconds = renew_seconds
        self.safe_seconds = safe_seconds
        self.expires = task["expires"]
        self.failure = None
        self.closed = threading.Event()
        self.thread = threading.Thread(target=self._renew, daemon=True)
        self.thread.start()

    @classmethod
    def claim(cls, client, task_id, owner, **options):
        claimed = client.call(
            "tasks.claim",
            {
                "id": task_id,
                "owner": owner,
                "idempotencyKey": "claim:" + uuid.uuid4().hex,
            },
        )
        return cls(client, claimed["lease"], claimed["task"], **options)

    def _renew(self):
        while not self.closed.wait(self.renew_seconds):
            try:
                self.task = self.client.call(
                    "tasks.renew",
                    {
                        "lease": self.lease,
                        "idempotencyKey": "renew:" + uuid.uuid4().hex,
                    },
                )
                self.expires = self.task["expires"]
                self.failure = None
            except Exception as error:
                self.failure = error

    def assert_submission_safe(self):
        if self.closed.is_set():
            raise Problem("session_closed", "任务会话已结束", status=409)
        if time.time() >= self.expires - self.safe_seconds:
            raise Problem(
                "lease_renewal_failed",
                "任务租约进入安全窗口，已停止新增提交",
                status=409,
                next_action="reconnect_and_claim_task",
            )

    def call(self, operation, parameters=None):
        parameters = dict(parameters or {})
        if OPS[operation]["write"]:
            self.assert_submission_safe()
            parameters.setdefault("lease", self.lease)
            parameters.setdefault("idempotencyKey", "session:" + uuid.uuid4().hex)
        return self.client.call(operation, parameters)

    def checkpoint(
        self, step, *, input_value=None, batch=None, receipts=(), artifacts=()
    ):
        checkpoint = {"step": step, "batch": batch, "receipts": list(receipts)}
        if input_value is not None:
            checkpoint["inputHash"] = hashlib.sha256(
                json.dumps(input_value, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
        self.task = self.call(
            "tasks.checkpoint",
            {"checkpoint": checkpoint, "artifacts": list(artifacts)},
        )
        return self.task

    def wait_external(self, reason, *, artifacts=()):
        if artifacts:
            self.checkpoint("waiting_external", artifacts=artifacts)
        self.task = self.call(
            "tasks.control",
            {"id": self.lease["taskId"], "action": "wait", "reason": reason},
        )
        self.close()
        return self.task

    def close(self):
        self.closed.set()
        if self.thread is not threading.current_thread():
            self.thread.join(timeout=1)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def shared_client(info):
    """Reuse discovery and connection policy across CLI and MCP calls."""
    key = (info["url"], info["token"])
    with _CLIENTS_LOCK:
        client = _CLIENTS.get(key)
        if client is None:
            client = PlatformClient(info)
            _CLIENTS[key] = client
    return client.ensure_compatible()
