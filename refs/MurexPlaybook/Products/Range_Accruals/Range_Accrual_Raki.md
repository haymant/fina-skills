# EQ Range Accrual (Raki)

## 1. Product Overview

The EQ Range Accrual, commonly known as "Raki," is a structured product whose payoff is linked to the performance of one or more underlying equities.

The core concept is that the investor receives a periodic coupon based on the number of days the underlying's performance stays within a pre-defined range. The periodic payment is calculated as:

`PayRate = AccrualRate * AccrualFactor + FixedCoupon`

Where the `AccrualFactor` represents the proportion of days in the period that the underlying remained within the specified range.

## 2. Key Features

### Range Accrual
The key component of the periodic coupon is the `AccrualFactor`, calculated as `N1/N2`:
-   **N2:** The total number of observation days in a period.
-   **N1:** The number of days within that period where the `Accrual Indicator` (typically the Worst-Performer) stayed between the `LowRange` and `UpRange` barriers.

### Knock-Out (KO)
The product can be knocked out, terminating early, based on two types of KO events. The KO indicator is typically the Worst-Performing Security (WPS).

-   **Local KO (Periodic):** A discrete check performed at the end of each observation period. If the WPS is at or above the `LocBar Price`, the deal knocks out.
-   **Global KO (Daily/Continuous):** A check that can be either discrete (daily) or continuous. If the WPS is at or above the `GblBar Price`, the deal knocks out. If both a Local and Global KO occur simultaneously, it is treated as a Global KO.

### Knock-In (KI)
At maturity, the final payoff depends on whether a Knock-In event has occurred during the life of the trade. A Knock-In event happens if the WPS drops below the `KnockIn Barrier`. This can be monitored on a discrete or continuous basis.

### Payoff Formulas

-   **Periodic Pay:**
    `PayRate[i] = AccruRate[i] * (N1/N2) + FixCoupon[i]`

-   **Local KO Event:**
    `PayRate[KO] = PayRate[i] + LocKO_Cpn + ReturnRatio`
    *(The `PayRate[i]` component is accrued up to the KO date)*

-   **Global KO Event:**
    `PayRate[KO] = PayRate[i] + GblKO_Cpn + ReturnRatio`
    *(The `PayRate[i]` component is accrued up to the KO date)*

-   **Maturity Payoff (if no KO):**
    -   **If KI Event Occurred:** `Notional * Min(Cap, Max(Floor, Final_Fixing / Initial_Fixing - KI_Strike))`
    -   **If No KI Event Occurred:** `Notional * NoKI_Pay`

## 3. Murex Configuration

### Trade Representation
The Raki product is booked in Murex as a flexible option:
-   **Family:** `EQD`
-   **Group:** `OPT`
-   **Type:** `FLEX`
-   **Flex Header:** `EqFlexRaki`

### Flex Blocks
The deal's structure is defined using five dedicated flex blocks:

-   **`KIKOSEL*`:** This is the main entry block. It allows users to activate or deactivate the Knock-Out and Knock-In features. It also contains fields for the `Return Ratio` (the notional percentage paid out on a KO event) and the initial fixing prices for the underlyings.

-   **`RGACCDATE`:** Used to define the schedule of daily observation dates for the range accrual feature. The system uses these dates to calculate the N1/N2 accrual factors. A screenshot from the source document shows a calendar-based schedule generator for these dates.

-   **`RGACCLKO`:** This block configures the periodic details. Users define period start/end dates, payment dates, accrual rates, fixed coupons, and local KO barriers. It also displays the calculated N1/N2 status for each period. A screenshot in the source shows this block with fields for period generation and a table listing each period's parameters.

-   **`GLOBALKO*`:** Configures the Global KO feature. It defines the GKO observation schedule (start/end dates, frequency) and whether the check is `Discrete` or `Continuous`. It also determines the payment timing upon a GKO event, which can be either at the `Period End Date` or the specific `KO Date`.

-   **`KNOCKIN*`:** Defines the parameters for the Knock-In event at maturity. This includes the KI barrier level, observation dates, and the parameters for the final payoff formula (Cap, Floor, KI Strike) depending on whether a KI event occurred.

### Pricing Payoff
To price the deal, the `EqFlexRaki` payoff script must be selected in the trade entry screen.

## 4. Pricing & Market Data

### GMP Configuration
The deal requires a specific Generic Market Parameter (GMP) setup for pricing via Monte Carlo simulation:
-   **TYPE:** `EQ_MONTECARLO`
-   **GROUP:** `EQ_RAKI`
A screenshot in the source document shows GMP settings, including `Nb of Paths = 30000`.

## 5. Operational Details & Constraints

### Fixing
Four comparison checkboxes on the `RGACCLKO` block control how fixings at the boundary are handled:
-   **`LowRangeCompare` / `UpRangeCompare`:** Determine whether the fixing is inclusive (`>=`, `<=`) or exclusive (`>`, `<`) of the range barriers for accrual calculation.
-   **`LocKOBarCompare` / `GblKOBarCompare`:** Determine whether a fixing equal to the barrier triggers a Knock-Out event (`>=`) or not (`>`).

### Cash Flows
-   **Accrual Payments:** Generated as payment flows on period end dates.
-   **Local KO:** The final accrual cash flow is generated separately from the early termination settlement flow, which consists of the Local KO coupon plus the returned notional.
-   **Global KO:** If the KO occurs on a period end date, the flow handling is similar to a Local KO. If it occurs mid-period, the final accrual cash flow is calculated up to the KO date and paid as part of the single early termination settlement flow.
-   **Maturity:** Accrual flows are always handled separately from the final expiry settlement flow.

### Constraints
The following limitations apply to this product structure in Murex:
-   The basket currency must equal the premium currency.
-   Supported FX rules for single underlyings are Basic `(S-K)X` and Quanto `(S*1-K)`. The Composite rule `(S*X-K)` is not supported.
-   The principal must be a nominal amount; "Quantity" principal is not supported.
-   The maximum supported tenor for the deal is two years.
