#!/usr/bin/env python3
"""Validate the complete FCN example chain without running services."""
from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, RefResolver

HERE = Path(__file__).resolve().parent
SCHEMA = HERE.parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance, schema_path: Path) -> None:
    schema = load(schema_path)
    resolver = RefResolver(schema_path.as_uri(), schema)
    Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker()).validate(instance)


def main() -> int:
    source = HERE / "source" / "termsheet1.fcn.sample.json"
    projection = HERE / "terms" / "fcn-terms-projection.example.json"
    process = HERE / "process" / "fcn-etl-to-olap.process.json"
    augment = HERE / "etl" / "augment-result.example.json"
    compile_result = HERE / "etl" / "compile-result.example.json"
    pricing_request = HERE / "pricing" / "pricing-request.example.json"
    quote = HERE / "pricing" / "native-quote-result.example.json"
    reprice = HERE / "pricing" / "native-reprice-result.example.json"

    validate(load(source), SCHEMA / "fcn-legacy-termsheet.schema.json")
    validate(load(projection), SCHEMA / "fcn-terms-projection.schema.json")
    validate(load(process), SCHEMA / "fina-process.schema.json")
    validate(load(augment), SCHEMA / "fcn-etl-result.schema.json")
    validate(load(compile_result), SCHEMA / "fcn-etl-result.schema.json")
    validate(load(pricing_request), SCHEMA / "pricing-request.schema.json")
    validate(load(quote), SCHEMA / "fcn-native-pricing-result.schema.json")
    validate(load(reprice), SCHEMA / "fcn-native-pricing-result.schema.json")

    source_data = load(source)
    projection_data = load(projection)
    request = load(pricing_request)
    compile_data = load(compile_result)
    process_data = load(process)
    assert len(source_data["Chunk"]["Jobs"]) == len(projection_data["source_ref"]["job_ids"])
    assert len(compile_data["requests"]) == 1
    assert compile_data["requests"][0] == request
    assert request["parameters"]["bump_size"] == 0.01
    assert request["parameters"]["bump_mode"] == "relative"
    assert request["parameters"]["common_random_numbers"] is True
    assert request["parameters"]["paths"] == 30000
    names = [thread["name"] for thread in process_data["threads"]]
    assert names == ["augment", "compile", "quote", "register_trade", "amend", "reprice", "olap"]
    assert any(sub["topic"] == "trade.lifecycle.amended" for sub in process_data["subscriptions"])
    assert load(quote)["engine"] == load(reprice)["engine"] == "cpp_daily_termsheet_eki"
    print("PASS legacy source -> terms projection -> ETL -> pricing request -> native results -> FinaProcess")
    print("PASS process role: executable orchestration recipe, separate from product semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
