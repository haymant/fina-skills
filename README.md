# FinA Skills

An agent skill book for the FinA equity-derivative trading ecosystem. Load [`skills/fina-index/SKILL.md`](skills/fina-index/SKILL.md) first; it routes work to the master architecture chapter and focused implementation chapters.

The standalone [`schema/`](schema/) directory contains the reviewed JSON Schema contracts. Load schemas independently from procedural skill guidance; do not embed duplicate schema copies in `SKILL.md` or chapter references.

## Structure

- `skills/fina-master` — architecture, principles, ADR routing, and non-goals
- `skills/fina-index` — task routing and repository map
- `skills/fina-core` — shared semantics and contracts
- `skills/fina-core-scheduler` — process orchestration and event subscriptions
- `skills/fina-etl` — street and bulk data lanes
- `skills/fina-trade` — lifecycle and durable events
- `skills/fina-risk` — pricing, risk, and backend conformance
- `skills/fina-olap` — Parquet/DuckDB, SSRM, MCP, and `fina-table`
- `skills/fina-e2e-coordinator` — cross-repository verification
- `skills/fina-product-development` — product-family delivery workflow and release gates
- `model-registry` — versioned product-to-model/backend/risk/evidence wiring

## Schema directory

The first reviewed tranche includes process, ETL, lambda-task, trade, pricing-request, job-status, risk-cell, P&L explanation, and storage-boundary contracts. See [`schema/README.md`](schema/README.md) for source provenance, review status, formatting rules, and the list of intentionally deferred schemas such as `ProductTerms`, `LifecycleState`, and `InstrumentModel`.

The chapters intentionally contain operational knowledge and links, not vendored source code. Source evidence is drawn from `FinA` revision `7818a28` and the public sibling repositories available during this bootstrap. The `tradeac` checkout was unavailable without GitHub authentication and is therefore not treated as verified evidence.

Product-family work starts with [`skills/fina-product-development/SKILL.md`](skills/fina-product-development/SKILL.md), then loads the closest [`model-registry/`](model-registry/) entry before changing semantic projections, pricing backends, lifecycle events, risk profiles, or E2E evidence.

## Maintenance

When a repository contract changes, update the owning chapter, its references, and the index routing table in the same change. Add conformance or E2E evidence before marking a capability as implemented.
