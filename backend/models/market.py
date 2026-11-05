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
    instrument_key: Optional[str] = None
    timeframe: str = "1D"
    data_source: str
    is_synthetic: bool = False
    is_live: bool = False
    is_replay: bool = False
    connection_status: str = "CONNECTED"
    last_timestamp: str
    candle_count: int
    current_price: float
    change_pct: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    candles: List[CandleData]
    indicators: IndicatorSummary
    raw_indicator_series: Optional[Dict[str, List[Optional[float]]]] = None

class InstrumentMetadata(BaseModel):
    id: str
    symbol: str
    name: str
    instrument_key: Optional[str] = None
    file_name: Optional[str] = None
    source: str
    is_synthetic: bool = False
    last_timestamp: str
    row_count: int
    latest_close: float
