# Discrete Barrier Worst-of / Nth Performer Product (DBrW)

## 1. Product Overview

The **Discrete Barrier Worst-of / Nth Performer Product (DBrW)** is the institution's strategic equity barrier framework. It is designed to handle both single-underlying and multi-stock basket barrier structures within a unified, flexible model.

Implemented fully within the Murex **FLEX** framework, the DBrW framework consolidates and replaces older, less efficient implementations:
*   **DBrS** (Discrete Barrier Single Underlying)
*   **Legacy DBrW**

### Strategic Objectives of the Redesign
1.  **Simplify Booking Workflows:** Streamline trade entry and life-cycle management.
2.  **Unify Product Lines:** Combine single-stock and basket products under a single booking and pricing paradigm.
3.  **Support Richer Structures:** Allow advanced barrier, step-up/step-down, and observation schedule configurations.
4.  **Operational Consistency:** Match the design patterns used in other strategic basket products, such as *RakiPlus* and *MemRakiPlus*.

---

## 2. Product Economics & Key Features

A discrete barrier option is a structured option whose existence or payoff depends on whether the underlying asset(s) cross predefined barrier levels on specified monitoring dates.

### 2.1 Supported Barrier Types
The DBrW framework supports both Knock-In and Knock-Out styles, including double barriers:

*   **Knock-In (KI) Structures:** The option becomes active only after a barrier is breached.
    *   **Up-and-In (UI)**
    *   **Down-and-In (DI)**
    *   **Double-In (Double Barrier)**
*   **Knock-Out (KO) Structures:** The option is terminated (extinguished) if a barrier is breached.
    *   **Up-and-Out (UO)**
    *   **Down-and-Out (DO)**
    *   **Double-Out (Double Barrier)**

### 2.2 Basket Performance Methodology
The performance of the basket can be linked to either the worst-performing stock or the $K$-th best-performing stock.

*   **Worst Performer:** The final payoff is linked to the asset with the lowest return in the basket.
    *   *Example:* For a basket containing AAPL ($+15\%$), TSLA ($-10\%$), and MSFT ($+8\%$), the Worst-of Performance is $-10\%$.
*   **K-th Best Performer:** The asset performance is ranked from 1 (Best Performer) to $N$ (Worst Performer, where $N$ is the number of constituents). The user specifies the rank $K$ during booking, subject to:
    $$1 \le K \le N$$
    *   *Example:* For $K=1$, the payoff is linked to the Best Performer. For $K=N$, the payoff is linked to the Worst Performer.

### 2.3 Rebate Timing
When a barrier event occurs, an associated rebate may be paid out. The framework supports two settlement timing options:
*   **Pay At Knock (`AT_Knock`):** The rebate is settled and paid immediately upon the occurrence of the knock event.
*   **Pay At Maturity (`On_Maturity`):** The rebate payment is deferred and settled on the final scheduled maturity date of the transaction.

### 2.4 Notional Return Configuration
The product can be structured as either an option-style or note-style payoff using the **Notional Return** configuration field. This parameter determines whether the principal repayment participates in the final settlement formula, allowing users to tailor the instrument's risk profile.

### 2.5 Additional Features
*   **Barrier Observation Frequency:** Supports **Daily Monitoring** (via explicit fixing dates), **Periodic Monitoring** (at period ends), or **Continuous Monitoring** (using Min-Max fixing indexes).
*   **Quanto Capabilities:** Full support for Quanto structures, allowing settlement in a premium currency different from the basket currency. Users can configure FX details such as:
    *   *FX Pair* (e.g., SGD/HKD)
    *   *FX Fix Source* (e.g., BFIX)
    *   *Fixing Time* (e.g., 0400)
    *   *Time Zone* (e.g., New York)
    *   *Rate Type* (e.g., Mid)

---

## 3. Murex Configuration

### 3.1 Trade Representation
In Murex, all DBrW transactions are booked as FLEX contracts under the following taxonomy:

| Murex Field | Configuration Value |
| :--- | :--- |
| **Family** | `EQD` |
| **Group** | `OPT` |
| **Type** | `FLEX` |
| **Flex Header** | `EqFlexDBrW` |
| **Instrument** | `FLEX_USD` |

#### The "Dummy Basket" Approach
To simplify operational support and speed up product onboarding, DBrW utilizes **market-oriented dummy baskets** (using a generic instrument like `FLEX_USD`) rather than requiring a unique pre-defined Murex equity basket for every transaction. The specific underlying constituents are defined directly inside the trade’s flex blocks, reducing system noise and administrative overhead.

### 3.2 Flex Blocks Structure
The economic terms and schedules of a trade are defined across three primary Flex blocks:

```
┌────────────────────────────────────────────────────────┐
│                      EqFlexDBrW                         │
└──────────────────────────┬─────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌───────────┐     ┌───────────┐     ┌───────────┐
   │ DISCBARR  │     │ FIXINGDATE│     │  PERIODS  │
   └───────────┘     └───────────┘     └───────────┘
```

#### 1. DISCBARR Block
This is the core block defining the trade's economic properties. It features a dynamic user interface where fields are shown or hidden based on the selected barrier style to prevent booking mistakes:

| Selected Style | Visible Fields | Hidden Fields |
| :--- | :--- | :--- |
| **Double Barrier** | Up Barrier, Up Rebate, Down Barrier, Down Rebate | None |
| **Up Barrier Only** | Up Barrier, Up Rebate | Down Barrier, Down Rebate |

#### 2. FIXINGDATE Block
This block is used to define the schedule for daily barrier monitoring. The daily monitoring schedule is generated dynamically based on the formula:
$$\text{FixingDate} = F(\text{StartDate}, \text{EndDate}, \text{ScheduleGenerator}, \text{Calendar})$$

#### 3. PERIODS Block
Partitions the life of the trade into distinct observation windows (periods). This enables the creation of complex step-up or step-down barrier structures, where each period can have its own:
*   Strike Level
*   Barrier Level
*   Scheduled Rebate

Periods and payment schedules are generated via:
$$\text{PeriodEndDate} = F(\text{StartDate}, \text{EndDate}, \text{ScheduleGenerator}, \text{Calendar})$$
$$\text{PaymentDate} = F(\text{PeriodEndDate}, \text{Shifter}, \text{Calendar})$$

### 3.3 Underlying Definition
Underlyings and their initial reference levels are entered directly within the trade's flex blocks:
*   **Initial Template:** Displays 4 empty underlying rows by default (users can insert more as needed).
*   **Reference Price:** Entered manually during booking to establish the strike reference for performance calculation.
*   **Basket Size Constraint:** Supports a maximum of 6 stocks.

---

## 4. Pricing & Market Data

### 4.1 GMP Configuration
Pricing and risk calculation are driven by the Monte Carlo pricing model configured within the General Market Parameters (GMP):

*   **Model Type:** `EQ_MONTECARLO`
*   **Model Group:** `EQ_DBARW`

### 4.2 Monte Carlo Engine Parameters
The Monte Carlo simulation engine uses the following baseline configuration to handle single-underlying, basket, worst-of, $K$-th performer, and quanto payoffs:

| Parameter | Baseline Value |
| :--- | :--- |
| **Number of Paths** | 30,000 |
| **Regression Order** | 1 |
| **Cashflows** | 1 |

---

## 5. Operational Details & Constraints

### 5.1 Cashflow Generation Logic
Unlike traditional structured notes that pay periodic coupons on a fixed schedule, DBrW is purely **event-driven**. Cashflows are triggered exclusively by barrier events:

```
Barrier Event (Knock-In / Knock-Out) ──> Cashflow Generation
```

#### Knock-In Rebate and Notional Flows
If a scheduled rebate is non-zero and a knock-in event is triggered:
*   The rebate cashflow (and potentially the notional repayment) is generated.
*   **Pay At Knock:** Cashflows are generated immediately upon trigger.
*   **Pay At Maturity:** Cashflows are deferred and processed at final maturity.

This event-driven framework significantly reduces system noise and simplifies settlement processing.

### 5.2 Payoff Mechanics Formulas

#### Knock-In Structures (Up-and-In, Down-and-In, Double-In)
*   **If a knock-in event occurs:**
    $$\text{Option Payoff} = \text{Final Option Value}$$
    $$\text{Rebate} = \text{Scheduled Rebate}$$
*   **If knock-in never occurs:**
    $$\text{Option Payoff} = 0$$
    $$\text{Rebate} = 0$$

#### Knock-Out Structures (Up-and-Out, Down-and-Out, Double-Out)
*   **If a knock-out event occurs:**
    $$\text{Option Payoff} = 0$$
    $$\text{Rebate} = \text{Scheduled Rebate}$$
*   **If knock-out never occurs:**
    $$\text{Option Payoff} = \text{Final Option Value}$$
    $$\text{Rebate} = 0$$

#### Settlement Payment Formula
The final cash settlement is calculated as:
$$\text{Payment} = (\text{Pay\_Option} + \text{Pay\_Rebate} - \text{ReturnRatio}) \times \text{Notional}$$
*Note: The notional repayment follows the same settlement timing (At Knock vs. On Maturity) as the rebate.*

### 5.3 Market Operations

#### 1. Expiry Processing
A trade progresses to expiry under two circumstances:
*   *Case 1:* A Knock-In event has occurred.
*   *Case 2:* A Knock-Out event has never occurred.

At expiry, the system aggregates the `Option Payoff` and the `Notional Return` into a single combined settlement cashflow.

#### 2. Knock Processing
For Knock-Out structures, a dedicated **Knock** market operation is executed to:
1.  Read the relevant fixing levels.
2.  Evaluate whether a barrier has been breached.
3.  Generate rebate cashflows (if applicable).
4.  Archive the knock event details. For double-barrier structures, the system records whether the `Upper Barrier Triggered` or `Lower Barrier Triggered`.

#### 3. Continuous Monitoring (Min-Max Fixing)
For continuous monitoring, Murex performs a **Min-Max fixing** rather than checking the standard daily close. The fixing index is set to:
*   `MIN` (for downside barriers)
*   `MAX` (for upside barriers)

#### 4. Knock Status Tracking
The system automatically tracks and updates the operational state variable:
$$\text{Already KnockIn} = \text{TRUE}$$
This provides a clear, high-level operational summary of the deal status.

### 5.4 Product Constraints & Restrictions

The framework enforces several system and risk boundaries:

*   **Instrument Booking Restrictions:**
    *   *Single Equity Instrument:* Not Supported (single-underlying structures must be booked as a basket of size 1 using the dummy basket template).
    *   *Quantity Principal:* Not Supported.
    *   *Composite FX Rule:* Not Supported.
*   **Supported FX Rules:**
    *   *Basic:* Supported (Basket Currency $=$ Premium Currency).
    *   *Quanto:* Supported (Basket Currency $\neq$ Premium Currency).
*   **Portfolio & Tenor Restrictions:**
    *   *Maximum Basket Size:* 6 stocks.
    *   *Maximum Tenor:* 25 months.
