# Common Product Features

This document defines and explains the key building blocks and recurring features that are used across many different structured products. Its purpose is to create a central reference for common terms used by traders, quants, and developers. Product specifications reference these definitions, so keeping this file accurate keeps every product page accurate.

## 1. How these Features Map to Murex Concepts

Product features never live in one place — each one is enacted across several Murex layers. Before reading the definitions below, keep the four-layer lens from the [Architecture Deep Dive](./Architecture_Deep_Dive.md) in mind:

| Layer | What it does for a feature |
| :--- | :--- |
| **Booking / UI** | A flex block field, table column, toggle, or dynamic-visibility rule captures the trader's choices (e.g., `LocBarUp` in `RGACCPERIO`). |
| **Wiring** | The payoff script binds the flex header (the UI above) to the **model group**; GMP binds the model group to a **generator** and its settings. |
| **Pricing** | The generator consumes the mapped C++ struct + market data on each simulated path and values the feature. |
| **Risk** | The sensitivity configuration group decides *which* greeks expose the feature's risk (e.g., barrier delta-gap, correlation). |
| **Operations** | Fixing/knock/expiry/exercise market operations and min-max fixing enact the feature over the deal's life. |

### Feature-by-feature mapping

| Financial / product concept | Booking & UI (flex) | Pricing (generator input) | Risk & operations |
| :--- | :--- | :--- | :--- |
| **Knock-Out / Knock-In barrier** | `DISCBARR`, `LOCALKO*`, `GLOBALKO*`, `KNOCKIN*`, feature toggles in `KIKOSELECT`; comparison operators (`>=`, `>`, `<=`, `<`) | Model monitors barriers on the simulated observation dates | **Delta-gap** sensitivity; `Knock` market operation; min-max fixing for continuous monitoring |
| **Observation style** (daily / periodic / continuous) | `FIXINGDATE`, `RGACCDATE` schedule generators; `Choice KO Barr` = Discrete/Continuous | The path time-grid must include every observation date | Continuous → Operations uses **min/max fixing** index |
| **Worst/Best/K-th/Average/All/Any performance** | Constituents in `KIKOSELECT`/`KIKOSTRUCT`; `Acc Indicator`, `PerfRank`, `Basket Perf` | Model ranks/computes the indicator on each path; needs the **eq-eq correlation** matrix | **Correlation sensi**; dispersion/outperformance basket risk |
| **Range accrual (N1/N2)** | `RGACCLKO`/`RGACCPERIO` bounds + compare ops; `RGACCDATE` observation dates | Model counts in/out days per simulated path | Coupon cash flows; period-end fixing procedures |
| **Memory coupon** | Coupon-barrier + memory flags | Model carries forward unpaid coupons across periods | Mutually exclusive with Global KO |
| **Memory KO (per-name locks)** | Per-stock `LKO Locked` / `GKO Locked` columns in `KIKOSEL*` | Model tracks per-name "breached at least once" memory | KO fires only when *all* names locked; operational state tracked |
| **Participation rate / Cap / Floor** | Per-period columns in `PERIODS` or `RGACCLKO` | Model payoff scaling/clamping | — |
| **KO coupon / Rebate / Return ratio** | `Return Ratio (%)`, KO Cpn fields | Early-termination payoff branch | Settlement flows on `Knock`; **Pay at Knock** vs **On Maturity** |
| **FX rules** (Basic / Quanto / Composite) | FX rule + premium ccy on the ticket; quanto FX fixing fields (pair, source, time, zone, rate type) | Quanto adjustment in the model; needs **FX vol** + **eq-fx correlation** | **FX vega**, quanto delta; Composite rejected at validation |
| **Settlement** (cash / delivery / nominal / quantity) | Ticket fields + `ITM Payment` | — | `EXR` / `EXP` / `XIT` market operations |
| **Step / balloon periods** | Per-period rows in `PERIODS` / `RGACCLKO` | Model applies period-specific parameters | Schedule generators → period/payment dates |
| **Dates & calendars** | Schedule generators `F(Start, End, ScheduleGen, Calendar)` + shifters | Time-grid construction | Fixing/payment calendar maintenance |

### A worked trace: "Local KO" through the layers

Take the `LocBarUp` Local-KO barrier in a Double No-Touch RA:

1. **Booking:** the `RGACCPERIO` block holds `LocBarUp`/`LocKOUppBarComp` per period.
2. **Mapping:** the C++ struct for `RGACCPERIO` exposes those fields to the model (name-for-name).
3. **Wiring:** payoff `EqFlexDblNT` → model group → GMP → `EQ_MONTECARLO` generator.
4. **Pricing:** the generator checks `BPS/WPS >= LocBarUp` on each period-end simulated fixing.
5. **Risk:** the simulation server computes delta-gap and correlation greeks per the sensitivity config group.
6. **Operations:** on the real period end, the `Knock` market operation reads the fixing and generates the KO settlement flows.

Every definition in this document §2–§8 can be traced the same way.

## 2. Barrier Events

A barrier option is a type of exotic option where the payoff depends on whether the underlying asset's price reaches a certain predetermined level (the "barrier") over a specified period.

### Knock-Out (KO)

A **Knock-Out (KO)** barrier causes an option to expire worthless or terminate if the underlying asset's price hits the barrier. This event can trigger a pre-agreed cash payment known as a rebate.

*   **Up-and-Out (UAO):** The option is knocked out if the underlying's price rises to or above the barrier level.
*   **Down-and-Out (DAO):** The option is knocked out if the underlying's price falls to or below the barrier level.
*   **Double Knock-Out:** The option has both an upper and a lower barrier. The option is knocked out if the price touches either of these levels.

### Knock-In (KI)

A **Knock-In (KI)** barrier causes an option to come into existence only if the underlying asset's price hits the barrier level. If the barrier is never touched, the option never becomes active and expires worthless.

*   **Up-and-In (UAI):** The option becomes active if the underlying's price rises to or above the barrier level.
*   **Down-and-In (DAI):** The option becomes active if the underlying's price falls to or below the barrier level.
*   **Double Knock-In:** The option has both an upper and a lower barrier. The option becomes active if the price touches either of these levels.

### Observation Types

The terms on which a barrier is monitored can vary:

*   **Discrete (or Daily):** The barrier is monitored only at specific, pre-defined dates. Most commonly, this is done at the market close each day. The convention must define whether a fixing *exactly at* the barrier triggers the event (inclusive `>=` / `<=`) or not (exclusive `>` / `<`).
*   **Periodic:** The barrier is monitored only on specific dates, such as at the end of each observation period (e.g., monthly or quarterly).
*   **Continuous:** The barrier is monitored at all times throughout the life of the trade. If the barrier is breached at any point, the event is triggered. In Murex, continuous monitoring is operationalized via **Min-Max fixing**: the intraday *maximum* price is used for up-barriers and the intraday *minimum* for down-barriers, recorded on a fixing index. The pricing model must use the same convention.

### Memory Knock-Out

In some basket products, a Knock-Out event only occurs after *each* underlying in the basket has individually breached its barrier at some point during the life of the trade. The product "remembers" which underlyings have already hit their barriers (tracked by per-stock "locked" flags and dates in the flex block). A Local Memory KO is checked on discrete dates; a Global Memory KO is checked daily/continuously. Memory KO and standard WPS-driven KO are mutually exclusive mechanisms in the Raki family.

## 3. Performance Indicators

For products based on a basket of multiple underlyings, the performance that determines the payoff is often based on a specific rank-ordering of the assets. The performance of each underlying is `Perf_k = S_k(t) / S_k(0) - 1` (or a ratio `S_k(t)/S_k(0)` for barrier triggers).

*   **Worst-of Performance (WPS):** The performance of the basket is linked to the underlying asset that has performed the worst relative to its initial price.
*   **Best-of Performance (BPS):** The performance of the basket is linked to the underlying asset that has performed the best relative to its initial price.
*   **K-th Best Performer:** The performance is linked to the asset that ranks K-th in the basket (e.g., the 2nd best performer in a basket of 5 assets). In this ranking, Rank 1 is the best performer and Rank N (where N is the number of assets) is the worst performer.
*   **Average Performance (AVG):** The performance is the simple average of all constituents' performance — used where the payoff should not depend on a single name (e.g., average-based dispersion and some outperformance structures).
*   **"All" / "Any":** Used as *accrual indicators* — the accrual condition must hold for all constituents, or at least for any one constituent, rather than a single rank.
*   **Dispersion:** The average absolute deviation of each stock's performance around the basket's average performance; a proxy for realized correlation/idiosyncratic risk. High dispersion (low correlation) pays a higher coupon.

## 4. Payoff Components

### Participation Rate (PR / Share Ratio)

The **Participation Rate** scales the payoff: `Payoff = PR × (Underlying Performance − Strike)`, often capped and floored. In cliquet-style structures two participation rates (up and down) can apply (`PR1`, `PR2`).

### Cap and Floor

A **Cap** sets the maximum payout rate and a **Floor** the minimum. They apply per period (periodic coupon cap/floor) and/or at maturity (final cap/floor). In maturity payoffs the standard pattern is:

```
PayRate = min{ Cap, max{ Floor, PR × (Perf − Strike) } }  (+ return ratio)
```

### Rebates

A rebate is a fixed cash amount paid out if a barrier event (typically a Knock-Out) occurs. The timing of this payment can be configured:

*   **Pay At Knock:** The rebate is paid shortly after the barrier event is triggered.
*   **Pay At Maturity:** The rebate payment is deferred and paid at the option's final maturity date.

### Return Ratio / Notional Return

The **Return Ratio** is the percentage of notional returned to the investor on an early termination (KO) event: `Notional Return = ReturnRatio% × Notional`. It is part of the settlement flow of the KO coupon and completes the early-exit economics. The notional repayment generally follows the same timing rule as the rebate (At Knock vs On Maturity).

### Range Accrual

A range accrual is a feature where a coupon is paid based on the number of days the underlying asset (or basket performance indicator) stays within a pre-defined range. The accrued coupon is typically calculated as:

**Accrued Coupon = Coupon Rate × (N1 / N2)**

*   **N1:** The number of days within the observation period that the underlying's price fixes inside the specified range.
*   **N2:** The total number of observation days in the period.

The range bounds (`LowRange`, `UpRange`) and their comparison operators (`LowRangeCompare`, `UpRangeCompare`) define inclusivity. For early-terminating (KO) deals the accrual factor is computed up to the KO date (N1 truncated at the event; N2 remains the full-period count or is truncated consistently — follow the product spec).

### Memory Coupon

The "Memory Coupon" feature allows unpaid coupons from previous periods to be recovered: if the condition (`WPS >= Coupon Barrier`) is satisfied in period `i`, the coupon for period `i` and all unpaid coupons from previous consecutive missed periods are paid together. If the condition is not met, the current coupon is skipped and accumulated. The **Coupon Barrier/Memory Coupon** feature is mutually exclusive with **Global KO** in the Raki family.

### Knock-Out Coupon / Bonus

A **KO coupon (KB / LKO Cpn / GKO Cpn)** is an extra fixed coupon paid on an early termination event, on top of the accrued periodic rate and the returned notional:

```
PayRate[KO] = PayRate[accrued] + KO Cpn + ReturnRatio
```

### Digital / Binary

A digital (binary) pays a fixed amount (or delivers a fixed quantity per unit) if a condition is met at expiry and zero otherwise. Edge behavior at `Final Price = Strike` must be configured (pay/not-pay). Settlement may be cash (`Nominal + Cash`) or asset delivery (`Quantity + Delivery`).

### Averaging (Asian)

Some structures average fixing prices over a window rather than using a single spot. Averaging affects the payoff and the greeks (lower gamma/vega); the schedule and average type (arithmetic vs geometric) must be specified.

### Cliquet / Ratchet

A cliquet locks in periodic gains: each period's positive performance is added to the previous locked value but not given back if a later period performs negatively (floor protection). The no-KI maturity formulation in the Raki family is a cliquet-style payoff:

```
PayRate[Maturity] = PayRate[N] + max{ min{ Cap, PR1×max(WPS/S1-1,0) + PR2×max(1-WPS/S2,0) }, Floor } + ReturnRatio
```

## 5. Settlement and FX

### FX Conversion Rules

The payoff currency handling follows a small set of rules. Let `S` = underlying performance, `K` = strike, `X` = spot FX rate. Murex structured equity products typically support:

*   **Basic `(S − K) × X`:** The basket currency is the same as the premium (settlement) currency. The basic rule multiplies a payoff by the FX rate when currencies differ.
*   **Quanto `(S × 1 − K)`:** The basket currency differs from the premium currency, and a **fixed** FX rate (fixed at trade inception) is used for settlement. This eliminates currency risk for the investor. FX fixing details (pair, fixing source e.g. `BFIX`, fixing time, time zone, rate type Mid/Bid/Ask) are captured for quanto products.
*   **Composite `(S × X − K)`:** The payoff converts the underlying price at a *variable* spot FX rate. This rule is **generally unsupported** by the products in this Playbook and is rejected at validation.

### Settlement Conventions

*   **Cash:** settlement by cash payment of the payoff amount (`Nominal`-based deals).
*   **Delivery/Physical:** settlement by delivery of shares (`Quantity`-based deals); the options market-operation generates an exercised ticket with the delivered quantity.
*   **ITM Payment:** a field on several products that specifies whether an in-the-money expiry settles `Cash` or `Delivery`.
*   **Principal:** deals are typically **Nominal**-based. "Quantity" principal is unsupported by most structures. Nominal + Cash and Quantity + Delivery are the two supported settlement combinations for digitals.

### Quanto Mechanics

Quanto adjustment: because the payoff is settled at a fixed FX rate and the underlying is denominated in a different currency, the pricing model applies a quanto correction (the volatility of the FX rate and its correlation with the underlying enter the drift/diffusion). Quanto products therefore need FX volatility surfaces and eq-fx correlations in market data — a common setup gap.

## 6. Schedule and Date Conventions

Most structures are described by several interlocking date schedules:

*   **Observation / Fixing Dates** — when prices are observed: `Date = F(Start, End, ScheduleGen, Calendar)`.
*   **Period Start / End Dates** — the boundaries of accrual/payment periods: `PeriodEnd = F(Start, End, ScheduleGen, Calendar)`.
*   **Payment Dates** — when cash flows pay: `Payment = F(PeriodEnd, Shifter, Calendar)`.
*   **Effective Dates** — start of accrual for a coupon or event window.

Standard business-date conventions (e.g., modified following, adjustment of holiday-affected dates) must be baked into the schedule generators and the exchange calendar. Continuous observation uses **min/max fixing** (see §2).

## 7. Balloon / Step Structures

The payoff parameters can vary by period:

*   **Step-up / Step-down barriers:** different barrier levels per period (rising or falling), enabling structures that widen/narrow the knock-out protection over time.
*   **Period-specific coupons and KO coupons:** accrual rate, fixed coupon, local/global KO coupons and barriers can be configured per period (e.g., in the `RGACCLKO` family of blocks).
*   **Guaranteed periods** (accumulators): if a KO event occurs, the holder is still entitled to accruals for remaining guaranteed periods, typically at the most advantageous quantity.

## 8. Product Constraint Patterns

These constraints recur throughout the Playbook and should be treated as platform-level conventions unless a product page explicitly overrides them:

| Constraint | Typical rule |
| :--- | :--- |
| Dummy basket booking | Book `BSKT SHARE` / `FLEX_USD`; constituents in blocks. Single equities booked as basket-of-1 (or forbidden). |
| FX rules | Basic and Quanto supported; Composite unsupported. |
| Principal | Nominal only (quantity principal unsupported). |
| Basket size | 6 stocks (Raki family/DBrW) up to 19 stocks (Dispersion). |
| Tenor | 2 years (Raki/MemRaki/AQDQ/Digital/Reverse KIKO), 25 months (RakiPlus/DBrW/DblNT), 37 months (Dispersion) — check each product page. |
| Single underlying | Some products (MemRaki, RakiPlus, DBrW) require basket booking. |
| Basket ccy vs premium ccy | Often must be equal unless the product supports quanto. |