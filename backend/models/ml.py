from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class DirectionPrediction(BaseModel):
    direction: str = Field(description="Predicted price direction: BULLISH, BEARISH, or NEUTRAL")
    confidence: float = Field(ge=0.0, le=1.0, description="Highest probability confidence score")
    probabilities: Dict[str, float] = Field(description="Probability distribution across classes")
    top_features: List[Dict[str, Any]] = Field(description="Key tabular features driving the prediction")

class VolatilityPrediction(BaseModel):
    predicted_volatility_pct: float = Field(description="Forecasted 5-day annualized volatility %")
    volatility_regime: str = Field(description="Regime: LOW_COMPRESSION, NORMAL, or HIGH_EXPANSION")
    atr_forecast: float = Field(description="Projected Average True Range in rupees")

class SentimentPrediction(BaseModel):
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Score from -1.0 (Extreme Bearish) to +1.0 (Extreme Bullish)")
    sentiment_label: str = Field(description="Categorical sentiment label")
    buying_pressure_pct: float = Field(description="Estimated institutional buying pressure %")

class MLAnalysisResult(BaseModel):
    instrument: str
    timestamp: str
    current_price: float
    direction: DirectionPrediction
    volatility: VolatilityPrediction
    sentiment: SentimentPrediction
    model_metadata: Dict[str, Any]
