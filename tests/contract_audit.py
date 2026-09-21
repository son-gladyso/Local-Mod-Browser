"""Audit the published registry without modifying business code or formal data.

Optional --runtime checks all unknown-parameter errors on an isolated HTTP service.
Missing examples and unconstrained result bodies remain findings, not silent passes.
"""

# ruff: noqa: E402 -- standalone tool loads the project registry
import argparse
import json
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(APP))
from contracts import OPS, Problem, validate, response_schema, openapi
from evidence import source_manifest, publish_json


def placeholder(schema):
    """Create schema-valid inert inputs; they are used only with a rejected extra key."""
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object":
        return {
            k: placeholder(schema["properties"][k]) for k in schema.get("required", [])
        }
    if kind == "array":
        return [
            placeholder(schema.get("items", {}))
            for _ in range(schema.get("minItems", 0))
        ]
    if kind == "integer":
        return schema.get("minimum", 0)
    if kind == "boolean":
        return False
    return "contract-fixture"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Check HTTP on a disposable synthetic service",
    )
    parser.add_argument(
        "--output", default=str(APP / "test-results/contract-audit.json")
    )
    args = parser.parse_args()
    output = pathlib.Path(args.output).resolve()
    if not output.is_relative_to(APP / "test-results"):
        parser.error("Output must stay under test-results")
    if args.fixture:
        if args.runtime:
            parser.error("Use --fixture or --runtime, not both")
        from fixture_service import isolated_service

        with isolated_service("contract-audit", start_worker=False) as fixture:
            return audit(fixture.info, output, exercise_resume=True)
    info = None
    if args.runtime:
        runtime = pathlib.Path(args.runtime).resolve()
        if not runtime.is_relative_to(APP / "test-results"):
            parser.error("Only an isolated test runtime may be used")
        info = json.loads(runtime.read_text(encoding="utf-8"))
    return audit(info, output)


def audit(info, output, *, exercise_resume=False):
    from jsonschema import Draft202012Validator
    from ai import v2_request

    report = dict(
        source=source_manifest(),
        operations=len(OPS),
        findings=[],
        checks=[],
        httpChecked=[],
    )
    document = openapi()
    for name, spec in OPS.items():
        for direction in ("inputSchema", "outputSchema"):
            Draft202012Validator.check_schema(spec[direction])
        Draft202012Validator.check_schema(response_schema(spec))
        endpoint = document["paths"][spec["path"]][spec["method"].lower()]
        assert endpoint["operationId"] == name
        assert isinstance(spec["sideEffects"], list), name
        assert spec["errorCodes"] and all(
            isinstance(code, str) for code in spec["errorCodes"]
        ), name
        try:
            validate(spec["example"], spec["inputSchema"])
        except Problem as error:
            report["findings"].append(
                dict(
                    operation=name,
                    kind="incomplete_example",
                    code=error.code,
                    required=spec["inputSchema"]["required"],
                )
            )
        result_shapes = spec["outputSchema"].get("oneOf", [spec["outputSchema"]])
        if all(
            set(shape.get("properties", {})) <= {"receiptId", "operation", "taskId"}
            for shape in result_shapes
        ):
            report["findings"].append(
                dict(operation=name, kind="undocumented_result_body")
            )
        # Input error behaviour is checked using valid shapes plus one unknown top-level key.
        request = dict(placeholder(spec["inputSchema"]), __contract_unknown__=True)
        try:
            validate(request, spec["inputSchema"])
            raise AssertionError("Unknown parameter accepted: " + name)
        except Problem as error:
            assert error.code == "unknown_parameter", (name, error.code)
        if info:
            result = v2_request(info, name, request)
            Draft202012Validator(response_schema(spec)).validate(result)
            if (
                result.get("ok")
                or result.get("error", {}).get("code") != "unknown_parameter"
            ):
                report["findings"].append(
                    dict(
                        operation=name,
                        kind="http_unknown_parameter_mismatch",
                        result=result,
                    )
                )
            report["httpChecked"].append(name)
    report["checks"] = [
        "Every operation has valid JSON schemas and an OpenAPI route",
        "Every operation documents side effects, stable error codes, and a schema-valid example",
        "Every operation rejects an unknown top-level parameter before execution",
    ]
    if exercise_resume:
        job = v2_request(info, "catalog.export", {})["data"]
        v2_request(info, "jobs.control", dict(id=job["id"], action="cancel"))
        for operation, arguments in [
            ("jobs.control", dict(id=job["id"], action="resume")),
            ("jobs.read", dict(id=job["id"])),
        ]:
            result = v2_request(info, operation, arguments)
            assert result["ok"], result
            for error in Draft202012Validator(
                OPS[operation]["outputSchema"]
            ).iter_errors(result["data"]):
                report["findings"].append(
                    dict(
                        operation=operation,
                        kind="response_schema_mismatch",
                        path="data." + ".".join(map(str, error.path)),
                        message=error.message,
                    )
                )
    report["ok"] = not report["findings"]
    publish_json(output, report)
    print(
        json.dumps(
            dict(
                ok=report["ok"],
                operations=len(OPS),
                findings=len(report["findings"]),
                httpChecked=len(report["httpChecked"]),
                report=str(output),
            ),
            ensure_ascii=False,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
