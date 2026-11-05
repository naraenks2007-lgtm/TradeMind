from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import pandas as pd

from backend.models.hypothesis import (
    TradingHypothesis,
    HypothesisRequest,
    MarketChatRequest,
    MarketChatResponse
)
from backend.services.data_loader import data_loader_service
from backend.services.technical_indicators import technical_indicator_service
from backend.services.llm_service import llm_service
from backend.services.replay_service import replay_service
from backend.services.upstox_service import upstox_service, UPSTOX_INSTRUMENTS
from backend.services.paper_trading_service import paper_trading_service
from backend.models.market import MarketSnapshot, CandleData

router = APIRouter(prefix="/api/hypothesis", tags=["Hypothesis Generator & AI Analysis"])

def _get_active_snapshot(instrument_id: str) -> MarketSnapshot:
    """Retrieves snapshot respecting active replay mode or Upstox live connection."""
    # If historical replay is active
    if replay_service.is_active and replay_service.instrument_id == instrument_id:
        return replay_service.get_snapshot(limit=120)

    # Historical data baseline
    df, info = data_loader_service.load_ohlcv_dataframe(instrument_id)
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
    open_val = float(recent_slice["Open"].iloc[-1])
    high_val = float(recent_slice["High"].iloc[-1])
    low_val = float(recent_slice["Low"].iloc[-1])
    vol_val = float(recent_slice["Volume"].iloc[-1])
    data_source_str = info["source"]
    is_live = False

    # Check for live Upstox feed
    upstox_status = upstox_service.get_connection_status()
    inst_info = UPSTOX_INSTRUMENTS.get(instrument_id.upper())
    if upstox_status.get("authenticated") and inst_info:
        try:
            quote = upstox_service.get_market_quote(inst_info["instrument_key"])
            if quote and "last_price" in quote:
                last_close = float(quote["last_price"])
                data_source_str = "Upstox Live Feed (Authorized)"
                is_live = True
        except Exception:
            pass

    change_pct = round(((last_close - prev_close) / prev_close * 100), 2)

    return MarketSnapshot(
        symbol=instrument_id,
        instrument_name=inst_info["display_name"] if inst_info else instrument_id.replace("_", " "),
        instrument_key=inst_info["instrument_key"] if inst_info else None,
        timeframe="1D",
        data_source=data_source_str,
        is_synthetic=info.get("is_synthetic") == "True",
        is_live=is_live,
        is_replay=False,
        connection_status="CONNECTED" if is_live else "HISTORICAL",
        last_timestamp=info.get("last_timestamp", str(recent_slice["Date"].iloc[-1])),
        candle_count=len(candles),
        current_price=last_close,
        change_pct=change_pct,
        open=open_val,
        high=high_val,
        low=low_val,
        close=last_close,
        volume=vol_val,
        candles=candles,
        indicators=ind_summary
    )

@router.post("/generate", response_model=TradingHypothesis)
def generate_trading_hypothesis(req: HypothesisRequest, x_trademind_session: Optional[str] = Header(default=None)):
    """Generates structured institutional trading hypothesis using Groq LLM and Hindsight memory."""
    try:
        snapshot = _get_active_snapshot(req.instrument_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Instrument '{req.instrument_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        hypothesis = llm_service.generate_hypothesis(
            snapshot=snapshot,
            include_memory=req.include_memory,
            user_notes=req.user_context,
            session_id=x_trademind_session
        )
        return hypothesis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Hypothesis generation failed: {e}")

@router.post("/chat", response_model=MarketChatResponse)
def chat_with_groq(req: MarketChatRequest):
    """Conversational market analysis powered by Groq, real data, and Hindsight memory."""
    try:
        snapshot = _get_active_snapshot(req.instrument_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load data for {req.instrument_id}: {e}")

    try:
        portfolio = paper_trading_service.get_portfolio_state({snapshot.symbol: snapshot.current_price})
        res = llm_service.chat_analysis(
            message=req.message,
            snapshot=snapshot,
            portfolio=portfolio,
            include_memory=req.include_memory
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat analysis failed: {e}")
