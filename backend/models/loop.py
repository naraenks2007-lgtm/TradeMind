from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.models.ml import MLAnalysisResult
from backend.models.hypothesis import TradingHypothesis
from backend.models.paper_trading import PaperOrder
from backend.models.memory import MemoryItem

class LoopStep(BaseModel):
    step_number: int
    name: str
    status: str = "completed"
    summary: str
    details: Dict[str, Any]

class CompellingLoopResponse(BaseModel):
    loop_id: str
    instrument: str
    timestamp: str
    
    # 6 Distinct Stages of the Loop
    step1_market_data: Dict[str, Any]
    step2_ml_analysis: MLAnalysisResult
    step3_hindsight_recall: Dict[str, Any]
    step4_groq_explanation: TradingHypothesis
    step5_paper_trading_result: Dict[str, Any]
    step6_hindsight_lesson_reply: Dict[str, Any]
    
    # Execution Timeline & Verdict
    summary_verdict: str
    execution_time_seconds: float
