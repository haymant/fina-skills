# Murex Structured Product Booking Overview

This document provides a high-level overview of the Murex platform architecture as it relates to equity structured products, and the common framework used to represent and book complex equity structured products within Murex. The concepts described here are shared across many products, including RakiPlus, Discrete Barrier Notes (DBrW), and Double No-Touch Range Accruals.

## 1. Murex Platform Context

Murex (MX.3) is a single-platform, single-database front-to-back system. For equity derivatives this means trade capture, pricing, risk, settlement, and reporting all operate on **one shared database** — there is no data duplication between front, middle, and back office.

### 1.1 Functional Modules

The platform is logically split into functional modules, all operating on the same data:

| Module | Responsibility |
| :--- | :--- |
| **Trade / Transaction Manager** | Trade capture, lifecycle events (expiry, exercise, knock, termination), versioning, validation. |
| **Risk Manager** | Sensitivity computation (greeks), scenario analysis, VaR/stress, trading matrices, LiveBook/RTPM. |
| **Settlement** | Cash flow management, payment instructions, nostro/vostro accounts, confirmations. |
| **Market Data** | Equity spot, volatility surfaces, dividend curves, FX rates, yield curves, correlation matrices. |
| **Datamart / Reporting** | Extracts structured data to downstream systems and regulatory/compliance reporting. |

### 1.2 Architecture Layers

- **Presentation layer:** Desktop (Java-based eTradepad/workspace) and web clients used by FO traders, MO risk managers, and BO operations.
- **Application layer:** Pricing engines, Monte Carlo simulation servers, risk servers, workflow engines, XVA/valuation engines. Computationally heavy tasks (end-of-day revaluation, XVA/PFE) are distributed over a grid.
- **Data layer:** The single database (Oracle or SQL Server) stores trades, market data, reference data, and configuration. Flex definitions, payoff scripts, model parameters (GMP), and risk configurations are all stored in this database as data — not hard-coded — which is what makes the platform configurable.

### 1.3 Implications for Development

Because configuration lives in the database, most "development" for a new product is a combination of:

1. **Configuration** (done in the GUI or via XML/import): flex headers/blocks, payoff scripts, GMP, market data, risk config.
2. **C++ code** (only where genuine new pricing logic is needed): mapping structures, pricing engines, payoff implementations.
3. **Scripting/validation rules** (MSL — Murex Scripting Language) for pre-trade checks.

This separation of configuration vs. code is the single most important mental model for Murex developers.

## 2. Murex Trade Representation

At the most basic level, all complex equity derivatives are booked using a standardized Murex instrument classification. This provides a consistent entry point for trade capture.

- **Family**: `EQD` (Equity Derivative)
- **Group**: `OPT` (Option)
- **Type**: `FLEX` (Flexible)

By classifying these trades as `FLEX`, Murex is instructed to use a customizable framework for defining the product's economic terms, rather than a rigid, pre-defined instrument type. The `FLEX` type triggers the display of the product's own "flex header" under the instrument's associated "payoff script" (see §5).

## 3. The FLEX Framework

The FLEX framework is the core of how these products are defined in Murex. It consists of two main components: Flex Headers and Flex Blocks.

-   **Flex Headers**: A Flex Header is a template that corresponds to a specific product type. It acts as a container for a collection of Flex Blocks. Examples include `EqFlexRakiP` (for RakiPlus products) and `EqFlexDBrW` (for Discrete Barrier products). In Murex terminology the header is the container ("Flex Header" / "Flex Page") that renders the product's booking screen.

-   **Flex Blocks**: A Flex Block is a user-interface component that groups together related economic parameters for a trade. For example, one block might define the periodic observation schedule, while another defines barrier conditions. By combining different blocks, a wide variety of products can be constructed. Each block can contain:
    - Simple fields (numeric, string, date, checkbox, dropdown)
    - Tables/grids (e.g., for underlying constituents, period schedules)
    - Conditional/visible field groups driven by other field values (dynamic UI)
    - Read-only, model-computed display columns

Common examples of Flex Blocks in equity structured products:
- `KIKOSTRUCT` / `KIKOSELECT`: Defines underlying constituents and high-level knock-in/knock-out features.
- `PERIODS` / `RGACCPERIO`: Defines the periodic schedule, coupons, and barriers for each period.
- `ACCUPAY`: Defines parameters for accumulator products, including quantities and strikes.
- `DISCBARR`: Defines the core barrier conditions (style, levels, rebates) for barrier-style products.
- `FIXINGDATE` / `RGACCDATE`: Generates the daily fixing/observation date schedules.
- `KNOCKIN*`, `LOCALKO*`, `GLOBALKO*`: Knock-in and knock-out configuration blocks.

The specific combination of Flex Blocks included in a Flex Header determines the exact features and data entry fields available to the user booking the trade.

### 3.1 How Flex is stored and rendered

Flex headers and blocks are defined by XML-like definitions stored in the Murex configuration database. At runtime, a parser (`MXFlex`) reads these definitions and renders the booking screen; the values entered by the user are stored as trade-specific attribute data. On the pricing side, a C++ "mapping" layer reads these stored attributes and populates C++ structures (`struct`/`class`) that the pricing model consumes. **The field names in the flex block definitions and the C++ structures must match exactly (case-sensitive).** This is one of the most common sources of bugs during product development.

## 4. Basket Booking Methodology

To avoid the operational overhead of creating a new, dedicated basket instrument for every multi-underlying trade, a "dummy basket" methodology is used.

Instead of defining a trade-specific basket (e.g., "Basket of AAPL, MSFT, GOOG"), the trade is booked against a generic, market-oriented instrument. This might be a dummy basket for a specific market (e.g., a basket for HK-listed stocks) or a universal instrument like `FLEX_USD`.

The actual basket constituents and their respective weights or reference prices are not defined in the basket instrument itself. Instead, they are specified directly within the **Flex Blocks** of the trade (typically in a block like `KIKOSTRUCT`). This approach significantly simplifies instrument setup and maintenance while retaining full descriptive power at the trade level.

Conventions for a correct dummy basket:
- Contract/type is typically `BSKT SHARE` (basket of shares) under family `EQD`.
- The instrument itself carries **no constituents**; it exists purely as a market/taxonomy anchor.
- FX/currency and market attributes of the dummy basket still matter (they define the basket currency and drive quanto behavior).
- All product-specific values (underlyings, reference prices, weights, denomination) live in the flex blocks.

For single-underlying products that still use this pattern, the trade is booked as a basket of size 1.

## 5. Payoff Configuration

The link between the trade booking screen, the underlying economic payoff, and the correct pricing model is established via a **Payoff Script** (also called the payoff "nomen" / payoff formula in Murex).

When a user initiates a new trade, they select a specific payoff script from a list in the pricing page (e.g., `EqFlexDblNT`, `EqFlexAccu`). This selection triggers several actions in Murex:

1.  **Loads the Correct UI**: Murex loads the Flex Header and its associated Flex Blocks corresponding to the selected payoff. This presents the trader with the correct fields for that specific product.
2.  **Assigns the Pricing Model**: The payoff script is linked to a specific pricing model **group** (e.g., `EQ_DBARW`), which in turn is mapped through the **GMP (Generic Market Parameters)** to a concrete pricing generator (e.g., an `EQ_MONTECARLO` Monte Carlo engine) and its configuration (number of paths, seed, regression options, etc.). This ensures that when the user requests a price, Murex uses the correct valuation engine and market-data assumptions for that product's unique features.

### 5.1 GMP (Generic Market Parameters) explained

GMPs are configuration objects that store the *parameters* of a pricing approach without hard-coding them. For each model group you define:

- The **generator / model type** used (e.g., Monte Carlo with local volatility, stochastic volatility, or analytical).
- Simulation settings: number of paths, random seed, regression order, cash-flow aggregation, variance-reduction flags.
- Which **market data** the model consumes (vol surfaces, curves, correlation matrices, dividend curves).

Changing GMP parameters (e.g., increasing the number of paths) is a data change, not a code change, and can be done without recompiling. This is a key operational advantage and a key governance risk (see Risk_Management.md on sensitivity configuration).

## 6. From Booking to Risk: the Data Flow

A high-level view of how a FLEX trade flows through the system:

```
Trade booking (Flex UI shows header/blocks for the payoff)
        │  fields stored as trade attribute data
        ▼
Payoff script lookup ──► Flex header + blocks rendered
        │                  C++ mapping reads attributes into structs
        ▼
Pricing model (model group via GMP) reads structs + market data
        │  Local Vol / MC engine values the payoff
        ▼
Premium + model outputs (cashflows, KO probabilties, greeks)
        │
        ▼
Risk / simulation servers compute sensitivities for the portfolio
        │
        ▼
Trading matrices, LiveBook/RTPM, batch reports, P&L explain
```

## 7. Key Governance Points

- **Config-as-data** means changes are instantly "production". Use environments (DEV → UAT → PROD) with controlled promotion (import/export of configuration) and sign-off.
- **Field-name coupling** between flex blocks and C++ mapping is fragile — protect it with automated checks (see product development guide).
- **Model/payoff coupling** via GMP must be regression-tested whenever a shared model group is modified, because many products may reuse the same group.
- Always keep a rolling set of **fixed-point benchmark trades** that must price within tolerance (e.g., 1e-6 premium, greeks within tolerance) after any configuration or code change.