# Murex Flex Development Guide

This guide provides a comprehensive, systematic walkthrough of the development process for creating new structured equity products using the Murex FLEX framework. It covers the complete lifecycle — from requirements and payoff design through configuration, C++ development, pricing model integration, testing, and production rollout — and consolidates the patterns used across RakiPlus, DBrW, Double No-Touch RA, and other products.

## 1. Architectural Foundation

> **New here?** Read [Architecture Deep Dive: Flex, Generators, and Configuration Groups](./Architecture_Deep_Dive.md) first — it explains how flex headers/blocks relate to payoff scripts, model groups, GMP, generators, and sensitivity configuration groups, with a worked example and C++ skeleton.

### 1.1 The FLEX Framework Overview

The FLEX framework is the core of how custom products are defined in Murex. It allows developers to create bespoke UIs and link them to specific pricing models.

-   **Flex Headers**: A Flex Header is a template that corresponds to a specific product type (e.g., `EqFlexRakiP` for RakiPlus). It acts as a container for a collection of Flex Blocks. The header is what the trader sees as the product's booking screen.

-   **Flex Blocks**: A Flex Block is a user-interface component that groups together related economic parameters for a trade. By combining different blocks, a wide variety of products can be constructed. Examples include `KIKOSELECT` for basket definitions or `PERIODS` for defining schedules. A block may contain:
    - Input fields (numeric, string, calendar/date, checkbox, combo/dropdown)
    - Tables/grids with many rows and columns (e.g., underlying components, period-by-period parameters)
    - Dynamic visibility rules (show/hide/enable fields based on other field values)
    - Read-only model-output columns (e.g., cashflow, KO probability, PayRate)

### 1.2 Configuration vs Code

Developing a new flex product is a mix of **database configuration** (GUI-driven) and **C++ development**:

| Layer | Technology | What it does |
| :--- | :--- | :--- |
| Flex UI | GUI / XML definitions in the database | Booking screen: fields, grids, dynamic display, validation |
| Payoff script | GUI configuration | Links product selection → flex header → model group |
| GMP | GUI configuration | Model type, paths, seed, market-data binding |
| Mapping | C++ header/library | Reads stored flex attributes into C++ structs |
| Pricing model | C++ (e.g., Monte Carlo engine) | Valuates the payoff, computes greeks |
| Pre-trade rules | MSL scripts | Booking-time validation/compliance/routing |

The golden rule: **field names in the flex block definition and in the C++ mapping struct must match exactly (case-sensitive).** Any mismatch silently breaks the data flow from UI to model.

## 2. The New Product Development Workflow

The following end-to-end workflow is the recommended systematic path for onboarding a new structured equity product. Each step should be tracked with the artefacts listed.

### Phase 0: Requirements & Feasibility

**Goal:** Turn a term sheet into a precise, buildable specification.

1.  Parse the term sheet into the product building blocks (see Common_Features.md): barrier types, observation style, accrual features, memory features, FX rule, settlement, tenor, basket size.
2.  Determine whether the product is **reducible to existing blocks/models** (preferred — reuse `KIKOSELECT`, `RGACCLKO`, `PERIODS`, etc.) or requires **new blocks/fields** and possibly **new payoff logic**.
3.  Identify constraints: tenor limits, basket size, FX rule support, principal type, single-underly vs basket. Document them explicitly (many are enforced by Murex validation; some must be enforced by MSL rules or booking convention).
4.  Produce a **product specification document** describing:
    - Payoff formulas for every scenario (periodic, KO, KI, maturity, no-KO).
    - Fixing/date schedules and comparison operators (inclusive vs exclusive).
    - Flex header and block layout (which blocks, which fields, dynamic display rules).
    - Pricing approach: analytical vs Monte Carlo, model group, GMP parameters.
    - Lifecycle operations (expiry, exercise, knock, terminate) and their flows.

### Phase 1: Flex UI Configuration (Murex Configuration / GUI)

This step defines the user interface for the new product within Murex.

1.  **Create or reuse the Flex Blocks:** Using the Murex Flex Block editor, design the UI for data entry. This includes adding all necessary fields: text inputs, checkboxes, date pickers, dropdowns, and grids (e.g., for defining underlying assets). Prefer reusing existing blocks (with the same semantics) over duplicating them.
2.  **Create the Flex Header:** Define a new Flex Header that will represent the product. Naming convention: `<Institution><ProductAbbrev>` e.g. `EqFlexRakiP`, `EqFlexDBrW`, `EqFlexDblNT`.
3.  **Attach the blocks to the header:** Link the Flex Blocks to the new Flex Header so the custom UI is displayed when the product is selected.
4.  **Design the dynamic UI:** Fields should be shown, hidden, or disabled based on the values of other fields to prevent booking errors. Examples:
    - In `DBrW`, the "Down Barrier" fields are hidden if the selected barrier style is "Up Barrier Only".
    - If "Global KO" is unticked, the GKO comparison and GKO coupon columns are hidden.
    - If both LKO and GKO are unticked, a single dummy period with a far barrier (e.g., 99999) is generated and the observation date set to maturity.
5.  **Add validation controls:** comparison operators (e.g., `>=`/`>` for barriers), mandatory-field checks, date-sequence checks (e.g., payment date after period end date).
6.  **Add model-output display columns:** a "Model Output" checkbox reveals read-only model-computed columns (e.g., `Cashflow`, `PayRate`, `KO Prob`, `AccruRatio`) for use in the pricing page.

### Phase 2: C++ Mapping Development (Code)

The UI fields created in the Murex GUI must be mapped to C++ variables that the pricing engine can understand.

-   **Update the mapping header/library:** A C++ developer edits the mapping layer (e.g., `MxMapping.h` under the content directory). In this file, they define or extend C++ data structures (`struct`s or `classes`) that store the values entered by the user into the flex block fields.
-   **Maintain exact naming consistency:** The names of the fields defined in the C++ header must precisely match the names configured in the Murex Flex Block editor. Any mismatch (including case) breaks the data flow.
-   **Write mapping unit tests:** For every new field, add a test that books a deal with known field values and asserts the C++ struct receives the exact same values. This catches the classic name-mismatch bug at build time rather than in pricing.

### Phase 3: Pricing Model Integration (Code)

The C++ pricing model (e.g., a Monte Carlo engine) needs to be updated to read the new parameters and implement the financial logic of the product.

1.  **Read input parameters:** The model reads the values from the C++ structures populated by the flex mapping.
2.  **Implement the payoff logic:** The core financial logic is implemented. The model must use the new parameters (barrier levels, strikes, observation dates, basket components) to correctly calculate the product's payoff and risk sensitivities.
3.  **Follow the shared engine conventions:** 
    - Path generation must use the engine's configured number of paths, seed, and variance-reduction settings (from GMP).
    - Observation dates must be aligned to the deal's fixing schedules so that discrete barriers are monitored on the right dates.
    - For continuous monitoring, model the barrier using intraday min/max proxies consistent with operations (see Common_Features.md).
    - Cash-flow aggregation must respect the product's payment timing (period end vs KO date vs maturity).
    - Greek computation is typically bump-and-revalue in Murex simulation servers: do not hand-roll bespoke greeks inside the model unless there is a strong production reason (the standard framework is faster and consistent).
4.  **Regression order / cashflow flags:** match the GMP production settings agreed in Phase 0.

### Phase 4: Payoff & GMP Configuration (GUI)

The final wiring step ties everything together in the Murex GUI.

1.  **Configure the payoff script:** A Murex Payoff Script is created. This script is the central link: selecting it on the trade screen loads the **Flex Header** (UI) and binds to the **Pricing Model Group** (valuation). Naming convention mirrors the flex header (e.g., `EqFlexRaki`, `EqFlexKioV`).
2.  **Configure the GMP:** A GMP entry is created (or extended) associating the model group with the generator type and parameters. Representative production settings used across the structured products described in this playbook:
    - Generator: `EQ_MONTECARLO` (Monte Carlo with local volatility / diffusion processes).
    - Number of paths: ~30,000 (watch runtime vs. accuracy; GMP allows tuning).
    - Regression order: 1, cashflow flag: 0–1 depending on payoff (see each product's notes).
    - Model groups per product family: `EQ_RAKI`, `EQ_MEMRAKI`, `EQ_DBARW`, `EQ_KIKOREVS`, `EQ_OPRF`, `EQ_DIGOPT`, etc.
3.  **Define the market-data binding:** ensure the model group's GMP references the expected vol surfaces, dividend curves, FX pairs, and correlation matrices. For quanto products the FX fixing source/rate type must be available in market data.

### Phase 5: Market Data & Instrument Setup (Configuration)

-   **Dummy basket instrument:** ensure a market-appropriate dummy basket exists (e.g., `FLEX_USD` or per-market baskets). If underlyings are defined in blocks, the instrument carries no constituents.
-   **Underlying market data:** spot prices, implied/local vol surfaces, dividend curves, FX rates and correlations must exist for the constituents targeted.
-   **Calendars/shifters:** the schedule generators reference exchange calendars and payment-date shifters; verify they cover the product's markets and holidays.
-   **Fixed data items:** anything that must not move (e.g., fixed quanto FX rate, fixing source `BFIX`, fixing time/timezone) should be captured as trade attributes or fixed data as designed.

### Phase 6: Pre-Trade Rules & Booking Validation (MSL / Configuration)

-   Enforce business constraints that are not native Murex validation: basket currency = premium currency, max tenor, FX rule support (no Composite for many products), quantity principal rejected, minimum/maximum basket size, denomination handling.
-   Implement as MSL (Murex Scripting Language) pre-trade rules so invalid deals are blocked or flagged at booking time.
-   Extensive cross-product regression testing of MSL rules is mandatory — a small change to a shared rule can affect many products.

### Phase 7: Testing & Validation (MXtest / MxCI)

Treat testing as part of the build, not an afterthought:

1.  **Unit / component tests (build-level):** mapping tests (field-name coupling), date-schedule generation, boundary comparison operators, rounding/denomination logic.
2.  **Functional tests (MXtest):** booking each scenario type, running each market operation (expiry, exercise, knock event, unwind), and asserting generated flows (amounts, dates, notional returns).
3.  **Pricing regression / fixed-points:** build a set of benchmark deals (one per scenario/tenor/market) with frozen market data. After any change, assert premium and greeks within tolerances (e.g., premium < 1e-6 relative, greeks within a few percent or absolute threshold depending on the greek). This is how you catch unintended model or config drift.
4.  **Validation against an external benchmark:** reconcile premiums against an independent library (e.g., Numerix, DerivaTools, Fincad, Bloomberg) or an in-house quant library for a representative set of deals. Document the tolerance and the reason for any deviation.
5.  **Performance tests:** measure pricing and simulation runtime with the production GMP (paths), and confirm intraday quoting and end-of-day batch complete in the required windows. Use sensitivity configuration groups (`MAIN`, `VAR`, `EQDELTA`, `EQVEGA`, `IRDELTA`) to compute only the greeks needed per task (see Risk_Management.md).
6.  **Parallel runs:** where feasible, run new model vs. reference model/old payoff in shadow mode on a sample of live trades to compare NPV and greeks.

### Phase 8: UAT, Rollout & Hypercare

1.  **UAT with stakeholders:** traders, structurers, and operations walk the booking screens, fixing procedures, and market operations on the UAT environment with realistic data.
2.  **Training & documentation:** update the product playbooks (this repository), booking guides, fixing procedures, and operational checklists.
3.  **Environment promotion:** promote configuration via controlled import/export DEV → UAT → PROD. Tag the C++ build and its configuration version together (they must ship as a pair).
4.  **Go-live / hypercare:** start with a pilot group of trades, monitor pricing consistency vs. expected behavior, watch batch times, and have a documented rollback path (deactivate payoff script/exclude from simulation groups).

## 3. Best Practices & Key Considerations

### 3.1 Dummy Basket Methodology

For products with multi-asset underlyings, use a "dummy basket" approach. Instead of creating a new basket instrument for every trade, use a generic instrument (e.g., `FLEX_USD`) and define the actual constituents within a flex block (`KIKOSTRUCT` or `KIKOSELECT`). This significantly reduces operational overhead and removes the constraint of pre-creating baskets for each stock combination. A dummy basket should be configured with the correct multi-currency/Quanto rule for the market it represents.

### 3.2 Dynamic UI Design

To prevent booking errors, design the Flex Block UI to be dynamic. Fields should be shown, hidden, or disabled based on other field values. Examples across the playbook products:

-   `DBrW`: "Down Barrier" fields hidden unless the barrier style uses a down/double barrier.
-   Reverse KIKO: GKO fields hidden if GKO disabled; LKO fields hidden if LKO disabled; a dummy period (barrier 99999, observation = maturity) is generated when both are disabled.
-   Double No-Touch RA: Knock-In fields stay hidden because KI is unsupported for the payoff.

### 3.3 Comparison Operators (Fixing at the Boundary)

Nearly every barrier/range product has a set of comparison checkboxes that define how a fixing exactly *at* the boundary is treated. Always expose and document them explicitly:

-   Range accrual bounds: `LowRangeCompare` (`>=`/`>`) and `UpRangeCompare` (`<=`/`<`).
-   KO barriers: `>=`/`>` for upper barriers, `<=`/`<` for lower barriers.
-   Strike comparisons in accumulators: `>=`/`>`.
-   Missing/ambiguous operator handling is a top cause of settlement disputes — cover it in the spec and in functional tests.

### 3.4 Denomination & Cash-Flow Rounding

For products with periodic cash flows, the `Denomination` field controls rounding granularity:

```
CashFlow[i] = Round(Denomination × PayRate[i], 2) × (Notional / Denomination)
```

The denomination should match the term sheet. If left at the default (Notional), rounding is coarser and can create visible discrepancies (see Dispersion notes for a worked example). This must be part of the booking conventions, plus a defaulting rule when the term sheet does not specify one.

### 3.5 Event-Driven vs Schedule-Driven Cash Flows

Design cash-flow generation to match product economics:

-   **Event-driven** (DBrW, Double No-Touch RA): cash flows exist only when a barrier event (knock-in/knock-out) occurs. Rebate and notional return follow the same timing (At Knock vs On Maturity). This reduces system noise and simplifies settlement.
-   **Schedule-driven** (Raki family): periodic coupons on payment dates, with separate settlement flows on KO and maturity.
-   Always handle the **dual-trigger** case (LKO and GKO on the same day): define precedence (typically GKO wins) and accrual cut-off rules.

### 3.6 Model Output Columns for Traders

Add a "Model Output" checkbox to reveal model-computed read-only columns inside the pricing page: `Cashflow`, `PayRate`, `KO Prob`, `AccruRatio`. This gives traders transparency on what the model is doing and supports pre-trade validation without leaving the pricing screen.

### 3.7 Performance Optimization

Sensitivity calculation is the most expensive part of interactive risk for exotic products. Use Murex **Sensitivity Configuration Groups** (`MAIN`, `VAR`, `EQDELTA`, `EQVEGA`, `IRDELTA`, ...) to compute only the greeks required for a task (e.g., all greeks off for a pure P&L report). Keep unnecessary sensitivities unticked in every group. This is detailed in Risk_Management.md.

## 4. Coding Standards & Common Pitfalls

| Pitfall | Mitigation |
| :--- | :--- |
| Flex field name ≠ C++ struct field name (case-sensitive) | Mapping unit tests; naming review in code review |
| Schedule generator/calendar mismatch | Test generated dates against the exchange calendar and holiday lists |
| Forgetting inclusive/exclusive boundary operators | Explicit spec sheet; functional tests for fixings exactly at the level |
| Wrong payment-date shifter for market operations | Verify payment dates against the term sheet; set shifters in config |
| Duplicate float/rounding drift on low-PayRate periods | Denomination rounding rule; UAT approval on sample cash-flow prints |
| Model reads wrong vol/correlation for quanto baskets | GMP market-data binding review; quanto test deals |
| Continuous barrier approximated differently by ops (min/max fixing) vs model | Align the model's continuous-monitoring convention with the Operations Min-Max fixing procedure |
| Regression path/seed not fixed in tests | Fixed seeds and frozen market data in fixed-point regression suite |
| Shared GMP/model group changed, other products drift | Version GMP; run full fixed-point suite on every model change |

## 5. Versioning, Deployment & Migration

-   **Versioning:** track (build, configuration) together. Record which payoff scripts, flex headers, and GMPs a given C++ build supports. Murex releases quarterly — bundle your local customizations with each upgrade and rerun the full regression suite.
-   **Migration strategy:** prefer adding a **new flex header** (e.g., `EqFlexRakiP`) over mutating a live one; re-point existing deals only when strictly necessary. New headers allow clean side-by-side rollout and rollback.
-   **Environment promotion:** promote configuration through DEV → UAT → PROD with signed-off import/export packages; never edit directly in PROD.
-   **Rollback plan:** the safest rollback is deactivating the payoff script (new deals cannot be booked) combined with excluding the model group from simulation config, then restoring the previous configuration package.

## 6. Delivery Checklist

Use this as a sign-off gate when taking a new structured equity product to production:

- [ ] Term-sheet spec with every payoff scenario and boundary operator
- [ ] Flex blocks + header created (or reuse documented) and attached
- [ ] Dynamic UI rules specified and tested
- [ ] C++ mapping extended, names match flex fields (unit-tested)
- [ ] Payoff logic implemented; model reads all new parameters
- [ ] Payoff script and GMP configured; production paths/seed agreed
- [ ] Dummy basket/market data available (spot, vol, divs, FX, corr)
- [ ] Pre-trade/MSL validation covers all constraints
- [ ] Fixed-point pricing/greeks regression suite updated and green
- [ ] External benchmark validation passed within tolerance
- [ ] MXtest functional coverage for all lifecycle events
- [ ] Performance/SLAs met (quote time, batch window)
- [ ] Operational playbook (fixing, hits/knocks, settlement) updated
- [ ] UAT signed off; training delivered; rollout + rollback plan approved