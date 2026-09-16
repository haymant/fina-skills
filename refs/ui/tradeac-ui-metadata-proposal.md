# TradeAC UI Metadata Proposal

## Review status

This document records the current state of `haymant/tradeac` and proposes a metadata contract for rendering the trading and RiskCube pages. It is intentionally a design review artifact. It does not implement the metadata schema or refactor the application.

The proposal follows the refined FinA architecture:

> **Product semantics, model wiring, process orchestration, UI metadata, and runtime evidence are separate contracts.**

The UI metadata should describe how an operator discovers and acts on a contract. It must not redefine the meaning of an FCN, duplicate native pricing inputs, or hide process and lifecycle transitions inside page code.

## Source revisions reviewed

| Repository | Revision | Observation |
|---|---:|---|
| `haymant/tradeac` | `bb67e96` | Current POC application with trading and RiskCube pages, server actions, and MCP adapters. |
| `haymant/fina-skills` | `2d42d67` | Current skill book with standalone schemas, FCN contract-chain examples, model registry, process fixtures, and evidence validation. |

The route inventory was taken from the Next.js app tree, sidebar navigation, page entrypoints, and `tac-app/src/server/fina-actions.ts`.

## Current route inventory

The requested `quote` route is implemented as `/trading/quote`; the word `quite` appears to be a typo in the route list.

| UI route | Current page role | Current backend operation | Current write actions |
|---|---|---|---|
| `/trading/rfq` | RFQ list and RFQ composition | `rfq_query` | `rfq_create` |
| `/trading/quote` | Quote workbench and quote list | `quote_query`, `rfq_query` | `pricing_and_sensitivity`, `quote_persist`, `trade_accept` |
| `/trading/trade` | Trade blotter and trade detail | `trade_query`, `trade_get`, `trade_lifecycle` | `trade_cancel`, `trade_amend` |
| `/trading/instruments` | Instrument inventory | `instrument_query` | None in the current page |
| `/trading/positions` | Position inventory | `position_query` | None in the current page |
| `/riskcube/scenarios` | Scenario list, editor, and batch trigger | `scenario_list` | `scenario_create`, `scenario_update`, `scenario_delete`, `scenario_trigger` |
| `/riskcube/versions` | Version list | `version_list` | None in the current page |
| `/riskcube/slice` | Slice list and slice editor | `slice_list`, `slice_get` | `slice_create`, `slice_update`, `slice_delete` |
| `/riskcube/cubes` | OLAP cube designer and pivot grid | `riskcube_partitions`, `olap_query`, `storage_status` | `set_storage_mode` |

The page structure is already grouped into two useful operator journeys:

1. **Trading:** RFQ → quote → trade → instrument → position.
2. **RiskCube:** scenario → version → slice → cube.

That grouping should become metadata rather than remain encoded only in `sidebar-items.tsx` and page-local components.

## What the POC does well

The POC has several strong foundations that should be preserved.

First, the application already separates browser pages from server-side Fina actions. The server action layer enforces authentication and translates page operations into `fina-trade` or `fina-pricer` MCP calls. This is a sound boundary for the first metadata implementation.

Second, the RiskCube pages expose useful domain concepts rather than a generic dashboard. Scenarios have keys, versions, market-data manipulations, and repository snapshots. Slices have conditions. Cubes have dimensions, measures, filters, aggregations, partition scopes, and read-only OLAP queries.

Third, the quote workflow already connects an RFQ to a full pricing request and to a native pricing result. This aligns with the FCN example chain in `fina-skills`, where the pricing request is an explicit engine DTO and the native quote/reprice results are evidence-bearing artifacts.

Fourth, the cube page treats version × scenario as a partition scope. This is compatible with the FinA principle that runtime results should be traceable to a process, market-data state, scenario, and engine execution.

## Where the POC does not yet conform to the refined contracts

### 1. The UI data boundary is structurally untyped

The server action aliases are currently broad records:

```ts
export type FinaRfq = Record<string, unknown>;
export type FinaQuote = Record<string, unknown>;
export type FinaTrade = Record<string, unknown>;
export type PricingRequest = Record<string, unknown>;
```

This makes page development fast, but it allows the UI to infer contract meaning from field names and casts. The FCN contract chain takes the opposite approach: source terms, semantic terms, pricing requests, lifecycle events, process definitions, and evidence each have explicit schemas.

The UI metadata proposal should not attempt to solve all domain typing at once. It should require every page resource to declare the schema or contract identifier for the data it renders, and it should distinguish a stable identifier from a provisional schema.

### 2. Page actions are not declared as lifecycle transitions

The current pages call operations such as `trade_accept`, `trade_amend`, `trade_cancel`, `scenario_trigger`, and `slice_delete` directly from components. The UI knows the button label and payload, but not the state precondition, resulting event, process, evidence requirement, or destructive-action policy.

For the refined model, an action should point to a declared operation or lifecycle transition. It should include:

- the operation name;
- the input contract;
- the selected-record binding;
- the required state or capability;
- the confirmation policy;
- the expected events and resulting resource refresh;
- the process and evidence references when the action invokes pricing or risk computation.

The metadata should describe the action. The backend remains authoritative for authorization, validation, lifecycle legality, and execution.

### 3. Pricing is treated as a page action rather than a process invocation

The quote workbench calls `pricing_and_sensitivity`, which is correct as an adapter operation, but the page metadata should identify it as a process step. For FCN, the relevant conceptual flow is:

```text
RFQ source
→ terms projection
→ ETL augment
→ ETL compile
→ pricing request
→ native quote or reprice
→ quote persistence or trade acceptance
→ lifecycle event
→ OLAP / RiskCube evidence
```

A quote page should therefore declare which process it invokes and which evidence it expects. It must not silently construct an incompatible pricing request merely because a form happens to contain fields with similar names.

### 4. RiskCube resources are not yet connected to model-registry metadata

The current scenario and cube screens have useful local contracts, but a scenario key, version key, slice condition, and cube measure are not yet linked to a product family, model wiring entry, or process definition.

For example, a scenario run should be able to identify:

- the product family or instrument population it targets;
- the source request or slice used to select instruments;
- the scenario and version definitions;
- the pricing process and native engine marker;
- the resulting partition and evidence manifest.

This is particularly important because the refined architecture rejects a generic “risk cube” as an unexplained data store. A RiskCube result is an execution artifact with declared scope and provenance.

### 5. Navigation is a presentation structure, not yet a capability model

`sidebar-items.tsx` declares titles, icons, URLs, and grouping. It does not declare whether a page is available for a user role, product family, engine capability, or deployment state. The new metadata should add these constraints without making navigation depend on client-side guesses.

## Proposed metadata layers

The metadata should be split into five related but independently evolvable documents.

### A. Application navigation metadata

Navigation metadata describes the route tree and page discovery.

```yaml
id: trading-rfq
kind: navigation
title: RFQs
path: /trading/rfq
group: trading
page: trading.rfq
icon: send
order: 10
capabilities:
  - rfq.read
  - rfq.create
```

Navigation metadata should not contain SQL, MCP argument shapes, product term definitions, or pricing formulas.

### B. Page resource metadata

A page declares the resources it loads and the presentation contract for each resource.

```yaml
id: trading.rfq
kind: page
path: /trading/rfq
resources:
  - id: rfqs
    source:
      adapter: fina-trade
      operation: rfq_query
      parameters:
        limit: 50
    schema: trade.rfq
    presentation:
      mode: table
      row_key: rfq_id
      columns:
        - key: rfq_id
          label: RFQ
        - key: instrument_id
          label: Instrument
        - key: status
          label: Status
        - key: created_at
          label: Created
          format: datetime
    refresh:
      interval_ms: 10000
```

A resource may be a table, detail record, timeline, form data source, OLAP result, or status panel. The metadata should support those modes explicitly rather than forcing every page into a table abstraction.

### C. Action metadata

Actions describe operator intent and bind a UI control to an adapter operation or process invocation.

```yaml
id: rfq.create
kind: action
label: Create RFQ
scope: collection
input_schema: trade.rfq-create
invoke:
  adapter: fina-trade
  operation: rfq_create
  arguments:
    rfq: $form
success:
  refresh: [trading.rfq.rfqs]
  event: rfq.created
```

A lifecycle action should declare its transition rather than only its transport operation.

```yaml
id: trade.amend
kind: action
label: Amend trade
scope: record
record_binding: trade_id
input_schema: trade.amendment
transition:
  resource: trade
  from: [BOOKED, AMENDED]
  to: AMENDED
invoke:
  adapter: fina-trade
  operation: trade_amend
  arguments:
    trade_id: $record.trade_id
    changes: $form.changes
    reason: $form.reason
success:
  event: trade.lifecycle.amended
  refresh: [trading.trade.trades, trading.positions.positions]
```

The backend must still reject an invalid transition. Metadata is a UI declaration and validation aid, not the authority for lifecycle state.

### D. Process invocation metadata

Pricing and scenario actions need a process reference and evidence policy.

```yaml
id: quote.price
kind: process-action
label: Price RFQ
scope: record
record_binding: rfq_id
process: fcn-termsheet-quote
input_schema: pricing-request
invoke:
  adapter: fina-pricer
  operation: pricing_and_sensitivity
  arguments:
    request: $record.pricing_request
evidence:
  required_engine_marker: cpp_daily_termsheet_eki
  result_schema: fcn-native-pricing-result.schema.json
success:
  result_resource: trading.quote.pricing_result
  refresh: [trading.quote.quotes]
```

A scenario run should use the same pattern, with a scenario, version, slice, request-template, and batch identifier explicitly represented.

### E. Provenance and capability metadata

Every resource or process action that touches FinA should be able to expose provenance. The minimum shared fields should include:

| Field | Purpose |
|---|---|
| `contract` | Stable identifier for the input or output contract. |
| `schema_version` | Version of the contract used by the UI adapter. |
| `source_revision` | Repository revision or registry revision when relevant. |
| `process_id` | Executable process definition invoked by the action. |
| `engine_marker` | Native engine identity for production evidence. |
| `scenario_scope` | Scenario and version scope for RiskCube results. |
| `request_id` | Correlation identifier across UI, MCP, lifecycle, and evidence. |
| `observed_at` | Time at which the UI received the resource. |

These fields may be returned by the backend even when they are not displayed in the primary table. They should be available to a detail drawer, audit view, or diagnostics panel.

## Proposed top-level schema shape

The first schema should be a document envelope rather than a single page-specific mega-schema.

```yaml
ui_document:
  metadata_version: ui-metadata-v1
  application: tradeac
  navigation: []
  pages: []
  resources: []
  actions: []
  contracts: []
  capabilities: []
```

The first implementation should define these discriminated object kinds:

- `navigation_item`;
- `page_definition`;
- `resource_definition`;
- `field_definition`;
- `action_definition`;
- `process_action_definition`;
- `contract_reference`;
- `capability_reference`;
- `refresh_policy`;
- `provenance_definition`.

Each object should have a stable `id`, a `kind`, and a `metadata_version`. Objects should reference one another by ID instead of nesting complete copies of other definitions. This keeps the document navigable and makes it possible to validate references independently.

## Route-by-route metadata responsibilities

### Trading RFQ

The RFQ page should render the list resource and a create form. The form should declare the RFQ contract and product-family selector. When a product family is selected, the UI should resolve product-specific terms from a product metadata reference rather than embedding FCN fields in the generic RFQ component.

The create action should return a durable RFQ identifier and a correlation identifier. The page should expose the route to quote as a next action, but the transition from RFQ to quote must remain an explicit process or action declaration.

### Trading quote

The quote page should declare a pricing process and separate the pricing result from quote persistence. A price result is not automatically a quote, and a persisted quote is not automatically a trade.

The page should expose:

- the selected RFQ and its pricing request reference;
- pricing status and engine marker;
- quote measures and sensitivities;
- evidence or diagnostics status;
- a persist-quote action;
- a trade-accept action subject to the declared transition.

### Trading trade

The trade page should render the trade record and lifecycle timeline as separate resources. Amend and cancel must declare state preconditions, input contracts, reason requirements, resulting events, and refresh targets.

The page should link to the instrument and position resources through identifiers, not by copying their data into the trade metadata.

### Trading instrument

The instrument page should describe the durable product instance created from the trading flow. It should declare its product-family contract and link to source RFQ, pricing request, trade, lifecycle, and model-registry references when available.

Instrument metadata should not be treated as a replacement for the semantic terms projection. It is a view and linkage contract.

### Trading positions

The positions page should declare whether positions come from `fina-trade` or from a separate OLAP or risk process. A position row should identify its aggregation grain and valuation timestamp. If it displays Greeks or P&L, the metadata must identify the source process, measure definition, and scenario scope.

### RiskCube scenarios

The scenario page should distinguish definition actions from execution actions. Create/update/delete operate on scenario definitions. Trigger executes a process and produces a batch report. These must not be represented as one generic form submit.

Scenario metadata should include the market-data manipulation contract, base market-data datetime, repository snapshot datetime, materialization mode, and applicable product or slice scope.

### RiskCube versions

The version page should declare whether versions are immutable runtime snapshots, logical configuration revisions, or both. The current adapter exposes `version_id`, `version_key`, `version_name`, `metadata`, and `created_at`; the UI contract should not infer immutability without backend confirmation.

### RiskCube slices

The slice page should render conditions as a structured predicate editor. A slice condition must declare its field, operator, value type, and whether the field is valid for the selected population. Free-form conditions are acceptable for a POC but should be constrained by a slice-field catalog before production use.

### RiskCube cubes

The cube page should declare dimensions, measures, aggregation functions, filters, pivot axes, and measure level-of-detail rules as metadata. The page may continue to generate read-only SQL, but the metadata should identify the allowed dimension and measure catalog and the query capability.

The cube result should include partition scope and provenance. `olap_query` must remain read-only, and the metadata should declare that constraint.

## Alignment with the refined FinA contracts

| FinA concern | UI metadata responsibility | UI metadata must not do |
|---|---|---|
| Product semantics | Reference the product family and terms contract. | Redefine payoff or term semantics in field labels. |
| Model wiring | Display selected model/backend and capability state. | Choose an engine by client-side convention. |
| ETL | Represent ETL/process status and result references. | Reimplement augment or compile logic in the browser. |
| Native pricing | Declare pricing process, request schema, and evidence expectations. | Treat arbitrary JSON as a production pricing request. |
| Lifecycle | Declare valid user actions and expected events. | Become the authority for transition legality. |
| RiskCube | Declare scenario/version/slice/cube resources and scopes. | Hide scenario and partition scope behind a generic table. |
| OLAP | Declare dimensions, measures, and read-only query capability. | Allow arbitrary write SQL or unbounded query input. |
| Evidence | Surface engine marker, process ID, request ID, and result status. | Claim production evidence from schema validation alone. |

## Recommended implementation order

### Phase 1: Introduce a metadata vocabulary without changing page behavior

Create a provisional `schema/ui-metadata.schema.json` and one document under `schema/examples/ui/tradeac-minimal.ui.json`. Model only the RFQ, quote, trade, scenario, and cube examples. Validate references, action targets, and contract identifiers.

At this stage, the existing page components can remain hand-written. The metadata is a checked inventory and a target contract.

### Phase 2: Make server actions contract-aware

Replace broad aliases with named contract references and typed envelopes at the server boundary. Keep MCP adapters behind the server actions. Add correlation and provenance fields to action results where the backend supports them.

### Phase 3: Drive navigation and resource tables

Move the trading and RiskCube sidebar definitions into metadata-backed navigation. Convert one read-only page first, preferably `/riskcube/versions` or `/trading/instruments`, because these pages have fewer mutations.

### Phase 4: Drive forms and lifecycle actions

Convert RFQ creation, trade amendment, scenario editing, and slice editing. Require action metadata to declare input contracts, state preconditions, refresh targets, and expected events.

### Phase 5: Drive process-backed pages

Convert quote pricing and scenario triggering only after the process and evidence references are available. This prevents the UI registry from becoming a second, weaker process engine.

## Open decisions for review

1. **Location:** Keep UI metadata under `fina-skills/schema/ui/` as canonical contracts and `fina-skills/refs/ui/` as explanatory references, or place the provisional schema directly under `refs/ui/` until the vocabulary stabilizes.
2. **Scope:** Decide whether this first metadata contract covers only the FinA trading/RiskCube pages or also the unrelated Alpaca, R&D, and dashboard routes in `tradeac`.
3. **Transport naming:** Decide whether metadata references MCP tool names directly or uses stable logical operations such as `rfq.create` and resolves them through an adapter registry.
4. **Schema ownership:** Decide whether `trade.rfq`, `trade.trade`, and related contracts should be authored in `fina-skills` or imported from the domain repositories and pinned by revision.
5. **Product selection:** Decide whether the product family is selected at RFQ creation or resolved from an instrument/product catalog before the RFQ form is rendered.
6. **Authorization:** Decide whether capabilities are declarative UI hints only or are also emitted by the backend as an authoritative capability set.
7. **Evidence visibility:** Decide which provenance fields are always visible, which are available in diagnostics, and which are only persisted in evidence manifests.

## Recommendation

Proceed with a small, schema-enforced metadata vocabulary for the ten FinA routes, but do not make the UI fully metadata-driven yet. First use metadata to inventory resources and actions, validate references, and expose the gaps between the POC adapters and the refined product/process/lifecycle contracts.

The strongest initial slice is:

```text
/trading/rfq
→ /trading/quote
→ /trading/trade
→ /riskcube/scenarios
→ /riskcube/cubes
```

This slice exercises source capture, pricing, lifecycle, scenario execution, OLAP, and evidence provenance. It will reveal whether the metadata vocabulary is expressive enough before it is applied to every page.

## References

[1]: https://github.com/haymant/tradeac "TradeAC application repository"
[2]: https://github.com/haymant/fina-skills "FinA agent skill book and contract repository"
[3]: https://github.com/haymant/fina-risk "FinA risk and native pricing repository"
[4]: https://github.com/haymant/fina-trade "FinA trade lifecycle repository"
