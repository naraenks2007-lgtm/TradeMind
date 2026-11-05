from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class MarketDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class TradingHypothesis(BaseModel):
    instrument: str = Field(description="Ticker or instrument identifier, e.g. NIFTY_50")
    market_direction: MarketDirection = Field(description="Projected market direction: BULLISH, BEARISH, or NEUTRAL")
    hypothesis: str = Field(description="Core trading thesis synthesizing price action and indicators")
    supporting_evidence: List[str] = Field(description="Specific technical indicator readings and pattern evidence")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    entry_condition: Optional[str] = Field(default=None, description="Conditional trigger requirement for trade entry")
    entry_assumption: float = Field(description="Assumed optimal entry price level")
    stop_loss_assumption: float = Field(description="Explicit price level for thesis invalidation and risk cutoff")
    target_assumption: float = Field(description="Target take-profit price level")
    support_level: Optional[float] = Field(default=None, description="Identified key support level")
    resistance_level: Optional[float] = Field(default=None, description="Identified key resistance level")
    invalidation_conditions: List[str] = Field(description="Specific market events or price breaks that negate the thesis")
    risk_explanation: str = Field(description="Comprehensive explanation of downside risks, volatility, and execution pitfalls")
    
    # Metadata for TradeMind data audit & Hindsight memory
    data_source: Optional[str] = None
    data_timestamp: Optional[str] = None
    memory_applied: bool = False
    recalled_lessons: Optional[List[str]] = None
    created_at: Optional[str] = None

class HypothesisRequest(BaseModel):
    instrument_id: str
    include_memory: bool = True
    user_context: Optional[str] = None

class MarketChatRequest(BaseModel):
    instrument_id: str
    message: str
    include_memory: bool = True

class MarketChatResponse(BaseModel):
    answer: str
    instrument: str
    current_price: float
    data_source: str
    data_timestamp: str
    recalled_memories: List[str] = []
    hypothesis: Optional[TradingHypothesis] = None
