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
    'WDC':  {'cik': '0000106040', 'name': 'Western Digital Corp.'}
    }
def get_operating_margin(ticker, form='10-K'):
    cik = COMPANIES[ticker]['cik']
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json" #e.g. TSLA --> ~~CIK{0001318605}

    try:
        response = requests.get(url, headers=HEADERS) #HEADERS is at line 6 (user agent)
        if response.status_code != 200: # status code is 200 when successful, ergo != 200 --> unsuccessful
            print(f"[{ticker}] Failed to fetch data. Status code: {response.status_code}")
            return None

        data = response.json() # convert the data to json for convenience in processing
        us_gaap = data.get('facts', {}).get('us-gaap', {}) # 'data' json is composed of multiple 'files' within, and what we want is just the 'us-gaap' within 'facts'
        ### why use '.get'?---> to make sure in case the files are not named 'facts' or 'us-gaap', the code doesn't generate error and instead give blanks (i.e. {})

        # 1. US-GAAP Revenue tag (trying different tag names)
        revenue_keys = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues']
        revenue_frames = []
        for key in revenue_keys:
            if key in us_gaap:
                revenue_frames.append(pd.DataFrame(us_gaap[key]['units']['USD']))

        # 2. US-GAAP Operating Income tag
        op_inc_keys = ['OperatingIncomeLoss', 'OperatingProfit']
        op_inc_frames = []
        for key in op_inc_keys:
            if key in us_gaap:
                op_inc_frames.append(pd.DataFrame(us_gaap[key]['units']['USD']))

        if not revenue_frames or not op_inc_frames:
            return None

        ## Converting to pandas DF 
        df_rev = pd.concat(revenue_frames, ignore_index=True)
        df_op  = pd.concat(op_inc_frames, ignore_index=True)

        # form filter (10-K or 10-Q)
        df_rev = df_rev[df_rev['form'] == form].copy()
        df_op  = df_op[df_op['form']  == form].copy()


        df_rev = df_rev.dropna(subset=['fy'])# if somehow 2 outputs exist for the same fy, drop duplicates
        df_op  = df_op.dropna(subset=['fy'])

        ## Filtering for 10-K only (if the same fy outputs from different tags, the most recently filed one remains)
        df_rev = df_rev.sort_values('filed').drop_duplicates(subset=['fy'], keep='last')
        df_op  = df_op.sort_values('filed').drop_duplicates(subset=['fy'], keep='last')
        df_merged = pd.merge(df_rev, df_op, on='fy', suffixes=('_rev', '_op'))
        df_merged['period_label'] = df_merged['fy'].astype(int).astype(str)# e.g. "2024" (prevent 2024.0)
        # Filtering for recent 3 years
        df_result = df_merged.sort_values('fy', ascending=False).head(3)

        # Integrating data for each period and calculating the OP%
        df_result['Operating_Margin'] = df_result['val_op'] / df_result['val_rev']
        df_result['Ticker'] = ticker # Adding column for the ticker ('ticker' was entered as parameter)
        return df_result[['Ticker', 'period_label', 'Operating_Margin']]

    # in case of error: exception linked to the 'try' above
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None
    def run_and_save_csv(form, filename="operating_margin_results.csv"):
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
        
        # [CSV  filecode]
        pivot_df.to_csv(filename, encoding='utf-8-sig') # utf-8-sig to prevent glitches in excel
        print(f"\n Data successfully saved as '{filename}'.")

        label = "Annual (10-K)" if form == '10-K' else "Quarterly (10-Q)"
        print(f"\n=== Operating Profit Margin — {label} ===")
        print(pivot_df.applymap(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A")) # turn to % figure
    else:
        print("No data retrieved. Please check your network or user-agent header.")


if __name__ == "__main__": # dundered just in case
    run_and_save_csv('10-K')

#################### Visualization

import matplotlib.pyplot as plt
import seaborn as sns

def plot_margin_heatmap(pivot_df, title="Operating Profit Margin — Annual (10-K)", save_path=None):
    """
    pivot_df: received directly from run_and_print() from line 91
              (index=Ticker, columns=period_label, values=Operating_Margin, decimal between 0~1)
    """

    # converted to %
    plot_df = pivot_df * 100

    # 1. sort the column names (by alphabet or number) 2. Use that order to reindex the columns
    plot_df = plot_df.reindex(sorted(plot_df.columns), axis=1)

    # 1. Get mean margin for each company 2. Sort by descending 3. Get the indices(company names) in that order 4. plot_df.loc[company names] Get the rows in that order
    plot_df = plot_df.loc[plot_df.mean(axis=1, skipna=True).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(1.4 * len(plot_df.columns) + 2, 0.55 * len(plot_df) + 2))

    sns.heatmap(
        plot_df,
        annot=True,                 # Number in the cells
        fmt=".1f",                  # 1 digit decimal
        cmap="RdYlGn",               # Red (low)-> Green (High)
        center=0,                    # 0% at the center
        linewidths=0.6,
        linecolor="white",
        cbar_kws={"label": "Operating Margin (%)"},
        annot_kws={"size": 10},
        mask=plot_df.isna(),         # N/A cells not colored
        ax=ax
    )

    # N/A cell treatments (light gray)  + "N/A" Text
    for i, ticker in enumerate(plot_df.index):
        for j, col in enumerate(plot_df.columns):
            if pd.isna(plot_df.iloc[i, j]):
                ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=True, color="#f0f0f0"))
                ax.text(j + 0.5, i + 0.5, "N/A", ha="center", va="center",
                        color="gray", fontsize=9)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()
    return fig


if __name__ == "__main__":
    # ── Demo data ──
    data = {
        "2023": [0.2982, 0.2886, 0.0261, 0.2742, 0.2482, 0.4177, 0.6243, 0.5412, 0.1091, 0.1941],
        "2024": [0.3151, 0.2895, 0.1075, 0.3974, 0.5950, 0.4464, 0.0519, 0.6242, 0.0724, -0.0244],
        "2025": [0.3197, 0.2922, 0.1116, 0.3203, 0.6173, 0.5243, 0.2614, 0.6038, 0.0459, 0.8960],
    }
    tickers = ["AAPL", "AMAT", "AMZN", "GOOGL", "META", "MSFT", "MU", "NVDA", "TSLA", "WDC"]
    demo_pivot_df = pd.DataFrame(data, index=tickers)

    plot_margin_heatmap(demo_pivot_df)
