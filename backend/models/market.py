from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CandleData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class IndicatorSummary(BaseModel):
    rsi: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    ema200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr: Optional[float] = None
    trend_summary: Optional[str] = "NEUTRAL"
    volatility_summary: Optional[str] = "NORMAL"

class MarketSnapshot(BaseModel):
    symbol: str
    instrument_name: str
    timeframe: str = "1D"
    data_source: str
    is_synthetic: bool = False
    last_timestamp: str
    candle_count: int
    current_price: float
    change_pct: float
    candles: List[CandleData]
    indicators: IndicatorSummary
    raw_indicator_series: Optional[Dict[str, List[Optional[float]]]] = None

class InstrumentMetadata(BaseModel):
    id: str
    symbol: str
    name: str
    file_name: str
    source: str
    is_synthetic: bool
    last_timestamp: str
    row_count: int
    latest_close: float
