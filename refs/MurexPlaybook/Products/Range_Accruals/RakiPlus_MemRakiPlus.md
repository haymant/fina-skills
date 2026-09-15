# RakiPlus & MemRakiPlus

## 1. Product Overview

"RakiPlus" and "MemRakiPlus" are enhanced versions of the original Raki (EQ Range Accrual) and MemRaki (EQ Memory Range Accrual) products. While they leverage the same underlying pricing models as their predecessors (`EqFlexRaki` and `EqFlexMemR`), they introduce significant improvements to the booking methodology and operational procedures to address user feedback and new requirements.

The primary goal of these enhancements is to streamline the trade booking process, improve performance, and add flexibility without requiring a stressful migration of existing live deals. This is achieved by introducing new Flex Headers: **`EqFlexRakiP`** for RakiPlus and **`EqFlexMemRP`** for MemRakiPlus.

Deals are booked under Family = `EQD`, Group = `OPT`, Type = `FLEX`.

## 2. Key Enhancements

The core improvements of RakiPlus and MemRakiPlus focus on basket configuration, fixing procedures, and cash flow calculations.

### Basket Configuration (Dummy Baskets)

This is the most significant enhancement. The new methodology moves away from the previous requirement of using pre-defined baskets containing all specific underlying constituents.

*   **Old Method:** Required creating a unique, pre-defined Murex basket for every specific combination of stocks that a trade might use. This led to a large and cumbersome number of baskets to manage.
*   **New Method (Dummy Baskets):** This approach uses "dummy baskets" which are merely market-oriented placeholders. For example, a single dummy basket can be created for all HK-listed stocks (e.g., market `HKEX EQ`). This basket definition itself contains no individual stock components. The basket should be configured with `Multi currency rule = Quanto`.

The *actual* basket components for a specific trade are then defined directly within the **`KIKOSELECT`** flex block of that individual trade. This dramatically reduces the number of pre-defined baskets needed, simplifying setup and maintenance.

## 3. Payoff Formula

The payoff logic is similar to the original Raki/MemRaki products but is included here for completeness.

### For RakiPlus Note Form:

*   **Periodic Pay:** `PayRate[i] = AccruRate[i] * AccruFactor + FixCoupon[i]`
    *   `AccruFactor = N1/N2`, where N1 is the number of days the Accrual Indicator (WPS or All) is within the range.
*   **Local KO:** If `WPS >= LocBar Price`, the deal knocks out.
    *   `PayRate[KO] = PayRate[i] + LocKO Cpn + ReturnRatio`
*   **Global KO:** If `WPS >= GblBar Price`, the deal knocks out.
    *   `PayRate[KO] = PayRate[i] + GblKO Cpn + ReturnRatio`
*   **Maturity Pay (if no KO):**

    $$ \text{If knock in, } PayRate[Maturity] = PayRate[NumOfPeriods] + \begin{cases} \min \left\{ Cap\_KI1, \max \left[ Floor\_KI1, PR\_KI1 \times \left( \frac{WPS}{Strike\_KI1} - 1 \right) \right] \right\} + ReturnRatio, & \text{if } WPS \ge MaturBarrier \\ \min \left\{ Cap\_KI2, \max \left[ Floor\_KI2, PR\_KI2 \times \left( \frac{WPS}{Strike\_KI2} - 1 \right) \right] \right\} + ReturnRatio, & \text{otherwise} \end{cases} $$

    $$ \text{Else not knock in, } PayRate[Maturity] = PayRate[NumOfPeriods] + \max \left\{ \min \left[ Cap, PR\_NOKI1 \times \max \left( \frac{WPS}{Strike1} - 1, 0 \right) + PR\_NOKI2 \times \max \left( 1 - \frac{WPS}{Strike2}, 0 \right) \right], Floor \right\} + ReturnRatio $$

### For MemRakiPlus Note Form:

*   **Periodic Pay:** Same as RakiPlus.
*   **Local Memory KO:** If `S(t)/S(0) >= LocMemBar` occurs at least once for **all** underlyings, the deal knocks out.
    *   `PayRate[KO] = PayRate[i] + Local KO Bonus + ReturnRatio`
*   **Global Memory KO:** If `S(t)/S(0) >= GlbMemBar` occurs at least once for **all** underlyings, the deal knocks out.
    *   `PayRate[KO] = PayRate[i] + GlobalKO Bonus + ReturnRatio`
*   **Maturity Pay (if no KO):** The formula is identical in structure to RakiPlus, but applies the specific MemRakiPlus parameters.

    If knock in,
    $$
    \text{PayRate}[\text{Maturity}] = \text{PayRate}[\text{NumOfPeriods}] +
    \begin{cases}
      \min\left\{ \text{Cap\_KI1}, \max\left[ \text{Floor\_KI1}, \text{PR\_KI1} \times \left( \frac{\text{WPS(mat)}}{\text{Strike\_KI1}} - 1 \right) \right] \right\} + \text{ReturnRatio}, & \text{if } \text{WPS(mat)} \ge \text{MaturBarrier} \\
      \min\left\{ \text{Cap\_KI2}, \max\left[ \text{Floor\_KI2}, \text{PR\_KI2} \times \left( \frac{\text{WPS(mat)}}{\text{Strike\_KI2}} - 1 \right) \right] \right\} + \text{ReturnRatio}, & \text{otherwise}
    \end{cases}
    $$

    Else not knock in,
    $$
    \text{PayRate}[\text{Maturity}] = \text{PayRate}[\text{NumOfPeriods}] + \max\left\{ \min\left[ \text{Cap}, \text{PR\_NOKI1} \times \max\left( \frac{\text{WPS(mat)}}{\text{Strike1}} - 1, 0 \right) + \text{PR\_NOKI2} \times \max\left( 1 - \frac{\text{WPS(mat)}}{\text{Strike2}}, 0 \right) \right], \text{Floor} \right\} + \text{ReturnRatio}
    $$

## 4. Murex Configuration: Flex Blocks

The trade structure is defined by a series of flex blocks.

*   **`KIKOSELECT`**: This is the central block for defining the trade's key features.
    *   **Underlying Definitions:** This is where the constituents of the "dummy basket" are now specified for each trade, along with their reference prices.
    *   **KO/KI Activation:** Checkboxes to activate or deactivate Local KO, Global KO, and Knock-In conditions.
    *   **`Denomination`**: A new field for tuning cash flow rounding.
    *   **`ITM Payment`**: Specifies settlement method (cash or physical) if the deal is in-the-money at expiry.
    *   **FX Fixing Details**: For quanto exercises, columns (`FXPair`, `FXFixSource`, etc.) provide references for FX rate fixing.
    *   **MemRakiPlus specific:** Contains fields for tracking KO status (`LKO Locked`, `GKO Locked`).

*   **`RGACCDATE`**: Designates the range accrual fixing dates used to calculate N1/N2.

*   **`RGACCLKO` (for RakiPlus) / `RGACCLKO+` (for MemRakiPlus)**:
    *   Defines range accrual periods, payment dates, and LKO observation periods.
    *   Specifies period-specific barriers (Low/Up Range, Local KO) and coupons.
    *   Allows customization of GKO coupons and barriers for different periods.
    *   Sets the `Accrual Indicator` (Worst Performance or All Underlying).

*   **`GLOBALKO*`**: Configures the Global Knock-Out (GKO) observation dates (discrete or continuous) and the payment logic (Period End Date vs. KO Date).

*   **`KNOCKIN*`**: Configures the Knock-In (KI) event, including the KI barrier, observation dates, and the payoff structure (cap, floor, strike) for both KI and non-KI scenarios at maturity.

## 5. Operational Details

### Fixing Procedure

The fixing and archiving process has been simplified. Instead of grouping fixings by individual underlying security names, the procedure is now grouped by **markets**. This makes the process more efficient, as operators can handle all fixings for a given market (e.g., `HKEX EQ`) in a single operation. When opening deals for fixing, the fixing values are now automatically populated, requiring only a confirmation tick.

### Cash Flow Calculation

A new field, **`Denomination`**, has been introduced in the `KIKOSELECT` flex block. This field is used to adjust the rounding calculation for periodic cash flows.

The new cash flow formula is:
$$ \text{CashFlow}[i] = \text{Round} (\text{Denomination} \times \text{PayRate}[i], 2) \times (\text{Notional} / \text{Denomination}) $$

For comparison, the old method was equivalent to this formula with the `Denomination` always being equal to the `Notional`, which could lead to small rounding differences.

### Market Operations

Standard market operations such as `Expiry` and `Knock` are fully supported.

For a **Knock event** (either Local or Global), the settlement flow consists of two main components:
1.  **Notional Return:** A cash flow to square off the additional flow, equal to the `Return Ratio %` multiplied by the deal notional.
2.  **KO Settlement Coupon:** A cash flow representing the knock-out coupon. The calculation depends on the KO type and date (e.g., LKO coupon for the period, or a pro-rated accrual plus GKO coupon for a GKO event on a non-period-end-date).

When a knock event is processed in Murex, operators select the knocked barrier, and the system generates the corresponding settlement flows based on the pre-configured logic for notional return and coupon payments.

## 6. Constraints

The following limitations apply to RakiPlus and MemRakiPlus products:
*   **Single Equity:** Deals on a single stock are not supported; they must be basket-based.
*   **FX Rules:** Only `Basic` (where basket currency = premium currency) and `Quanto` (where basket currency <> premium currency) FX rules are supported. `Composite` is not.
*   **Principal:** The `Quantity` principal type is not supported.
*   **Tenor:** Maximum deal tenor is 25 months.
*   **Basket Size:** The basket is limited to a maximum of 6 underlying stocks.
