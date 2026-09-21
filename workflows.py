"""Declarative, allow-listed workflow runner; imported content is never executable."""

from __future__ import annotations

import json
import pathlib
import time
import uuid

from catalog import digest, dumps
from contracts import OPS, Problem


DEFINITIONS_PATH = pathlib.Path(__file__).with_name("workflows.json")
DEFINITIONS = {
    value["id"]: value
    for value in json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))["workflows"]
}


def public_definition(value):
    return {key: item for key, item in value.items() if key != "internal"}


def listing():
    return {
        "items": [public_definition(value) for value in DEFINITIONS.values()],
        "total": len(DEFINITIONS),
        "page": 1,
    }


def definition(workflow_id):
    if workflow_id not in DEFINITIONS:
        raise Problem("not_found", "流程不存在", status=404)
    return public_definition(DEFINITIONS[workflow_id])


def _path(value, path):
    for part in path.split(".") if path else []:
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


def resolve(value, run, external):
    if isinstance(value, str) and value.startswith("$"):
        root, _, path = value[1:].partition(".")
        source = {
            "input": run["input"],
            "output": run["outputs"],
            "external": external,
        }[root]
        return _path(source, path)
    if isinstance(value, dict):
        return {key: resolve(item, run, external) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, run, external) for item in value]
    return value


def public_run(run):
    definition_value = DEFINITIONS[run["workflowId"]]
    steps = []
    for index, step in enumerate(definition_value["steps"]):
        status = (
            "complete"
            if index < run["step"]
            else "current"
            if index == run["step"]
            else "pending"
        )
        summary = {"index": index, "operation": step["operation"], "status": status}
        if index < len(run["outputs"]):
            output = run["outputs"][index]
            summary["result"] = {
                key: output[key]
                for key in (
                    "id",
                    "status",
                    "receiptId",
                    "batchId",
                    "total",
                    "valid",
                    "artifact",
                )
                if key in output
            }
        steps.append(summary)
    return {
        key: run[key]
        for key in (
            "id",
            "workflowId",
            "title",
            "status",
            "step",
            "runVersion",
            "inputHash",
            "waitingReason",
            "created",
            "updated",
        )
        if key in run
    } | {"steps": steps}


def new_run(workflow_id, inputs, idempotency_key):
    value = definition(workflow_id)
    unknown = set(inputs) - set(value["requiredInputs"]) - {"lease"}
    missing = set(value["requiredInputs"]) - set(inputs)
    if unknown:
        raise Problem(
            "unknown_workflow_input", "流程输入包含未知字段", fields=sorted(unknown)
        )
    if missing:
        raise Problem(
            "missing_workflow_input", "流程输入不完整", fields=sorted(missing)
        )
    return {
        "id": uuid.uuid5(uuid.NAMESPACE_URL, "workflow:" + idempotency_key).hex,
        "workflowId": workflow_id,
        "title": value["title"],
        "status": "ready",
        "step": 0,
        "input": inputs,
        "inputHash": digest(dumps(inputs)),
        "definitionHash": digest(dumps(DEFINITIONS[workflow_id])),
        "runVersion": 1,
        "outputs": [],
        "resumeKeys": {},
        "waitingReason": "",
        "created": time.time(),
        "updated": time.time(),
    }


def advance(run, external, invoke, *, execution_lease=None, checkpoint=None):
    checkpoint = checkpoint or (lambda _run: None)
    value = DEFINITIONS[run["workflowId"]]
    if run["step"] >= len(value["steps"]):
        run["status"] = "complete"
        return run
    step = value["steps"][run["step"]]
    pending = run.get("pendingJob")
    if pending:
        if pending["step"] != run["step"]:
            raise Problem("workflow_state_invalid", "流程等待的作业与当前步骤不一致")
        output = invoke("jobs.read", {"id": pending["id"]})
        if output.get("status") in ("queued", "running"):
            run.update(
                status="waiting_job",
                waitingReason=output.get("message", "等待后台作业"),
                updated=time.time(),
            )
            return run
        if output.get("status") != "complete":
            run.update(
                status="blocked",
                waitingReason=output.get("message", "后台作业失败"),
                updated=time.time(),
            )
            return run
        run.pop("pendingJob", None)
        run["outputs"].append(output)
        run["step"] += 1
        run["status"] = "complete" if run["step"] == len(value["steps"]) else "ready"
        run["waitingReason"] = ""
        run["updated"] = time.time()
        return run
    if step.get("externalKey") and step["externalKey"] not in external:
        run.update(status="waiting_external", waitingReason="等待外部翻译结果")
        return run
    arguments = resolve(step.get("arguments", {}), run, external)
    operation = step["operation"]
    if operation not in OPS:
        raise Problem("workflow_operation_denied", "流程包含未登记操作")
    if OPS[operation]["write"]:
        arguments.setdefault(
            "idempotencyKey", f"workflow:{run['id']}:step:{run['step']}"
        )
        lease = execution_lease or run["input"].get("lease")
        if lease and operation not in ("tasks.claim",):
            arguments.setdefault("lease", lease)

    def invoke_exact(current, ordinal=None):
        identity = {"step": run["step"], "ordinal": ordinal, "operation": operation}
        pending_request = run.get("pendingRequest")
        if pending_request:
            if any(pending_request.get(key) != value for key, value in identity.items()):
                raise Problem(
                    "workflow_state_invalid",
                    "流程存在另一个尚未核对的请求",
                    status=409,
                )
            exact = pending_request["arguments"]
        else:
            exact = current
            run["pendingRequest"] = dict(identity, arguments=exact)
            checkpoint(run)
        output_value = invoke(operation, exact)
        run.pop("pendingRequest", None)
        return output_value

    if step.get("foreach"):
        state = run.get("foreachState")
        if not state:
            state = {"step": run["step"], "next": 0, "outputs": []}
            run["foreachState"] = state
            checkpoint(run)
        if state["step"] != run["step"]:
            raise Problem("workflow_state_invalid", "流程循环检查点与当前步骤不一致")
        items = resolve(step["foreach"], run, external)
        for ordinal in range(state["next"], len(items)):
            item = items[ordinal]
            current = dict(arguments, **item)
            if operation == "profiles.select" and not run.get("pendingRequest"):
                profile = invoke("profiles.read", {"id": current["profileId"]})
                current["revision"] = profile["revision"]
            current["idempotencyKey"] = (
                f"workflow:{run['id']}:step:{run['step']}:{ordinal}"
            )
            state["outputs"].append(invoke_exact(current, ordinal))
            state["next"] = ordinal + 1
            checkpoint(run)
        output = {"items": state["outputs"], "total": len(state["outputs"])}
        run.pop("foreachState", None)
    else:
        output = invoke_exact(arguments)
    if step.get("waitForJob") and output.get("status") in ("queued", "running"):
        run["pendingJob"] = {
            "step": run["step"],
            "id": output["id"],
            "operation": operation,
        }
        run.update(
            status="waiting_job",
            waitingReason=output.get("message", "等待后台作业"),
            updated=time.time(),
        )
        return run
    if (
        step.get("waitForJob")
        and "status" in output
        and output.get("status") != "complete"
    ):
        run.update(
            status="blocked", waitingReason=output.get("message", "后台作业失败")
        )
        return run
    run["outputs"].append(output)
    run["step"] += 1
    run["status"] = "complete" if run["step"] == len(value["steps"]) else "ready"
    run["waitingReason"] = ""
    run["updated"] = time.time()
    return run
