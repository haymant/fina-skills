---
name: finap-dev
description: Develop and maintain FinAP, the authenticated equity-derivatives application built from the TradeAC dashboard shell. Use for FinAP pages, schema-driven React rendering, flex-block workflows, trading and RiskCube flows, FinA MCP integration, lifecycle actions, and UI provenance.
---

# FinAP Development

## Mission

Build FinAP as a focused operator application for equity-derivative trading and risk. Preserve the TradeAC dashboard shell, authentication, theme system, accessible shadcn components, and server-side integration boundaries. Do not reintroduce unrelated TradeAC screens.

Read the relevant reference before changing a feature:

- `references/business-requirements.md` — product scope, required routes, and acceptance criteria.
- `references/ui-runtime-principles.md` — schema-driven React renderer, rich arrays, expandable objects, and flex-block workflows.
- `references/fin-a-boundaries.md` — product, model, process, lifecycle, evidence, and adapter boundaries.
- `../../schema/ui/ui-metadata.schema.json` — canonical shape for pages, layouts, workflows, flex blocks, renderer hints, actions, and resources.
- `../../schema/ui/examples/fcn-rfq.ui.json` — minimal UI metadata fixture; validate it independently before wiring a page.

## Repository rules

1. Keep route-owned code beside its route under `src/app/(main)/<group>/<page>/`.
2. Keep shared dashboard shell code under `src/app/(main)/_components/`, shared UI under `src/components/`, and shared runtime code under `src/lib/`.
3. Keep the sidebar limited to the FinAP Trading and RiskCube route families.
4. Keep authentication and authorization on the server boundary. Never handle session cookies in client components.
5. Keep MCP calls behind server actions or a typed adapter. Do not call MCP servers directly from browser code.
6. Use precise TypeScript types. Replace `Record<string, unknown>` at feature boundaries with named contract envelopes as contracts stabilize.
7. Keep JSON Schema, UI metadata, workflow metadata, and action metadata separate. Do not put rendering rules into product schemas.
8. Treat client validation as early feedback. Backend validation remains authoritative for lifecycle, authorization, product semantics, market data, and pricing.
9. Use React Hook Form for form state and AJV for JSON Schema validation when implementing the renderer runtime.
10. Preserve provenance for pricing and risk operations: request ID, process ID, schema version, scenario scope, engine marker, and evidence status.

## Required development loop

1. Read the applicable business requirement and FinA boundary reference.
2. Inspect the closest existing screen and shared component before coding.
3. Define or update the contract and metadata before adding product-specific UI logic.
4. Implement the smallest route-owned component that consumes the metadata.
5. Wire server actions through a logical operation or typed adapter.
6. Handle loading, empty, error, disabled, validation, and mobile states.
7. Validate UI metadata against `schema/ui/ui-metadata.schema.json`.
8. Run `pnpm check` and `pnpm build` before declaring the change complete.
9. Record new renderer patterns, process assumptions, or contract decisions in the appropriate reference.

## Renderer policy

Prefer a registered renderer over page-specific field branching. Support scalar fields, nested objects, rich arrays, schedules, read-only property grids, diagnostics, and flex blocks. Unknown renderer IDs must fail validation or show a visible fallback; never silently render an incompatible control.

## Workflow policy

Use flex blocks for semantic substructures such as underlying baskets, coupon schedules, protection, settlement, scenario manipulations, and review. A child flow edits a bound sub-object or array item and returns a validated value to its parent. The parent workflow owns final submission and action invocation.

## Action policy

Metadata describes user intent and invokes a registered logical operation. An action declares input schema, record binding, state preconditions, confirmation policy, process reference, refresh targets, expected events, and evidence requirements. The backend remains the authority for authorization and transition legality.
