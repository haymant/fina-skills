---
name: fina-product-development
description: FinA product-family delivery workflow and model-wiring governance. Use when turning a term sheet into a supported product, adding a payoff family, choosing pricing/risk backends, defining lifecycle and operational gates, or preparing release evidence.
---

# FinA Product Development

Use this skill to take an equity-derivative product from **term sheet to controlled, evidence-backed delivery**. It complements `fina-core` (shared meaning), `fina-risk` (pricing), `fina-trade` (lifecycle), `fina-core-scheduler` (orchestration), and `fina-e2e-coordinator` (wired proof).

## Product-family workflow

1. **Classify the product.** Identify payoff family, basket indicator, barrier/observation style, accrual and memory features, FX rule, settlement, tenor, calendars, and unsupported constraints.
2. **Write the product specification.** Define every payoff branch, date/fixing schedule, comparison operator, rounding rule, market-data dependency, lifecycle operation, cashflow, and required sensitivity.
3. **Choose reuse before building.** Map the product to existing feature semantics, schemas, model registry entries, lifecycle reducers, and native/reference engines. Record each new field or algorithm that cannot be reused.
4. **Project the terms.** Convert the source into versioned `ProductTerms` and then a typed `PricingRequest`; preserve source identity and provenance. Do not make a pricing kernel consume an unversioned legacy document directly.
5. **Register the wiring.** Add or update a `model-registry/*.yaml` entry connecting product family, terms/request versions, lifecycle, market-data dependencies, pricing backends, risk profiles, and evidence requirements. Read [`references/model-wiring-contract.md`](references/model-wiring-contract.md).
6. **Implement the owning chapters.** Update `fina-core` for shared semantics, `fina-risk` for model/backends, `fina-trade` for durable state/events, and scheduler/ETL/OLAP chapters only where their contracts change.
7. **Build conformance fixtures.** Cover ordinary, boundary, lifecycle, and invalid cases. Compare the reference/oracle path with every claimed production backend using declared tolerances and method labels.
8. **Run the wired E2E.** Use real adapters and the smallest complete journey: quote → register → amend/fixing → event-triggered reprice → OLAP. Assert durable state, event delivery, backend identity, provenance, and derived output.
9. **Pass delivery gates.** Do not call a product ready until specification, schema, pricing, lifecycle, risk, operations, performance, and rollback evidence are recorded.

## Required product specification

Use [`references/product-family-template.md`](references/product-family-template.md) as the starting structure. A complete product family must document:

- product economics and supported variants;
- canonical terms and pricing-request projections;
- feature-to-field and feature-to-payoff mapping;
- schedules, calendars, fixing conventions, and boundary operators;
- market snapshot requirements and version anchors;
- pricing model, backend, engine marker, and fallback policy;
- risk profiles and units for each sensitivity;
- lifecycle state transitions, events, fixing/knock/expiry/exercise operations;
- settlement, cashflow, rounding, and operational procedures;
- constraints, negative cases, conformance fixtures, tolerances, and performance limits.

## Model-wiring rules

- Keep **pricing model**, **execution backend**, **risk profile**, and **evidence profile** as separate axes.
- Name the actual implementation, not only a logical handler. For native C++, record module, function, source revision, binary/build identity, and the required engine marker.
- Permit a reference backend only for oracle/conformance or explicitly labeled fallback use. Never silently turn a failed native E2E into a reference pass.
- Treat calendars, observation grids, fixing sources, volatility surfaces, correlations, and discount/dividend/FX inputs as versioned dependencies.
- Keep backend plurality behind shared semantics: native C++, Python/reference, AAD, pathwise, and finite-difference lanes may coexist but must consume compatible contracts.
- Record method provenance for every material risk output, including fallback reason and whether the result is suitable for production, validation, or demonstration only.

## Delivery gates

| Gate | Evidence required |
|---|---|
| Design | Product specification, reuse/build decision, constraints |
| Semantic | Versioned terms/request schemas and valid/invalid fixtures |
| Pricing | Oracle/native comparison, payoff branches, market snapshot provenance |
| Lifecycle | State transitions, event payloads, fixing/knock/expiry/exercise replay |
| Risk | Sensitivity profile, units, bump/method conventions, tolerances |
| Operations | Booking, fixing, settlement, incident and rollback procedures |
| Performance | Quote and batch measurements under production-like configuration |
| Release | Source revisions, model registry version, binary identity, evidence manifest |

## Routing

- Shared fields, terms, events, or schemas → `fina-core`.
- Pricing, Greeks, payoff graph, model/backend, or parity → `fina-risk`.
- Trade state, amendments, fixing, market operations, or event history → `fina-trade`.
- Processes, dependencies, subscriptions, or adapters → `fina-core-scheduler`.
- Street projection or legacy conversion → `fina-etl`.
- Materialization, query, reports, or provenance views → `fina-olap`.
- Any cross-repository proof → `fina-e2e-coordinator`.

## Resource navigation

- Read [`references/product-family-template.md`](references/product-family-template.md) when creating or reviewing a product specification.
- Read [`references/model-wiring-contract.md`](references/model-wiring-contract.md) when adding a registry entry or selecting a backend/profile.
- Inspect [`model-registry/README.md`](../../model-registry/README.md) and the closest product YAML before changing model wiring.
