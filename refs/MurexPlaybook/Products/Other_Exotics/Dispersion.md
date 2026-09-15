# Equity Dispersion Swap (EQ Flex Dispersion)

## 1. Product Overview

An **Equity Dispersion Swap** (booked in Murex as **EQ Flex Dispersion**) is a structured exotic equity product whose payoff is derived from the "dispersion" of returns within a defined basket of stocks.

### Core Concept
The product pays a periodic coupon based on the average absolute difference between the performance of each individual stock in the basket and the average performance of the entire basket (the basket performance). 

It represents a volatility-based investment strategy that acts as a bet on high dispersion (low correlation or high idiosyncratic risk) among the constituent stocks in the basket:
- **High Dispersion (Low Correlation):** If the individual stocks move independently or in opposite directions, the absolute spreads from the average basket performance will be large, resulting in a higher coupon payout.
- **Low Dispersion (High Correlation):** If the stocks move in lockstep, the performance of each stock will be very close to the basket's average performance. The absolute spreads will be near zero, leading to a minimal or zero coupon payout.

---

## 2. Payoff Structure

The option pays out a periodic coupon ($PayRate$) at the end of each period $i$, bounded by a pre-defined Cap and Floor.

### Payoff Formula
For each observation period $i$ ($1 \leq i \leq \text{Number of Periods}$):

$$\text{PayRate}[i] = \min\left\{\max\left\{\text{Floor}[i], \text{PR}[i] \times \left(\text{Average of Absolute Spreads}_i - \text{Strike}[i]\right)\right\}, \text{Cap}[i]\right\}$$

Where:
- $\text{PR}[i]$ is the Participation Rate for period $i$.
- $\text{Strike}[i]$ is the strike parameter for period $i$.
- $\text{Floor}[i]$ and $\text{Cap}[i]$ are the floor and cap parameters for period $i$.

### Key Definitions & Calculations
The components of the payoff are defined as follows:

*   **Stock Performance:** The return of each individual stock in the basket relative to its initial value.
    $$\text{Stock Performance\_Period}[i] = \frac{\text{Share Price\_Period}[i]}{\text{Initial Share Price}} - 1$$

*   **Basket Performance:** The simple average of the individual stock performances within the basket.
    $$\text{Basket Performance\_Period}[i] = \text{Average of all individual Stock Performance\_Period}[i]$$

*   **Absolute Spread:** The absolute difference between an individual stock's performance and the overall basket performance.
    $$\text{Absolute Spread\_Period}[i] = \left|\text{Stock Performance\_Period}[i] - \text{Basket Performance\_Period}[i]\right|$$

*   **Average of Absolute Spreads:** The average of these absolute spreads across all $N$ underlyings in the basket.
    $$\text{Average of Absolute Spreads\_Period}[i] = \frac{1}{N} \sum_{k=1}^{N} \text{Absolute Spread\_Period}[i]_k$$

### Pricing Model Assumptions
- **Interest Rates (IR):** Assumed to be deterministic.
- **Equity Underlying:** Assumed to follow geometric Brownian motion (GBM) with local volatility calibrated to the implied volatility surface.

---

## 3. Murex Configuration

### Trade Representation
The deal is booked in Murex using the following hierarchy:
- **Family:** `EQD` (Equities)
- **Group:** `OPT` (Options)
- **Type:** `FLEX` (Flexible contracts)
- **Flex Header:** `EqFlexDisps` *(Pricing > Equities > Flex headers)*

#### Booking Style
To conform to established Murex booking conventions, the deal uses a dummy basket booking style:
- **Contract:** `BSKT SHARE`
- **Instrument:** `FLEX_USD`
- **Constraint:** Booking a single equity as the deal instrument is strictly unsupported.

---

### Flex Blocks
The `EqFlexDisps` flex header contains two essential flex blocks that define the trade structure and parameters:

#### 1. `KIKOSTRUCT`
The `KIKOSTRUCT` block is used to define the basket components (underlyings), their reference prices, and the deal's denomination.

*   **Underlying Definition:**
    - The flex block initially populates with **10 blank rows** indicating the default 10 underlyings.
    - Users can insert more rows if needed, up to a **maximum of 19 underlyings** (based on model validation limits). If there are fewer than 10 underlyings, the unused rows must be kept blank.
    - **Selection Procedure:** To define an underlying, the user clicks on an empty row, presses the space bar, and selects the stock from the populated `Sec-Mkt` ticket. Selection is performed using `SE_D_LABLE` (ensure `View = LABEL` is chosen to display this column).
    - **Name Auto-fill:** The underlying names appear blank upon selection but will automatically populate once the deal is saved and reopened.
    - **Reference Prices:** Reference prices must be keyed manually by the user based on the trade's initial pricing.

*   **Denomination:**
    - This field is keyed according to the term sheet. If the term sheet does not specify a denomination, it defaults to the **deal notional**.
    - *Note:* While this field has no impact on pricing or simulation, it directly affects the rounding of periodic cash flows.

> **Murex UI Visual (KIKOSTRUCT Flex Block):**
> *The KIKOSTRUCT interface displays a tabular layout where the user defines the underlyings (up to 19 rows) and enters their corresponding manually keyed reference prices. A separate Denomination field is displayed at the top or bottom of this block, which holds the currency-denominated unit size for cash flow rounding.*

> **Murex UI Visual (Sec-Mkt Ticket Selection):**
> *The stock selection window shows search filters and a result list with the `SE_D_LABLE` column highlighted under `View = LABEL`, ensuring that dealers can search and select correct stock codes across markets.*

---

#### 2. `PERIODS`
The `PERIODS` block provides the interface to generate the periodic schedule and define payoff parameters for each period.

*   **Schedule Generation:**
    - **Period End Date:** Generated dynamically using the formula:
      $$\text{Period End Date} = F(\text{Start Date}, \text{End Date}, \text{Schedule Gen.}, \text{Calendar})$$
    - **Payment Date:** Determined by shifting the Period End Date:
      $$\text{Payment Date} = F(\text{Period End Date}, \text{Shifter}, \text{Calendar})$$

*   **Payoff Parameters:**
    - For each period, users define: `Cap`, `Floor`, `PR` (Participation Rate), and `Strike`.

*   **Model Output Verification:**
    - In the pricing page, ticking the **"Model Output"** box reveals two calculated columns: `Cashflow` and `PayRate`. These values are dynamically computed by the pricing model for review.

> **Murex UI Visual (PERIODS Schedule Interface):**
> *The PERIODS flex block displays a grid containing the generated periods with columns for Start Date, End Date, Payment Date, and the period-specific payoff parameters (Cap, Floor, PR, Strike). The header contains parameters like Frequency, Calendar, and Shifter to generate the dates.*

> **Murex UI Visual (Model Output View):**
> *The pricing page screenshot displays the active valuation window with the "Model Output" option selected, revealing the read-only, model-calculated columns for Cashflow and PayRate alongside the user-defined parameters for each scheduled period.*

---

### Model Input
The complete product input consists of two parts:
1.  **Flex Block Fields:** All fields defined in `KIKOSTRUCT` and `PERIODS` blocks.
2.  **Financial Definition Fields:** Four main fields located on the standard Murex deal screen:
    - **Basket Market**
    - **Nominal (Notional)**
    - **Maturity Date**
    - **FX Rule & Premium Currency**
    *(Note: Other standard ticket fields such as call/put flag, strike, etc., are dummy fields and are ignored by the model).*

> **Murex UI Visual (Main Deal Ticket Inputs):**
> *The standard Murex deal ticket screen shows the main transaction details, highlighting the active fields: basket market, deal nominal, maturity date, and the FX rule/premium currency. Standard options fields (like call/put flag or standard strike) are greyed out or marked as dummy parameters.*

---

## 4. Operational Details & Constraints

### Fixing Procedure
*   EQ Dispersion requires **cut-off fixing** declarations on period end dates.
*   Archiving is grouped and processed by markets.
*   In the **"Opened deals"** view of the Murex fixing tool, the archived fixing values automatically display in the `Fixing Value` column. Users only need to verify and tick the active box to execute and finalize the fixings.

> **Murex UI Visual (Fixing & Archiving Tool):**
> *The market archiving window lists active market fixings grouped by region/exchange, allowing the operations team to run bulk updates for equity prices.*

> **Murex UI Visual (Opened Deals Fixing View):**
> *The fixing execution screen shows open trade IDs with their corresponding underlyings. The 'Fixing Value' column displays the retrieved market close prices, and check boxes are provided next to each record to confirm and write the fixing to the trade database.*

---

### Periodic Cash Flows
Because EQ Dispersion has neither daily accrual nor Knock-Out (KO) events, fixing is performed solely on the period end dates to declare the periodic cash flow.

To ensure consistency with Raki/MemRaki products, the cash flow calculation is adjusted based on the `Denomination` field defined in the `KIKOSTRUCT` block. The cash flow for each denomination unit is rounded to the nearest cent before scaling to the full notional:

$$\text{CashFlow}[i] = \text{Round}\left(\text{Denomination} \times \text{PayRate}[i], 2\right) \times \frac{\text{Notional}}{\text{Denomination}}$$

#### Rounding Impact Example
Consider a deal with:
-   $\text{Notional} = \$3,500,000$
-   $\text{Denomination} = \$10,000$
-   Calculated $\text{PayRate}[1] = 0.66667\%$

1.  **With Denomination Adjustment (Standard Booking):**
    $$\text{CashFlow}[1] = \text{Round}(\$10,000 \times 0.66667\%, 2) \times \left(\frac{\$3,500,000}{\$10,000}\right)$$
    $$\text{CashFlow}[1] = \text{Round}(\$66.667, 2) \times 350 = \$66.67 \times 350 = \$23,334.50$$

2.  **Without Denomination Adjustment (Denomination = Notional = \$3,500,000):**
    $$\text{CashFlow}'[1] = \text{Round}(\$3,500,000 \times 0.66667\%, 2) \times 1$$
    $$\text{CashFlow}'[1] = \text{Round}(\$23,333.45, 2) \times 1 = \$23,333.45$$

*Discrepancy:* There is a **\$1.05 discrepancy** due to rounding at the denomination level. This highlights why entering the correct `Denomination` from the term sheet is operationally critical.

> **Murex UI Visual (Denomination Input in KIKOSTRUCT):**
> *A close-up of the KIKOSTRUCT block highlighting the Denomination numeric input field, emphasizing its importance in the downstream rounding of periodic payments.*

---

### Market Operations
EQ Dispersion supports standard market operations. Murex Flex does not customize these operations, except for two basic validation checks:

*   **Supported Operations:**
    - **Unwind:** Allowed if:
      $$\text{Market Operation Date} \geq \text{Deal Trade Date}$$
    - **Expiry:** Allowed if:
      $$\text{Market Operation Date} \geq \text{Expiry Date}$$
      and the underlying equity fixings have been finalized on the expiry date.
    - **Restructuring** and **C&R (Close & Re-open)** are also supported.

*   **Unsupported Operations:**
    - **Exercise** and **Knock** operations are strictly disabled and cannot be performed.

---

### Constraints
The following limitations apply to the booking and setup of EQ Dispersion trades:

1.  **No Single Equity Instruments:**
    - Cannot book against a single stock. The trade must use a dummy basket style: `Contract = "BSKT SHARE"` and `Instrument = "FLEX_USD"`.
    *(Murex UI Visual: An error popup is shown if a dealer attempts to save a deal configured with a single equity instrument instead of a basket).*

2.  **FX Rules Limitation:**
    - Only **Basic** and **Quanto** FX rules are supported.
      - **Basic:** Supported if the basket currency matches the premium currency.
      - **Quanto:** Supported if the basket currency differs from the premium currency.
      - **Composite:** Strictly **unsupported**.
    *(Murex UI Visual: Selecting 'Composite' in the FX rule dropdown and attempting to save displays an error box: "FX Rule Composite not supported for this product").*

3.  **No Quantity Principal:**
    - Deals must be booked using **Nominal** principal. "Quantity" principal is not supported.
    *(Murex UI Visual: An error alert is triggered on saving if 'Quantity' is selected as the principal mode).*

4.  **Tenor Constraint:**
    - Maximum supported deal tenor is **37 months**.
    *(Murex UI Visual: If the difference between the Trade Date and Maturity Date exceeds 37 months, saving the trade fails with a validation error popup).*

5.  **Basket Size Constraint:**
    - The underlying basket can contain a maximum of **19 stocks**.
    *(Murex UI Visual: Attempting to save a basket containing more than 19 rows in KIKOSTRUCT generates an error indicating that the basket size exceeds model limits).*
