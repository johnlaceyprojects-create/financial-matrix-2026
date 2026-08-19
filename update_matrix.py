import pandas as pd
import yfinance as yf
import datetime
import sys

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
    # Fetch data and clean up columns smoothly
    raw_data = yf.download(list(tickers.values()), start=start_date, end=end_date)
    
    if raw_data.empty or 'Adj Close' not in raw_data:
        print("Error: Received an empty data response from the market API.")
        sys.exit(1)
        
    asset_data = raw_data['Adj Close']
    
    # Map the columns backward correctly to their clean names
    inv_tickers = {v: k for k, v in tickers.items()}
    asset_data = asset_data.rename(columns=inv_tickers)
    
    # Forward fill gaps (like weekends for stocks while crypto stays open)
    asset_data = asset_data.ffill().dropna()

    if len(asset_data) < 65:
        print("Error: Not enough data historical entries gathered to compute a matrix.")
        sys.exit(1)

except Exception as e:
    print(f"Data ingestion error: {e}")
    sys.exit(1)

# 3. Calculate Daily Returns securely
returns_df = asset_data.pct_change().dropna()

# 4. Generate 60-Day Rolling Correlation Matrix
correlation_matrix = returns_df.tail(60).corr().fillna(0)

# 5. Build HTML Visual Matrix Page
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
            z: {correlation_matrix.values.tolist()},
            x: {list(correlation_matrix.columns)},
            y: {list(correlation_matrix.index)},
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
