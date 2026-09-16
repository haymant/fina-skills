# Model-Wiring Registry Contract

The registry separates four decisions that are often conflated: the product semantic version, the logical handler, the execution backend, and the runtime risk/evidence profile. A registry entry is descriptive governance, not a replacement for the canonical JSON Schemas.

## Scope — flex is documentation, not a runtime

The `flex` section in the model-registry YAML is **informational only**. It is not consumed by finap's runtime. Its purposes are:

- **Schema formulation guide**: it tells schema authors which terms the Murex Playbook groups together (KIKOSelect, RGACCDate, etc.), which finap domain-schema properties (`/features/return_ratio`, `/protection/barrier_type`, etc.) to create, and which `field-ui` entries to register.
- **Coverage tracking**: the feature map column and Playbook↔registry matrix let reviewers verify that finap covers every Murex flex block field before a freeze.

**finap's UI rendering does NOT read the flex blocks.** The runtime stack is: `trade.rfq-create.schema.json` → `field-ui/*.json` (per-kind files, keyed by `schema_path` + `renderer`) → `metadata-registry.ts` (`fieldUiForPath`) → `renderer-registry.tsx` (React component). A developer looking at `flex.blocks[].fields` will not find a code path that feeds those into the UI.

The separate `flex-block` kind that *does* exist in finap's bundle (`src/data/fina-ui/blocks/`) is a different concept — reusable layout fragments (e.g., `fcn.underlyings`, `shared.review-submit`) referenced in workflow steps. These have no connection to the Murex block names in the registry YAML.

## Required fields

| Field | Meaning |
|---|---|
| `product_family` / `version` | Stable product identity and registry revision |
| `flex` | Booking layer: Murex flex header, payoff script, model group, and the flex blocks (name, purpose, fields, terms path) |
| `terms` / `pricing_request` | Canonical semantic and engine-input contracts |
| `lifecycle` | State machine and event topics used by the product |
| `market_data` | Required snapshot items and versioned calendar/observation conventions |
| `pricing.logical_handler` | Scheduler-facing name, if one exists |
| `pricing.backends` | Reference/native implementations and their provenance |
| `risk_profiles` | Runtime-selected sensitivity sets and conventions |
| `evidence` | Required markers, parity comparisons, and tolerances |

## Flex-wiring rules

The `flex` section implements the product → header → payoff → model group → blocks dictionary. Record the Murex `header`, its `payoff_script`, the `model_group`, and one entry per `block` with its `purpose`, canonical `fields`, aliases (block names drift: `KIKOSEL*` vs `KIKOSELECT`, `GLOBALKO*` vs `DAILYKO`), and the `terms_path` the block maps into. Flex field names are the authoritative booking names and must match the C++ mapping struct case-for-case; the registry is where that coupling is made reviewable before code.

## Backend rules

A backend entry must state its `kind` (`reference`, `native_cpp`, `python`, `aad`, `pathwise`, or another explicit lane), module/repository, callable, source revision, and engine marker where applicable. A `native_cpp` backend must also state the build target and whether native execution is mandatory for production evidence. A fallback is a separate backend, never an implicit behavior; its output must carry a fallback reason and cannot satisfy a native-only gate.

## Risk-profile rules

A risk profile declares the measures, numerical method, bump convention, units, scaling, market-data shifts, and tolerance. For example, `quote` may request PV only, while `full-trading` may request Delta, Gamma, Vega, Rho, correlation, dividend, and FX sensitivities. The pricing engine does not decide which profile a report or simulation uses.

## Evidence rules

Every E2E or parity run should emit enough information to reproduce the result: registry version, source revisions, backend/module/function, engine marker, binary/build identity, market snapshot and calendar versions, path/seed configuration, result values, tolerances, and check status. Human-readable reports such as `daily-termsheet-parity.md` should be generated or cross-linked from machine-readable evidence.

## Change procedure

1. Load the closest registry entry and owning skills.
2. Confirm semantic/schema compatibility before changing execution wiring.
3. Add or update a conformance fixture and expected engine marker.
4. Run the reference and target backend where both are claimed.
5. Run the full real-adapter E2E for lifecycle and OLAP wiring.
6. Update the registry revision and provenance; do not overwrite historical evidence.
