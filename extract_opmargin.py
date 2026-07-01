import requests
import pandas as pd

HEADERS = {'User-Agent': "seonho2015214@gmail.com"}

# CIK of Mag 7 + Micron + AMAT + Western Digital
COMPANIES = {
    'AAPL': {'cik': '0000320193', 'name': 'Apple Inc.'},
    'MSFT': {'cik': '0000789019', 'name': 'Microsoft Corp.'},
    'GOOGL': {'cik': '0001652044', 'name': 'Alphabet Inc.'},
    'AMZN': {'cik': '0001018724', 'name': 'Amazon.com Inc.'},
    'NVDA': {'cik': '0001045810', 'name': 'NVIDIA Corp.'},
    'META': {'cik': '0001326801', 'name': 'Meta Platforms, Inc.'},
    'TSLA': {'cik': '0001318605', 'name': 'Tesla, Inc.'},
    'MU':   {'cik': '0000723125', 'name': 'Micron Technology, Inc.'},
    'AMAT': {'cik': '0000006951', 'name': 'Applied Materials, Inc.'},
    'WDC':  {'cik': '0000106040', 'name': 'Western Digital Corp. (SanDisk)'}
}

def get_operating_margin(ticker, form='10-K'): # uses the ticker & form as inputs to generate df containing ticker, period, op margin as columns
    cik = COMPANIES[ticker]['cik'] # cik value
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json" #e.g. TSLA --> ~~CIK{0001318605}

    try:
        response = requests.get(url, headers=HEADERS) # HEADERS is at line 6 (user agent)
        if response.status_code != 200: # status code is 200 when successful, ergo != 200 --> unsuccessful
            print(f"[{ticker}] Failed to fetch data. Status code: {response.status_code}")
            return None

        data = response.json() # convert the data to json for convenience in processing
        us_gaap = data.get('facts', {}).get('us-gaap', {}) # 'data' json is composed of multiple 'files' within, and what we want is just the 'us-gaap' within 'facts'
        ### why use '.get'?---> to make sure in case the files are not named 'facts' or 'us-gaap', the code doesn't generate error and instead give blanks (i.e. {})

        # 1. US-GAAP Revenue tag
        revenue_keys = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues'] # Trying all 3 different names for Rev
        revenue_data = None 
        for key in revenue_keys:
            if key in us_gaap:
                revenue_data = us_gaap[key]['units']['USD']
                break # don't bother with the next iteration (from revenue_keys) upon successful run

        # 2. US-GAAP Operating Income tag
        op_inc_keys = ['OperatingIncomeLoss', 'OperatingProfit']
        op_inc_data = None
        for key in op_inc_keys:
            if key in us_gaap:
                op_inc_data = us_gaap[key]['units']['USD']
                break

        if not revenue_data or not op_inc_data: # if both were not found
            return None

        ## Converting to pandas DF
        df_rev = pd.DataFrame(revenue_data) # has 10K, 10Q and even 10K/A possibly
        df_op  = pd.DataFrame(op_inc_data)

        # form 필터 (10-K or 10-Q)
        df_rev = df_rev[df_rev['form'] == form].copy() # leave data rows with 'True' only
        df_op  = df_op[df_op['form']  == form].copy()

        if form == '10-K':
            ## Filtering for 10-K only
            df_rev = df_rev.drop_duplicates(subset=['fy']) # if somehow 2 outputs exist for the same fy, drop duplicates
            df_op  = df_op.drop_duplicates(subset=['fy'])
            df_merged = pd.merge(df_rev, df_op, on='fy', suffixes=('_rev', '_op')) # since the headers are named the same for both df_rev & op, adding suffixes to distinguish them
            df_merged['period_label'] = df_merged['fy'].astype(str)  # e.g. "2024" # turning 10K labels to string bc of consistency(i.e. the period labels for 10Q are strings)
            # Filtering for recent 3 years
            df_result = df_merged.sort_values('fy', ascending=False).head(3)

        else:  # 10-Q
            ## Filtering for 10-Q only
            # 10-Q uses 'end' (quarter end date) instead of 'fy' for deduplication
            # --> because same fy can contain Q1, Q2, Q3 all at once, so dedup by 'fy' would wrongly drop valid rows
            # 'end' column: last day of that quarter (e.g. "2024-06-30")
            df_rev = df_rev.drop_duplicates(subset=['end'])
            df_op  = df_op.drop_duplicates(subset=['end'])
            df_merged = pd.merge(df_rev, df_op, on='end', suffixes=('_rev', '_op'))
            df_merged['period_label'] = df_merged['end']  # e.g. "2024-06-30"
            # Filtering for recent 6 quarters
            df_result = df_merged.sort_values('end', ascending=False).head(6)

        # Integrating data for each period and calculating the OP%
        df_result['Operating_Margin'] = df_result['val_op'] / df_result['val_rev']
        df_result['Ticker'] = ticker # Adding column for the ticker ('ticker' was entered only as parameter)
        return df_result[['Ticker', 'period_label', 'Operating_Margin']]

    # in case of error: exception linked to the 'try' above
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None


def run_and_print(form):
    print(f"\nConnecting to SEC EDGAR API and extracting data... [{form}]")
    results = []
    for ticker in COMPANIES.keys():
        df = get_operating_margin(ticker, form=form)
        if df is not None:
            results.append(df) # added to 'results' as more valid df's come in

    if results: # if there's any data in 'results'
        final_df = pd.concat(results, ignore_index=True) # turn the discrete df's in 'results' into pd df, ignore original index and assign new one

        # Transformation to pivot df for readability
        pivot_df = final_df.pivot(index='Ticker', columns='period_label', values='Operating_Margin')
        label = "Annual (10-K)" if form == '10-K' else "Quarterly (10-Q)"
        print(f"\n=== Operating Profit Margin — {label} ===")
        print(pivot_df.applymap(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A")) # turn to % figure
    else:
        print("No data retrieved. Please check your network or user-agent header.")


if __name__ == "__main__": # dundered just in case
    run_and_print('10-K')
    run_and_print('10-Q')
