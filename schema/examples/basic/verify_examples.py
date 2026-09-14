#!/usr/bin/env python3
"""Validate and optionally summarize the standalone FinA schema examples."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_ROOT = HERE.parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='print a compact summary after validation')
    args = parser.parse_args()
    failures = []
    passed = []
    for example_path in sorted(HERE.glob('*.example.json')):
        schema_path = SCHEMA_ROOT / example_path.name.replace('.example.json', '.schema.json')
        try:
            schema = json.loads(schema_path.read_text(encoding='utf-8'))
            example = json.loads(example_path.read_text(encoding='utf-8'))
            errors = sorted(Draft202012Validator(schema).iter_errors(example), key=lambda e: list(e.path))
            if errors:
                failures.append((example_path.name, '; '.join(e.message for e in errors)))
            else:
                passed.append((schema_path.name, example_path.name, example))
        except Exception as exc:
            failures.append((example_path.name, str(exc)))
    for schema_name, example_name, _ in passed:
        print(f'PASS {schema_name} <- {example_name}')
    for name, error in failures:
        print(f'FAIL {name}: {error}')
    if args.demo:
        print('\nDemo summary:')
        for schema_name, example_name, value in passed:
            keys = ', '.join(value.keys()) if isinstance(value, dict) else type(value).__name__
            print(f'- {schema_name}: {keys}')
    print(f'\nValidated {len(passed)} examples; failures: {len(failures)}')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
