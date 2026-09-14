# Standalone schema examples

Each `*.example.json` file is a small, human-readable fixture for the same-named schema in `../../`. The fixtures are intentionally minimal but representative: they show the contract shape without pretending to be production data.

## Verify independently

From the repository root:

```bash
python schema/examples/basic/verify_examples.py
```

The verifier uses the installed `jsonschema` package, resolves each schema locally, validates every fixture, and reports the schema/example pair. It has no dependency on FinA runtime services, databases, MCP, cloud credentials, or network access.

## Demo independently

To print a compact contract demo after validation:

```bash
python schema/examples/basic/verify_examples.py --demo
```

The demo prints each fixture’s required fields and a few identifying values. Add a new schema and example together; keep the filename stem aligned with the schema filename.
