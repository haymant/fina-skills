---
name: fina-trade
description: FinA trade domain lifecycle, RFQ/quote/trade/instrument/position state machines, durable event sourcing, amendments, and version anchors. Use for trade persistence or lifecycle behavior.
---

# FinA Trade

Use when changing trade identity, registration, amendments, lifecycle events, instruments, positions, or reconciliation history.

For repository revamps, fixing and corporate-event handling, transition registries, transactional outbox design, stdio MCP integration, or FinAP metadata/actions, read [`references/trade-repository-and-ui-design.md`](references/trade-repository-and-ui-design.md).

## Invariants

- A trade mutation, lifecycle event, and outbox record commit atomically; downstream publication occurs only after commit.
- Lifecycle events are append-only and replayable.
- Quote and report versions carry stable anchors such as `quote_version` and `priced_at`.
- Handlers receive complete typed inputs and dependency results; they do not reach into another service’s mutable state.
- Lifecycle state is explicit and can be snapshotted into repricing requests.
- RFQ, quote, and trade statuses are separate state machines; mutations resolve through a legal transition registry.
- Fixings are immutable and idempotent; corrections supersede prior records rather than overwriting economic history.
- Positions are derived projections, not a second source of trade truth.

## Workflow

1. Locate the state transition and its durable record.
2. Define the event payload and compatibility/version impact.
3. Make the repository mutation atomic from the caller’s perspective.
4. Commit the lifecycle event and outbox record with the mutation, then publish only after success.
5. Add replay, idempotency, stale-version, fixing, amendment, and terminal-state tests.
6. Verify the stdio MCP adapter and scheduler subscription path if the event triggers downstream work.

Keep product semantics in `fina-core`; keep pricing behavior in `fina-risk`.

## Canonical schema

Use the shared contracts under [`schema/trade/`](../../schema/trade/): RFQ, immutable quote, trade, lifecycle event, fixing record, market operation, and position. Product-specific semantics may extend these contracts but must not duplicate the repository event or operation envelope.
