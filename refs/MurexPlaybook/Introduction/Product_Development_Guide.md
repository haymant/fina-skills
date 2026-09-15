# Systematic Guide to Developing New Structured Equity Products in Murex

This document is the program-level guide for taking a new structured equity product from concept to production on Murex. It complements **Flex_Development.md** (the tactical, configuration/code walkthrough) with a structured delivery framework: roles, phases, workstreams, entry/exit criteria, and governance. Use it as a roadmap; use the product-specific pages of this Playbook as the reference for each family's constraints and conventions.

## 1. Roles & Responsibilities

| Role | Responsibilities |
| :--- | :--- |
| **Structuring / Product Manager** | Owns the term sheet, the product economics, and the client use case. Signs off the spec. |
| **Quant** | Owns the payoff mathematics, pricing model choice, Greeks methodology, benchmark validation. |
| **Equity Derivatives Developer (Murex)** | Flex UI, C++ mapping, model integration, payoff script/GMP wiring, testing, deployment. |
| **Market Data / FO Config** | Underlying setup, dummy baskets, vol surfaces, dividend curves, FX, correlations, calendars. |
| **Operations / MO** | Fixing procedures, market operations (knock, expiry, exercise), settlement flows, confirmation. |
| **Risk / Middle Office** | Sensitivity configuration groups, trading matrices, batch reports, limits, P&L explain coverage. |
| **BA / Project Manager** | Coordinates UAT, training, environment promotion, sign-offs, rollout and hypercare. |

A single "Murex developer" often covers the developer + config rows; the important point is that **all rows must have an owner and sign-off**, or the product ships with operational gaps.

## 2. Delivery Phases & Gate Criteria

### Phase A — Design & Feasibility

**Activities**
1. Convert term sheet → product spec (see Common_Features.md for the vocabulary).
2. Classify the product along the standard dimensions:
   - Payoff family (range accrual / barrier / accumulator / digital / dispersion / outperformance / ...)
   - Barrier style & observation (KI/KO, single/double, daily/periodic/continuous)
   - Basket vs single underlying, basket size, worst/best/nth/average performance
   - FX rule (Basic / Quanto / Composite), settlement (cash/delivery), principal (nominal/quantity)
   - Memory / coupon-barrier / cliquet features
3. Assess **reuse**: which existing flex blocks, headers, model groups, GMPs, and market-data items can be reused. Reuse is almost always cheaper and lower-risk than new builds.
4. Confirm constraints against supported ranges (tenor, basket size, FX rules, principal type) and record the ones that need custom validation.

**Exit criteria**
- Product spec signed off; reuse vs build decision made; constraint list complete; high-level delivery plan dated.

### Phase B — Configuration Development (Flex UI, Payoff, GMP)

**Activities**
1. Build/reuse flex blocks & header (dynamic UI, operators, model-output columns).
2. Configure payoff script + model group + GMP.
3. Prepare dummy baskets and market-data placeholders.
4. Draft booking conventions (denomination, reference price entry, fixing procedure).

**Exit criteria**
- Screens render correctly in DEV; sample deals can be booked; basic pricing runs without errors.

### Phase C — C++ & Model Development

**Activities**
1. Extend mapping structs; exact field-name match; unit tests.
2. Implement payoff logic in the model (or extend an existing engine).
3. Wire market data consumption (vol, divs, FX, correlation).
4. Implement/verify lifecycle cash-flow generation (periodic, KO, KI, maturity, early termination flows).

**Exit criteria**
- Code builds; mapping tests green; sample deals price sensibly book-to-model.

### Phase D — Validation & Testing

**Activities**
1. Fixed-point regression suite (premium + greeks) added to the running set.
2. External benchmark reconciliation (in-house quant library, Numerix/Fincad/Bloomberg, etc.).
3. MXtest functional coverage: all scenarios, all lifecycle events, all boundary operators.
4. Performance: interactive quote time and EOD batch time within SLA; sensitivity groups sized correctly.
5. Risk coverage: trading matrices, LiveBook/RTPM viewers, P&L explain buckets.

**Exit criteria**
- Fixed-points green; benchmark within tolerance; lifecycle flows match spec; performance SLAs met.

### Phase E — UAT, Training, Rollout

**Activities**
1. UAT on UAT environment with realistic market data; traders, structurers, ops walk real workflows.
2. Update product playbooks, booking/fixing/ops guides (this repository).
3. Controlled configuration promotion (DEV → UAT → PROD) with the C++ build version recorded.
4. Pilot group of trades; hypercare monitoring; documented rollback path.

**Exit criteria**
- UAT sign-off; training delivered; rollout complete with no open Sev-1/2 issues; rollback plan on file.

## 3. Reusable Pattern Library

These patterns recur across the products in this Playbook. Reusing them reduces development time and operational variance.

### 3.1 Booking Patterns
- **Dummy basket booking:** book against `FLEX_USD` / market basket; constituents and reference prices live in `KIKOSTRUCT` / `KIKOSELECT`. (Used by: DBrW, RakiPlus, MemRakiPlus, Double No-Touch RA, Dispersion.)
- **Basket-of-1 for single underlying:** products that forbid a bare equity instrument still support single names as a 1-element basket.
- **Denomination-driven rounding:** `CashFlow = Round(Denom × PayRate, 2) × Notional/Denom`. (RakiPlus, MemRakiPlus, Double No-Touch RA, Dispersion.)

### 3.2 Block Reuse Families

| Block family | Purpose | Used by |
| :--- | :--- | :--- |
| `KIKOSTRUCT` / `KIKOSELECT` / `KIKOSEL*` | Basket definition, feature toggles (LKO/GKO/KI), return ratio, initial fixing, denomination, quanto FX | Raki, MemRaki, RakiPlus, MemRakiPlus, Reverse KIKO, Double No-Touch RA, Dispersion |
| `RGACCDATE` / `FIXINGDATE` | Daily fixing / observation date generation | Raki family, DBrW, Double No-Touch RA |
| `RGACCLKO` / `RGACCLKO+` / `RGACCPERIO` / `PERIODS` | Period schedules, coupons, local barriers | Raki family, Reverse KIKO, DBrW, Dispersion |
| `GLOBALKO*` / `DAILYKO` | Global/daily KO observation + payment timing | Raki family, Double No-Touch RA, Reverse KIKO |
| `KNOCKIN*` | KI barrier + final payoff parameters | Raki family, Reverse KIKO |
| `ACCUPAY` / `FIXING` | Accumulator schedule, barriers, quantities | AQDQ |
| `DISCBARR` | Barrier style, levels, rebates | DBrW |
| `OPRF` | Outperformance parameters | Oprf |
| `DIGITAL` | Digital edge behavior at strike | Digital Option |
| `IRLEGP` | Swap-form payoff leg (ignored for note form) | Double No-Touch RA |

### 3.3 Payoff Family Blueprint

When designing a new payoff, use the closest existing family as the blueprint and modify:

```
Range accrual family (Raki/MemRaki/RakiPlus/DblNT):
  Periodic:   PayRate[i] = AccruRate[i] × (N1/N2) + FixCoupon[i]
  LKO/GKO:    PayRate[KO] = PayRate[accrued] + LOCpn/GKO Cpn + ReturnRatio
  Maturity:   contingent payoff (KI or no-KI formulations) + principal return

Barrier family (DBrW):
  Event-driven rebate + notional; Pay At Knock vs On Maturity

Accumulator family (AQDQ):
  Periodic purchase obligations, KO barrier, guaranteed periods
```

## 4. Naming & Configuration Standards

Adopt institution-wide standards so products stay consistent and supportable:

| Item | Convention | Example |
| :--- | :--- | :--- |
| Flex header | `EqFlex<Abbrev>` | `EqFlexDBrW`, `EqFlexRakiP` |
| Payoff script | `EqFlex<Abbrev>` (or `EqFlexs<Abbrev>` variant) | `EqFlexDblNT`, `EqFlexsKioV` |
| Model group | `EQ_<ABBREV>` | `EQ_DBARW`, `EQ_MEMRAKI` |
| MC generator type | `EQ_MONTECARLO` | — |
| C++ mapping file | `MxMapping.h` (+ content module) | — |
| Block naming | Upper-case, semantic | `KIKOSELECT`, `RGACCLKO`, `DISCBARR` |
| Portfolio / filter | Institution prefix, semantic | `TRDESK_EQ_FLEX_FILTER` |
| Batch matrix | `<ABBR><num>` with `VAR`/`SPB` variants | `TREQ00`→`EQ_EU1[VAR]` |

Keep a **dictionary** (registry) of product → header → payoff → model group → GMP → blocks so new developers can trace any product end to end.

## 5. Environments & Governance

- **DEV** — developer freedom; flex/model testing.
- **UAT** — realistic market data; UAT, functional sign-off, training.
- **PROD** — controlled; no direct configuration edits.
- **Promotion mechanism:** configuration packages exported from lower envs and imported to higher envs; C++ build version recorded alongside. Never rebuild production config from memory.
- **Change control:** any change to a shared flex block, payoff script, GMP, or MSL rule requires regression sign-off on the full fixed-point suite because the blast radius spans multiple products.

## 6. Common Failure Modes and How to Avoid Them

| Failure mode | Avoidance |
| :--- | :--- |
| Field-name mismatch between flex and C++ | Mapping unit tests at build time |
| Silent model/qant drift after config change | Versioned GMP + fixed-point suite on every change |
| Ops unable to operate the product (fixing/knocks) | Ops involved from Phase A; playbooks written before go-live |
| Product needs Composite FX rule or >25m tenor that model can't do | Constraint gates in Phase A; MSL pre-trade blocks |
| FLEX generations differ from exchange calendar | Date-schedule generation tests per market |
| Benchmark values disagree → long divergence | Early external benchmark in Phase C/D; agree tolerance & source |
| Grid/batch times blow out with 30k paths on many products | Per-product sensitivity groups; monitor batch SLAs |
| UAT stakeholders not available at decision points | Governance: fixed decision cadence and named approvers |

## 7. Relationship to the Rest of this Playbook

- **Common_Features.md** — the vocabulary and building blocks referenced by every product spec.
- **Flex_Development.md** — the hands-on configuration/code walkthrough.
- **Risk_Management.md** — greeks, sensitivity configuration, and validation methodology.
- **Product pages** — each family's economics, flex blocks, GMP, constraints, and operational details.
- **Operations/LiveBook.md** — day-to-day risk processing for the products.