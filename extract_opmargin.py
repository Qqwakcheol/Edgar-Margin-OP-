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

        # 1. US-GAAP Revenue tag (모든 후보 태그를 합쳐서 사용 — 태그 전환 대응)
        revenue_keys = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues']
        revenue_frames = []
        for key in revenue_keys:
            if key in us_gaap:
                revenue_frames.append(pd.DataFrame(us_gaap[key]['units']['USD']))

        # 2. US-GAAP Operating Income tag (마찬가지로 모두 합침)
        op_inc_keys = ['OperatingIncomeLoss', 'OperatingProfit']
        op_inc_frames = []
        for key in op_inc_keys:
            if key in us_gaap:
                op_inc_frames.append(pd.DataFrame(us_gaap[key]['units']['USD']))

        if not revenue_frames or not op_inc_frames:
            return None

        ## Converting to pandas DF (여러 태그에서 온 데이터를 하나로 합침)
        df_rev = pd.concat(revenue_frames, ignore_index=True)
        df_op  = pd.concat(op_inc_frames, ignore_index=True)

        # form 필터 (10-K or 10-Q)
        df_rev = df_rev[df_rev['form'] == form].copy()
        df_op  = df_op[df_op['form']  == form].copy()


        df_rev = df_rev.dropna(subset=['fy'])# if somehow 2 outputs exist for the same fy, drop duplicates
        df_op  = df_op.dropna(subset=['fy'])

        ## Filtering for 10-K only (같은 fy가 여러 태그에서 오면 가장 최근에 filed된 값을 남김)
        df_rev = df_rev.sort_values('filed').drop_duplicates(subset=['fy'], keep='last')
        df_op  = df_op.sort_values('filed').drop_duplicates(subset=['fy'], keep='last')
        df_merged = pd.merge(df_rev, df_op, on='fy', suffixes=('_rev', '_op'))
        df_merged['period_label'] = df_merged['fy'].astype(int).astype(str)# e.g. "2024" (int 경유로 "2024.0" 방지)
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
        
        # [CSV 저장 코드 추가]
        # utf-8-sig를 지정해줘야 Excel에서 한글이나 기호가 깨지지 않고 깔끔하게 열립니다.
        pivot_df.to_csv(filename, encoding='utf-8-sig')
        print(f"\n데이터가 성공적으로 '{filename}' 파일로 저장되었습니다.")

        label = "Annual (10-K)" if form == '10-K' else "Quarterly (10-Q)"
        print(f"\n=== Operating Profit Margin — {label} ===")
        print(pivot_df.applymap(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A")) # turn to % figure
    else:
        print("No data retrieved. Please check your network or user-agent header.")


if __name__ == "__main__": # dundered just in case
    run_and_save_csv('10-K')


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def plot_margin_heatmap(pivot_df, title="Operating Profit Margin — Annual (10-K)", save_path=None):
    """
    pivot_df: run_and_print()에서 만들어지는 pivot_df를 그대로 받음
              (index=Ticker, columns=period_label, values=Operating_Margin, 0~1 소수 형태)
    """

    # % 단위로 변환 (0.298 -> 29.8)
    plot_df = pivot_df * 100

    # 보기 좋게 컬럼(연도) 오름차순 정렬
    plot_df = plot_df.reindex(sorted(plot_df.columns), axis=1)

    # 평균 마진 기준으로 티커 정렬 (내림차순) -> 위쪽에 고마진 기업이 오도록
    plot_df = plot_df.loc[plot_df.mean(axis=1, skipna=True).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(1.4 * len(plot_df.columns) + 2, 0.55 * len(plot_df) + 2))

    sns.heatmap(
        plot_df,
        annot=True,                 # 셀 안에 숫자 표시
        fmt=".1f",                  # 소수점 1자리
        cmap="RdYlGn",               # 빨강(낮음) -> 초록(높음)
        center=0,                    # 0%를 기준 색으로
        linewidths=0.6,
        linecolor="white",
        cbar_kws={"label": "Operating Margin (%)"},
        annot_kws={"size": 10},
        mask=plot_df.isna(),         # N/A 셀은 색칠하지 않음
        ax=ax
    )

    # N/A 셀에 연한 회색 표시 + "N/A" 텍스트
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
    # ── 데모용 예시 데이터 (실제로는 run_and_print()의 pivot_df를 그대로 넣으면 됨) ──
    data = {
        "2023": [0.2982, 0.2886, 0.0261, 0.2742, 0.2482, 0.4177, 0.6243, 0.5412, 0.1091, 0.1941],
        "2024": [0.3151, 0.2895, 0.1075, 0.3974, 0.5950, 0.4464, 0.0519, 0.6242, 0.0724, -0.0244],
        "2025": [0.3197, 0.2922, 0.1116, 0.3203, 0.6173, 0.5243, 0.2614, 0.6038, 0.0459, 0.8960],
    }
    tickers = ["AAPL", "AMAT", "AMZN", "GOOGL", "META", "MSFT", "MU", "NVDA", "TSLA", "WDC"]
    demo_pivot_df = pd.DataFrame(data, index=tickers)

    plot_margin_heatmap(demo_pivot_df)
