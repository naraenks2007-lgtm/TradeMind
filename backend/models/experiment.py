from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentExperimentResult(BaseModel):
    agent_id: str
    agent_name: str
    has_memory: bool
    market_direction: str
    hypothesis_summary: str
    confidence: float
    entry_price: float
    stop_loss: float
    target: float
    supporting_factors: List[str]
    recalled_lessons_used: List[str] = []
    trade_outcome: Optional[str] = None
    realized_pnl_pct: Optional[float] = None
    was_direction_correct: Optional[bool] = None
    repeated_known_mistake: bool = False

class ScenarioEvaluation(BaseModel):
    scenario_id: str
    instrument: str
    decision_date: str
    evaluation_date: str
    decision_close_price: float
    future_close_price: float
    actual_return_pct: float
    actual_market_trend: str
    agent_a_no_memory: AgentExperimentResult
    agent_b_with_memory: AgentExperimentResult

class ExperimentReport(BaseModel):
    total_scenarios_evaluated: int
    agent_a_metrics: Dict[str, Any]
    agent_b_metrics: Dict[str, Any]
    scenarios: List[ScenarioEvaluation]
    summary_analysis: str
    disclaimer: str = (
        "DISCLAIMER: Improved performance of Agent B (with Hindsight memory) represents an experimental backtest result "
        "on historical data. It does not constitute financial advice or guarantee future trading performance."
    )
