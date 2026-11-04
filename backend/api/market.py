from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import pandas as pd

from backend.models.market import InstrumentMetadata, MarketSnapshot, CandleData
from backend.services.data_loader import data_loader_service
from backend.services.technical_indicators import technical_indicator_service

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/instruments", response_model=List[InstrumentMetadata])
def get_instruments():
    return data_loader_service.list_available_instruments()

@router.get("/{instrument_id}", response_model=MarketSnapshot)
def get_market_data(instrument_id: str, limit: int = 180):
    try:
        df, info = data_loader_service.load_ohlcv_dataframe(instrument_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading data: {e}")

    # Calculate Python-powered technical indicators
    df_with_indicators, ind_summary = technical_indicator_service.calculate_indicators(df)

    # Slice latest bars for response
    slice_df = df_with_indicators.tail(limit)

    candles = [
        CandleData(
            date=str(row["Date"]),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"])
        )
        for _, row in slice_df.iterrows()
    ]

    last_close = float(slice_df["Close"].iloc[-1])
    prev_close = float(slice_df["Close"].iloc[-2]) if len(slice_df) > 1 else last_close
    change_pct = round(((last_close - prev_close) / prev_close * 100), 2)

    def clean_val(v):
        if v is None or pd.isna(v):
            return None
        return round(float(v), 2)

    # Indicator series for chart overlays
    raw_series = {
        "rsi": [clean_val(v) for v in slice_df["RSI"]] if "RSI" in slice_df.columns else [],
        "ema20": [clean_val(v) for v in slice_df["EMA_20"]] if "EMA_20" in slice_df.columns else [],
        "ema50": [clean_val(v) for v in slice_df["EMA_50"]] if "EMA_50" in slice_df.columns else [],
        "macd": [clean_val(v) for v in slice_df["MACD"]] if "MACD" in slice_df.columns else [],
        "macd_signal": [clean_val(v) for v in slice_df["MACD_SIGNAL"]] if "MACD_SIGNAL" in slice_df.columns else [],
        "macd_hist": [clean_val(v) for v in slice_df["MACD_HIST"]] if "MACD_HIST" in slice_df.columns else [],
        "bb_upper": [clean_val(v) for v in slice_df["BB_UPPER"]] if "BB_UPPER" in slice_df.columns else [],
        "bb_lower": [clean_val(v) for v in slice_df["BB_LOWER"]] if "BB_LOWER" in slice_df.columns else []
    }

    return MarketSnapshot(
        symbol=instrument_id,
        instrument_name=instrument_id.replace("_", " "),
        timeframe="1D",
        data_source=info["source"],
        is_synthetic=info["is_synthetic"] == "True",
        last_timestamp=info["last_timestamp"],
        candle_count=len(candles),
        current_price=last_close,
        change_pct=change_pct,
        candles=candles,
        indicators=ind_summary,
        raw_indicator_series=raw_series
    )

@router.post("/upload", response_model=InstrumentMetadata)
async def upload_csv_data(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    try:
        content = await file.read()
        meta = data_loader_service.save_uploaded_csv(file.filename, content)
        return meta
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV structure: {e}")
