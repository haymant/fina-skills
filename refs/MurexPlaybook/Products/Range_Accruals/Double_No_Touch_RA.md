# EQ Double No-Touch RA

## 1. Product Overview

The **EQ Double No-Touch RA (Range Accrual)** is an exotic equity structured product that represents a powerful extension of the standard Raki range accrual family (which includes Raki, MemRaki, RakiPlus, and MemRakiPlus). 

Traditional range accruals in the Raki family typically support only a single-direction, "Up-and-Out" knock-out barrier structure. In contrast, the **EQ Double No-Touch RA**'s defining feature is its support for **Double Knock-Out ("Double-Out") barriers**. The deal will knock out early if the performance of the underlying asset/basket goes either above a specified upper barrier OR below a specified lower barrier, in addition to paying a coupon based on standard range accrual logic.

The product is booked in Murex as an equity flexible option using the dedicated flex header **`EqFlexDblNT`** (contained within the general `KikoSwap` flex template).

---

## 2. Key Features

### Double Knock-Out (Double-Out) Barrier
The product supports dual-barrier Knock-Out (KO) boundaries to manage downside and upside early termination:
*   **Local KO (LKO):** A periodic, discrete check performed on specific fixing dates at the end of each observation period. If the underlying performance breaches either the upper local barrier or the lower local barrier, the deal knocks out.
*   **Global KO (GKO):** A daily check that can be configured as either discrete (checked against the daily closing price) or continuous (checked against intraday pricing). If the underlying performance breaches either the upper or lower global barrier, the deal knocks out.

### Flexibility in Accrual Indicators
To calculate range accrual days, the product moves beyond simple worst-performer restrictions, offering four choices for the **Accrual Indicator**:
1.  **`Worst Performance` (WPS):** Based on the worst-performing stock in the basket.
2.  **`All`:** Based on the performance of all underlying components.
3.  **`Best Performance` (BPS):** Based on the best-performing stock in the basket.
4.  **`Any`:** Based on the performance of any underlying component.

### Independent KO Indicators
The KO indicators can be set separately and independently for the upper and lower barriers:
*   **`KOUppBarIndicat` (Upper Barrier KO Indicator):** Can be set to `Worst Performance` (`WPS`) or `Best Performance` (`BPS`).
*   **`KOLowBarIndicat` (Lower Barrier KO Indicator):** Can be set to `Worst Performance` (`WPS`) or `Best Performance` (`BPS`).

### Payoff Formulas

#### Periodic Accrual
Periodically, the product pays a range accrual coupon:
$$\text{PayRate}[i] = \text{AccruRate}[i] \times \text{AccruFactor} + \text{FixCoupon}[i]$$

Where:
*   $$\text{AccruFactor} = \frac{N_1}{N_2}$$
*   $$N_2$$ is the total number of observation days in the period.
*   $$N_1$$ is the number of days within that period where the selected **Accrual Indicator** remained within the range bounds ($$\text{LowRange} \le \text{Accrual Indicator} \le \text{UpRange}$$).

#### Local KO Event (LKO)
If a Local KO is triggered on a periodic fixing date:
$$\text{PayRate}[\text{KO}] = \text{PayRate}[i] + \text{LocKO Cpn} + \text{ReturnRatio}$$
*(Where the periodic accrual coupon $$\text{PayRate}[i]$$ is paid up to the KO date).*

#### Global KO Event (GKO)
If a Global KO is triggered on a daily or continuous basis:
$$\text{PayRate}[\text{KO}] = \text{PayRate}[i] + \text{GblKO Cpn} + \text{ReturnRatio}$$
*   **Mid-Period Trigger:** If the GKO occurs on a non-period-end-date, the accrual factor ($N_1$) is calculated up to the date the GKO happened. The cash flow paid is a combination of the prorated accrual cash flow, the GKO coupon, and the return ratio.
*   **Dual Triggering:** If both a Local KO and a Global KO occur on the same date, the event is treated as a Global KO. Accrual ($N_1$) runs up to the GKO date, and $N_2$ represents the total accrual days for the entire period.

#### Maturity Payoff (No KO)
Because **Knock-In (KI)** is not supported for Double No-Touch RA, if the deal does not knock out during its lifetime, the maturity payoff consists simply of the final period's range accrual coupon plus the return of the principal/notional.

---

## 3. Murex Configuration

### Trade Representation
*   **Family:** `EQD`
*   **Group:** `OPT`
*   **Type:** `FLEX`
*   **Flex Header:** `EqFlexDblNT`
*   **Booking Style:** **Dummy Basket**. The Front Office does not define basket components globally. Instead, market-oriented empty baskets (e.g., `HKEX EQ` dummy basket with user-defined type, constant weighting spot formula, theoretical pricing enabled, and volatility calculated by asset) are used. The specific underlying stocks and their initial reference prices are defined directly inside each individual trade's `KIKOSTRUCT` block.

### Flex Blocks

#### 1. `KIKOSTRUCT`
The central entry and definition block for the trade structure.
*   **Features selection:** Checkboxes are provided for `Local KO`, `Global KO`, and `Knock In`. For Double No-Touch RA, `Local KO` and `Global KO` are ticked, while `Knock In` is unticked and its associated fields are hidden.
*   **Basket Definition:** Users enter the underlying stocks in a component table by specifying `SE_D_LABLE` and keying in initial reference prices manually. Stock names are auto-populated upon saving.
*   **Quanto FX Parameters:** For Quanto trades, users provide `FXPair`, `FXFixSource`, `Timing`, `TimeZone`, and rate type (`Mid/Bid/Ask`) to support execution.
*   **Denomination:** Stores the deal denomination based on the term sheet. If unspecified, it defaults to the deal notional. It is used to adjust rounding in cash flow calculations:
    $$\text{CashFlow}[i] = \text{Round}(\text{Denomination} \times \text{PayRate}[i], 2) \times \frac{\text{Notional}}{\text{Denomination}}$$
*   **ITM Payment:** Specifies `Delivery` or `Cash` settlement upon in-the-money expiry.

> **UI Screenshot Annotation - `KIKOSTRUCT` Block:**
> *The Murex trade entry layout displays the KIKOSTRUCT flex block panel on the left containing checkboxes for Local KO and Global KO, with the Knock In checkbox disabled. Below it, a grid represents the constituent basket where multiple columns define SE_D_LABLE, reference prices, and Quanto FX parameters like FXPair and FXFixSource.*

#### 2. `FIXINGDATE`
Generates the schedule of daily range accrual fixing dates.
*   Uses a linked formula schedule generator: `FixingDate = F(Start Date, End Date, Schedule Gen, Calendar)`.
*   Includes a **"Past Fixing"** checkbox. Ticking this reveals `past periodKO` and `past DailyKO` columns to track past events and execution.

#### 3. `RGACCPERIO`
The core configuration block defining period dates, range accrual parameters, and double-barrier conditions.
*   **Range Accrual Bounds:** Specifies the range parameters: `LowRange`, `UpRange`, and their comparison operators (`LowRangeCompare`, `UpRangeCompare`).
*   **Double Barriers:**
    *   **Local KO Barriers:** `LocBarUp` and `LocBarLow` are defined along with their comparison operators (`LocKOUppBarComp`, `LocKOLowBarComp`).
    *   **Global KO Barriers:** `GblBarUp` and `GblBarLow` are defined along with comparison operators (`GblKOUppBarComp`, `GblKOLowBarComp`).
*   **KO Indicators:** Specifies `KOUppBarIndicat` and `KOLowBarIndicat` independently for the upper and lower barriers.
*   **Accrual Indicator:** Specified in the `Acc Indicator` dropdown (WPS, All, BPS, or Any).
*   **Past N1N2Fixing:** Checkbox to display N1 and N2 values for past periods.
*   **Model Output:** Checkbox that displays `KO Prob` (combined KO probability calculated by the model), `Cashflow`, and `AccruRatio` columns inside the pricing interface.

> **UI Screenshot Annotation - `RGACCPERIO` Double Barriers:**
> *The RGACCPERIO block contains a tabular grid displaying consecutive accrual periods. Dedicated columns define the double barriers: range accrual bounds (LowRange/UpRange), Local KO upper and lower barriers (LocBarUp/LocBarLow), and Global KO upper and lower barriers (GblBarUp/GblBarLow), alongside their respective indicator selectors and comparison operator dropdowns.*

#### 4. `DAILYKO`
Specifies daily observation schedules for Global KO.
*   Observation dates are generated using a linked formula: `Observ. Date = F(Start Date, End Date, Schedule, Calendar)`.
*   **Choice KO Barr:** Configured as `Discrete` (monitored against closing prices) or `Continuous` (monitored intraday).
*   **GKO Coupon Payment Methods:**
    1.  `Period_End_Date`: Coupon is paid on the Payment Date of the next periodic LKO block.
    2.  `KO_Date`: Coupon is paid on the exact GKO observation/payment date.

#### 5. `KNOCKIN*`
Contains six default fields but is not used because the Knock-In feature is not supported for this payoff.

#### 6. `IRLEGP`
Designed for payoffs that support swap form. It is ignored since Double No-Touch RA only supports Note form.

---

## 4. Operational Details & Constraints

### Fixing Logic (Barrier Crossings)
Murex uses six comparison checkboxes on the `RGACCPERIO` block to handle calculations when fixings land exactly at the barrier level:

| Feature / Bound | Field Name | Comparison Options | Operational Logic |
| :--- | :--- | :--- | :--- |
| **Low Range Accrual** | `LowRangeCompare` | `>=` or `>` | If `>=`, accrues if Indicator $\ge$ LowRange. If `>`, accrues only if Indicator $>$ LowRange. |
| **Up Range Accrual** | `UpRangeCompare` | `<=` or `<` | If `<=`, accrues if Indicator $\le$ UpRange. If `<`, accrues only if Indicator $<$ UpRange. |
| **Local KO Upper** | `LocKOUppBarComp` | `>=` or `>` | If `>=`, triggers LKO if Upper Indicator $\ge$ LocBarUp. If `>`, triggers only if strictly greater. |
| **Local KO Lower** | `LocKOLowBarComp` | `<=` or `<` | If `<=`, triggers LKO if Lower Indicator $\le$ LocBarLow. If `<`, triggers only if strictly less. |
| **Global KO Upper** | `GblKOUppBarComp` | `>=` or `>` | If `>=`, triggers GKO if Upper Indicator $\ge$ GblBarUp. If `>`, triggers only if strictly greater. |
| **Global KO Lower** | `GblKOLowBarComp` | `<=` or `<` | If `<=`, triggers GKO if Lower Indicator $\le$ GblBarLow. If `<`, triggers only if strictly less. |

---

### Market Operations

#### Expiry
If the trade does not knock out, it runs to expiry. Murex generates a single cash flow combining any final option payout and the return of the principal/notional.

#### Knock
When a Knock-Out event is triggered, operators execute the **`Knock`** market operation:
1.  **Comment Box:** This is a crucial audit and diagnostic field. The comment box displays the exact barrier triggered (e.g., indicating whether the Upper or Lower barrier caused the Knock-Out).
2.  **Flow Tabs:** Shows two generated cash flows:
    *   **Return Notional:** Calculated as `Notional * Return Ratio %`.
    *   **Rebate / Coupon:** 
        *   *Scenario 1 (GKO on non-period-end-date):* Rebate = GKO coupon + pro-rated Accrual Cash Flow.
        *   *Scenario 2 (LKO or GKO on period-end-date):* Rebate = KO coupon.
        *   *Scenario 3 (No KO triggered on or before the market operations date):* Rebate is NIL.

> **UI Screenshot Annotation - Market Operation Ticket:**
> *The Market Operation confirmation window shows the status of the early termination event. A text field labeled 'Comments' displays audit text stating which specific barrier (Upper or Lower) was breached on the fixing date. The Cash Flows grid below lists the Return Notional payment alongside the calculated Rebate cash flow.*

---

### Product Constraints

1.  **No Single Equity:** Booking on a single stock is not supported. It must be booked using the dummy basket structure (even if modeled around a single underlying, it must be represented as a basket).
2.  **FX Rules:** Only `Basic` (where basket currency = premium currency) and `Quanto` (where basket currency $\neq$ premium currency) FX rules are supported. `Composite` FX rule is **NOT** supported.
3.  **No Quantity Principal:** Only nominal-based principal is supported. Quantity-based principal cannot be booked.
4.  **Maximum Tenor:** Restricted to a maximum tenor of **25 months**.
5.  **Maximum Basket Size:** The dummy basket can contain at most **6 underlying stocks**.
