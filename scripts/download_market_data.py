"""
Market Data Downloader for TradeMind
Downloads 1-year daily OHLCV data for:
- NIFTY 50 (^NSEI)
- BANK NIFTY (^NSEBANK)
- RELIANCE (RELIANCE.NS)
- TCS (TCS.NS)
- INFY (INFY.NS)
Saves standardized CSVs to data/historical/
Also generates a clearly labeled synthetic demonstration dataset in data/synthetic/ as an offline fallback.
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import yfinance as yf
except ImportError:
    yf = None

INSTRUMENTS = {
    "NIFTY_50": {"symbol": "^NSEI", "name": "NIFTY 50 Index"},
    "BANK_NIFTY": {"symbol": "^NSEBANK", "name": "NIFTY Bank Index"},
    "RELIANCE": {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd"},
    "TCS": {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd"},
    "INFY": {"symbol": "INFY.NS", "name": "Infosys Ltd"}
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "historical")
SYNTHETIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")

def download_and_save():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SYNTHETIC_DIR, exist_ok=True)
    
    downloaded_count = 0
    
    for key, info in INSTRUMENTS.items():
        symbol = info["symbol"]
        print(f"Downloading historical data for {info['name']} ({symbol})...")
        try:
            if yf is None:
                raise RuntimeError("yfinance not installed")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y", interval="1d", auto_adjust=False)
            
            if df.empty:
                print(f"Warning: No data returned for {symbol}")
                continue
                
            df = df.reset_index()
            
            # Format Date column
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            elif "Datetime" in df.columns:
                df["Date"] = pd.to_datetime(df["Datetime"]).dt.strftime("%Y-%m-%d")
                
            # Handle multi-level columns if present in yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
                
            df = df[[c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]]
            
            # Data cleansing: remove nulls, remove duplicates, sort ascending
            df = df.dropna(subset=["Date", "Open", "High", "Low", "Close"])
            df = df.drop_duplicates(subset=["Date"])
            df = df.sort_values(by="Date", ascending=True)
            
            # Ensure valid numeric types
            for num_col in ["Open", "High", "Low", "Close", "Volume"]:
                if num_col in df.columns:
                    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
            
            # Verify high >= low, high >= open, high >= close
            df["High"] = df[["Open", "High", "Close"]].max(axis=1)
            df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)
            
            out_path = os.path.join(OUTPUT_DIR, f"{key}.csv")
            df.to_csv(out_path, index=False)
            print(f"  [OK] Saved {len(df)} rows to {out_path} (Latest: {df['Date'].iloc[-1]})")
            downloaded_count += 1
            
        except Exception as e:
            print(f"  [FAIL] Failed to download {symbol}: {e}")
            
    generate_synthetic_fallback()
    print(f"\nDownload completed: {downloaded_count}/{len(INSTRUMENTS)} downloaded successfully.")

def generate_synthetic_fallback():
    synth_path = os.path.join(SYNTHETIC_DIR, "DEMO_NIFTY_FALLBACK.csv")
    print("Generating clearly labeled synthetic demonstration dataset...")
    
    dates = pd.date_range(end=pd.Timestamp.now(), periods=120, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    
    base_price = 24000.0
    returns = np.random.normal(0.0005, 0.012, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    opens = prices * (1 + np.random.normal(0, 0.003, len(dates)))
    closes = prices * (1 + np.random.normal(0, 0.003, len(dates)))
    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.005, len(dates))))
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.005, len(dates))))
    volumes = np.random.randint(150000, 600000, len(dates))
    
    synth_df = pd.DataFrame({
        "Date": dates,
        "Open": np.round(opens, 2),
        "High": np.round(highs, 2),
        "Low": np.round(lows, 2),
        "Close": np.round(closes, 2),
        "Volume": volumes
    })
    
    synth_df.to_csv(synth_path, index=False)
    print(f"  [OK] Saved synthetic fallback with {len(synth_df)} rows to {synth_path}")

if __name__ == "__main__":
    download_and_save()
