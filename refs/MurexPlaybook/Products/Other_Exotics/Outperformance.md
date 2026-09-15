# Equity Outperformance Option (Oprf)

## 1. Product Overview

An **Equity Outperformance Option ("Oprf")** is an exotic equity derivative whose payoff is determined by the relative performance of one or more underlying equity assets (stocks or baskets) compared to a specific reference asset or compared to each other. 

- A **Call Option** pays out if the underlying stock or basket outperforms the reference asset.
- A **Put Option** pays out if the underlying stock or basket underperforms the reference asset.

Unlike standard options that depend on the absolute performance of an underlying, the Outperformance Option allows investors to capture pure relative performance, neutralizing general market direction or sector-wide movements.

---

## 2. Payoff Scenarios

The relative performance of the assets can be measured in several ways. These are configured using two key fields within the Murex trade structure: **`Basket Perf`** and **`PerfRank`**. 

Depending on these field settings, the payoff script supports four distinct performance scenarios:

### Worst Performance
The payoff is based on the worst-performing asset in the basket (excluding the reference asset itself) relative to the reference asset.
* **`Basket Perf`**: `Rank`
* **`PerfRank`**: `n` (where `n` is the number of non-reference underlyings in the basket).
* *Murex Screen Representation:* Displays a list of basket underlyings where the selected performance rank matches the total number of underlyings `n`, focusing the payoff on the laggard.

### Best Performance
The payoff is based on the best-performing asset in the basket relative to the reference asset.
* **`Basket Perf`**: `Rank`
* **`PerfRank`**: `1`
* *Murex Screen Representation:* Configured to select the top-performing underlying (Rank 1) from the basket for the payoff calculation.

### Middle Performance
The payoff is based on a specific mid-ranked asset in the basket relative to the reference asset.
* **`Basket Perf`**: `Rank`
* **`PerfRank`**: `k` (where `1 < k < n`).
* *Murex Screen Representation:* Configured to track the performance of the $k$-th ranked asset, providing a middle-of-the-pack performance measure.

### Average Performance
The payoff is based on the average performance of all assets in the basket relative to the reference asset.
* **`Basket Perf`**: `AVG`
* **`PerfRank`**: Not applicable (typically configured as `0` or left blank).
* *Murex Screen Representation:* Configured with average performance settings, where individual rankings are bypassed in favor of a flat basket average.

---

## 3. Murex Configuration

### Trade Representation
In Murex, the Outperformance Option is booked under the following contract hierarchy:
- **Family**: `EQD`
- **Group**: `OPT`
- **Type**: `FLEX`

### Basket Configuration
The underlying basket must be configured precisely to enable relative performance calculations:
- **Basket Type**: Must be set to **`List of Assets`** since the individual underlyings are tracked independently (no overall composite basket index calculation is performed).
- **Reference Asset**: Crucially, the **first stock in the basket list represents the reference asset** (index position `0`). The remaining stocks (positions `1` to `n`) are evaluated against this reference asset.
- **Market Data Feed**: Each underlying in the basket is linked to a specific Publisher (Archiving table) and CutOff. The historical fixing tables contain the fixings fed by a market data provider (e.g., Bloomberg or Reuters).
- **Contract Attachment**: The basket must be attached to an Equity Options contract.

*Murex Screen Visual Reference:*
- **Basket Definition Screen:** Shows the Basket Name and Description with Type set to 'List of Assets'. The underlyings table lists the constituent equities, their quantities, weights, and market data routing.
- **Basket Underlyings List Screen:** Shows the selected underlyings for the contract, where the very first entry (Position 0, highlighted in Murex) is identified as the reference asset.

### Flex Blocks
The trade structure is defined through a single flex block attached to the flex header. 

> **Developer Note:** It is necessary to match the names of the fields/blocks defined in the C++ mapping header file `eqpr/content/mx/MxMapping.h` with the names configured in Murex.

* **Flex Block Name**: `OPRF`
* **Flex Block Parameters**:
  - `Cap`: The maximum cap on the payoff as per the trade termsheet.
  - `Floor`: The minimum floor on the payoff as per the trade termsheet.
  - `Initial fix date`: The date when the initial reference prices of all underlyings are determined.
  - `Basket Perf`: `Rank` or `AVG` (determines the scenario type).
  - `PerfRank`: The rank position `k` (used if `Basket Perf` is set to `Rank`).

*Murex Screen Visual Reference:*
- **Flex Block Editor:** Displays the parameters (`Cap`, `Floor`, `Initial fix date`, `Basket Perf`, and `PerfRank`) and their data types within the `OPRF` block.
- **Flex Header Screen:** Displays how the `OPRF` block is mapped to the main flex template, allowing these exotic fields to be exposed directly on the deal ticket.

### Main Deal Ticket Fields
The complete Outperformance model configuration requires inputs across both the OPRF flex block and the main Murex deal screen. The seven core financial definition fields on the main screen are:
1. **Nominal / Quantity**: The principal size of the deal.
2. **Call / Put**: Determines whether the option pays on outperformance (Call) or underperformance (Put) relative to the reference asset.
3. **Cash / Delivery**: Settlement method (typically Cash).
4. **Maturity Date**: The final fixing/valuation date. For Oprf, there are only initial and final fixing dates to determine the payoff. The maturity date follows the conventions of the underlying market.
5. **Strike**: The strike performance barrier.
6. **Exercise Convention**: Can be used to redefine specific payment dates.
7. **Premium Currency**: The currency in which the premium is paid.

### Pricing Payoff
To price the deal, the user must select the payoff script corresponding to the **`Oprf`** flex header. Selecting this payoff script automatically displays the `OPRF` flex block and its fields on the pricing utility screen.

---

## 4. Pricing & Market Data

### Generic Market Parameters (GMP) Configuration
The pricing engine uses a Monte Carlo simulation. The required GMP configuration for pricing is:

* **TYPE**: `EQ_MONTECARLO`
* **GROUP**: `EQ_OPRF`

All other parameters (such as number of paths, regression order, and discount curves) are identical to the standard **Kiko Setting** (refer to the Kiko configuration documentation for full details).

*Murex Screen Visual Reference:*
- **GMP Configuration Screen:** Displays the assigned generator `EQ_MONTECARLO` mapped to the specific pricing group `EQ_OPRF` for proper model evaluation.

---

## 5. Operational Details

### Market Operations (MKT OP)

The following table summarizes the system behavior and conditions for lifecycle operations on the Outperformance Option:

| Operation | Allow Condition | Behavior / Procedures |
| :--- | :--- | :--- |
| **Expiry** | Only on Maturity Date, after the last fixing is completed. | Generates a cashflow with `[Final PayDate, 0]`. |
| **Exercise (EXR)** | Only on Maturity Date, after the last fixing is completed. | Generates a cashflow with `[Final PayDate, LastPayAmount]`. Front Office (FO) must manually trigger `EXR` to mature the deal, verifying that the payment date and payout amount are correct.<br><br>*Note on Funded Deals:* The principal amount will be reflected in a linked bond booking, and the bond will be left to expire naturally. |
| **XIT (Unwind)** | Any day after trade start. | Generates a cashflow with `[Current PayDate, Present Value]`. For a full trade unwind, insert a `BUY` bond booking to offset the original bond, and then execute the `XIT` operation on the flex deal. |
| **Restructure** | Any day during the trade lifecycle. | Follows default Murex behavior. Used to reduce the deal nominal for partial unwinds. Any unwind fees should be entered as additional flows in the newly restructured deal. |

*Murex Screen Visual Reference:*
- **Market Operations Booking Screen:** Displays the deal lifecycle interface showing the manual execution (`EXR`) option, with cashflow validation details for final payout.
