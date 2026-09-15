# Equity Digital Option

## 1. Product Overview

An Equity Digital Option is a simple, binary or "all-or-nothing" option. It provides a fixed, pre-determined payoff to the buyer if the underlying asset's price meets a specified condition at expiry. If the condition is not met, the option expires worthless.

- A **Digital Call Option** pays out if the underlying's final price is above the strike price at expiry.
- A **Digital Put Option** pays out if the underlying's final price is below the strike price at expiry.

---

## 2. Payoff Structure

The payoff is triggered if the option is in-the-money at expiry.

#### Call Option Payoff
```
If Final Price > Strike:
  Payoff = Notional
Else:
  Payoff = 0
```

#### Put Option Payoff
```
If Final Price < Strike:
  Payoff = Notional
Else:
  Payoff = 0
```

**Settlement Type:**
- **Cash:** The fixed `Notional` amount is paid.
- **Asset:** A number of shares equal to `Notional * asset` is delivered.

---

## 3. Murex Configuration

> **Reference:** This product is used as the worked example in the [Architecture Deep Dive](../../Introduction/Architecture_Deep_Dive.md) — see it for an end-to-end walkthrough of flex header → flex block → C++ mapping → generator → sensitivity configuration, with a code skeleton.

### Trade Representation
Digital Options are booked in Murex using the following hierarchy:
- **Family:** `EQD`
- **Group:** `OPT`
- **Type:** `FLEX`
- **Flex Header:** `EqFlexDOpt`

### Flex Blocks
The `EqFlexDOpt` header contains a single flex block named **`DIGITAL`**. Its purpose is to define the exercise behavior for the edge case where the fixing price is exactly equal to the strike price (`Fixing Price = Strike`). Dealers can configure this based on the specific terms of the trade.

### Model Input
The pricing model uses a combination of standard option parameters and the specific flex block setting:
- **Main Ticket Fields:**
    - Nominal/Quantity
    - Call/Put
    - Cash/Delivery
    - Maturity Date
    - Strike Price
- **Flex Block Field:**
    - `DIGITAL` block setting for behavior at the strike.

### Pricing Payoff
The payoff script used for pricing is **`EqFlexDOpt`**.

---

## 4. Pricing & Market Data

### Generic Market Parameters (GMP) Configuration
For pricing, the following GMP configuration is required for Monte Carlo simulation settings:
- **TYPE:** `EQ_MONTECARLO`
- **GROUP:** `EQ_DIGOPT`
- **Parameters:**
    - `Nb of Paths`: 10000
    - `Regression Order`: 1
    - `Cashflows`: 0

---

## 5. Operational Details & Constraints

### Market Operations
- **Exercise:** If the option is in-the-money at expiry, the Market Operations team runs the exercise procedure. For out-of-the-money deals, the option is either exercised or left to expire with a zero payoff.
- **Nominal Deals:** The `EXR` operation generates an "exercize" ticket where the default payoff is calculated. This amount can be amended if needed.
- **Quantity Deals:** The `EXR` operation generates an "exercize" ticket with a zero payment amount, which populates a new deal that can be modified.

### Constraints
The following limitations apply to this product configuration:

- **FX Rules:**
    - **Supported:** Quanto (`S.1-K`) and the default (no FX rule, where Premium Ccy = Underlying Ccy).
    - **Unsupported:** Basic (`S-K)X`) and Composite (`SX-K`).
- **Settlement Combinations:**
    - **Supported:** `Nominal + Cash` and `Quantity + Delivery`.
    - **Unsupported:** `Quantity + Cash`, `Nominal + Delivery`, and `Quantity + Delivery + Quanto`.
- **Tenor:** The maximum supported tenor for deals is **two years**.
