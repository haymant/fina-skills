---
name: fina-risk
description: FinA equity-derivative pricing, sensitivities, P&L, model DSLs, conformance corpora, and plural execution backends. Use for pricing kernels, Greeks, lifecycle valuation, or risk-engine parity.
---

# FinA Risk

Use for pricing and risk computation. Preserve backend plurality: terminal parity, daily batch, hybrid AAD, and future kernels can coexist behind shared semantics.

## One spec, two proving backends

Define product-family lifecycle functions once in a closed, versioned DSL. Maintain a reference interpreter/oracle in the shared semantic layer and a compiled vectorized kernel in `fina-risk`. Keep them equal with a conformance corpus; do not make the JSON reducer the production hot path.

A kernel should represent state as small integer vectors, guards as predicated compares, schedules as static masks, operations as vector ops, and leg liveness as branchless selection where practical.

## Workflow

1. Start from typed `PricingRequest` plus a `LifecycleState` snapshot.
2. Identify observation, market-data, calendar, and corporate-action dependencies.
3. Run the oracle on deterministic fixtures.
4. Run the target backend and compare PV, cashflows, state transitions, and Greeks within declared tolerances.
5. Record method/backend/model version and market snapshot in provenance.
6. Never replace a failed real pricing call with mocked output in an E2E pass.

## Risk outputs

Keep PV, currency, price, full sensitivity vector, P&L attribution, checksums, method, and provenance distinct. Consumers may choose different lanes; reconciliation comes from shared meaning and inputs, not identical engines.

## Canonical schemas

Use [`schema/pricing-request.schema.json`](../../schema/pricing-request.schema.json) for engine inputs; use [`schema/risk-cell.schema.json`](../../schema/risk-cell.schema.json), [`schema/pnl-explain.schema.json`](../../schema/pnl-explain.schema.json), and [`schema/job-status.schema.json`](../../schema/job-status.schema.json) for reviewed output contracts.
