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

The source `FinA` revision for the first three schemas is `7818a28`. The `fina-trade` sources were reviewed at `3788c65`; the `fina-risk` sources were reviewed at `8884093`. `fina-olap` was inspected at `6b67553`, but no OLAP schema was promoted in this tranche because its current contract is implemented in Python and its report-version materialization schema is not yet frozen.

## Boundary and review policy

The unification plan identifies `ProductTerms`, `LifecycleState`, `InstrumentModel`, typed event envelopes, report-version manifests, and daily risk materialization as important but not yet frozen. Do **not** invent or freeze those schemas here solely from prose. Add each only after its owning repository has a concrete implementation or an explicit schema decision.

When adding a schema:

1. Identify the owning repository and source path.
2. Copy and format the concrete source schema without changing semantics.
3. Record source revision and review status in this file.
4. Update the relevant skill chapter to link to this standalone schema.
5. Validate JSON syntax and all local `$ref` targets.
6. Add an example or contract test where ambiguity remains.
