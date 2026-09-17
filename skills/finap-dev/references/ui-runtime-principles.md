# FinAP UI Runtime Principles

## Recommendation

FinAP should provide a reusable **metadata-driven form and page runtime**, not a generic JSON Schema-to-HTML wrapper.

```text
FinA JSON Schema
        +
UI metadata
        +
process/action metadata
        ↓
React UI runtime
        ↓
React Hook Form + AJV + custom renderers
```

Use **React Hook Form** for form state, field registration, dirty tracking, and submission; **AJV** for JSON Schema validation; JSON Forms concepts for renderer selection and schema-driven layout; a custom renderer registry for financial-domain components; and a dedicated navigation/state machine for Murex-style flex blocks and wizard steps.

JSON Forms should not be the entire runtime. Its ideas are valuable, but FinAP needs stronger control over lifecycle actions, process invocation, native pricing evidence, rich arrays, nested expandable objects, record context, conditional product blocks, wizard navigation, partial-save semantics, and read-only and diagnostic views. A thin internal runtime preserves this control while borrowing proven schema-driven patterns.

## Proposed package structure

The library could eventually become a separate package or repository:

```text
fina-ui/
├── packages/
│   ├── schema-runtime/
│   ├── react-renderer/
│   ├── financial-controls/
│   ├── workflow-runtime/
│   ├── adapters-tradeac/
│   └── theme/
└── examples/
    └── fcn-rfq/
```

Initially, it may live inside an application while contracts stabilize:

```text
tac-app/src/lib/fina-ui/
├── schema-runtime.ts
├── renderer-registry.tsx
├── form-runtime.tsx
├── workflow-runtime.ts
├── action-runtime.ts
├── provenance-panel.tsx
└── renderers/
```

Start in `fina-skills` with the contracts and a small reference implementation. Extract a reusable runtime only after the metadata shape has been exercised by the FCN and RiskCube reference flows.

## Runtime layers

### Schema runtime

The schema runtime is framework-independent. It loads JSON Schema, resolves `$ref`, validates data with AJV, calculates required fields, resolves conditional branches, exposes property metadata to renderers, and reports errors using JSON Pointer paths.

```ts
interface SchemaRuntime {
  resolve(schemaRef: string): JsonSchema;
  validate(schemaRef: string, value: unknown): ValidationResult;
  describe(path: string): PropertyDescriptor | undefined;
}
```

It must not know about React, product payoff logic, or RiskCube SQL.

### UI metadata runtime

The UI metadata runtime resolves field labels and descriptions, selects layouts, determines renderer hints, evaluates visibility and enablement rules, attaches logical actions, and exposes presentation metadata.

```ts
interface UiMetadataRuntime {
  page(pageId: string): PageDefinition;
  resource(resourceId: string): ResourceDefinition;
  action(actionId: string): ActionDefinition;
  layout(layoutId: string): LayoutDefinition;
}
```

### React renderer runtime

The React runtime renders fields and layouts, connects them to React Hook Form, displays validation errors, renders nested objects and arrays, and supports read-only, editable, and diagnostic modes.

```tsx
<SchemaForm
  schema="trade.rfq-create"
  ui="trading.rfq.create"
  value={draft}
  onChange={setDraft}
/>
```

Prefer registered renderers over page-specific field branching. Unknown renderer IDs must fail metadata validation or show a visible diagnostic fallback; they must never silently produce an incompatible generic control.

### Action runtime

The action runtime evaluates preconditions, constructs registered MCP/server-action arguments, validates input, invokes the declared adapter operation, handles result and error envelopes, refreshes declared resources, and exposes correlation and provenance information.

```tsx
<ActionButton
  action="quote.price"
  context={{ rfq: selectedRfq }}
/>
```

Metadata must reference registered logical operations. The action runtime must not permit arbitrary client-defined backend calls.

### Workflow runtime

The workflow runtime manages wizard steps, preserves parent and child state, supports nested flex blocks, validates each block, allows return to parent context, supports draft/save/resume, and produces one final canonical payload.

```tsx
<FlexWorkflow
  workflow="fcn.rfq"
  initialValue={draft}
  onSubmit={createRfq}
/>
```

## Murex-style flex blocks

A **flex block** is a reusable semantic substructure, not merely a visual card. It is appropriate for structured derivatives and RiskCube operations.

An FCN RFQ may be composed as:

```text
FCN RFQ
├── Product Identity
├── Underlying Basket
│   ├── Underlying 1
│   ├── Underlying 2
│   └── Underlying 3
├── Coupon Schedule
├── Observation Schedule
├── Protection and Knock-In
├── Settlement
├── Pricing Configuration
└── Review and Submit
```

The parent workflow should only need to know each block’s identity, schema, completion state, navigation target, dependency rules, repeatability, and editability in the current lifecycle state. It should not need to know every field within every block.

### Workflow metadata

```yaml
id: fcn.rfq
kind: workflow
title: FCN RFQ
schema: trade.rfq-create
steps:
  - id: identity
    title: Product identity
    block: fcn.product-identity
    required: true

  - id: underlyings
    title: Underlyings
    block: fcn.underlying-basket
    repeatable: true
    required: true
    navigation:
      mode: subflow

  - id: coupon
    title: Coupon schedule
    block: fcn.coupon-schedule
    required: true

  - id: protection
    title: Protection
    block: fcn.protection
    required: true

  - id: settlement
    title: Settlement
    block: fcn.settlement
    required: true

  - id: pricing
    title: Pricing
    block: fcn.pricing-configuration
    required: true
    visible_when:
      path: /product_type
      in: [FCN, ELI_FCN]

  - id: review
    title: Review
    block: shared.review-submit
    required: true
```

A repeatable block can open a nested list-detail subflow:

```yaml
id: fcn.underlying-basket
kind: flex-block
schema: fcn.underlying-basket
collection:
  path: /underlyings
  item_schema: fcn.underlying
navigation:
  mode: list-detail
  list_title: Underlyings
  item_title: Underlying
actions:
  - add
  - duplicate
  - remove
  - reorder
```

The user can navigate from the parent workflow into `AAPL`, `NVDA`, or a new underlying and then return to the parent. The parent draft remains intact while the child block is edited.

## Rendering conventions

### Arrays

Arrays should not default to a plain repeated form. Their presentation is selected declaratively:

```yaml
type: array
items:
  $ref: "#/$defs/underlying"
ui:
  renderer: rich-list
  item_title: "$.symbol"
  item_subtitle: "$.role"
  item_status: "$.status"
  summary:
    - path: $.symbol
    - path: $.weight
    - path: $.barrier
  actions:
    - add
    - duplicate
    - remove
    - reorder
```

Supported array renderers include `simple-list`, `rich-list`, `editable-table`, `list-detail`, `timeline`, `schedule-grid`, `pill-list`, `key-value-list`, and `risk-measure-list`.

For example, an FCN underlying basket can present:

```text
AAPL      Primary     50%     Barrier 70%     Active
NVDA      Secondary   50%     Barrier 65%     Active
```

The summary must be declarative so every product page does not manually reconstruct the same card. Array items require stable semantic keys, not array indexes, wherever the item can be reordered.

### Nested objects

Nested objects outside the current primary step should default to an expandable card with a useful summary:

```yaml
type: object
properties:
  payment:
    $ref: "#/$defs/payment"
    ui:
      renderer: expandable-card
      title: Payment
      summary:
        - path: $.payment_date
        - path: $.currency
        - path: $.amount
```

Recommended object renderers are `inline-object`, `expandable-card`, `detail-panel`, `property-grid`, `diagnostic-panel`, `wizard-block`, and `read-only-json`. A collapsed object must not become an opaque “advanced settings” box, and collapsing it must not reset state.

### Schedules

Schedules deserve specialized renderers rather than generic arrays:

```yaml
ui:
  renderer: schedule-grid
  columns:
    - date
    - observation_type
    - coupon
    - fixing
    - payment
```

Use schedule-grid or timeline renderers for coupon schedules, observation dates, fixing records, settlement dates, and lifecycle event timelines.

### Financial quantities

Display metadata must not change the underlying canonical value:

```yaml
currency:
  type: string
  ui:
    renderer: currency-code

notional:
  type: number
  ui:
    renderer: money-input
    currency_path: /currency
    scale: 2

coupon_rate:
  type: number
  ui:
    renderer: percentage-input
    unit: decimal
    display_scale: 2
```

The payload remains schema-compatible. Formatting must never silently change decimal-versus-percentage semantics.

### Barrier and option enums

Barrier and observation-style enums must render as plain selected options from the schema `enum` — never scripted conditional branching:

```yaml
ki_operator:
  type: string
  enum: ["<", "<="]
  ui:
    renderer: select

ki_monitoring:
  type: string
  enum: ["discrete", "continuous"]
  ui:
    renderer: select
```

Engineering values such as `>`, `>=`, `<`, `<=` are valid select options; the option label must equal the canonical value so the payload round-trips exactly. Products that mix semantics on one screen (e.g. KIKO: barrier family, performance indicator, global/local scope, KO economics) belong in one shared protection flex block plus per-underlying barrier levels on the underlying item, rather than a single unbounded form.

## Separate product schema from UI layout

This separation is critical. Product schemas define meaning and validation:

```json
{
  "type": "object",
  "properties": {
    "coupon_rate": {
      "type": "number",
      "minimum": 0
    }
  },
  "required": ["coupon_rate"]
}
```

UI metadata defines presentation:

```yaml
schema: fcn.terms-projection
path: /coupon_rate
ui:
  renderer: percentage-input
  label: Coupon rate
  help: Annualized coupon expressed as a decimal.
  group: coupon
```

Workflow metadata defines navigation:

```yaml
workflow: fcn.rfq
step: coupon
paths:
  - /coupon_rate
  - /coupon_frequency
  - /coupon_observation_dates
```

Action metadata defines execution:

```yaml
action: quote.price
process: fcn-termsheet-quote
input_schema: pricing-request
```

These must not be merged into one enormous page-specific schema.

## Recommended metadata model

### Layout definitions

```yaml
id: fcn.coupon-layout
kind: layout
layout: section
title: Coupon
children:
  - kind: field
    path: /coupon_rate
  - kind: field
    path: /coupon_frequency
  - kind: field
    path: /coupon_observation_dates
```

Layouts control composition without changing the domain schema.

### Renderer hints

```yaml
id: fcn.coupon-rate
kind: field-ui
schema_path: /coupon_rate
renderer: percentage-input
format:
  unit: decimal
  display_scale: 2
```

Renderer hints must be validated against a registry. Unknown renderers should fail validation or fall back visibly rather than silently producing a poor generic control.

### Workflow definitions

```yaml
id: fcn.rfq
kind: workflow
root_schema: trade.rfq-create
steps:
  - id: identity
    layout: fcn.identity-layout
  - id: underlyings
    layout: fcn.underlyings-layout
    navigation: subflow
  - id: terms
    layout: fcn.terms-layout
  - id: review
    layout: shared.review-layout
```

One schema should support multiple workflows, including FCN RFQ, FCN amendment, FCN fixing, and FCN operations. Fields may overlap while visibility, editability, ordering, and lifecycle rules differ.

## React Hook Form, JSON Forms, and AJV

### React Hook Form

React Hook Form is the underlying form state engine because it supports high-performance large forms, dynamic arrays, nested field paths, partial drafts, controlled submission, custom financial controls, and wizard state.

### JSON Forms concepts

Borrow JSON Forms ideas for JSON Schema-driven field selection, UI schemas, renderer tester/ranking, custom renderer registries, layouts, and categorization. Do not adopt JSON Forms as the entire application runtime.

### AJV

Use AJV as the canonical client-side validator and early feedback mechanism. The backend remains authoritative for lifecycle legality, authorization, process input validation, product semantics, market-data availability, and pricing-engine compatibility.

## Flex-block state model

Nested workflows need explicit state:

```ts
interface WorkflowState<T> {
  workflowId: string;
  currentStep: string;
  value: T;
  completedSteps: string[];
  dirtySteps: string[];
  errors: Record<string, ValidationError[]>;
  childFlows: Record<string, ChildFlowState>;
  status: "draft" | "ready" | "submitting" | "submitted" | "failed";
}

interface ChildFlowState {
  blockId: string;
  parentPath: string;
  itemKey?: string;
  currentStep: string;
  value: unknown;
  status: "draft" | "complete" | "cancelled";
}
```

Example binding:

```text
parentPath: /underlyings
itemKey: AAPL
blockId: fcn.underlying
```

When a child flow completes, it returns a validated object to the parent array. When cancelled, the parent remains unchanged. This is safer than allowing every nested component to mutate the entire form state directly.

Support partial validation for the current step and full validation before submission. Review must show unresolved errors by block and link directly to their steps.

## Action and lifecycle integration

A flex-block wizard must not submit directly to an MCP tool. The sequence is:

```text
User edits blocks
→ client-side AJV validation
→ canonical payload assembly
→ server action validation
→ process invocation
→ backend lifecycle validation
→ MCP execution
→ event/evidence result
→ UI refresh
```

For an FCN RFQ:

```text
FCN RFQ wizard
→ trade.rfq-create
→ rfq.create
→ fcn-termsheet-quote process
→ pricing request
→ native quote result
→ quote persistence
```

The UI action runtime should expose `idle`, `validating`, `submitting`, `accepted`, `rejected`, `awaiting_confirmation`, and `completed_with_warnings` states.

A price result is not automatically a persisted quote, and a quote is not automatically a trade. Logical operations, process references, lifecycle preconditions, refresh targets, expected events, and evidence requirements must be explicit in action metadata.

## Provenance

Pricing and risk actions must render execution provenance alongside results:

```text
Request ID: ...
Process: fcn-termsheet-quote
Engine: cpp_daily_termsheet_eki
Evidence: verified
```

At minimum, preserve request ID, process ID, input contract and schema version, scenario/version scope, native engine marker, evidence status, resulting lifecycle events, and refresh targets. This provenance is a primary reason to build a FinA-specific runtime rather than use a generic form library.

## Suggested implementation phases

### Phase 1: renderer foundation

Implement JSON Schema resolution, AJV validation, a React Hook Form adapter, scalar renderers, nested-object rendering, rich arrays, expandable cards, read-only property grids, a renderer registry, and basic layout metadata.

### Phase 2: flex blocks

Implement step navigation, parent-child workflows, repeatable blocks, list-detail arrays, partial validation, draft state, back navigation, and a review page.

### Phase 3: action runtime

Implement a logical action registry, input construction, authenticated server-action invocation, refresh targets, success/error envelopes, lifecycle and process references, and provenance display.

### Phase 4: FCN reference flow

Use the FCN example as the first reference:

```text
FCN RFQ
→ product identity
→ underlying basket
→ terms
→ pricing configuration
→ review
→ quote.price
```

Then add trade amendment with lifecycle-aware flex blocks, an amend action, and event/evidence refresh.

### Phase 5: RiskCube reference flow

Use the same runtime for:

```text
Scenario definition
→ manipulation blocks
→ version selection
→ slice selection
→ scenario trigger
→ cube exploration
```

The same renderer must support both product-terms workflows and RiskCube operation workflows without embedding either domain in the core library.

## Architectural rules

1. **JSON Schema defines data meaning and validation.**
2. **UI metadata defines presentation and renderer selection.**
3. **Workflow metadata defines flex blocks and navigation.**
4. **Action metadata defines user intent and process invocation.**
5. **Backend contracts remain authoritative.**
6. **Product-specific behavior belongs in product metadata, not generic renderers.**
7. **Every pricing or risk action carries process and evidence references.**
8. **The first implementation should target the FCN RFQ/quote flow and one RiskCube scenario flow, not dynamically generate every TradeAC page.**

The target is a **schema-validated React runtime for FinA contracts, layouts, flex-block workflows, lifecycle actions, and execution provenance**.


## FCN economics and generated leg allocation

FCN should add an **Economics and Payoff Composition** step after protection and before settlement or pricing. Use semantic flex blocks for Funding, Coupon, Terminal Optionality, and Generated Leg Preview. The canonical leg contract is `schema/ui/leg-allocation.schema.json`.

The first three blocks bind to editable product terms. The preview binds to compiler and pricing results. Do not expose PV, Greeks, `N1`, `N2`, engine markers, payoff graph node IDs, or evidence status as editable controls. Use a rich read-only list or property grid for generated legs, with source term paths, lifecycle conditions, payment schedule, origin, PV, currency, and evidence status.

Use `PUT / Terminal Optionality` as the display label when a RakiPlus-derived FCN has a conditional terminal residual. Do not claim it is a standalone vanilla put unless the product contract proves that interpretation.

The data flow is:

```text
editable terms → ETL projection and compile → payoff graph and leg allocation
               → pricing request → native quote/reprice → PVs and evidence
```

## Operation-action metadata

Use the canonical `schema/ui/operation-action.schema.json` for actions. Action metadata must identify a registered logical operation, input and result schemas, process, record binding, confirmation policy, lifecycle preconditions, actor capability, idempotency binding where needed, refresh targets, expected events, and evidence requirements.

Action metadata describes intent. It never authorizes a lifecycle transition. The authenticated server action must enforce actor capability, state legality, reason requirements, idempotency, and adapter routing. Keep `quote.price`, `quote.reprice`, quote persistence, trade acceptance, amendment, cancellation, knock, and expiry as distinct operations.

The action runtime should perform this sequence:

```text
resolve metadata → validate input → evaluate visible preconditions
→ invoke authenticated server adapter → normalize result envelope
→ publish event/provenance → refresh declared resources
```

The browser must not choose MCP tools, pricing engines, repositories, or credentials. A price result is not a persisted quote, and a quote is not a trade.
