import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from groq import Groq
from pydantic import ValidationError

from backend.config import settings
from backend.models.hypothesis import TradingHypothesis, MarketDirection
from backend.models.market import MarketSnapshot, IndicatorSummary
from backend.services.hindsight_service import hindsight_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key, timeout=25.0)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None

    def check_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"connected": False, "error": "GROQ_API_KEY not configured"}
        if not self.client:
            return {"connected": False, "error": "Groq client not initialized"}
        try:
            # Check model availability
            models = self.client.models.list()
            available = [m.id for m in models.data]
            return {
                "connected": True,
                "model": self.model,
                "is_model_available": self.model in available,
                "available_models_sample": available[:5]
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def generate_hypothesis(
        self,
        snapshot: MarketSnapshot,
        include_memory: bool = True,
        user_notes: Optional[str] = None
    ) -> TradingHypothesis:
        if not self.client:
            raise RuntimeError("Groq LLM Client is not initialized. Please set GROQ_API_KEY.")

        indicators = snapshot.indicators
        current_price = snapshot.current_price
        
        # 1. Retrieve Hindsight long-term memories if requested
        recalled_lessons = []
        memory_context_str = "No historical long-term memories retrieved."
        
        if include_memory:
            query = (
                f"Trading {snapshot.symbol} under {indicators.trend_summary} trend with "
                f"RSI={indicators.rsi}, MACD={indicators.macd}, Volatility={indicators.volatility_summary}. "
                f"Past mistakes, lessons learned, and high probability setups."
            )
            recalled_items = hindsight_service.recall_memories(query=query, limit=4)
            if recalled_items:
                recalled_lessons = [item.content for item in recalled_items]
                memory_context_str = "RECALLED PREVIOUS EXPERIENCES & LESSONS (FROM HINDSIGHT):\n" + "\n".join(
                    [f"- {l}" for l in recalled_lessons]
                )
            else:
                # Try reflection if recall is empty
                reflection = hindsight_service.reflect_lessons(query=query)
                if reflection:
                    recalled_lessons = [reflection]
                    memory_context_str = f"HINDSIGHT HISTORICAL REFLECTION:\n{reflection}"

        # 2. Build verified prompt with exact Python-calculated technical indicator data
        system_prompt = (
            "You are TradeMind AI, an institutional-grade quantitative trading strategist specializing in Indian equities "
            "(NSE/NIFTY/BANKNIFTY/Bluechips). Your task is to formulate a disciplined, probabilistic trading hypothesis.\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT invent or alter technical indicator numbers. Use ONLY the exact calculated indicator values provided.\n"
            "2. Always output strictly valid JSON conforming exactly to the requested schema.\n"
            "3. Specify clear, realistic numerical levels for entry, stop_loss, and target.\n"
            "4. For BULLISH: stop_loss < entry_price < target. For BEARISH: target < entry_price < stop_loss.\n"
            "5. If historical memory lessons are provided, directly integrate them to avoid repeating past mistakes.\n"
            "6. Never claim certainty; present market direction as BULLISH, BEARISH, or NEUTRAL with calibrated confidence (0.0 to 1.0)."
        )

        user_prompt = f"""
INSTRUMENT: {snapshot.instrument_name} ({snapshot.symbol})
CURRENT MARKET CLOSE: ₹{current_price:,.2f}
LATEST TIMESTAMP: {snapshot.last_timestamp}
DATA SOURCE: {snapshot.data_source} (Synthetic: {snapshot.is_synthetic})

PYTHON-CALCULATED TECHNICAL INDICATORS (DO NOT ALTER):
- RSI (14): {indicators.rsi if indicators.rsi is not None else 'N/A'}
- EMA 20: ₹{indicators.ema20:,.2f} ({"Above" if indicators.ema20 and current_price > indicators.ema20 else "Below"} price)
- EMA 50: ₹{indicators.ema50:,.2f} ({"Above" if indicators.ema50 and current_price > indicators.ema50 else "Below"} price)
- EMA 200: {f"₹{indicators.ema200:,.2f}" if indicators.ema200 else 'Insufficient history for EMA200'}
- MACD Line: {indicators.macd if indicators.macd is not None else 'N/A'}
- MACD Signal: {indicators.macd_signal if indicators.macd_signal is not None else 'N/A'}
- MACD Histogram: {indicators.macd_hist if indicators.macd_hist is not None else 'N/A'}
- Bollinger Upper Band: ₹{indicators.bb_upper:,.2f}
- Bollinger Middle (20 SMA): ₹{indicators.bb_middle:,.2f}
- Bollinger Lower Band: ₹{indicators.bb_lower:,.2f}
- ATR (14): ₹{indicators.atr:,.2f}
- Trend Summary: {indicators.trend_summary}
- Volatility State: {indicators.volatility_summary}

{memory_context_str}

USER SPECIFIC NOTES: {user_notes or 'None'}

Please generate a trading hypothesis. You MUST respond with a JSON object containing EXACTLY these keys:
{{
  "instrument": "{snapshot.symbol}",
  "market_direction": "BULLISH" | "BEARISH" | "NEUTRAL",
  "hypothesis": "Detailed quantitative thesis explaining expected price behavior",
  "supporting_evidence": ["Evidence 1 referencing actual indicator values", "Evidence 2", "Evidence 3"],
  "confidence": 0.72,
  "entry_assumption": {current_price},
  "stop_loss_assumption": {round(current_price * 0.985, 2)},
  "target_assumption": {round(current_price * 1.035, 2)},
  "invalidation_conditions": ["Condition 1 breaking key support/resistance", "Condition 2 volume anomaly"],
  "risk_explanation": "Detailed explanation of downside risks, volatility traps, and market context"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            
            # Ensure proper schema fields
            if "instrument" not in parsed:
                parsed["instrument"] = snapshot.symbol
                
            hypothesis = TradingHypothesis(**parsed)
            hypothesis.memory_applied = include_memory and len(recalled_lessons) > 0
            hypothesis.recalled_lessons = recalled_lessons
            hypothesis.created_at = datetime.now().isoformat()
            
            # Retain this newly generated decision context into Hindsight for future learning
            if include_memory:
                decision_summary = (
                    f"Decision for {snapshot.symbol} on {snapshot.last_timestamp}: "
                    f"Direction={hypothesis.market_direction.value}, Confidence={hypothesis.confidence}, "
                    f"Entry={hypothesis.entry_assumption}, SL={hypothesis.stop_loss_assumption}, "
                    f"Target={hypothesis.target_assumption}, RSI={indicators.rsi}, Trend={indicators.trend_summary}. "
                    f"Thesis: {hypothesis.hypothesis}"
                )
                hindsight_service.retain_memory(
                    content=decision_summary,
                    tags=[snapshot.symbol, hypothesis.market_direction.value, "hypothesis_generated"],
                    metadata={"instrument": snapshot.symbol, "timestamp": snapshot.last_timestamp}
                )
                
            return hypothesis
            
        except ValidationError as ve:
            logger.error(f"Pydantic validation error from LLM response: {ve}")
            # Fallback to calibrated deterministic hypothesis
            return self._build_deterministic_fallback_hypothesis(snapshot, include_memory, recalled_lessons, str(ve))
        except Exception as e:
            logger.error(f"Groq API call error: {e}")
            raise RuntimeError(f"Groq LLM generation failed: {e}")

    def _build_deterministic_fallback_hypothesis(
        self,
        snapshot: MarketSnapshot,
        include_memory: bool,
        recalled_lessons: List[str],
        err_msg: str
    ) -> TradingHypothesis:
        ind = snapshot.indicators
        cp = snapshot.current_price
        atr = ind.atr or (cp * 0.015)
        
        direction = MarketDirection.NEUTRAL
        if ind.trend_summary in ["BULLISH", "STRONG_BULLISH"]:
            direction = MarketDirection.BULLISH
            entry = cp
            sl = round(cp - (1.5 * atr), 2)
            target = round(cp + (2.5 * atr), 2)
        elif ind.trend_summary in ["BEARISH", "STRONG_BEARISH"]:
            direction = MarketDirection.BEARISH
            entry = cp
            sl = round(cp + (1.5 * atr), 2)
            target = round(cp - (2.5 * atr), 2)
        else:
            direction = MarketDirection.NEUTRAL
            entry = cp
            sl = round(cp - atr, 2)
            target = round(cp + atr, 2)
            
        return TradingHypothesis(
            instrument=snapshot.symbol,
            market_direction=direction,
            hypothesis=f"Technical alignment on {snapshot.symbol} indicates {direction.value} posture around {cp:,.2f}.",
            supporting_evidence=[
                f"Trend state: {ind.trend_summary}",
                f"RSI 14 at {ind.rsi}",
                f"Bollinger Band width volatility: {ind.volatility_summary}"
            ],
            confidence=0.65,
            entry_assumption=entry,
            stop_loss_assumption=sl,
            target_assumption=target,
            invalidation_conditions=[
                f"Price crosses stop-loss level of ₹{sl:,.2f}",
                "Opposing volume expansion"
            ],
            risk_explanation=f"Calculated using deterministic fallback due to formatting constraint: {err_msg[:60]}",
            memory_applied=include_memory and len(recalled_lessons) > 0,
            recalled_lessons=recalled_lessons,
            created_at=datetime.now().isoformat()
        )

llm_service = LLMService()
