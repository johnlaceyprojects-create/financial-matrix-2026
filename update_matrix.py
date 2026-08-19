import pandas as pd
import yfinance as yf
import datetime
import sys
import json

# 1. Define Timeframe (Last 2 years)
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=2*365)

tickers = {
    'Equities (S&P 500)': '^GSPC',
    'Bonds (10Y Yield)': '^TNX',
    'Gold': 'GC=F',
    'Oil (WTI)': 'CL=F',
    'US Dollar Index': 'DX-Y.NYB',
    'Bitcoin (Crypto)': 'BTC-USD',
    'Ethereum (Crypto)': 'ETH-USD',
    'Real Estate (VNQ REIT)': 'VNQ'
}

print("Fetching financial data from Yahoo Finance...")
try:
    # Disable multi-level layers for a completely flat data grid
    asset_data = yf.download(
        tickers=list(tickers.values()), 
        start=start_date, 
        end=end_date, 
        multi_level_index=False
    )
    
    if asset_data.empty:
        print("Error: Received an empty data response from the market API.")
        sys.exit(1)
        
    # Standardise column headers to lowercase to avoid case-matching errors
    asset_data.columns = [str(c).lower() for c in asset_data.columns]
    
    # Isolate closing price columns matching our target ticker symbols
    valid_cols = []
    for clean_name, symbol in tickers.items():
        sym_lower = symbol.lower()
        # Find any column header that contains our ticker symbol string
        matched_col = next((c for c in asset_data.columns if sym_lower in c), None)
        if matched_col:
            asset_data = asset_data.rename(columns={matched_col: clean_name})
            valid_cols.append(clean_name)
            
    # Filter the dataframe to hold only our renamed valid asset classes
    asset_data = asset_data[valid_cols]
    
    # Forward fill gaps (aligns stock market weekend closures with 24/7 crypto)
    asset_data = asset_data.ffill().dropna()

    print(f"Successfully processed {len(asset_data)} rows across {len(asset_data.columns)} assets.")

except Exception as e:
    print(f"Data processing error: {e}")
    sys.exit(1)

# 2. Calculate Daily Returns
returns_df = asset_data.pct_change().dropna()

# 3. Generate 60-Day Rolling Correlation Matrix
correlation_matrix = returns_df.tail(60).corr().fillna(0)

# Securely serialize the arrays via JSON to prevent raw python strings breaking HTML
matrix_values = json.dumps(correlation_matrix.values.tolist())
clean_columns = json.dumps(list(correlation_matrix.columns))
clean_rows = json.dumps(list(correlation_matrix.index))

# 4. Build HTML Visual Matrix Page
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Live Global Asset Relationship Matrix</title>
    <script src="https://plot.ly"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #121212; color: #ffffff; text-align: center; margin: 40px; }}
        .container {{ max-width: 900px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5); }}
        h1 {{ margin-bottom: 5px; color: #00adb5; }}
        p {{ color: #aaaaaa; font-size: 14px; margin-bottom: 25px; }}
        .footer {{ margin-top: 25px; font-size: 12px; color: #666666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Inter-Asset Relationship Matrix</h1>
        <p>60-Day Rolling Pearson Correlation. Automatically updated daily. <br><strong>Last Update: {end_date}</strong></p>
        <div id="heatmap"></div>
        <p class="footer">Legend: +1.0 = Moves perfectly together (Red) | 0.0 = No relationship | -1.0 = Moves oppositely (Blue)</p>
    </div>

    <script>
        var data = [{{
            z: {matrix_values},
            x: {clean_columns},
            y: {clean_rows},
            type: 'heatmap',
            colorscale: 'RdBu',
            reversescale: true,
            zmin: -1,
            zmax: 1
        }}];

        var layout = {{
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font: {{ color: '#ffffff' }},
            margin: {{ l: 150, r: 50, b: 100, t: 30 }},
            xaxis: {{ tickangle: -45 }}
        }};

        Plotly.newPlot('heatmap', data, layout);
    </script>
</body>
</html>
"""

with open('index.html', 'w') as f:
    f.write(html_content)

print("Web matrix successfully built!")
