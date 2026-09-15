# FinA Product-Family Specification Template

Copy this structure when introducing or reviewing a product family. Replace bracketed values; do not leave implementation-critical conventions implicit.

## 1. Identity and scope

- Product family:
- Version:
- Source term-sheet/reference:
- Owner:
- Supported variants:
- Explicit non-goals:

## 2. Economics

- Underlyings and basket indicator: single, worst-of, best-of, average, ranked, all/any.
- Principal and settlement: nominal/quantity; cash/delivery.
- Currency and FX rule: basic, quanto, composite, supported/rejected.
- Payoff formula for every branch: ordinary, KI, KO, memory, maturity, exercise, unwind.
- Rounding and denomination convention:

## 3. Feature map

| Feature | Terms field(s) | Pricing input | Lifecycle state | Event/operation | Risk output |
|---|---|---|---|---|---|
| [feature] | [path] | [field] | [state] | [event] | [greek/cashflow] |

Cover barriers, observation style, accrual, memory, participation/cap/floor, settlement, FX, and corporate actions where relevant.

## 4. Schedules and market data

- Evaluation and effective dates:
- Fixing/observation schedule:
- Period and payment schedule:
- Calendar and shifters:
- Boundary operators (`>=`, `>`, `<=`, `<`):
- Spot/reference fixing source:
- Volatility surfaces and interpolation:
- Discount/dividend/FX curves:
- Equity-equity and equity-FX correlations:
- Market snapshot/version anchors:

## 5. Canonical projections

- `ProductTerms` schema/version:
- `PricingRequest` schema/version:
- Legacy/source emitter and reverse parser:
- Preserved source/provenance fields:
- Invalid-input and constraint behavior:

## 6. Model wiring

- Registry entry:
- Logical handler:
- Reference/oracle backend:
- Native/production backend:
- Module and function:
- Engine marker:
- Build/source revision:
- Fallback policy:
- Path count, seed, timestep/grid policy:
- Cashflow and state representation:

## 7. Risk profiles

| Profile | Measures | Method | Units | Bump/market shift | Tolerance |
|---|---|---|---|---|---|
| quote | PV | [method] | [unit] | [shift] | [tol] |
| full-trading | PV, Delta, Gamma, ... | [method] | [unit] | [shift] | [tol] |

Distinguish pricing output from runtime-selected sensitivity profiles. Record sticky-strike/sticky-delta, relative/absolute, FX conversion, and notional scaling conventions.

## 8. Lifecycle and operations

| Transition/operation | Preconditions | State mutation | Event | Cashflows | Reprice? |
|---|---|---|---|---|---|
| register/fix/knock/expire/exercise/amend | [condition] | [state] | [topic] | [flows] | yes/no |

Define idempotency, replay, correction, missing-fixing, and late-data behavior.

## 9. Validation corpus

- Ordinary fixtures:
- Boundary fixtures:
- KI/KO and memory fixtures:
- Schedule/calendar fixtures:
- Settlement/FX fixtures:
- Invalid/constraint fixtures:
- Oracle/native tolerances:
- External benchmark:
- Performance/SLA test:
- Full real-adapter E2E command:

## 10. Release evidence

Record source revisions, schema/model-registry versions, native binary/build identity, market snapshot, calendar, seed/path configuration, results, tolerances, failed checks, and rollback procedure.
