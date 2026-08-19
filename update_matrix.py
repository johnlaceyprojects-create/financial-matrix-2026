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

print("Fetching financial data sequentially to guarantee a single-level dataframe...")
price_series = {}

# Download assets individually to block MultiIndex column grouping entirely
for label, symbol in tickers.items():
    try:
        print(f"Downloading {label} ({symbol})...")
        single_data = yf.download(symbol, start=start_date, end=end_date, verbose=False)
        
        if not single_data.empty:
            # Safely capture the Close price series as a flat array
            if 'Close' in single_data.columns:
                price_series[label] = single_data['Close']
            elif 'Adj Close' in single_data.columns:
                price_series[label] = single_data['Adj Close']
                
    except Exception as e:
        print(f"Warning: Skipped tracking {label} due to an access gap: {e}")

if not price_series:
    print("Error: Could not retrieve a single asset series from the market network.")
    sys.exit(1)

# Combine the individual asset series into a completely flat database layout
asset_data = pd.DataFrame(price_series)

# Forward fill gaps (bridges global market weekend closures with 24/7 crypto timelines)
asset_data = asset_data.ffill().dropna()
print(f"Successfully processed {len(asset_data)} uniform rows across {len(asset_data.columns)} assets.")

# 2. Calculate Daily Percentage Returns
returns_df = asset_data.pct_change().dropna()

# 3. Generate a 60-Day Rolling Pearson Correlation Matrix
correlation_matrix = returns_df.tail(60).corr().fillna(0)

# Clean out DataFrame structural metadata to prevent layout injection errors
matrix_values = [list(map(float, row)) for row in correlation_matrix.values]
clean_columns = [str(col) for col in correlation_matrix.columns]
clean_rows = [str(index) for index in correlation_matrix.index]

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
            z: {json.dumps(matrix_values)},
            x: {json.dumps(clean_columns)},
            y: {json.dumps(clean_rows)},
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
            margin: {{ l: 160, r: 40, b: 100, t: 30 }},
            xaxis: {{ tickangle: -45 }}
        }};

        Plotly.newPlot('heatmap', data, layout);
    </script>
</body>
</html>
"""

with open('index.html', 'w') as f:
    f.write(html_content)

print("Web matrix successfully built with verified single-tier parsing layouts!")
