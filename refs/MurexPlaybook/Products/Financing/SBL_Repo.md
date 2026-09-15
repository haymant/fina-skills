# Product and Risk Overview: SBL & Basket Repo

This document provides a high-level overview of Stock Borrowing/Lending (SBL) and Basket Repo products, detailing their purpose and how their associated risks are managed within the Murex system.

## 1. Product Overview

Stock Borrowing/Lending (SBL) and Basket Repo are financing trades that involve the exchange of securities against cash or other securities. They are essential tools for market participants to finance positions, cover short sales, or manage collateral.

The primary variations handled by the system include:

*   **Vanilla SBL:** A straightforward loan of an equity or bond against a fee, without an accompanying cash leg.
*   **SBL Financing (Basket):** A transaction where a basket of securities is lent against a cash amount.
*   **Basket REPO:** A repurchase agreement where a basket of securities is exchanged for cash, with an agreement to reverse the transaction at a future date.
*   **Collateral Swaps:** A package transaction that combines SBL and Basket Repo components to swap one form of collateral for another.

## 2. Risk Management Framework

The risk treatment for these products is specifically tailored to their structure and is governed by legal agreements, pre-deal checks, and specific risk calculations for counterparty and settlement exposure.

### Governing Agreements

Trades are governed by industry-standard legal agreements, which must be correctly tagged to the counterparty in Murex to receive appropriate risk treatment.

*   **GMSLA (Global Master Securities Lending Agreement):** The standard agreement for SBL trades.
*   **GMRA (Global Master Repurchase Agreement):** The standard agreement for Repo trades.
*   **BMLA (via ISDA tag):** For trades with China-based entities, a BMLA agreement can be used if a GMSLA is not in place. This is tagged under the ISDA field as a workaround.

### Sanity Checks

The system performs automated pre-deal sanity checks to ensure the correct legal agreements are in place.

If a trader attempts to book an SBL trade with a counterparty that does not have a `GMSLA` (or `BMLA` for China) tagged, a pre-deal check fails. This triggers a workflow and temporarily "chalks" (allocates) a punitive risk exposure equal to **100% of the notional amount** until the issue is resolved. A similar check exists for Repo trades and the `GMRA`.

### Settlement Risk (SR)

Settlement Risk arises from the potential failure of a counterparty to deliver on their side of a transaction. For these products, SR is calculated only on transactions involving a cash exchange.

*   **Applicable Products:** SBL Financing (Basket), Basket REPO.
*   **Exposure Calculation:** The SR exposure is equal to the **cash amount** being exchanged.
*   **Out of Scope:** Vanilla SBL and Collateral Swaps do not have a cash component, so they are not subject to this specific settlement risk calculation.

### Counterparty Risk (PCE)

Counterparty Risk, or Potential Credit Exposure (PCE), measures the potential loss if a counterparty defaults. These products are routed to a dedicated limit group for monitoring (`EQ_SBL`, `CN_SBL`).

The PCE calculation varies by product structure:

| Product Type | Simplified PCE Calculation |
| :--- | :--- |
| **Equity/Bond SBL (No Cash)** | `Market Value of Security * Haircut` + Add-on |
| **Basket Repo / SBL Financing** | `|Market Value of Securities - Cash Amount|` + Add-on |

**Note on Market Value (MV):** The calculations assume that trades governed by `GMRA` or `GMSLA` are **daily margined**. This means the counterparty is required to post additional collateral to meet the agreed-upon haircut if the market value of the securities changes. Consequently, the effective market exposure is simply the difference between the value of the securities and the cash exchanged. The system uses specific User-Defined Fields (UDFs) to capture trade-level details like haircuts needed for this calculation.

### Wrong Way Risk (WWR)

Wrong Way Risk occurs when the exposure to a counterparty is adversely correlated with the credit quality of that counterparty.

*   **Bond SBL:** WWR is explicitly calculated.
*   **Equity SBL:** WWR is not required.
*   **Basket Repo:** WWR is considered to be embedded within the **Structured PCE** add-on and is not calculated separately.
*   **Collateral Swaps:** WWR treatment depends on the underlying components of the swap.
