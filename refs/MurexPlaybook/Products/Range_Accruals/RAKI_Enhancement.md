# RAKI Enhancement Overview

This document outlines several advanced features and enhancements that can be added to RAKI-style (Range Accrual) products, such as Coupon Barriers, Memory Coupons, and Memory/Non-Memory Knock-Out (KO) mechanisms. These features provide additional flexibility and payoff tailoring for structured investment products.

## Enhanced Features

### Coupon Barrier
The basic periodic payment rate is calculated as:
`PayRateInter1[i] = AccruRate[i] * AccruFactor + FixCoupon1[i]`

Where:
*   `AccruFactor = N1/N2`
*   `N2` is the total number of observation days in the period.
*   `N1` is the number of days where the `Accrual Indicator` (which can be the Worst-Performing Security `WPS` or all underlying performances) remains within the `[LowRange, UpRange]` bounds.

When the **Coupon Barrier** feature is active:
*   The actual periodic payment rate depends on the Worst-Performing Security (`WPS`) relative to a pre-defined `Coupon Barrier`.
*   If `WPS` is below the coupon barrier, the periodic payment is affected (typically not paid in that period).
*   If the Coupon Barrier is not present, `PayRateInter[i] = PayRateInter1[i]`.
*   *Note: The Coupon Barrier / Memory Coupon feature and the Global KO feature are mutually exclusive and cannot co-exist in the same product.*

### Memory Coupon
The **Memory Coupon** feature allows investors to recover unpaid coupons from previous periods if the payoff conditions are met in a future period:
*   **WPS >= Coupon Barrier:** If the Worst-Performing Security is at or above the coupon barrier in period `i`, the accumulated unpaid coupons from previous periods are paid out.
    `PayRate[i] = PayRateInter1[i] + … + PayRateInter1[j]`
    where `j` is the first period after the immediate preceding period before `i` with `WPS >= Coupon barrier` (i.e., `WPS[j-1] >= Coupon barrier[j-1]` and `WPS[k] < Coupon barrier[k]` for all `j <= k <= i-1`).
*   **WPS < Coupon Barrier:** If `WPS` is below the coupon barrier, the coupon for period `i` is not paid (treated as 0) and is accumulated for future periods.
*   If there is no Memory Coupon feature, `PayRate[i] = PayRateInter[i]`.

### Memory KO vs. Non-memory KO
The product supports two distinct Knock-Out (KO) mechanisms, both of which can have Local (discrete observation on fixing dates) and Global (daily discrete or continuous observation) barriers.

#### Memory KO
Memory KO tracks the performance of each individual underlying security over time rather than relying solely on the Worst-Performing Security (`WPS`) on a specific date.
*   **Trigger Condition:** A Knock-Out is triggered only if the performance ratio $S_k(t)/S_k(0) \ge \text{Barrier}$ has occurred **at least once for all underlyings** in the basket.
*   **Local Memory KO:** Monitored discretely on fixing dates. Triggered if $S_k(t)/S_k(0) \ge \text{LocMemBar}$ has occurred at least once for all underlyings.
*   **Global Memory KO:** Monitored daily or continuously. Triggered if $S_k(t)/S_k(0) \ge \text{GlbMemBar}$ has occurred at least once for all underlyings.
*   **Payoff on KO:** `PayRate[KO] = PayRate[i] + KO Bonus + ReturnRatio`

#### Non-memory KO
Non-memory KO is the standard mechanism based directly on the Worst-Performing Security (`WPS`) on a given observation date.
*   **Trigger Condition:** A Knock-Out is triggered if `WPS >= Barrier`.
*   **Local KO:** Monitored discretely on fixing dates. Triggered if `WPS >= Barrier`.
*   **Global KO:** Monitored daily or continuously. Triggered if `WPS >= Barrier`.
*   **Payoff on KO:** `PayRate[KO] = PayRate[i] + KO Bonus + ReturnRatio`

#### KO Interactions
*   If both Local KO and Global KO are triggered, it is treated as a Global KO.
*   For Global KO, the range accrual (`N1`) is calculated up to the date the Global KO event occurred (with `N2` representing the total accrual days for the whole period).
*   Payment can be made either at the `Period End Date` or the specific `KO Date`.

## Payoff Logic Summary

The overall payoff structure of an enhanced RAKI product integrates range accrual, optional coupon barrier/memory mechanics, and KO/KI events:

1.  **Periodic Coupon Flow:**
    *   Determined by range accrual over the period (`AccruFactor`).
    *   If Coupon Barrier and Memory Coupon are enabled, payments are conditional and can accumulate across periods.
2.  **Early Termination (Knock-Out):**
    *   The trade terminates early if either a Memory KO or Non-Memory KO condition is met (via Local or Global barriers).
    *   Upon KO, the investor receives the accrued periodic rate, any KO Bonus, and the Return Ratio.
3.  **Maturity Payoff (if no KO occurred):**
    The payoff at maturity is determined by a hierarchy of conditions:

    *   **If `WPS >= Lower Call Strike`:**
        A standard call-like payoff is applied.
        $$ \text{PayRate}[\text{Maturity}] = \text{PayRate}[\text{NumOfPeriods}] + \min\{\text{Cap\_up}, \max[\text{Floor\_up}, \text{PR\_up} \times (\frac{\text{WPS}}{\text{Strike\_up}} - 1)]\} + \text{ReturnRatio} $$

    *   **If `WPS < Lower Call Strike` and a Knock-In has occurred:**
        The payoff depends on whether the final `WPS` is above or below a maturity barrier.
        $$ \text{PayRate}[\text{Maturity}] = \text{PayRate}[\text{NumOfPeriods}] + \begin{cases} \min\{\text{Cap\_KI1}, \max[\text{Floor\_KI1}, \text{PR\_KI1} \times (\frac{\text{WPS}}{\text{Strike\_KI1}} - 1)]\} + \text{ReturnRatio}, & \text{if } \text{WPS} \ge \text{MaturBarrier} \\ \min\{\text{Cap\_KI2}, \max[\text{Floor\_KI2}, \text{PR\_KI2} \times (\frac{\text{WPS}}{\text{Strike\_KI2}} - 1)]\} + \text{ReturnRatio}, & \text{otherwise} \end{cases} $$

    *   **If `WPS < Lower Call Strike` and no Knock-In has occurred:**
        A cliquet-style payoff is applied.
        $$ \text{PayRate}[\text{Maturity}] = \text{PayRate}[\text{NumOfPeriods}] + \max\{\min[\text{Cap}, \text{PR\_NOKI1} \times \max(\frac{\text{WPS}}{\text{Strike1}} - 1, 0) + \text{PR\_NOKI2} \times \max(1 - \frac{\text{WPS}}{\text{Strike2}}, 0)], \text{Floor}\} + \text{ReturnRatio} $$
    
    A Knock-In (KI) event happens if `WPS < Knock-In Barrier`, monitored either discretely on fixing dates or continuously from the deal start to end date.
