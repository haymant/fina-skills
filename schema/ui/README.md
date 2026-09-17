# Canonical UI metadata

The `schema/ui/` directory is the source of truth for metadata that drives FinAP pages and the future `fina-ui` runtime. It is deliberately separate from product and process schemas:

| Contract | Responsibility |
|---|---|
| `schema/*.schema.json` | Domain meaning, data shape, and validation |
| `schema/ui/*.schema.json` | UI metadata shape and metadata validation |
| `schema/ui/examples/` | Concrete page, layout, workflow, and action metadata |
| `skills/finap-dev/` | Development procedure, renderer policy, and implementation guidance |

UI metadata may reference domain schemas by stable ID, but it must not redefine product semantics or embed React component code.

## Metadata kinds

The canonical `ui-metadata.schema.json` supports these entry kinds:

- `page`: page-level root schema, layout, workflow, and mode configuration;
- `layout`: compositional sections and field references;
- `workflow`: ordered wizard steps and navigation;
- `flex-block`: reusable semantic substructure or collection editor;
- `field-ui`: renderer and formatting hints for a schema path;
- `action`: registered logical operation, process, input schema, lifecycle preconditions, refresh targets, events, and evidence requirements;
- `resource`: refreshable record or query resource.

The schema is intentionally metadata-oriented. Renderer IDs, logical operations, process references, and resource IDs are validated as references or identifiers; their implementations remain in the application and FinA adapters.

## Validation

Validate a metadata document locally with `jsonschema`:

```bash
python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path("schema/ui/ui-metadata.schema.json").read_text())
validator = Draft202012Validator(schema)
for name in ("fcn-rfq.ui.json", "fcn-rfq.workflow.json"):
    example = json.loads(Path(f"schema/ui/examples/{name}").read_text())
    validator.validate(example)
print("UI metadata is valid")
PY
```

The `examples/` directory holds the page fixture (`fcn-rfq.ui.json`) and the workflow fixture it references (`fcn-rfq.workflow.json`), whose steps mirror the current FCN RFQ flow: identity → underlyings → coupon → protection → settlement → pricing → review.

Read [`skills/finap-dev/references/ui-runtime-principles.md`](../../skills/finap-dev/references/ui-runtime-principles.md) for the renderer runtime, flex-block state model, action lifecycle, provenance, and rollout phases.


## FCN economics and operation contracts

The UI contract is intentionally split into three related schemas. `ui-metadata.schema.json` defines composition and presentation. `leg-allocation.schema.json` separates editable FCN economics from compiler- and pricing-generated funding, coupon, and terminal-optionality legs. `operation-action.schema.json` defines logical operations, lifecycle preconditions, actor capabilities, refresh targets, expected events, and evidence requirements. Action metadata describes intent; it does not authorize a transition.

The examples demonstrate the intended boundary. `examples/fcn-economics-leg-allocation.json` contains declared and generated FCN legs, while `examples/fcn-quote-price.action.json` describes a native quote operation without exposing MCP routing to browser code.

The implementation guide is [`skills/finap-dev/references/fcn-leg-allocation-and-actions.md`](../../skills/finap-dev/references/fcn-leg-allocation-and-actions.md). It includes the Economics and Payoff Composition workflow, renderer rules, action lifecycle, and a ready-to-use developer handoff prompt.
