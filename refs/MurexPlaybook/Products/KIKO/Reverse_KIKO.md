# EQ Reverse Kiko ("KioV")

## 1. Product Overview

The **EQ Reverse Kiko ("KioV")** is a path-dependent, equity-linked structured product featuring both Knock-Out (KO) and Knock-In (KI) barriers. It is designed and developed based on the existing `KikoPlus` product framework, inheriting most of its core features but reversing the option's knock-in and knock-out logic.

Unlike standard KIKO structures where barriers are typically monitored against the worst-performing underlying (WPS), the **Reverse KIKO (KioV)** triggers are driven by the **Best Performer (BPS)** of the underlying equity basket (or single underlying). The payoff at maturity is highly conditional on whether a Knock-Out event, a Knock-In event, or neither occurred during the option's lifetime.

---

## 2. Product Economics & Payoff

The product's economics consist of periodic Knock-Out observations during its lifetime and a conditional payoff at maturity if no Knock-Out occurs.

### Knock-Out Triggers (Local & Global KO)
A Knock-Out event can be triggered via two types of barrier observations, both monitored against the **Best Performer (BPS)** of the basket:

1.  **Local KO (LKO):** Checked periodically on discrete observation dates. A Local KO occurs if:
    $$\text{BPS} \le \text{LocBar Price}$$
    *   **LKO Payoff:** Upon occurrence, the contract terminates early, and the holder receives a KO payment rate:
        $$\text{PayRate}[\text{KO}] = \text{LocKO Cpn} + \text{ReturnRatio}$$
        *(where `ReturnRatio` is the notional return percentage defined in the `KIKOSEL*` block, and `LocKO Cpn` is the periodic Local KO coupon).*

2.  **Global KO (GKO):** Checked on a daily/continuous basis during the observation period. A Global KO occurs if:
    $$\text{BPS} \le \text{GblBar Price}$$
    *   **GKO Payoff:** Upon occurrence, the contract terminates early, and the holder receives:
        $$\text{PayRate}[\text{KO}] = \text{GblKO Cpn} + \text{ReturnRatio}$$
        *(where `GblKO Cpn` is the Global KO coupon configured in the `LOCALKO*` block).*

**Note on Simultaneous Events:** If both a Local KO and a Global KO occur on the same day, the event is treated as a Global KO.

### Maturity Payoff
If the product survives to maturity without triggering any Knock-Out (neither Local nor Global KO has occurred), the final payoff depends on whether a **Knock-In (KI)** event occurred:

*   **Knock-In Event:** A Knock-In event is triggered if the Best Performer (BPS) exceeds the Knock-In Barrier at any point during the observation period (either via discrete observation dates or continuous monitoring):
    $$\text{BPS} > \text{Knock-In Barrier}$$
    *   **KI Payoff:** If a KI event occurs, the payoff is typically calculated as:
        $$\text{Maturity Payoff} = \max\left(\text{Floor}, \min\left(\text{Cap}, \text{BPS} - \text{Strike}\right)\right)$$
        *(where Cap, Floor, and Strike are parameters specified in the `KNOCKIN*` block).*

*   **No Knock-In Event:** If no KI event occurs during the lifetime of the option, the payoff is a fixed rebate rate:
    $$\text{Maturity Payoff} = \text{Rebate}$$

### Payoff Summary Table / Formula
$$\begin{cases} 
\text{LocKO Cpn} + \text{ReturnRatio} & \text{if Local KO occurs }(\text{BPS} \le \text{LocBar Price}) \\
\text{GblKO Cpn} + \text{ReturnRatio} & \text{if Global KO occurs }(\text{BPS} \le \text{GblBar Price}) \\
\max\left(\text{Floor}, \min\left(\text{Cap}, \text{BPS} - \text{Strike}\right)\right) & \text{if No KO, and KI occurs }(\text{BPS} > \text{KI Barrier}) \\
\text{Rebate} & \text{if No KO and No KI occurs}
\end{cases}$$

---

## 3. Murex Configuration

### Trade Representation
Reverse Kiko transactions are booked in Murex as flexible equity options with the following details:
-   **Family:** `EQD` (Equity Derivatives)
-   **Group:** `OPT` (Options)
-   **Type:** `FLEX` (Flexible Exotic Options)
-   **Flex Header:** `EqFlexKioV`

### Flex Blocks
The trade structure and financial terms of the Reverse Kiko are configured using four specialized flex blocks. These block names end in an asterisk (`*`) to distinguish them from the standard KikoPlus (`+`) blocks:

1.  **`KIKOSEL*` (Main Selection Block):**
    *   Serves as the main entry point to enable or disable the KO and KI features (Local KO, Global KO, and Knock In) via checkboxes.
    *   Defines the `Return Ratio (%)` for the early termination notional return.
    *   Specifies the initial fixing date.
    *   **Critical Distinction:** Dealers specify the **initial fixing prices** within this block. This is a key difference from the KikoPlus product.
    *   *UI Image Description:* The user interface displays checkboxes for activating LKO, GKO, and KI, along with input fields for Return Ratio (%) and a dedicated grid for entering initial fixing prices for each basket member.

2.  **`LOCALKO*` (Local KO Configuration Block):**
    *   Generates the periodic (Local) KO observation and effective date schedules based on start date, end date, frequency, and calendar.
    *   Contains the `LocKOBarCompare` and `GblKOBarCompare` comparison checkboxes to determine KO events and handle accrual for Back Office (BO) operations.
    *   **GKO Coupon Customization:** Crucially, period-specific GKO coupons and barriers are configured here, allowing for different GKO coupons and barriers in different periods.
    *   **Special Visibility Cases:**
        *   *No GKO:* If GKO is disabled in `KIKOSEL*`, the `GblKOBarCompare` checkbox and the `GblKO Cpn` and `GblBar Price` columns are hidden.
        *   *No LKO:* If LKO is disabled in `KIKOSEL*`, the `LocKOBarCompare` checkbox and the `LocKO Cpn`, `LocBar Price`, and `LocalKO` columns are hidden. (Observation dates are still generated to define the periods for GKO coupons and barriers).
        *   *No LKO & No GKO:* If both are disabled, one period is generated with a dummy barrier of 99999 and the observation date set to maturity, following the standard KikoPlus behavior.
    *   **Model Outputs:** A "Model Output" checkbox reveals three additional columns for pricing page analysis: `KO Prob` (future KO probability), `KI Prob` (future KI probability), and `CashFlow` (actual and expected cash flows).
    *   *UI Image Description:* Displays fields for date generation (Start/End Date, Schedule Gen., Calendar) and comparison checkboxes, alongside a tabular sheet containing columns for observation/effective dates, local and global barriers/coupons, and historical knock-out status.

3.  **`GLOBALKO*` (Global KO Configuration Block):**
    *   Configures the daily (Global) KO observation and effective date schedules.
    *   Supports choosing between **Discrete** (triggers based on the close price on observation dates) and **Continuous** monitoring (triggers based on intra-day prices monitored during trading).
    *   Supports two payment timing methods upon a GKO event:
        *   **Period End Date:** Payment is made on the effective date of the active period defined in the `LOCALKO*` block.
        *   **KO Date:** Payment is made on the GKO trigger date, shifted by the specified calendar days (using effective dates generated in the `GLOBALKO*` block).
    *   *UI Image Description:* Shows configuration fields for continuous/discrete monitoring, payment timing selection (Period End Date vs. KO Date), and a table for global KO tracking.

4.  **`KNOCKIN*` (Knock-In Configuration Block):**
    *   Configures the KI barrier (%) and schedule generator fields.
    *   Like GKO, supports **Discrete** and **Continuous** checking options for the KI event.
    *   Contains parameters for the payoff at maturity if KI occurs: **Cap**, **Floor**, and **Knock-In Strike (%)**.
    *   Contains parameters for when neither KI nor KO occurs, such as **Rebate** or default payoff parameters.
    *   *UI Image Description:* Shows fields for specifying KI barrier, discrete/continuous selection, the KI schedule grid, and inputs for Cap, Floor, Strike, and Rebate.

### Pricing Payoff Script
The pricing is driven by the Murex payoff script **`EqFlexKioV`**. Selecting this payoff on the main Murex trade screen automatically loads the `EqFlexKioV` flex header and its four underlying flex blocks.
*   *UI Image Description:* Illustrates the main Murex transaction booking screen with `EqFlexKioV` selected in the payoff formula field and the associated flex blocks displayed.

---

## 4. Pricing & Market Data

### Model & GMP Configuration
To enable Monte Carlo valuation for the Reverse Kiko, a dedicated Generic Market Parameter (GMP) group must be configured:
*   **TYPE:** `EQ_MONTECARLO`
-   **GROUP:** `EQ_KIKOREVS`
-   **Paths and Cash Flows:** In the production environment, the simulation typically uses:
    *   `Nb of Paths = 30000`
    *   `Cashflows = 1`
*   *UI Image Description:* Displays the Murex GMP configuration window for `EQ_KIKOREVS` with 30,000 paths and cashflow calculation enabled.

### Summary of Model Input Fields
The valuation model takes inputs from:
1.  All data fields configured in the four flex blocks (`KIKOSEL*`, `LOCALKO*`, `GLOBALKO*`, `KNOCKIN*`).
2.  Three critical financial definition fields on the main Murex screen:
    *   `Nominal` (Notional amount)
    *   `Maturity Date`
    *   `Premium Ccy` (Premium currency)
    *   *Note:* Other standard option fields (like standard strike, call/put flags, etc.) are treated as dummy fields.
*   *UI Image Description:* Shows the main transaction screen highlighting the Nominal, Maturity Date, and Premium Currency fields as the key inputs, and other fields as unutilized.

---

## 5. Operational Details & Constraints

### FX Rules Support
The product supports specific FX rules depending on whether the trade uses a basket or a single underlying instrument:

| FX Rule | Basket Underlyings | Single Underlying | Description |
| :--- | :---: | :---: | :--- |
| **Default (No FX Rule)** | **Supported** | **Supported** | Premium currency matches the underlying currency. (Baskets can also fulfill a quanto payoff if basket currency does not match constituent currencies). |
| **$(S-K) \times X$ (Basic FX Rule)** | *Not Supported* | **Supported** | Standard option payoff scaled by the FX rate. |
| **$(S \times X - K)$ (Composite)** | *Not Supported* | *Not Supported* | Payoff with the strike converted using a variable FX rate. |
| **$(S \times 1 - K)$ (Quanto)** | *Not Supported* | **Supported** | Option payoff converted at a pre-agreed fixed FX rate. |

*   *UI Image Description:* Shows screens demonstrating how the basic FX rules and Quanto FX rules are selected and configured in Murex for single underlyings.

### Constraints & Limitations
To ensure correct valuation and system stability, the following constraints must be strictly adhered to (unsupported configurations will fail validation):

1.  **Basket Currency must equal Premium Currency:**
    *   $$\text{Basket Ccy} = \text{Premium Ccy}$$
    *   *UI Image Description:* Displays Murex error warnings triggered when the basket currency and premium currency are mismatched.
2.  **No Composite FX Rule for Single Underlyings:**
    *   The composite FX rule $(S \times X - K)$ is completely unsupported for both baskets and single underlyings in the current release.
    *   *UI Image Description:* Displays validation alerts when trying to assign a composite FX rule.
3.  **No Quantity Principal:**
    *   Quantity-based principal is not supported; only nominal-based definitions are allowed.
    *   *UI Image Description:* Shows a validation error when attempting to book a trade using quantity principal.
4.  **Maximum Tenor Restriction:**
    *   Deals with a tenor greater than **two years** (24 months) are not supported.
    *   *UI Image Description:* Displays system rejection prompt for a transaction with a maturity date exceeding two years from the trade date.
