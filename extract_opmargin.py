import requests
import pandas as pd
import json


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
    'MU': {'cik': '0000723125', 'name': 'Micron Technology, Inc.'},
    'AMAT': {'cik': '0000006951', 'name': 'Applied Materials, Inc.'},
    'WDC': {'cik': '0000106040', 'name': 'Western Digital Corp. (SanDisk)'}
}

def get_operating_margin(ticker):
    cik = COMPANIES[ticker]['cik']
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json" #e.g. TSLA --> ~~CIK{0001318605}
    
    try:
        response = requests.get(url, headers=HEADERS) #HEADERS is at line 6 (user agent)
        if response.status_code != 200: # status code is 200 when successful, ergo != 200--> unsuccessful
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
                break # don't bother with the next one upon successful run
                
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
        df_rev = pd.DataFrame(revenue_data)
        df_op = pd.DataFrame(op_inc_data)

        ##  Filtering for 10K only
        df_rev = df_rev[df_rev['form'] == '10-K'].drop_duplicates(subset=['fy']) # if somehow 2 outputs exist for the same fy, drop duplicates
        df_op = df_op[df_op['form'] == '10-K'].drop_duplicates(subset=['fy'])
        
        # Integrating data for each fy and calculating the OP%
        df_merged = pd.merge(df_rev, df_op, on='fy', suffixes=('_rev', '_op'))
        df_merged['Operating_Margin'] = df_merged['val_op'] / df_merged['val_rev']
        
        # Filtering for recent 3 years
        df_result = df_merged[['fy', 'Operating_Margin']].sort_values(by='fy', ascending=False).head(3)
        df_result['Ticker'] = ticker # Adding column for the ticker ('ticker' was entered at line 22)
        return df_result

    # in case of error: exception linked to the 'try' at line 26
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

if __name__ == "__main__": # dundered just in case
    print("Connecting to SEC EDGAR API and extracting data...")
    results = []
    for ticker in COMPANIES.keys():
        df = get_operating_margin(ticker)
        if df is not None:
            results.append(df) # added to 'results' as more valid df's come in
            
    if results: # if there's any data in 'results'
        final_df = pd.concat(results, ignore_index=True) # turn the discrete df's in 'results' into pd df, ignore original index and assign new one
      
        # Transformation to pivot df for readability 
        pivot_df = final_df.pivot(index='Ticker', columns='fy', values='Operating_Margin') 
        print("\n=== Operating Profit Margin (Recent 10-K Filings) ===")
        print(pivot_df.applymap(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A")) # turn to % figure
    else:
        print("No data retrieved. Please check your network or user-agent header.")
