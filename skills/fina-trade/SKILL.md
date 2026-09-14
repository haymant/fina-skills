---
name: fina-trade
description: FinA trade domain lifecycle, RFQ/quote/trade/instrument/position state machines, durable event sourcing, amendments, and version anchors. Use for trade persistence or lifecycle behavior.
---

# FinA Trade

Use when changing trade identity, registration, amendments, lifecycle events, instruments, positions, or reconciliation history.

## Invariants

- A trade mutation becomes visible before its lifecycle event is published.
- Lifecycle events are append-only and replayable.
- Quote and report versions carry stable anchors such as `quote_version` and `priced_at`.
- Handlers receive complete typed inputs and dependency results; they do not reach into another service’s mutable state.
- Lifecycle state is explicit and can be snapshotted into repricing requests.

## Workflow

1. Locate the state transition and its durable record.
2. Define the event payload and compatibility/version impact.
3. Make the repository mutation atomic from the caller’s perspective.
4. Publish the typed event after success.
5. Add replay, idempotency, and amendment tests.
6. Verify the scheduler subscription path if the event triggers downstream work.

Keep product semantics in `fina-core`; keep pricing behavior in `fina-risk`.

## Canonical schema

Use [`schema/trade.schema.json`](../../schema/trade.schema.json) for the current trade contract. ProductTerms and lifecycle-state schemas remain pending explicit freezing.
