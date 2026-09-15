# EQ Memory Range Accrual ("MemRaki")

## 1. Product Overview

The **EQ Memory Range Accrual ("MemRaki")** is a structured product that extends the standard **Raki** (Range Accrual with Knock-In and Knock-Out) by introducing a "memory" feature to its Knock-Out (KO) conditions.

While it shares the core range accrual payoff structure, its primary distinction is the innovative Memory Knock-Out mechanism. This feature requires a specific condition to be met at least once for *all* underlyings in the basket before a Knock-Out event is triggered.

## 2. Key Features

### Memory Knock-Out

This is the defining feature of MemRaki. The Knock-Out condition is not triggered by a single event on the worst-performing underlying. Instead, it relies on a "memory" of past events for each constituent of the basket.

-   **Local Memory KO:** A Local KO event occurs if the condition `S(t) / S(0) >= LocMemBar` has happened *at least once* for *every* underlying in the basket on their respective discrete observation dates.
-   **Global Memory KO:** Similarly, a Global KO event occurs if the condition `S(t) / S(0) >= GlbMemBar` has happened *at least once* for *every* underlying during the observation period (discrete or continuous).

If both a Local and Global KO are triggered on the same day, the event is treated as a Global KO.

### Range Accrual & Payoffs

-   **Periodic Payoffs:** The product pays a periodic coupon based on an accrual factor and a fixed coupon:
    `PayRate[i] = AccruRate[i] * (N1/N2) + FixCoupon[i]`
    -   `N1` is the number of days the accrual condition is met (e.g., `LowRange <= Indicator <= UpRange`).
    -   `N2` is the total number of days in the observation period.

-   **Knock-Out Payoff:** If a Memory KO event occurs, the deal terminates, and the payoff is:
    `PayRate[KO] = PayRate[i] + KO_Bonus + ReturnRatio`
    - The `PayRate[i]` is accrued up to the KO date.

-   **Maturity Payoff:** If no KO event occurs, the payoff at maturity depends on whether a final Knock-In (KI) event has happened (typically if the worst-performing stock is below a KI barrier). The payoff structure is similar to a standard Raki, potentially involving a call/put option on the underlying basket performance.

## 3. Murex Configuration

### Trade Representation

MemRaki deals are booked in Murex as a flexible exotic option:
-   **Family:** `EQD`
-   **Group:** `OPT`
-   **Type:** `FLEX`
-   **Flex Header:** `EqFlexMemR`

### Flex Blocks

The trade's structure is defined using five key flex blocks:

1.  **`KIKOSEL*` (Main Entry Block):**
    -   Activates and deactivates the Local KO, Global KO, and Knock-In features.
    -   Specifies initial fixing prices and dates.
    -   **Key Difference for MemRaki:** Introduces four new columns to track the memory KO status for each underlying:
        -   `LKO Locked` (checkbox): Checked if the Local KO condition has been met for the underlying.
        -   `LKO date`: The date the condition was met.
        -   `GKO Locked` (checkbox): Checked if the Global KO condition has been met.
        -   `GKO date`: The date the condition was met.
    -   These fields are typically updated automatically by the system but can be manually adjusted. A KO event is only triggered when all checkboxes in the respective "Locked" column are ticked.

2.  **`RGACCDATE` (Accrual Dates):**
    -   Defines the daily range accrual fixing dates used to calculate `N1` and `N2`.

3.  **`RGACCLKO+` (Period Definitions):**
    -   Generates the range accrual periods and payment schedules.
    -   Defines period-specific parameters like accrual ranges, Local KO barriers, and coupons.
    -   **Note:** Global KO coupons and barriers are also configured here, allowing them to vary by period.

4.  **`GLOBALKO*` (Global KO Dates):**
    -   Configures the observation schedule (discrete or continuous) for the Global KO condition.

5.  **`KNOCKIN*` (Knock-In Payoff):**
    -   Specifies the KI barrier, observation dates, and the final call/put option parameters for the payoff at maturity if no KO occurs.

### Pricing Payoff

-   The pricing script used for valuation is `EqFlexMemR`.

## 4. Pricing & Market Data

### GMP Configuration

To price a MemRaki deal, the following Generic Market Parameter (GMP) setup is required:
-   **TYPE:** `EQ_MONTECARLO`
-   **GROUP:** `EQ_MEMRAKI`

## 5. Operational Details & Constraints

### KO Status Tracking

Operationally, the `LKO Locked` and `GKO Locked` checkboxes in the `KIKOSEL*` flex block serve as the official record for the memory KO condition.
-   The system checks past equity fixings and automatically ticks these boxes and fills in the corresponding dates when an underlying meets its KO condition.
-   A full Local or Global Knock-Out event is only registered for the trade when all underlyings have their respective "Locked" boxes checked.

### Fixing & Cash Flows

-   **Fixing:** The logic for determining accrual (N1) and KO events is driven by comparison operators (`>=`, `>`, `<=`, `<`) specified in the `RGACCLKO+` block. This allows for precise control over how boundary conditions are handled.
-   **Cash Flows:** Accrual cash flows are handled as standard payments. In case of an early termination due to a KO event, the settlement flow includes the final accrued coupon, the KO bonus coupon, and the returned notional.

### Constraints

The MemRaki product has several key limitations in Murex:
-   **FX Rules:** Does not support composite, quanto, or other complex FX rules.
-   **Currency:** The basket currency must be the same as the premium currency.
-   **Principal:** Does not support quantity-based principal.
-   **Tenor:** Not supported for deals with tenors greater than two years.
-   **Underlyings:** Does not support single-equity instruments; it is designed for baskets.
