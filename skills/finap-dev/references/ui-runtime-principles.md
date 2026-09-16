# FinAP UI Runtime Principles

## Renderer architecture

Use React Hook Form for form state and AJV for JSON Schema validation. Borrow JSON Forms ideas such as UI schemas, renderer testers, and ranked renderer registries, but keep the runtime under FinAP control so it can integrate lifecycle actions, process invocation, and provenance.

```text
JSON Schema + UI metadata + workflow metadata + action metadata
→ schema/runtime → renderer registry → React Hook Form → validation/action runtime
```

The core runtime must not know FCN payoff rules or RiskCube SQL. It resolves contracts and delegates product behavior to metadata and registered adapters.

## Rendering defaults

Scalar fields use registered text, number, date, datetime, currency, percentage, enum, boolean, identifier, and read-only renderers. Display formatting must not change canonical payload units.

Non-primary nested objects render as expandable cards with useful summaries. Support inline object, expandable card, detail panel, property grid, diagnostics panel, wizard block, and read-only JSON modes. Collapsing a card must not reset state.

Arrays support simple list, rich list, editable table, list-detail, timeline, schedule grid, pill list, key-value list, and risk-measure list renderers. A rich list declares title, subtitle, status, summary fields, and add/duplicate/remove/reorder actions with stable item keys.

Use schedule-grid or timeline renderers for coupon, observation, fixing, payment, settlement, and lifecycle event arrays.

## Flex blocks

A flex block is a reusable semantic substructure, not merely a visual container. Typical blocks include product identity, underlying basket, coupon schedule, observation schedule, protection and knock-in, settlement, pricing configuration, scenario manipulation, and review.

A workflow declares its root schema and ordered steps. A repeatable block can open a list-detail child flow for each array item.

```yaml
id: fcn.underlying-basket
kind: flex-block
schema: fcn.underlying-basket
collection:
  path: /underlyings
  item_schema: fcn.underlying
navigation:
  mode: list-detail
```

## Parent-child state

A child flow edits a bound sub-object or array item and returns a validated value to the parent. Back preserves the parent draft; cancel leaves the parent unchanged; completion validates before merging.

```ts
interface ChildFlowState {
  blockId: string;
  parentPath: string;
  itemKey?: string;
  currentStep: string;
  value: unknown;
  status: "draft" | "complete" | "cancelled";
}
```

Support partial validation for the current step and full validation before submission. Review must show unresolved errors by block and link directly to their steps.

## Action runtime

A submit does not call an arbitrary MCP tool. The runtime validates the canonical payload, resolves a registered logical operation, attaches record and process context, invokes the authenticated server action, interprets success/rejection/warning/event/evidence fields, and refreshes declared resources.

Action states include `idle`, `validating`, `submitting`, `accepted`, `rejected`, `awaiting_confirmation`, and `completed_with_warnings`.

## Separation and renderer registry

Product schemas define meaning. UI metadata defines presentation. Workflow metadata defines navigation. Action metadata defines intent and execution. Do not merge them into a page-specific mega-schema.

Every renderer ID has a schema tester and component. Unknown renderers produce a visible diagnostic fallback or fail metadata validation. Renderers support read-only, disabled, validation, keyboard, and responsive modes.
