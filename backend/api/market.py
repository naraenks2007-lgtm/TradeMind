from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any, Optional
import pandas as pd

from backend.models.market import InstrumentMetadata, MarketSnapshot, CandleData
from backend.services.data_loader import data_loader_service
from backend.services.technical_indicators import technical_indicator_service
from backend.services.upstox_service import upstox_service, UPSTOX_INSTRUMENTS
from backend.services.replay_service import replay_service

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/instruments", response_model=List[InstrumentMetadata])
def get_instruments():
    """Lists all available instruments with verified Upstox instrument keys."""
    instruments = data_loader_service.list_available_instruments()
    
    # Attach official Upstox instrument keys if matched
    for inst in instruments:
        key_match = UPSTOX_INSTRUMENTS.get(inst.id.upper())
        if key_match:
            inst.instrument_key = key_match["instrument_key"]
            inst.name = key_match["display_name"]
            
    return instruments

@router.get("/{instrument_id}", response_model=MarketSnapshot)
def get_market_data(instrument_id: str, limit: int = 180):
    """
    Returns market data for the instrument.
    - If Historical Replay is active: returns strictly look-ahead free snapshot.
    - If Upstox is connected and live: integrates Upstox market quotes.
    - Otherwise: serves verified historical dataset, clearly labeled without claiming live.
    """
    # 1. Check if Historical Replay is active
    if replay_service.is_active and replay_service.instrument_id == instrument_id:
        return replay_service.get_snapshot(limit=limit)

    # 2. Load historical OHLCV baseline
    try:
        df, info = data_loader_service.load_ohlcv_dataframe(instrument_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading data: {e}")

    # Check for live Upstox connection
    upstox_status = upstox_service.get_connection_status()
    is_upstox_live = upstox_status.get("authenticated", False)
    inst_info = UPSTOX_INSTRUMENTS.get(instrument_id.upper())

    live_quote = None
    if is_upstox_live and inst_info:
        try:
            live_quote = upstox_service.get_market_quote(inst_info["instrument_key"])
        except Exception:
            live_quote = None

    # Calculate indicators
    df_with_indicators, ind_summary = technical_indicator_service.calculate_indicators(df)
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
    open_val = float(slice_df["Open"].iloc[-1])
    high_val = float(slice_df["High"].iloc[-1])
    low_val = float(slice_df["Low"].iloc[-1])
    vol_val = float(slice_df["Volume"].iloc[-1])
    
    data_source_label = info["source"]
    is_live_flag = False
    conn_status = "HISTORICAL_MODE"

    # If Upstox live quote available, augment latest bar with live LTP and OHLC
    if live_quote and "last_price" in live_quote:
        live_ltp = float(live_quote["last_price"])
        live_ohlc = live_quote.get("ohlc", {})
        last_close = live_ltp
        if "open" in live_ohlc and live_ohlc["open"]:
            open_val = float(live_ohlc["open"])
        if "high" in live_ohlc and live_ohlc["high"]:
            high_val = float(live_ohlc["high"])
        if "low" in live_ohlc and live_ohlc["low"]:
            low_val = float(live_ohlc["low"])
        if "volume" in live_quote and live_quote["volume"]:
            vol_val = float(live_quote["volume"])

        change_pct = round(float(live_quote.get("net_change", 0.0)) / prev_close * 100, 2) if prev_close else 0.0
        data_source_label = "Upstox Live Feed (Authorized)"
        is_live_flag = True
        conn_status = "CONNECTED"
    else:
        change_pct = round(((last_close - prev_close) / prev_close * 100), 2)
        if is_upstox_live:
            conn_status = "CONNECTED"
        elif upstox_status.get("configured"):
            conn_status = "UPSTOX_TOKEN_REQUIRED"
        else:
            conn_status = "OFFLINE_FALLBACK"

    def clean_val(v):
        if v is None or pd.isna(v):
            return None
        return round(float(v), 2)

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
        instrument_name=inst_info["display_name"] if inst_info else instrument_id.replace("_", " "),
        instrument_key=inst_info["instrument_key"] if inst_info else None,
        timeframe="1D",
        data_source=data_source_label,
        is_synthetic=info.get("is_synthetic") == "True",
        is_live=is_live_flag,
        is_replay=False,
        connection_status=conn_status,
        last_timestamp=info.get("last_timestamp", str(slice_df["Date"].iloc[-1])),
        candle_count=len(candles),
        current_price=last_close,
        change_pct=change_pct,
        open=open_val,
        high=high_val,
        low=low_val,
        close=last_close,
        volume=vol_val,
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
