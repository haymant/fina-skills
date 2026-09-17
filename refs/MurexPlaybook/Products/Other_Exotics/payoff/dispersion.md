# Equity Dispersion Swap: Payoff Chapter

## Purpose and classification

The **EQ Flex Dispersion** product pays a periodic coupon linked to cross-sectional dispersion among a basket of equities. For each period, it compares each stock's return with the simple average return of the basket, takes the absolute spreads, and averages them. Greater disagreement among constituents produces a larger coupon; synchronized movement produces a small coupon. [1]

The documented Murex representation is `EQD` / `OPT` / `FLEX`, with Flex Header `EqFlexDisps`, contract `BSKT SHARE`, and instrument `FLEX_USD`. The model assumes deterministic interest rates and equity GBM with local volatility calibrated to implied volatility. [1]

## State and payoff calculation

For constituent \(k\) in period \(i\), define:

\[
R_{k,i}=\frac{S_{k,i}}{S_{k,0}}-1,
\qquad
\bar R_i=\frac{1}{N}\sum_{k=1}^{N}R_{k,i}.
\]

The absolute spread and cross-sectional dispersion are:

\[
D_{k,i}=|R_{k,i}-\bar R_i|,
\qquad
D_i=\frac{1}{N}\sum_{k=1}^{N}D_{k,i}.
\]

The period rate is:

\[
P_i=\min\left\{Cap_i,\max\left\{Floor_i,PR_i(D_i-Strike_i)\right\}\right\}.
\]

`PERIODS` generates period-end and payment dates and stores `Cap`, `Floor`, `PR`, and `Strike`. The product has no daily accrual and no KO event; fixing is declared at period ends. [1]

## Cashflow and decomposition

The denomination rule is:

\[
CashFlow_i=Round(Denomination\times P_i,2)\times\frac{Notional}{Denomination}.
\]

| Component | Interpretation |
|---|---|
| Funding / principal | No separate principal-return branch is described beyond the standard trade notional and maturity convention. Do not invent redemption terms. |
| Coupon | The entire periodic dispersion-linked amount, including participation, strike, floor, cap, and denomination rounding. |
| Embedded option / residual | The capped/floored exposure to cross-sectional dispersion. It is a basket-relative option-like residual rather than a vanilla single-name option. |

The source does not describe exercise or knock operations. Supported lifecycle operations include unwind, expiry after final fixing, restructuring, and close-and-reopen subject to date checks. [1]

## Flex-block mapping

| Input | Source location | Graph role |
|---|---|---|
| Basket constituents and reference prices | `KIKOSTRUCT` | Normalize each constituent return. |
| Denomination | `KIKOSTRUCT` | Periodic rounding node. |
| Period dates and payment dates | `PERIODS` schedule generator | Observation/payment schedule. |
| Cap, Floor, PR, Strike | `PERIODS` | Dispersion payoff function. |
| Basket market, nominal, maturity, FX rule, premium currency | Standard financial definition | Context, scale, settlement, and FX conversion. |

## Explicit payoff graph

```text
initial prices + period fixings → constituent returns
                                  → basket average
                                  → absolute spreads and average dispersion
                                  → participation / strike
                                  → floor / cap
                                  → denomination rounding → cashflow
```

Retain each constituent return and spread as explainability nodes. A model output view may show `Cashflow` and `PayRate`, but those are results, not independent inputs.

## Lifecycle, constraints, and open points

Cut-off fixings are declared on period-end dates and archived by market. Expiry requires the final fixing to be finalized. Single-equity booking is unsupported; the basket may contain at most 19 stocks. Nominal principal is required, Composite FX is unsupported, and maximum tenor is 37 months. Basic and Quanto are supported. [1]

The source does not specify the legal status of the final principal exchange, premium cashflow, missing-fixing policy, weighting conventions beyond simple average, or exact rate-to-currency sign. These belong in the deployed payoff script or a conformance fixture.

## References

[1]: ../Dispersion.md "Murex Playbook — Equity Dispersion Swap"
