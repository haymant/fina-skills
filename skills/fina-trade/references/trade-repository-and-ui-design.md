# FinA Trade Repository and Metadata-Driven UI Design

## Scope and conclusion

The current `fina-trade` POC is a useful repository boundary. It already contains a Postgres-backed RFQ, quote, trade, instrument, position, and lifecycle-event model; transactional mutation methods; append-only lifecycle events; query methods; an in-memory deterministic test repository; and a FastMCP server whose default transport is stdio.

The revamp should preserve that foundation while making the contracts canonical, the lifecycle state machine explicit, fixings first-class and idempotent, and UI operations metadata-driven. The central rule is:

> **A trade repository is an event-producing state machine with durable projections, not a CRUD table wrapper.**

## Findings from the POC

The current implementation has several strong patterns:

- quote versions are inserted rather than overwritten;
- an instrument is created at the first quote and becomes non-indicative when a quote is accepted;
- accepted trades aggregate into positions by `(portfolio, instrument_id)`;
- mutations use database transactions and row locks;
- lifecycle rows capture before and after state;
- fixing-like observations and corporate events exist in the in-memory repository;
- the MCP entrypoint already defaults to `mcp.run(transport="stdio")`;
- the large RiskCube remains outside the trade repository, which is the correct ownership boundary.

The main gaps to resolve before aligning FinAP and the canonical schemas are:

1. The database schema, Python methods, FCN fixtures, and UI action names are not yet one versioned contract.
2. Lifecycle transitions are represented by status strings and guard checks but not by one explicit transition registry with legal from/to states, actor capability, repricing effect, settlement effect, and idempotency semantics.
3. `fixing-record` is present as an FCN fixture concept but is not yet a first-class shared repository contract and operation with uniqueness and replay rules.
4. Lifecycle event publication needs an outbox or equivalent committed-event boundary so downstream repricing cannot observe a mutation that later rolls back.
5. Concurrency must use an explicit state-version or optimistic-concurrency check in addition to row locks where commands can be retried or reordered.
6. Accepting, amending, cancelling, fixing, knocking, expiring, exercising, and settling are distinct operations and should not be collapsed into a generic update.
7. The current query surface is useful but should expose stable pagination and a consistent result envelope rather than only a date range and limit.
8. FinAP should call the stdio MCP server through a server-side adapter, not `FINA_TRADE_MCP_URL` from browser or UI code.

## Canonical ownership model

```text
fina-trade
├── RFQ and quote-version records
├── instrument identity and indicative/real status
├── accepted trade terms and lifecycle state
├── fixing records and corporate-event records
├── append-only lifecycle events / outbox
├── position projections
└── logical MCP operations

fina-risk
├── terms projection and pricing request
├── native C++ valuation and risk
├── quote/reprice result and evidence
└── large risk-cube persistence

fina-olap
├── normalized analytical datasets
├── report versions and SSRM queries
└── analytical projections, not authoritative trade state

FinAP
├── schema-driven presentation
├── operation-action invocation through authenticated server actions
└── no direct database, MCP URL, or engine selection
```

## Lifecycle model

Use a transition registry rather than accepting arbitrary status updates. A transition record should declare:

```yaml
operation: trade.amend
from: [LIVE, AMENDED]
to: AMENDED
actor_capability: trading.trade.amend
requires_reason: true
requires_expected_state_version: true
idempotent: false
reprice_required: true
cashflow_effect: NONE
event_topic: trade.lifecycle.amended
```

The minimum lifecycle should distinguish RFQ, quote, and trade state. Do not use one status enum for all three aggregates. A practical model is:

```text
RFQ: RECEIVED → QUOTED → CONVERTED | EXPIRED | CANCELLED
Quote: VALID → ACCEPTED | EXPIRED | REJECTED | CANCELLED
Trade: LIVE → AMENDED → MATURED | TERMINATED | CANCELLED
```

Product-specific observation and settlement state belongs inside a lifecycle-state object, for example:

```text
observation_state: NOT_STARTED | FIXING_PENDING | FIXED | KNOCKED_IN | KNOCKED_OUT | COMPLETED
settlement_state: NOT_DUE | COUPON_DUE | CASH_SETTLEMENT_DUE | PHYSICAL_DELIVERY_DUE | SETTLED | WAIVED
```

A command must validate the current aggregate, expected state version, actor capability, idempotency key, and product-specific preconditions before changing state. A successful command writes the aggregate, lifecycle event, and outbox record in one transaction.

## Fixings and market operations

A fixing is not a mutable field on a trade. It is an immutable market observation keyed by at least:

```text
(trade_id, fixing_date, observation_type, source, idempotency_key)
```

A fixing record should preserve the underlying identifier, reference, fixing, performance, data quality, barrier indicators, coupon decision, state patch, market snapshot, calendar, source revision, recorded time, and idempotency key. Replaying the same fixing must return the original result without adding a second economic event. A corrected market observation should create a superseding correction event with a new version and explicit causation, not silently overwrite history.

The operation flow is:

```text
market snapshot
→ validate trade is eligible for observation
→ normalize fixing record
→ check idempotency and expected lifecycle version
→ calculate product decision through the product process
→ persist fixing and trade state atomically
→ append lifecycle event and outbox message
→ schedule repricing or settlement if required
```

Do not let the fixing endpoint invent product payoff rules. The product process or risk engine returns the decision. The repository records the decision, state transition, and references.

Corporate events should follow the same pattern. Store the event source, effective date, adjustment policy, affected underlyings, input payload, and resulting lifecycle action. Keep market-data ingestion, product interpretation, and repository mutation separate.

## Transaction and event rules

Every mutation should be one database transaction:

```text
lock aggregate
→ check idempotency
→ validate transition
→ write aggregate/version
→ write fixing or lifecycle record
→ write append-only event
→ write outbox row
→ update derived position projection
→ commit
```

Only after commit should a scheduler or risk service receive the event. An outbox worker can publish `trade.lifecycle.amended`, `trade.lifecycle.fixed`, `trade.lifecycle.knocked`, `trade.lifecycle.expired`, and `trade.lifecycle.settled`. The consumer must deduplicate by `event_id` and preserve `correlation_id` and `causation_id`.

Positions are derived projections. They can be recomputed from non-terminal trades and should carry a projection version or refreshed timestamp. They are not a second authority for trade status.

## Canonical schemas

Use these shared contracts under `schema/trade/`:

- `rfq.schema.json` for received RFQs;
- `quote.schema.json` for immutable quote versions;
- `trade.schema.json` for accepted trades;
- `lifecycle-event.schema.json` for committed events;
- `fixing-record.schema.json` for immutable observations;
- `market-operation.schema.json` for commands;
- `position.schema.json` for derived aggregates.

Product-specific lifecycle details may extend these contracts, but a product must not copy the repository event or operation envelope into its own namespace.

## Metadata-driven UI and actions

FinAP should render trade pages from UI metadata and invoke logical operations from action metadata. A trade detail page should compose:

```text
Trade identity
→ accepted quote and source pricing evidence
→ current lifecycle state
→ terms and amendments
→ fixing timeline
→ corporate events
→ settlement obligations
→ position impact
→ audit/event timeline
```

The UI metadata should reference the domain schema and operation-action contracts. Actions should be separate:

```text
rfq.create
quote.persist
trade.accept
trade.amend
trade.cancel
trade.record-fixing
trade.apply-corporate-event
trade.knock
trade.expire
trade.exercise
trade.settle
trade.get
trade.query
position.query
lifecycle.query
```

Each mutation action should declare:

- input and result schemas;
- record binding;
- lifecycle preconditions;
- actor capability;
- confirmation policy;
- expected state version requirement;
- idempotency-key path;
- whether repricing or settlement is required;
- refresh targets;
- expected event topics;
- evidence and provenance requirements.

Use wizard steps for high-dimensional operations. For example, `trade.record-fixing` can use market snapshot selection, underlying fixing grid, barrier/coupon decision preview, validation, and commit. The final commit action remains distinct from preview and must display the exact fixing date, source snapshot, affected state, event topic, and idempotency key.

Use read-only rich lists or expandable cards for lifecycle events and fixing records. Terms remain editable only through a declared amendment action. Generated payoff decisions, state transitions, event IDs, pricing evidence, and settlement IDs are read-only.

## Stdio MCP integration

The target FinAP path is:

```text
FinAP authenticated server action
→ local fina-trade stdio MCP client
→ typed logical operation
→ Postgres repository transaction
→ event/outbox result
→ FinAP resource refresh
```

The stdio process should be configured as a trusted server-side dependency. The UI must never receive database credentials, choose the MCP tool, or call a remote `FINA_TRADE_MCP_URL`. A logical action such as `trade.amend` can resolve to the stdio MCP tool `trade_amend` through an adapter registry.

The adapter should normalize every result into an envelope containing `status`, `record`, `event`, `correlation_id`, `idempotency_key`, `state_version`, and `refresh_targets`. Errors should distinguish validation failure, illegal transition, stale version, duplicate idempotency key, missing record, database failure, and downstream publication failure.

## Recommended revamp phases

### Phase 1: Freeze shared contracts

Adopt the schemas under `schema/trade/`. Add examples and validators. Map each existing POC table and method to one schema. Keep migration compatibility for existing columns.

### Phase 2: Implement the transition and operation registry

Define legal transitions, capability requirements, idempotency rules, repricing flags, settlement effects, and event topics. Make all mutation tools resolve through this registry.

### Phase 3: Promote fixing and corporate events

Add durable fixing and corporate-event records, uniqueness constraints, state-version checks, correction/supersession semantics, and product-process callbacks. Keep the repository independent of payoff implementation.

### Phase 4: Add transactional outbox and projections

Persist events and outbox records atomically. Make scheduler and risk consumers idempotent. Recompute or incrementally update position projections with a clear projection version.

### Phase 5: Replace remote FinAP integration

Add a server-side stdio MCP adapter in FinAP. Migrate action metadata from `FINA_TRADE_MCP_URL` to logical operations resolved through the local process. Test RFQ → quote → accept → amend/fixing → event → reprice → position refresh.

### Phase 6: Evidence and operational hardening

Add Postgres-backed concurrency tests, duplicate command tests, fixing replay tests, rollback/outbox tests, migration idempotency tests, and a real stdio E2E. Record repository revision, schema versions, event IDs, state versions, and downstream response IDs.

## Developer-agent prompt

> Read the canonical FinA skill index, `skills/fina-trade/SKILL.md`, `skills/fina-trade/references/trade-repository-and-ui-design.md`, `skills/fina-risk/SKILL.md`, `skills/fina-risk/references/native-engine-design.md`, and every schema under `schema/trade/` before coding. Study the current `haymant/fina-trade` repository at its latest revision, including `fina_trade/repository.py`, `fina_trade/postgres_repository.py`, `fina_trade/mcp_server.py`, `schema/postgres.sql`, `tests/test_repository.py`, and the existing FinAP action adapter.
>
> Revamp `fina-trade` as the authoritative event-producing trade repository while preserving working POC behavior and migration compatibility. Map RFQs, immutable quote versions, instruments, accepted trades, lifecycle events, fixings, corporate events, positions, commands, and outbox messages to the canonical contracts in `fina-skills/schema/trade/`. Add schema validation and representative examples. Do not keep a second divergent copy of the canonical schema without documenting the source revision and synchronization rule.
>
> Implement an explicit transition/operation registry. Separate RFQ, quote, and trade state machines. Require legal from/to states, actor capability, reason policy, expected state version, idempotency key, repricing requirement, settlement effect, event topic, and refresh behavior for each mutation. Keep `trade.accept`, `trade.amend`, `trade.cancel`, fixing, knock, expiry, exercise, and settlement as distinct operations. Reject stale state versions and illegal transitions with typed errors.
>
> Promote fixings to immutable, idempotent records keyed by trade, fixing date, observation type, and source/idempotency key. Persist each fixing, product decision, state patch, lifecycle event, and outbox message transactionally. Support replay without duplicate economics. Model corrections as superseding records/events rather than silent overwrites. Keep product payoff interpretation in the product process or fina-risk adapter; fina-trade records and governs the decision but does not reimplement pricing.
>
> Add a transactional outbox or equivalent committed-event boundary. Downstream scheduler and risk consumers must only receive committed events and must deduplicate by event ID. Preserve correlation ID, causation ID, event sequence, state version, actor, and source revision. Keep positions as derived projections that can be recomputed from non-terminal trades.
>
> Preserve the existing FastMCP server and add a production stdio path using `mcp.run(transport="stdio")`. Keep the MCP adapter thin and expose logical operations with typed request/result envelopes. FinAP will call this process through a server-side stdio adapter; remove the design dependency on `FINA_TRADE_MCP_URL` and do not expose transport or credentials to browser code. Add explicit health, migration, query, mutation, fixing, lifecycle, and position tools with stable names.
>
> Update tests for schema conformance, migration idempotency, duplicate commands, stale-version rejection, terminal-state rejection, quote-version immutability, instrument birth at the initial quote, position recomputation, fixing replay, correction/supersession, transaction rollback, outbox publication, and a real stdio MCP E2E: RFQ → quote persist → quote accept → trade amend or fixing → lifecycle event → downstream reprice trigger → position/resource refresh.
>
> Update the FinAP metadata and action definitions to use `schema/ui/ui-metadata.schema.json` and `schema/ui/operation-action.schema.json`. Build trade detail and fixing workflows from metadata. Use expandable cards for nested lifecycle state, rich fixing grids for underlying observations, read-only event timelines, and separate preview/commit actions. The browser must never call a database endpoint or select an MCP tool.
>
> Run the complete test suite, schema validators, migration twice, stdio MCP smoke test, and cross-repository E2E. Report changed files, canonical schema mappings, transition registry, event/outbox design, concurrency behavior, stdio command/configuration, test results, unresolved lifecycle semantics, and the exact FinAP migration steps.
