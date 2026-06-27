# Edgar-Margin-OP-
Extracting crucial financial figures such as Operating Profit Margin etc from edgar
# SEC EDGAR Financial Data Extractor (Mag 7 & Semiconductors)

An automated financial analysis tool built in Python to programmatically connect to the **US SEC EDGAR API**, extract US-GAAP financial elements, and calculate operating profit margins for Tier-1 Tech (Magnificent 7) and Major Semiconductor companies.

## Overview
- **Objective:** Eliminate manual financial data gathering from PDF filings by shifting to structured corporate reporting data (XBRL/JSON).
- **Target Companies:** 
  - **Mag 7:** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
  - **Semiconductors & Equipment:** MU (Micron), AMAT (Applied Materials), WDC (Western Digital / SanDisk)
- **Key Metric Evaluated:** Operating Profit Margin ($Operating\,Income \div Gross\,Revenue$) across recent 10-K (Annual Report) filings.

## 🛠️ Key Technical Implementations
- **SEC EDGAR API Protocol:** Embedded compliant User-Agent headers required by the SECイ민국 to prevent automated bot blocks.
- **Dynamic US-GAAP Mapping:** Handled non-standardized XBRL taxonomy variations (e.g., parsing multiple financial tags like `RevenueFromContractWithCustomerExcludingAssessedTax` and `SalesRevenueNet` depending on the company's reporting structure).
- **Data Pipeline:** Leveraged `pandas` to clean, merge, deduplicate 10-K forms, and pivot complex nested JSON metrics into structured analytical tables.

## 📈 Sample Analytical Output
```text
=== Operating Profit Margin (Recent 10-K Filings) ===
fy          2023     2024     2025
Ticker
AAPL      29.82%   30.58%      N/A
NVDA      43.73%   61.34%   64.12%
MSFT      41.77%   44.57%      N/A
... (Automated output truncated)
