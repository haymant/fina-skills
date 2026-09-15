#!/usr/bin/env python3
"""Validate FinA model-wiring YAML entries and evidence manifests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
REGISTRY_DIR = ROOT / "model-registry"


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        details = "; ".join(f"{label} at {list(error.path)}: {error.message}" for error in errors)
        raise SystemExit(details)


def check_registry(path: Path, data: dict[str, Any]) -> None:
    lifecycle = data["lifecycle"]
    for field in ("state_schema", "event_schema", "transition_schema", "fixing_record_schema", "market_operation_schema"):
        value = lifecycle.get(field)
        if value and value != "pending-freeze" and not (SCHEMA_DIR / value).exists():
            raise SystemExit(f"{path}: lifecycle.{field} does not resolve to schema/{value}")
    native = data["pricing"]["backends"].get("native")
    if data["status"] == "executable" and native is None:
        raise SystemExit(f"{path}: executable entries require pricing.backends.native")
    if native is not None and native["kind"] == "native_cpp" and data["status"] == "executable":
        for field in ("source_revision", "module", "callable", "engine_marker"):
            if not native.get(field):
                raise SystemExit(f"{path}: executable native_cpp backend missing {field}")
        if native.get("fallback_allowed") is not False:
            raise SystemExit(f"{path}: executable native_cpp backend must explicitly set fallback_allowed: false")
    evidence = data["evidence"]
    if data["status"] == "executable":
        required = ("required_engine_marker", "parity_reference", "e2e_command", "checks")
        for field in required:
            if not evidence.get(field):
                raise SystemExit(f"{path}: executable evidence missing {field}")
        parity = ROOT.parent / evidence["parity_reference"]
        if not parity.exists():
            raise SystemExit(f"{path}: parity_reference does not exist: {parity}")


def validate_registry() -> list[dict[str, Any]]:
    entries = []
    schema_path = SCHEMA_DIR / "model-wiring.schema.json"
    for path in sorted(REGISTRY_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        validate_schema(data, schema_path, str(path))
        check_registry(path, data)
        entries.append(data)
    if not entries:
        raise SystemExit("no model registry entries found")
    return entries


def validate_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_schema(data, SCHEMA_DIR / "evidence-manifest.schema.json", str(path))
    if data["backend"]["engine"] != data["results"]["pricing_engine"]:
        raise SystemExit(f"{path}: backend.engine and results.pricing_engine differ")
    if data["backend"]["engine"] != "cpp_daily_termsheet_eki":
        raise SystemExit(f"{path}: unexpected native engine {data['backend']['engine']}")
    if not all(data["checks"].values()):
        raise SystemExit(f"{path}: evidence contains a failed check")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, action="append", default=[])
    args = parser.parse_args()
    entries = validate_registry()
    for path in args.manifest:
        validate_manifest(path)
    print(f"Validated {len(entries)} model registry entries")
    if args.manifest:
        print(f"Validated {len(args.manifest)} evidence manifests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
