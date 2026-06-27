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
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"[{ticker}] Failed to fetch data. Status code: {response.status_code}")
            return None
        
        data = response.json()
        us_gaap = data.get('facts', {}).get('us-gaap', {})
        
        # 1. US-GAAP Revenue tag
        revenue_keys = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues']
        revenue_data = None
        for key in revenue_keys:
            if key in us_gaap:
                revenue_data = us_gaap[key]['units']['USD']
                break
                
        # 2. US-GAAP Operating Income tag
        op_inc_keys = ['OperatingIncomeLoss', 'OperatingProfit']
        op_inc_data = None
        for key in op_inc_keys:
            if key in us_gaap:
                op_inc_data = us_gaap[key]['units']['USD']
                break
        
        if not revenue_data or not op_inc_data:
            return None
            
        # DataFrame transformation and 10-K filtering
        df_rev = pd.DataFrame(revenue_data)
        df_op = pd.DataFrame(op_inc_data)
        
        df_rev = df_rev[df_rev['form'] == '10-K'].drop_duplicates(subset=['fy'])
        df_op = df_op[df_op['form'] == '10-K'].drop_duplicates(subset=['fy'])
        
        # Integrating data for each fy and calculate the OP%
     
        df_merged = pd.merge(df_rev, df_op, on='fy', suffixes=('_rev', '_op'))
        df_merged['Operating_Margin'] = df_merged['val_op'] / df_merged['val_rev']
        
        # Recent 3 years
        df_result = df_merged[['fy', 'Operating_Margin']].sort_values(by='fy', ascending=False).head(3)
        df_result['Ticker'] = ticker
        return df_result
        
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

if __name__ == "__main__":
    print("Connecting to SEC EDGAR API and extracting data...")
    results = []
    for ticker in COMPANIES.keys():
        df = get_operating_margin(ticker)
        if df is not None:
            results.append(df)
            
    if results:
        final_df = pd.concat(results, ignore_index=True)
      
        # Pivot transformation for readability 
        pivot_df = final_df.pivot(index='Ticker', columns='fy', values='Operating_Margin')
        print("\n=== Operating Profit Margin (Recent 10-K Filings) ===")
        print(pivot_df.applymap(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A"))
    else:
        print("No data retrieved. Please check your network or user-agent header.")
