from fastapi import APIRouter, HTTPException
import pandas as pd

from backend.models.hypothesis import TradingHypothesis, HypothesisRequest
from backend.services.data_loader import data_loader_service
from backend.services.technical_indicators import technical_indicator_service
from backend.services.llm_service import llm_service
from backend.models.market import MarketSnapshot, CandleData

router = APIRouter(prefix="/api/hypothesis", tags=["Hypothesis Generator"])

@router.post("/generate", response_model=TradingHypothesis)
def generate_trading_hypothesis(req: HypothesisRequest):
    try:
        df, info = data_loader_service.load_ohlcv_dataframe(req.instrument_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Instrument '{req.instrument_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Calculate indicators
    df_with_ind, ind_summary = technical_indicator_service.calculate_indicators(df)
    
    recent_slice = df_with_ind.tail(120)
    candles = [
        CandleData(
            date=str(row["Date"]),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"])
        )
        for _, row in recent_slice.iterrows()
    ]
    
    last_close = float(recent_slice["Close"].iloc[-1])
    prev_close = float(recent_slice["Close"].iloc[-2]) if len(recent_slice) > 1 else last_close
    change_pct = round(((last_close - prev_close) / prev_close * 100), 2)
    
    snapshot = MarketSnapshot(
        symbol=req.instrument_id,
        instrument_name=req.instrument_id.replace("_", " "),
        timeframe="1D",
        data_source=info["source"],
        is_synthetic=info["is_synthetic"] == "True",
        last_timestamp=info["last_timestamp"],
        candle_count=len(candles),
        current_price=last_close,
        change_pct=change_pct,
        candles=candles,
        indicators=ind_summary
    )

    try:
        hypothesis = llm_service.generate_hypothesis(
            snapshot=snapshot,
            include_memory=req.include_memory,
            user_notes=req.user_context
        )
        return hypothesis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Hypothesis generation failed: {e}")
