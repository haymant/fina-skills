# FinAP Business Requirements

## Product purpose

FinAP is an authenticated operator workspace for an equity-derivative trading ecosystem. It provides a consistent dashboard shell for RFQ capture, pricing, trade lifecycle, instrument and position views, scenario definition, RiskCube execution, and OLAP exploration.

FinAP is not a general-purpose TradeAC dashboard. It retains the shared authenticated shell and visual language while removing unrelated Alpaca, R&D, CRM, productivity, and demonstration pages.

## Required routes

### Trading

- `/trading/rfq` — create and monitor RFQs.
- `/trading/quote` — price RFQs, inspect quote results, persist quotes, and accept trades.
- `/trading/trade` — inspect trades, lifecycle history, amend, and cancel where legal.
- `/trading/instruments` — inspect durable product instances and source references.
- `/trading/positions` — inspect positions with valuation time, aggregation grain, and risk provenance.

### RiskCube

- `/riskcube/scenarios` — define, edit, delete, and trigger market-data scenarios.
- `/riskcube/versions` — inspect version or snapshot metadata.
- `/riskcube/slice` — define and maintain structured population predicates.
- `/riskcube/cubes` — explore partition-scoped dimensions, measures, filters, pivots, and read-only OLAP results.

The dashboard landing route may redirect to `/trading/rfq`. Navigation exposes only these FinAP route families.

## Platform requirements

FinAP preserves authenticated access, server-side authorization, the TradeAC sidebar/header/account/theme/responsive layout, shadcn component style, server actions as the FinA MCP boundary, accessible states, and light/dark themes using existing design tokens.

## Schema-driven UI requirements

The application evolves toward a React runtime that consumes JSON Schema for data meaning and validation, UI metadata for labels/renderers/layouts, workflow metadata for flex blocks and navigation, and action metadata for logical operations, preconditions, refresh targets, events, and evidence. Product schemas must not contain React layout instructions.

## Financial workflow requirements

The first product workflow supports an FCN-like journey:

```text
Product identity → underlying basket → coupon and observation schedules
→ protection and knock-in → settlement → pricing configuration
→ review → quote pricing
```

These structures are independently renderable flex blocks. Repeated structures support list-detail editing, reorder, duplicate, remove, and validation.

## FCN protection feature coverage

The FCN protection flex block covers the barrier and knock-out feature set from the Murex playbook (Common_Features.md feature-by-feature mapping), driven from the `$defs/protection` and `$defs/settlement` blocks of `trade.rfq-create`:

- **Barrier families**: AKI, EKI, KO, and KIKO selection; global (basket indicator) or local (per-underlying level) scope. Local levels live on each underlying (`barrier`, `barrier_ko`); shared semantics live on the protection block.
- **Basket performance indicator**: worst-of, best-of, average, or k-th best (`performance_indicator`, `perf_rank`), plus the coupon accrual condition (`accrual_indicator`: all/any).
- **Observation style**: discrete vs continuous, configured independently for knock-in and knock-out (`ki_monitoring`, `ko_monitoring`), with comparison operators (`ki_operator`, `ko_operator`) and barrier type (`ko_type`: american/european).
- **Knock-out economics**: `ko_enabled`, `return_ratio`, `ko_coupon`, rebate payment timing (`rebate_payment_type`: at_knock/at_maturity), and legacy `barrier_rebate`/`smooth_barrier`.
- **Memory KO**: `memory_ko` per-name locks, mutually exclusive with a global knock-out.
- **Settlement and FX**: `$defs/settlement` carries delivery method, ITM payment, principal convention, and FX rule (basic/quanto; composite is rejected by the booking boundary), including quanto fixing fields.

Coupon-side features already covered by `trade.rfq-create`: memory coupon, pay-if-KI, autocall, observation cadence. Participation/cap/floor payoff features are RAKI-family and are out of scope for the FCN booking flow in this pass.

## FinA integration requirements

Pricing and risk actions preserve or expose request ID, process ID, input contract and schema version, scenario/version scope, native engine marker, evidence status, resulting lifecycle events, and refresh targets.

A price result is not automatically a persisted quote. A quote is not automatically a trade. Scenario definition is separate from execution. Cube exploration is read-only.

## Acceptance criteria

A feature is complete when its contract and metadata are named, server calls remain behind authenticated adapters, forms validate against declared contracts, arrays and objects use registered renderers, lifecycle/process actions declare events and refreshes, pricing/risk provenance is available, all relevant UI states are handled, and `pnpm check` plus `pnpm build` pass.
