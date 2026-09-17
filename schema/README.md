# FinA standalone schemas

This directory is the canonical, reviewable schema surface for the FinA skill book. Schemas are kept out of individual `SKILL.md` files so agents can load contracts independently from procedural guidance.

## Formatting rule

Use JSON Schema Draft 2020-12. Format with two-space indentation and `json.dumps(..., indent=2)`-equivalent output: every property name must appear on its own row, including nested properties. Do not compress objects or arrays into single-line property definitions. Preserve schema semantics while formatting; any semantic change requires a separate review.

## Reviewed tranche

The following existing schemas were copied from the source repositories and formatted without semantic changes:

| Standalone schema | Source | Review status |
|---|---|---|
| `fina-process.schema.json` | `FinA/skills/fina-core-scheduler/schema/fina-process.schema.json` | reviewed: concrete process contract |
| `etl.schema.json` | `FinA/skills/fina-core-scheduler/schema/etl.schema.json` | reviewed: concrete pipeline contract |
| `lambda-task.schema.json` | `FinA/skills/fina-e2e-coordinator/references/lambda-task.schema.json` | reviewed: concrete task context |
| `trade.schema.json` | `fina-trade/schema/trade.schema.json` @ `3788c65` | reviewed: concrete trade envelope |
| `pricing-request.schema.json` | `fina-risk/skills/fina-risk/schema/pricing-request.schema.json` @ `8884093` | reviewed: concrete engine input |
| `job-status.schema.json` | `fina-risk/skills/fina-risk/schema/job-status.schema.json` @ `8884093` | reviewed: concrete job output |
| `risk-cell.schema.json` | `fina-risk/skills/fina-risk/schema/risk-cell.schema.json` @ `8884093` | reviewed: concrete risk output |
| `pnl-explain.schema.json` | `fina-risk/skills/fina-risk/schema/pnl-explain.schema.json` @ `8884093` | reviewed: concrete P&L output |
| `storage-boundaries.schema.json` | `fina-risk/skills/fina-risk/schema/storage-boundaries.schema.json` @ `8884093` | reviewed: concrete storage contract |
| `model-wiring.schema.json` | FinA skill-book Phase 2A contract | reviewed: registry governance contract |
| `evidence-manifest.schema.json` | FinA skill-book Phase 2A contract | reviewed: executable E2E evidence contract |
| `fcn-lifecycle-state.schema.json` | `fina-trade` status contract plus FCN observation/settlement state | reviewed: FCN lifecycle state contract |
| `fcn-lifecycle-event.schema.json` | `fina-trade` in-memory event envelope plus FCN event topics | reviewed: FCN lifecycle event contract |
| `fcn-lifecycle-transition.schema.json` | FinA skill-book Phase 2B contract | reviewed: FCN transition/replay contract |
| `fcn-fixing-record.schema.json` | FinA skill-book Phase 2B contract | reviewed: FCN fixing provenance contract |
| `fcn-market-operation.schema.json` | FinA skill-book Phase 2B contract | reviewed: FCN operational command contract |
| `fcn-legacy-termsheet.schema.json` | `fina-risk` legacy `Chunk/Jobs` fixture boundary | reviewed: source-boundary contract |
| `fcn-terms-projection.schema.json` | FinA skill-book example-level migration contract | provisional: semantic bridge pending ProductTerms freeze |
| `fcn-etl-result.schema.json` | `fina-risk` `run_etl_task` output shape | reviewed: captured ETL result contract |
| `fcn-native-pricing-result.schema.json` | `fina-risk` native daily-term-sheet output | reviewed: captured native result contract |

The source `FinA` revision for the first three schemas is `7818a28`. The `fina-trade` sources were reviewed at `3788c65`; the `fina-risk` sources were reviewed at `8884093`. `fina-olap` was inspected at `6b67553`, but no OLAP schema was promoted in this tranche because its current contract is implemented in Python and its report-version materialization schema is not yet frozen.

## RiskCube contracts

The application and service ownership, submodule policy, stdio/Streamable HTTP MCP boundary, tac-engine status, and FinAP RiskCube workflow are defined in [`../refs/finap-architecture-and-mcp.md`](../refs/finap-architecture-and-mcp.md). This architecture reference is normative for FinAP integration work; legacy `tradeac` and `fina-pricer` remain reference-only systems.

The `schema/riskcube/` family is the canonical contract for scenario/version metadata, report metadata, and generated columnar dataset manifests:

| Schema | Responsibility |
|---|---|
| `riskcube/scenario.schema.json` | Durable market-data definition |
| `riskcube/version.schema.json` | Immutable release/execution anchor |
| `riskcube/report.schema.json` | Risk, P&L, Taylor, and forecast report metadata |
| `riskcube/slice.schema.json` | Reusable instrument-universe slice definition |
| `riskcube/dataset-manifest.schema.json` | Typed Parquet/DuckDB storage manifest |
| `riskcube/olap-query.schema.json` | Typed SSRM query envelope |
| `riskcube/olap-result.schema.json` | Typed OLAP result envelope |

Generated sensitivity, P&L, Taylor, and forecast values are not JSON fields. They are typed columns in Hive-partitioned Parquet queried through DuckDB. The normalized RFK tuple is the composite risk-factor key; see [`../refs/riskcube/columnar-storage-and-olap.md`](../refs/riskcube/columnar-storage-and-olap.md).

## Boundary and review policy

The unification plan identifies `ProductTerms`, `LifecycleState`, `InstrumentModel`, typed event envelopes, report-version manifests, and daily risk materialization as important but not yet frozen. Do **not** invent or freeze those schemas here solely from prose. Add each only after its owning repository has a concrete implementation or an explicit schema decision.

When adding a schema:

1. Identify the owning repository and source path.
2. Copy and format the concrete source schema without changing semantics.
3. Record source revision and review status in this file.
4. Update the relevant skill chapter to link to this standalone schema.
5. Validate JSON syntax and all local `$ref` targets.
6. Add an example or contract test where ambiguity remains.

## Examples

UI metadata is maintained separately under [`ui/`](ui/). Its canonical shape is [`ui/ui-metadata.schema.json`](ui/ui-metadata.schema.json), with an independent FCN fixture under [`ui/examples/`](ui/examples/). The UI metadata contract governs presentation and workflow references; it does not replace or merge with product schemas.

See [`examples/basic/README.md`](examples/basic/README.md) for one minimal fixture per reviewed schema and an independent verifier. Run `python schema/examples/basic/verify_examples.py --demo` from the repository root; validation uses only the local schemas and the `jsonschema` package, without FinA services, MCP, databases, cloud credentials, or network access.

See [`examples/fcn/README.md`](examples/fcn/README.md) for the `ELIFCN_KI` term-sheet sample and the real ETL-to-native-C++ scheduler E2E runner. Unlike the basic fixtures, the FCN example requires the local FinA runtime and compiled `fina_risk_cpp` module.

Validate the model-wiring registry with `python scripts/validate_model_registry.py`. The native FCN E2E emits a machine-readable manifest (default `/tmp/fina-evidence/fcn/latest-run.json`) and validates it against `evidence-manifest.schema.json`; the manifest records source revisions, native engine identity, market configuration, lifecycle checks, and OLAP evidence.

Validate the FCN lifecycle fixtures independently with `python schema/examples/fcn/lifecycle/verify_lifecycle.py`. These fixtures cover the implemented trade status/event envelope and the explicit FCN contracts for state, transitions, fixing records, and market operations.

Validate the complete offline FCN chain with `python schema/examples/fcn/verify_fcn_examples.py`. It checks the legacy source, semantic projection, captured ETL outputs, compiled pricing request, native quote/reprice results, and `FinaProcess` definition as separate contracts.
