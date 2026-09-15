# Barrier Option (BAROPT)

## 1. Product Overview

The **BAROPT** product represents a standard Vanilla Barrier Option. A barrier option is a type of exotic option where the payoff depends on whether the underlying asset's price reaches a predetermined barrier level during the life of the option.

The option can either be "knock-in," meaning it only comes into existence if the underlying hits the barrier, or "knock-out," meaning it is extinguished if the barrier is hit. The barrier itself can be "up" (above the initial price) or "down" (below the initial price).

## 2. Booking and Data Flow

Trades are specified via a structured JSON payload, which is then processed and mapped to Murex fields for booking. The JSON is typically divided into two main sections:

*   `Specs`: Defines the high-level characteristics of the product, such as the option type (Call/Put), barrier style (Knock-In/Knock-Out), and observation type (Continuous/Discrete).
*   `Variables`: Contains the specific economic details of the trade, including dates, prices, quantities, and counterparty information.

This structure allows for a standardized way to capture trade details before they are transformed into the Murex native format.

## 3. Key Parameters & Murex Mapping

The following table summarizes the mapping of the most critical JSON fields to their corresponding Murex functions.

| JSON Field | JSON Section | Description | Murex Target |
| :--- | :--- | :--- | :--- |
| `Cond0` | `Specs` | Buy or Sell | `Eq.Option.1.Buy/Sell` |
| `Cond1` | `Specs` | Call or Put | `Eq.Option.1.Payout` |
| `StrikePrice` / `StrikeLevel` | `Variables` | The strike price/level of the option. | `Strike` |
| `EQBarrierType` | `Variables` | The barrier style (e.g., Down and In). | `Barrier_Type` |
| `BarrierLevelPercent` / `KOLevel` | `Variables` | The barrier level, often as a percentage. | `KO` |
| `Cond3` | `Specs` | Barrier observation type (Continuous/Discrete). | `DiscrContinuos` |
| `TradeDate` | `Variables` | The execution date of the trade. | `Trading Date` |
| `FinalFixingDate` | `Variables` | The final valuation date for the option. | `Eq.Option.1.Option expiration period` |
| `MaturityDate` | `Variables` | The maturity date of the contract. | Maps to Final Valuation Date |
| `Currency` | `Variables` | The currency of the trade. | Trade Currency (`MAR_CCY`) |
| `Quantity` | `Variables` | The number of options. | `TrancheOrder.FilledQuantity` |
| `Nominal` | `Variables` | The notional amount of the trade. | `Nominal` |
| `Portfolio` | `Variables` | The Murex portfolio for booking. | `Eq.Option.1.Portfolio` |
| `ClientCounterpartyLabel` | `Variables` | The client-side counterparty. | `Eq.Option.1.Counterpart` |

### Underlying Specification

The underlying asset is defined within the `UnderlyingTableList` array in the `Variables` section. Each object in this array defines one underlying with the following key fields:

*   `T_TickerR`: The Murex ticker for the underlying instrument (e.g., `GOOGL.O`). This maps to `Eq.Option.1.Instrument`.
*   `T_InitialPrice`: The initial spot price of the underlying asset.
*   `T_MXCalendar`: The exchange calendar to be used for date calculations (e.g., `NYSE`). This maps to the `CDR` field.

## 4. Murex Configuration

Based on the mapping data, the booking in Murex is configured as follows:

*   **Murex Product:** The trade is booked under the generic `BAROPT` product type.
*   **Murex Instrument:** The instrument used is a flexible one, typically `FLEX_USD` or a similar variant, which allows for the custom parameters defined in the JSON to be attached.
