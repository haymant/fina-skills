#!/usr/bin/env python3
"""Validate concrete FCN lifecycle fixtures against standalone schemas."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
CASES = {
    "fcn-lifecycle-state.example.json": "fcn-lifecycle-state.schema.json",
    "fcn-lifecycle-event.example.json": "fcn-lifecycle-event.schema.json",
    "fcn-lifecycle-transition.example.json": "fcn-lifecycle-transition.schema.json",
    "fcn-fixing-record.example.json": "fcn-fixing-record.schema.json",
    "fcn-market-operation.example.json": "fcn-market-operation.schema.json",
}


def main() -> int:
    for example_name, schema_name in CASES.items():
        example = json.loads((HERE / example_name).read_text(encoding="utf-8"))
        schema = json.loads((HERE.parents[2] / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
        print(f"PASS {schema_name} <- {example_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
