---
name: fina-core
description: Shared FinA domain semantics, schemas, event envelopes, ownership boundaries, and compatibility rules. Use when designing or changing canonical ProductTerms, InstrumentModel, lifecycle state, or cross-repository contracts.
---

# FinA Core — shared meaning

Use this chapter before changing a cross-repository contract. Treat it as the semantic foundation, not as an execution engine.

## Non-negotiable position

Adopt semantic unification and reject execution unification. FinA uses **one model, many engines**: shared product terms, lifecycle functions, event envelopes, and conformance fixtures; plural pricing, trade, risk, and query runtimes.

## Canonical ownership

- `ProductTerms` and `instrument-model.schema.json` belong in the shared `FinA/schemas/` package.
- `fina-trade` owns durable trade identity, lifecycle events, and version anchors.
- `fina-risk` owns compiled/vectorized pricing and sensitivity backends.
- `fina-core` owns shared schema-facing adapters and the reference lifecycle/oracle path.
- `fina-core-scheduler` owns process orchestration, not business valuation.
- `fina-olap` owns columnar query, materialization, and report presentation contracts.

Do not make the engine read `ProductTerms` directly. Project terms into a typed pricing request at quote time and persist that projection beside the quote result.

## Workflow

1. Identify whether the change is semantic, lifecycle, execution, or presentation.
2. Update the owning chapter and schema first; record compatibility/version impact.
3. Add or update a conformance fixture before changing multiple runtimes.
4. Verify event correlation, version anchors, and replay behavior.
5. Run the affected chapter checks plus the end-to-end coordinator checks.

## Read next

- For schema and event details, read `references/contracts.md`.
- For the CDM boundary and non-goals, read `references/position.md`.
- For product-family additions, read `fina-risk` and `fina-trade` chapters.

