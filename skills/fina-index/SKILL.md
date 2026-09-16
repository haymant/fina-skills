---
name: fina-index
description: FinA skill-book routing and repository map. Use at the start of any FinA development, design review, migration, or debugging task to select the relevant chapters and verification path.
---

# FinA Skill Index

Start here for every FinA task. Classify the request, load the smallest relevant chapters, then finish with `fina-e2e-coordinator` when more than one service is involved.

Canonical JSON Schemas live in the repository-root `schema/` directory. Read the relevant schema directly instead of relying on prose or a duplicated copy inside a skill.

## Routing table

| Concern | Chapter |
|---|---|
| Shared schemas, events, product semantics | `fina-core` |
| Process YAML, dependencies, subscriptions, adapters | `fina-core-scheduler` |
| Street-to-terms projections and bulk columnar ingestion | `fina-etl` |
| Trade identity, lifecycle, amendments, event log | `fina-trade` |
| Pricing, Greeks, P&L, model DSL, compiled kernels | `fina-risk` |
| Parquet/DuckDB SSRM, MCP, `fina-table`, report versions | `fina-olap` |
| Full RFQ → quote → trade → reprice → OLAP proof | `fina-e2e-coordinator` |
| Product-family onboarding, model wiring, delivery gates, release evidence | `fina-product-development` |
| FinAP dashboard, schema-driven React UI, flex-block workflows, and UI provenance | `finap-dev` |
| Architecture decisions and non-goals | `fina-master` |

## Selection rules

1. Load `fina-core` for any shared payload or schema change.
2. Load the owning implementation chapter for code changes.
3. Load `fina-core-scheduler` for orchestration, even if the handler is in another repository.
4. Load `fina-e2e-coordinator` for cross-repository verification.
5. Load `fina-product-development` and the closest `model-registry/*.yaml` entry when adding or reviewing a product family, backend, risk profile, lifecycle, or release gate.
6. Never claim MCP wiring, deployment, or publication is live without a real tool call or CI evidence.

## Source map

- `FinA`: schemas, core adapters, scheduler, ETL, examples, architecture notes.
- `fina-trade`: trade domain and lifecycle persistence.
- `fina-risk`: risk/pricing engines and conformance lanes.
- `fina-olap`: OLAP service, React table, demo, and columnar store.
- `model-registry`: product-to-terms, lifecycle, backend, risk-profile, and evidence wiring.
