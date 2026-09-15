# A Definitive Guide to Risk Management for Murex EQ Flex Products

## Introduction

This document is the definitive guide to the primary risk greeks and sensitivities for EQ Flex products in Murex. It outlines the definitions, calculation methodologies, and configuration of various risk parameters, plus how greeks are validated.

### Risk Nomenclature Used in Murex

Before reading the formulas, understand the Murex viewer conventions, because the same greek appears with different units in different screens:

| Term | Meaning |
| :--- | :--- |
| **Mid** | The *rate* greek (dimensionless % or units), e.g., delta as a percentage of notional per 1% spot move, computed by central finite difference. Found on the Pricing page. |
| **Cntrct** | The greek expressed *per contract* — scaled by notional and lot size into units of the underlying. |
| **BUC** | "Base Unit Currency" — greek expressed in the position's base unit currency (the portfolio/market's reporting currency for the risk view). |
| **GR** | "Group" — greek expressed in the currency of the risk group / underlying group, before FX conversion to BUC. |
| **adj_factor** | A capital-factor ratio converting between currencies using each currency's capital factor at the relevant settlement (shift) date. |

The general relationship is:

```
Rate greek (Mid)  →  multiply by notional/lot to get per-contract  →  convert FX to get BUC/GR
```

All bump-and-revalue definitions below assume the pricing model is re-valued with the shifted market data, other things being equal ("parallel" shift of a whole axis, or "term"/bucket shift for a single tenor — see EQ Compute Vega vs EQ Term Vega).

---

## Equity-Related Greeks

This section details the risk sensitivities related to equity price and volatility movements.

### EQ Delta

**Related Risk Reports:**
*   EQ Delta

**Market Data Movements:**
*   EQ spot price +1%

**Risk Value Calculation:**
*   **Pricing Page:**
    `Delta Mid = [(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2 * 1% * spot)] * 100 * fx`
    Where `fx`: 1 premium currency = units of underlying currency.

    This is a central finite difference scaled to "per 1% move" and expressed per 100 units of notional. The `* fx` converts to premium currency.

*   **Simulation Page (in MX_EQD_Summary viewer):**
    `Delta Cntrct = (Delta Mid * Nominal / 100 / LotSize) * adj_factor`
    `EqDelta = Delta Cntrct * spot * LotSize`
    `= (Delta Mid * Nominal * spot / 100) * adj_factor`
    Where `adj_factor` is a capital factor adjustment between the underlying and premium currencies based on their respective settlement dates. It is calculated as:
    `adj_factor = capital_factor (underlying_ccy, underlying_shift_date) / capital factor (premium_ccy, premium_shift_date)`
    *   `underlying_ccy` and `underlying_shift_date` are defined in the equity's market information configuration.
    *   `premium_ccy` is from the deal ticket.
    *   `premium_shift_date` is defined in the market information for a basket or in the date details for a single equity.
    *(Image description: The source document contains screenshots showing the Murex UI for finding the 'payment date' as the underlying shift date and the 'option spot date' as the premium shift date.)*

*   **Simulation Page (in RSENSI_EQ_DELTA viewer):**
    `Eq deltaGR = EqDelta` in `MX_EQD_Summary` viewer
    `Eq deltaBUC = EqDelta` in `MX_EQD_Summary` viewer

*   **In SpreadsheetLoadingTool:**
    `EQ Delta = [(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2 * 1% * spot)] * 100`

### EQ Sticky Strike Delta

**Related Risk Reports:**
*   EQ Delta

**Market Data Movements:**
*   EQ spot price +/- 1%

**Risk Value Calculation:**
*   **Pricing Page:**
    `SS_Delta Mid = [(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2* 1% * spot)] * 100 * fx`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **Simulation Page (in MX_EQD_Summary viewer):**
    `SS_Delta = [(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2* 1% * spot)] * Nominal * Eq_Spot * fx`
    Where `fx`: 1 premium currency = units of underlying currency.

> **Convention note.** Sticky-strike delta keeps the implied vol **fixed at each strike level** as the spot moves (absolute strikes do not slide on the vol surface). It differs from sticky-delta (vol fixed at each delta) or sticky-by-moneyness. Sticky-strike is commonly used for barrier/exotic books where the barrier location relative to strikes matters for hedging.

### EQ Delta Gap

**Related Risk Reports:**
*   EQ Delta

**Market Data Movements:**
*   EQ spot price jump to barrier +/- 0.01
*   EQ spot price +/- 1%

**Risk Value Calculation:**
*   **Pricing Page:**
    `Delta Gap = (Delta when spot is true barrier + 0.01X) – (Delta when spot is true barrier – 0.01X)`
    Where X = 1 for Up Knock and X = -1 for Down Knock.

    Let:
    `A = [(Premium( (Barrier + 0.01)*101%) – Premium( (Barrier + 0.01)*99%)) / (2* 1% * (Barrier + 0.01))]`
    `B = [(Premium( (Barrier - 0.01)*101%) – Premium( (Barrier - 0.01)*99%)) / (2* 1% * (Barrier - 0.01))]`

    *   If X = 1 (Up Knock): `Delta Gap = (A – B) * 100 * fx`
    *   If X = -1 (Down Knock): `Delta Gap = (B – A) * 100 * fx`

*   **Simulation Page:**
    `Delta Gap = Delta Gap in pricing page * Nominal * Eq_Spot / 100`

> **Convention note.** Delta Gap measures the discrete jump in delta as spot crosses the barrier — a key risk for barrier products where the hedge must be adjusted precisely at the barrier. Notional-value terms (Nominal × Eq_Spot) are applied in simulation.

### EQ Gamma

**Related Risk Reports:**
*   EQ Gamma

**Market Data Movements:**
*   EQ spot price +1%
*   EQ spot price - 1%

**Risk Value Calculation:**
*   **Pricing Page:**
    `Gamma Mid = [(Premium(spot + 1% * spot) – 2 * Premium(spot) + Premium(spot - 1% * spot)) / (1% * spot) ^ 2 ] * 100 * fx`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **Simulation Page (in MX_EQD_Summary viewer):**
    `Gamma Cntrct = (Gamma Mid * Nominal * spot / 10000 / Lot Size) * adj_factor`
    `EqGamma = Gamma Cntrct * spot * LotSize`
    `= (Gamma Mid * Nominal * spot * spot / 10000) * adj_factor`
    Where `adj_factor` = `capital factor(underlying_ccy, underlying_shift_date)`.
    *(Note: for gamma the documented convention multiplies only the underlying currency's capital factor, whereas delta uses a ratio of underlying to premium factors; verify the convention in effect for your product before relying on the sign/scale.)*

*   **Simulation Page (in RSENSI_EQ_GAMMA viewer):**
    `Eq Gamma = (Gamma Mid * Nominal / 100 ) * adj_factor`

*   **In SpreadsheetLoadingTool:**
    `EQ Gamma = [(Premium(spot + 1% * spot) – 2 * Premium(spot) + Premium(spot - 1% * spot)) / (1% * spot) ^ 2 ] * 100`

*   **Cross Gamma:**
    `[(Premium(spoti *(1+ 1%), spotj *(1+ 1%)) – Premium(spoti *(1+ 1%), spotj)- Premium(spoti, spotj*(1+ 1%) + Premium(spoti, spotj)) / (1%) ^ 2 ]*Notional *DiscFXSpot(1st Underlying CCY-USD)/ FXSpot(1st Underlying CCY-Premium CCY)*DF(premium)`

> **Convention note.** Cross gamma measures the second-order sensitivity of the premium to two different equities moving together. It is priced by a 2-dimensional finite difference (all four corner points). For worst-of/best-of basket products cross-gamma is economically significant and risks being missed by assumptions of independence.

### EQ Theta

**Related Risk Reports:**
*   EQ Theta

**Market Data Movements:**
*   Pricing date +1 day. This indirectly affects yield curve start/end dates, implied vol tenor, FX vol tenor, and local vol input parameters.

**Risk Value Calculation:**
*   **Pricing Page:** `Premium(Shift +1 day) – Premium(Original)`
*   **Simulation Page:** `NPV(Shift +1 day) – NPV(Original)`

### EQ Rho

**Related Risk Reports:**
*   EQ Compute Rho (parallel shift Rho)
*   EQ Term Rho (bucket shift Rho)

**Market Data Movements:**
*   Yield Curve zero rates +/- 10bps

**Risk Value Calculation:**
*   **Pricing Page:**
    `Rho = [Premium (zero rate + 10bps) – Premium(original)] * fx / 0.001`

*   **Simulation Page (in Rate tab -> zero coupon sensitivities):**
    `Rho_i = [premium (zero_rate_i + 10bps) – premium (zero_rate_i – 10bps)] * fx /0.002`
    `IRPV01_i = Rho_i * Notional / 10000 = [premium (zero_rate_i + 10bps) – premium (zero_rate_i – 10bps)] * Notional * fx / 20`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **Simulation Page (in RSENSI_IR_DELTA viewer):**
    `DV01 (zero) BUC_i = [premium (zero_rate_i + 10bps) – premium (zero_rate_i – 10bps)] * Notional * fx / 20`
    Where `fx`: 1 premium currency = units of underlying currency.

> **Convention note.** For products with both deterministic and stochastic rates this split continues to hold; the discounting and the underlying repo/funding curves are both shifted. Whether the product's greeks drive from the discount curve only, or also the forward/div curves, is a model setting to verify per product.

### EQ Vega

**Related Risk Reports:**
*   EQ Compute Vega (parallel shift vega)
*   EQ Term Vega (bucket shift vega)

**Market Data Movements:**
*   **EQ Compute Vega:** Equity Implied Volatility +/- 0.01
*   **EQ Term Vega:** Equity Implied Volatility +/- 0.01 by Tenor

**Risk Value Calculation:**
*   **Pricing Page:**
    `EqVega = (Premium (Vol+0.01) – Premium (Vol – 0.01)) * fx / 0.02`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **Simulation Page (in MX_EQD_Summary viewer):**
    `EqVega_i = (Premium (Vol_i + 0.01) – Premium (Vol_i – 0.01)) * Notional * fx / 2`
    `EqVega = Sum of EqVega_i`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **Simulation Page (in RSENSI_EQ_VEGA viewer):**
    `EqVegaGR_i = (Premium(Vol_i + 0.01) – Premium(Vol_i – 0.01)) * Notional / 2`
    `EqVegaBUC_i = EqVegaGR_i * fx`
    Where `fx`: 1 premium currency = units of underlying currency.

*   **In SpreadsheetLoadingTool:**
    `EQ VegaParallel = (Premium(Vol+0.01) – Premium(Vol – 0.01)) / 2`

---

## FX-Related Greeks

### FX Vega

**Related Risk Reports:**
*   FX Compute Vega
*   FX Term Vega

**Market Data Movements:**
*   FX vol + 0.01

**Risk Value Calculation:**
*   **Simulation Page (in RSENSI_FX_VEGAN viewer):**
    `FX vegaBUC = (Premium(vol_i + 0.01) – Premium(original)) * Notional`
    Term Vega is mapped from volatility tenors to displayed tenors using a specific rule: if `Display_Tenor(m) < FX_Vol_Tenor(n) <= Display_Tenor(m+1)`, then `FX_Vol_Tenor(n)` is mapped to `Display_Tenor(m+1)`.

> **Convention note.** FX vega matters for quanto products: the quanto FX rate's volatility and correlation with the underlying are risk factors, and FX vega captures the residual vega after the quanto adjustment is marked to market. FX vega tenors are bucketed to display tenors with an "upper mapping" rule as shown.

## Other Sensitivities

### Correlation Sensi

**Market Data Movements:**
*   For each eq-eq or eq-fx pair, the correlation entry is shifted +/- 0.01.

**Risk Value Calculation:**
*   **Pricing Page:**
    `CorrSensi = (Premium(Corr_i_j + 0.01) – Premium(Corr_i_j))`

*   **Simulation Page:**
    `CorrSensi = [Premium(Corr_i_j + 0.01) – Premium(Corr_i_j)] * Notional * F`

> **Convention note.** Correlation is material for baskets: worst/best-of, dispersion, and outperformance payoffs all depend on the eq-eq correlation matrix; quanto payoffs additionally depend on eq-fx correlations. Correlation matrices must be positive semi-definite and cover every pair actually used by the model.

### Dividend Sensi

**Risk Value Calculation:**
*   `DivSensi = (Premium(dividend * 1.01) – Premium(dividend)) / 10`

> **Convention note.** Dividend sensitivity is expressed per 1% dividend change on the dividend yield/amount curve. It matters for structures with long vega and positive payoffs (e.g., autocalls) that are sensitive to the forward path.

### IR PV01

This sensitivity is the same as EQ Term Rho.

**Related Risk Reports:**
*   EQ Term Rho

---

## Murex Risk Configuration

### Sensitivity Configuration Groups

In Murex, sensitivity configuration groups are used to selectively calculate greeks for performance optimization. These are defined under `Configuration -> Settings -> Securities Evaluation Settings`. Different groups can be created to compute only the necessary sensitivities for a given task (e.g., batch reporting, interactive pricing).

The main groups are:
*   **MAIN / SPB:** The standard configuration where all primary greeks (Delta, Gamma, Vega, Theta, Rho, FxVega, Sticky Strike) are enabled for in-house structured products.
*   **VAR / SPBNOSENSI:** A performance-oriented group where all major greeks are disabled. This is useful when only the P&L is required.
*   **EQDELTA:** Only EQ Delta is calculated. Used for the `eq_delta` batch report.
*   **EQVEGA:** Only EQ Vega is calculated. Used for the `eq_vega` batch report.
*   **IRDELTA:** Only Rho (IR Delta) is calculated. Used for the `IRPV01` batch report.

Ideally, all groups should have unnecessary sensitivities unticked to improve performance. Greek-enabled groups should be limited to what each consumer genuinely needs; over-computing greeks is the most common cause of batch window slippage.

*(Image description: The source document contains several screenshots illustrating the Murex UI for managing these configuration groups. They show lists of sensitivities with checkboxes to enable or disable their calculation for different product types within groups like 'MAIN', 'VAR', and 'EQDELTA'.)*

### Applying Configuration Groups

**In a Simulation:**
The evaluation configuration can be selected from the 'Securities' menu within the simulation screen. This is useful for debugging, for instance using the `SPBNOSENSI` group to isolate P&L issues from sensitivity calculations.

*(Image description: A screenshot shows the 'Securities' dropdown in the Murex simulation window, where a user can select the desired 'Evaluation configuration'.)*

**In a Trading Matrix Report:**
The configuration group is specified in the "reporting setup" of the report itself (e.g., when running a `risk_matrix` report).

*(Image description: Screenshots show the process of selecting a report in Murex and then navigating to its 'reporting setup' to choose the sensitivity configuration group.)*

---

## Specialized Calculations

### Greeks in SPE (Structured Product Engine)

For calculations within the SPE, certain adjustments are made, primarily removing the `fx` factor from some calculations.

*   **SS_Delta:** `[(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2* 1% * spot)] * Nominal * Eq_Spot`
*   **EqVega:** The per-tenor calculation remains `(Premium (Vol_i + 0.01) – Premium (Vol_i – 0.01)) * Notional * fx / 2`, but is also expressed as a percentage: `EqVega (%) = Sum of EqVega_i / Notional`.
*   **CorrSensi:** `(Premium(Corr_i_j + 0.01) – Premium(Corr_i_j -0.01)) / 2`
*   **DivSensi:** `(Premium(dividend * 1.1) – Premium(dividend*0.9)) / 2`
*   **IRPV01:** `[premium (zero_rate_i + 10bps) – premium (zero_rate_i – 10bps)] / 20`

To align delta direction with the institution's sell position, a `Position` multiplier (`-1` or `1`) is applied based on the product type. This multiplier is also applied to Vega, Dividend Sensi, IRPV01, and Corr Sensi.

### Greeks for Customized Index

For a deal involving a customized index, the greeks are first calculated at the index level and then decomposed to the individual underlying components.

An index is defined as: `Index_k = Σ(w_i^k * FX_i^k * S_i)`

1.  **Step 1: Calculate Index-Level Greeks:** `Delta(Index_k)`, `Gamma(Index_k1, Index_k2)`, and `Vega(Index_k)` are calculated for each index.
    `Delta(Index_k) = [(Premium(spot + 1%*spot) – Premium(spot - 1%*spot)) / (2* 1% * spot)] * 100`

2.  **Step 2: Decompose to Underlying Components:**
    *   **EQ Delta:**
        `EqDelta_Index_k(S_i) = w_i^k * FX_i^k * (Delta(Index_k) / 100) * Spot * fx_i`
        `EqDelta(S_i) = Σ(EqDelta_Index_k(S_i))` (summed over all indices)
        Where `fx_i`: 1 premium currency = units of underlying currency.

    *   **Gamma:**
        `Gamma(S_i, S_j) = Σ(w_i^k1 * (Σ(w_j^k2 * Gamma(Index_k1, Index_k2))))` (summed over all indices k1 and k2)

    *   **Vega:**
        `Vega_Index_k(S_i^Tj) = Σ(Vega(Index_k^Tidx_m) * (∂Vol(Index_k^Tidx_m) / ∂Vol(S_i^Tj)))` (summed over all index tenors)
        `Vega(S_i^Tj) = Σ(Vega_Index_k(S_i^Tj))` (summed over all indices)
        Where the partial derivative is calculated via finite difference.

**Decomposition Rules:**
*   **Decomposed to Underlyings:** EQ Delta, EQ Dividend Sensi, IRPV01
*   **At Index Level:** EQ Vega, CorrSensi, FX Vega

---

## Validating Greeks & Risk Quality Control

Bump-and-revalue greeks are only as good as the bumps, the repricing stability, and the market data. Set up a repeatable validation process:

1.  **Finite-difference sanity checks:** reduce the bump size and confirm the greek is stable (noise-dominated bumps indicate a pricing seed/path issue or too few paths). Compare central vs one-sided differences where applicable.
2.  **Path consistency:** valuations used for greeks must use a consistent random seed control — greeks are differences of prices; using different seeds per bump injects Monte Carlo noise. Murex handles this via the simulation framework, but new bespoke models must not re-seed per bump.
3.  **Cross-checks:**
    - For vanilla sub-cases of an exotic payoff, the model's greeks should approach the analytical greeks (Black-Scholes/local-vol).
    - Sum of term greeks ≈ parallel greek (e.g., sum of EqVega_i ≈ EqVega parallel).
    - Delta gap at a barrier should be consistent with the barrier's discrete/continuous monitoring probability.
4.  **Blind tests:** periodically recompute a sample portfolio with an independent python/spreadsheet implementation and compare greeks within agreed tolerances.
5.  **P&L attribution:** verify that explained P&L (from greeks × market moves) reconciles to actual P&L within tolerance; unexplained P&L signals missing risk factors (e.g., dividends, correlation, FX vega, barrier delta gap).
6.  **Fixed-point suite:** keep the per-product benchmark deals referenced in the product development guide as the regression baseline for greeks after any model/config change.

## P&L Explain & VaR Context

- **P&L explain:** decomposes daily P&L into contributions from each risk factor (spot, vol, rates, FX, dividends, correlation, theta). A working P&L explain is the strongest validation that the greeks set is complete and consistent for the product.
- **VaR / ETL:** computed on the risk-factor sensitivities with Monte Carlo or historical simulation. Synthetic/exotic products are frequently driven more by vega, correlation, and barrier-gap than by delta; ensure the VaR decorrelation and the sensitivity groups used by the VaR engine match the batch treasury settings.
- **Position direction:** the `Position` multiplier aligns reported greeks with the institution's convention (sell-side books report hedged risk from the client's position). Validate it per product after rollout.

## Exotics Risk Checklist

When a new structured equity product is introduced, confirm coverage of these risks before go-live:

- [ ] EQ Delta / Sticky Strike / Delta Gap (single & cross terms for baskets)
- [ ] EQ Gamma + cross gamma (worst/best of, dispersion)
- [ ] EQ Vega term structure (parallel vs term both available)
- [ ] FX vega and quanto adjustments (quanto products)
- [ ] Correlation sensi (eq-eq and eq-fx matrices complete & PSD)
- [ ] Dividend sensi
- [ ] IR PV01 / rho (parallel + term)
- [ ] Theta / carry
- [ ] Barrier gap behavior at discrete/continuous monitor dates
- [ ] Sensitivity groups sized to consumer needs; fixed-point suite green