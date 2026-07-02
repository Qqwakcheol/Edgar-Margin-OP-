# Edgar-Margin-OP-
Extracting crucial financial figures such as Operating Profit Margin etc from edgar
# SEC EDGAR Financial Data Extractor (Mag 7 & Semiconductors)

An automated financial analysis tool built in Python to connect to the **US SEC EDGAR API**, extract US-GAAP financial elements, and calculate operating profit margins for Mag 7 and Major Semiconductor companies.

## Overview
- ** Extraction of OP% into DF format
- **Target Companies:** 
  - **Mag 7:** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
  - **+ 3 Semiconductors & Equipment firms:** MU (Micron), AMAT (Applied Materials), WDC (Western Digital / SanDisk)
- **Key Metric Evaluated:** Operating Profit Margin ($Operating\,Income \div Gross\,Revenue$) across recent 10-K (Annual Report) filings.

## Key Technical Implementations
- Def function iterating through each cik:
- 1. Response (SEC) file identified -->
  2. 2. converted to json-->
  3. Dig deeper and get the json element for us-gaap figures
  4. Revenue and OP identified within us-gaap
  5. convert data to df and filter for 10K only and the recent 3 years etc.
  6. then executes the iteration from line 77 onward
  7. merged and turned into pivot df in later lines


## Sample Analytical Output
```text
=== Operating Profit Margin (Recent 10-K Filings) ===
fy            2023        2024        2025
Ticker
AAPL        29.82%      30.58%         N/A
NVDA        43.73%      61.34%      64.12% (NVDA's financial year treatment differs from the conventional)
MSFT        41.77%      44.57%         N/A
... (Automated output truncated)
```

## Visualization codes added
