import os
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from backend.config import settings
from backend.models.market import InstrumentMetadata, CandleData

INSTRUMENT_NAMES = {
    "NIFTY_50": "NIFTY 50 Index",
    "BANK_NIFTY": "NIFTY Bank Index",
    "RELIANCE": "Reliance Industries Ltd",
    "TCS": "Tata Consultancy Services Ltd",
    "INFY": "Infosys Ltd",
    "DEMO_NIFTY_FALLBACK": "Demo Synthetic Nifty (Offline Fallback)"
}

class DataLoaderService:
    def __init__(self):
        self.hist_dir = settings.HISTORICAL_DATA_DIR
        self.synth_dir = settings.SYNTHETIC_DATA_DIR
        self.uploads_dir = settings.UPLOADS_DATA_DIR

    def list_available_instruments(self) -> List[InstrumentMetadata]:
        instruments: List[InstrumentMetadata] = []
        
        # Check historical directory
        for f in sorted(glob.glob(str(self.hist_dir / "*.csv"))):
            meta = self._get_metadata_from_file(Path(f), is_synthetic=False, source_type="Historical (yfinance demonstration feed)")
            if meta:
                instruments.append(meta)
                
        # Check user uploads
        for f in sorted(glob.glob(str(self.uploads_dir / "*.csv"))):
            meta = self._get_metadata_from_file(Path(f), is_synthetic=False, source_type="User Uploaded Dataset")
            if meta:
                instruments.append(meta)
                
        # Check synthetic fallback
        for f in sorted(glob.glob(str(self.synth_dir / "*.csv"))):
            meta = self._get_metadata_from_file(Path(f), is_synthetic=True, source_type="Synthetic Demonstration Fallback")
            if meta:
                instruments.append(meta)
                
        return instruments

    def _get_metadata_from_file(self, path: Path, is_synthetic: bool, source_type: str) -> Optional[InstrumentMetadata]:
        try:
            df = pd.read_csv(path)
            if df.empty:
                return None
            clean_df = self._clean_ohlcv_dataframe(df)
            if clean_df.empty:
                return None
                
            inst_id = path.stem
            name = INSTRUMENT_NAMES.get(inst_id, inst_id.replace("_", " ").title())
            
            return InstrumentMetadata(
                id=inst_id,
                symbol=inst_id,
                name=name,
                file_name=path.name,
                source=source_type,
                is_synthetic=is_synthetic,
                last_timestamp=str(clean_df["Date"].iloc[-1]),
                row_count=len(clean_df),
                latest_close=float(clean_df["Close"].iloc[-1])
            )
        except Exception:
            return None

    def load_ohlcv_dataframe(self, instrument_id: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
        # Search in historical, uploads, then synthetic
        candidates = [
            (self.hist_dir / f"{instrument_id}.csv", False, "Historical (yfinance demonstration feed)"),
            (self.uploads_dir / f"{instrument_id}.csv", False, "User Uploaded Dataset"),
            (self.synth_dir / f"{instrument_id}.csv", True, "Synthetic Demonstration Fallback"),
            # Case insensitive search
        ]
        
        target_path = None
        is_synth = False
        source = "Unknown"
        
        for p, synth, src in candidates:
            if p.exists():
                target_path = p
                is_synth = synth
                source = src
                break
                
        if not target_path:
            # Try finding any match by prefix or lowercase
            all_files = list(self.hist_dir.glob("*.csv")) + list(self.uploads_dir.glob("*.csv")) + list(self.synth_dir.glob("*.csv"))
            for f in all_files:
                if f.stem.lower() == instrument_id.lower():
                    target_path = f
                    is_synth = "synthetic" in str(f)
                    source = "Synthetic Demonstration Fallback" if is_synth else "Historical (yfinance demonstration feed)"
                    break
                    
        if not target_path:
            # Default to synthetic demo fallback if available
            fallback = self.synth_dir / "DEMO_NIFTY_FALLBACK.csv"
            if fallback.exists():
                target_path = fallback
                is_synth = True
                source = "Synthetic Demonstration Fallback"
            else:
                raise FileNotFoundError(f"Instrument '{instrument_id}' not found and fallback unavailable.")
                
        df = pd.read_csv(target_path)
        clean_df = self._clean_ohlcv_dataframe(df)
        
        info = {
            "file": target_path.name,
            "source": source,
            "is_synthetic": str(is_synth),
            "last_timestamp": str(clean_df["Date"].iloc[-1]) if not clean_df.empty else "N/A"
        }
        return clean_df, info

    def _clean_ohlcv_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
            
        # Standardize column names
        col_map = {}
        for c in df.columns:
            low = c.strip().lower()
            if low in ["date", "timestamp", "datetime"]:
                col_map[c] = "Date"
            elif low == "open":
                col_map[c] = "Open"
            elif low == "high":
                col_map[c] = "High"
            elif low == "low":
                col_map[c] = "Low"
            elif low == "close":
                col_map[c] = "Close"
            elif low in ["volume", "vol"]:
                col_map[c] = "Volume"
                
        df = df.rename(columns=col_map)
        
        required = ["Date", "Open", "High", "Low", "Close"]
        for req in required:
            if req not in df.columns:
                raise ValueError(f"Required OHLCV column '{req}' is missing.")
                
        if "Volume" not in df.columns:
            df["Volume"] = 100000.0
            
        # Parse Dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["Date", "Open", "High", "Low", "Close"])
        df = df.drop_duplicates(subset=["Date"])
        df = df.sort_values(by="Date", ascending=True)
        
        # Convert numerics
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        
        # Enforce consistency: High >= max(Open, Close), Low <= min(Open, Close)
        df["High"] = df[["Open", "High", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Low", "Close"]].min(axis=1)
        
        return df.reset_index(drop=True)

    def save_uploaded_csv(self, filename: str, content: bytes) -> InstrumentMetadata:
        clean_name = Path(filename).stem.replace(" ", "_").upper()
        save_path = self.uploads_dir / f"{clean_name}.csv"
        
        with open(save_path, "wb") as f:
            f.write(content)
            
        df = pd.read_csv(save_path)
        clean_df = self._clean_ohlcv_dataframe(df)
        clean_df.to_csv(save_path, index=False)
        
        return InstrumentMetadata(
            id=clean_name,
            symbol=clean_name,
            name=f"Custom: {clean_name}",
            file_name=save_path.name,
            source="User Uploaded Dataset",
            is_synthetic=False,
            last_timestamp=str(clean_df["Date"].iloc[-1]),
            row_count=len(clean_df),
            latest_close=float(clean_df["Close"].iloc[-1])
        )

data_loader_service = DataLoaderService()
