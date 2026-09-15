# Murex LiveBook and Batch Report Guide

This guide provides standard operating procedures for running Murex LiveBook for on-the-fly calculations and for processing risk matrices using batch reports.

## 1. Murex LiveBook Guide

### Purpose

Murex LiveBook is used for the on-the-fly calculation of Profit & Loss (P/L) and greeks for selected portfolios. It allows for real-time risk assessment.

### Procedure

#### Step 1: Start the LiveBook Service

This is typically performed once at the beginning of the day after the Murex market data has been updated.

1.  Log in to the equity LiveBook Murex group (e.g., **`LB EQU`**).
2.  Launch the **LiveBook Administration Dashboard**.
3.  Trigger the **"start"** action for the LiveBook service.
4.  Wait for the service status to change to **"started"**. The initial run may take 30-60 minutes.

#### Step 2: Refresh Market Data

If market data needs to be updated during the day, follow these steps:

1.  In the LiveBook group, navigate to **Market data -> Viewer**.
2.  Select the data set you wish to update (e.g., `MD_EQ_SPOT`).
3.  Modify the required values. You can batch-edit by exporting to and importing from Excel.
4.  Click **"Publish"** to apply the changes.
5.  Return to the **LiveBook Administration Dashboard** and click the **refresh** button. A refresh typically takes around 20 minutes.

### Portfolios for Simulation

You can use the following portfolios for simulations (names are illustrative; substitute your institution's actual portfolio names):

*   Small portfolio (~hundreds of deals)
*   Large KIKO portfolio
*   Large US structured portfolio (~3000 live deals)

To filter for Flex trades only, use the pre-configured Flex trade filter (e.g., `TRDESK_EQ_FLEX_FILTER`).

---

## 2. Batch Report Guide (Trading Matrices)

### Purpose

Batch reports are used to process and generate risk matrices for trading portfolios.

### Procedure

#### Step 1: Run a Batch Report

1.  Navigate to **Middle office -> Reporting -> Print batch of reports**.
2.  Select the batch report you need to run from the list.
3.  Double-click the report name and click **"Proceed"** to start the process.

#### Step 2: Check Batch Status

1.  To monitor the progress of a running report, navigate to **Middle office -> Reporting -> Display batch status**.

### Report Examples

Below is an illustrative mapping between batch reports and the risk matrices they process. Each risk matrix is typically generated in a `VAR` configuration variant (all major greeks disabled for pure P&L) and an `SPB` variant (full greeks enabled).

| Batch Report | Risk Matrix | Portfolios       | Config Group |
| :----------- | :---------- | :--------------- | :----------- |
| `TREQ00`     | `EQ_EU1`    | EU Non-Structured, EU Structured | `VAR` |
| `TREQ24`     | `EQ_EU2`    | EU Non-Structured, EU Structured | `SPB` |
| `TREQ25`     | `EQ_US13`   | US Non-Structured, US Accounts   | `VAR` |
| `TREQ29`     | `EQ_US15`   | US Non-Structured, US Accounts   | `SPB` |
| `TREQ26`     | `EQ_US14`   | KIKO Portfolio                   | `VAR` |
| `TREQ30`     | `EQ_US16`   | KIKO Portfolio                   | `SPB` |
| *Unknown*    | `EQ_US17`   | US Structured Portfolio          | `VAR` |
| *Unknown*    | `EQ_US18`   | US Structured Portfolio          | `SPB` |