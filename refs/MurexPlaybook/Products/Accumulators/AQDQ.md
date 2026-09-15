# Equity Accumulator (AQ/DQ)

## 1. Product Overview

The Equity Accumulator (Option), often referred to as AQ/DQ, is a flexible, path-dependent option structure available in Murex. It supports both Accumulator (buy) and Decumulator (sell) variants.

The basic concept is that the holder periodically buys (in an Accumulator) or sells (in a Decumulator) a specific quantity of an underlying stock at a predetermined strike price. This obligation is conditional upon the underlying stock's price remaining within a specified range (i.e., not hitting a knock-out barrier).

## 2. Key Features

### Accumulator vs. Decumulator

The core difference lies in the direction of the trade and the type of knock-out barrier:
-   **Accumulator (AQ):** The holder *buys* the underlying. The deal has an **upper knock-out barrier (`Barr Up`)**. If the spot price touches or crosses this barrier, the deal terminates.
-   **Decumulator (DQ):** The holder *sells* the underlying. The deal has a **lower knock-out barrier (`Barr Down`)**. If the spot price touches or crosses this barrier, the deal terminates.

### Periodic Structure

The deal is divided into multiple periods, each defined by a schedule of dates:
-   **Observation Dates:** Dates on which the knock-out condition is monitored.
-   **Fixing Dates:** Dates within each period where the underlying's spot price is compared against the strike.
-   **Payment Dates:** Dates on which the settlement for each period occurs.

### Daily Fixing

On each fixing date within a period, the underlying's spot price is observed:
-   If the spot price is at or above the `Strike`, it is a **"Call Day,"** and the holder buys the `Call Qty`.
-   If the spot price is below the `Strike`, it is a **"Put Day,"** and the holder buys the `Put Qty`. (Note: For a standard accumulator, `Put Qty` is often set to double the `Call Qty`, creating a leveraged position on down days).

### Knock-Out (KO)

The deal terminates prematurely if the underlying's spot price breaches the knock-out barrier on any observation date.
-   For an **Accumulator**, this happens if `Spot >= Barr Up`.
-   For a **Decumulator**, this happens if `Spot <= Barr Down`.

Some periods can be marked as **Guaranteed**. If a KO event occurs, the holder is still entitled to the accruals for any remaining guaranteed periods, typically at the most advantageous quantity (e.g., `Call Qty` for an accumulator).

## 3. Murex Configuration

### Trade Representation

The product is booked in Murex as a flexible option:
-   **Family:** `EQD`
-   **Group:** `OPT`
-   **Type:** `FLEX`
-   **Flex Header:** `EqFlexAccu`

### Flex Blocks

The deal's economic terms are defined in two main flex blocks:

-   **`ACCUPAY`**: This is the primary block for defining the deal's structure.
    -   **Purpose:** Defines the period schedules, barriers, strike, and quantities.
    -   **Key Fields:**
        -   `Accu Type`: `Accumulator` or `De-accumulator`.
        -   `Barr Up` / `Barr Down`: The upper or lower knock-out barrier level.
        -   `Strike`: The fixed price at which shares are bought or sold.
        -   `Call Qty`: Quantity for "Call Days" (when `Spot >= Strike`).
        -   `Put Qty`: Quantity for "Put Days" (when `Spot < Strike`).
        -   **Schedule Generation:** Fields to define the start date, end date, and frequency of periods.
        -   `Guarantee Flag`: A checkbox for each period to mark it as guaranteed.

-   **`FIXING`**: This block defines the daily observation dates.
    -   **Purpose:** Generates the schedule of daily fixing and knock-out observation dates. It is also used to record the outcome (Call, Put, or KO) of past fixings.

### Pricing Payoff

-   The pricing model is invoked using the payoff script **`EqFlexAccu`**.

### Model Input

The pricing model uses inputs from the flex blocks along with standard deal ticket fields:
-   All fields from the `ACCUPAY` and `FIXING` blocks.
-   `Nominal`
-   `Delivery`
-   `Maturity Date`
-   `Premium Ccy`

## 4. Operational Details & Constraints

### Fixing Logic

Comparison checkboxes in the `ACCUPAY` block control the outcome when a fixing is exactly at a barrier or strike level:
-   `BarUpCompare` / `BarDownCompare`: Determines if the barrier is inclusive (`>=`, `<=`) or exclusive (`>`, `<`) for a KO event.
-   `StrikeCompare`: Determines if the strike comparison is inclusive (`>=`) or exclusive (`>`) for determining a Call vs. Put day.

### Market Operations

Standard Murex market operations are used for lifecycle events:
-   **Expiry (EXP):** Used by daily batch jobs to expire deals with no further cash flows.
-   **Early Termination (XIT):** Used to manually unwind a deal. The settlement amount defaults to the deal's market value but can be manually overridden.
-   **Exercise (EXR):** Used to settle the delivery of shares at the end of a period or upon a KO event.
    -   **Normal Period End:** The exercised quantity is the `Accued Qty` for that period (`Call Dates * Call Qty + Put Dates * Put Qty`), and the settlement price is the `Strike`.
    -   **Knock-Out (KO):** The logic is more complex. The deal is terminated. The exercise quantity includes accruals from past dates plus any guaranteed future accruals. The settlement price is the weighted average of the strikes for all periods being settled.

### Constraints

This Murex product has several limitations:
-   Does not support a basket of underlyings.
-   Does not support quantity-based principal (must be cash nominal).
-   Does not support cash settlement (physical delivery only).
-   Does not support any FX rules for the single underlying.
-   The maximum supported tenor is two years.
