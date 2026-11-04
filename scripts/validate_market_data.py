"""
Market Data Validator for TradeMind
Validates OHLCV CSV files according to quantitative trading standards:
- Checks column existence: Date/Timestamp, Open, High, Low, Close, Volume
- Validates ascending chronological ordering
- Checks for duplicate timestamps
- Verifies price consistency: High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
- Detects NaN, nulls, or negative price anomalies
- Displays summary statistics and source labeling
"""

import os
import sys
import glob
import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def validate_csv(filepath: str) -> dict:
    basename = os.path.basename(filepath)
    issues = []
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return {"file": basename, "valid": False, "issues": [f"Cannot read CSV: {e}"], "rows": 0}
        
    if df.empty:
        return {"file": basename, "valid": False, "issues": ["CSV file is empty"], "rows": 0}
        
    # Check date column
    date_col = None
    for candidate in ["Date", "date", "Timestamp", "timestamp", "datetime", "Datetime"]:
        if candidate in df.columns:
            date_col = candidate
            break
            
    if not date_col:
        issues.append("Missing required date/timestamp column")
    else:
        # Check duplicate dates
        duplicates = df[date_col].duplicated().sum()
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate timestamps")
            
        # Check ascending order
        converted_dates = pd.to_datetime(df[date_col], errors="coerce")
        if converted_dates.isna().any():
            issues.append(f"Found {converted_dates.isna().sum()} invalid date formats")
        elif not converted_dates.is_monotonic_increasing:
            issues.append("Timestamps are not strictly in ascending order")
            
    # Check required numeric columns
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        matches = [c for c in df.columns if c.lower() == col.lower()]
        if not matches:
            issues.append(f"Missing required column: {col}")
        else:
            actual_col = matches[0]
            non_numeric = pd.to_numeric(df[actual_col], errors="coerce").isna().sum()
            if non_numeric > 0:
                issues.append(f"Column '{actual_col}' contains {non_numeric} non-numeric/null values")
            else:
                if (df[actual_col] < 0).any():
                    issues.append(f"Column '{actual_col}' contains negative values")
                    
    # Validate price relationships
    try:
        high = pd.to_numeric(df["High"], errors="coerce")
        low = pd.to_numeric(df["Low"], errors="coerce")
        opn = pd.to_numeric(df["Open"], errors="coerce")
        close = pd.to_numeric(df["Close"], errors="coerce")
        
        invalid_high = (high < low) | (high < opn) | (high < close)
        if invalid_high.any():
            issues.append(f"Found {invalid_high.sum()} rows where High is not >= Low/Open/Close")
            
        invalid_low = (low > opn) | (low > close)
        if invalid_low.any():
            issues.append(f"Found {invalid_low.sum()} rows where Low is not <= Open/Close")
    except Exception:
        pass
        
    latest_ts = str(df[date_col].iloc[-1]) if date_col and not df.empty else "N/A"
    first_ts = str(df[date_col].iloc[0]) if date_col and not df.empty else "N/A"
    
    return {
        "file": basename,
        "path": filepath,
        "valid": len(issues) == 0,
        "issues": issues,
        "rows": len(df),
        "start_date": first_ts,
        "end_date": latest_ts,
        "last_close": float(df["Close"].iloc[-1]) if "Close" in df.columns else None
    }

def validate_all():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_dir = os.path.join(base_dir, "data", "historical")
    synth_dir = os.path.join(base_dir, "data", "synthetic")
    
    files = glob.glob(os.path.join(hist_dir, "*.csv")) + glob.glob(os.path.join(synth_dir, "*.csv"))
    print(f"Validating {len(files)} market data files...\n")
    
    all_valid = True
    for f in files:
        res = validate_csv(f)
        status = "[VALID]" if res["valid"] else "[INVALID]"
        is_synth = "synthetic" in f
        source_label = "SYNTHETIC DEMO" if is_synth else "HISTORICAL (yfinance NSE/Yahoo)"
        
        print(f"{status} {res['file']} ({source_label})")
        print(f"   Rows: {res['rows']} | Date Range: {res['start_date']} to {res['end_date']} | Last Close: {res['last_close']}")
        if not res["valid"]:
            all_valid = False
            for issue in res["issues"]:
                print(f"   - ISSUE: {issue}")
        print()
        
    return all_valid

if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
