import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from groq import Groq
from pydantic import ValidationError

from backend.config import settings
from backend.models.hypothesis import TradingHypothesis, MarketDirection, MarketChatResponse
from backend.models.market import MarketSnapshot, IndicatorSummary
from backend.models.ml import MLAnalysisResult
from backend.models.paper_trading import PortfolioState
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
        user_notes: Optional[str] = None,
        ml_analysis: Optional[MLAnalysisResult] = None
    ) -> TradingHypothesis:
        if not self.client:
            raise RuntimeError("Groq LLM Client is not initialized. Please set GROQ_API_KEY.")

        indicators = snapshot.indicators
        current_price = snapshot.current_price
        
        # 1. Retrieve Hindsight long-term memories if requested
        recalled_lessons = []
        memory_context_str = "No historical long-term memories retrieved."
        
        if include_memory:
            ml_context_tag = f"ML_DIR={ml_analysis.direction.direction}" if ml_analysis else ""
            query = (
                f"Trading {snapshot.symbol} {ml_context_tag} under {indicators.trend_summary} trend with "
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
                reflection = hindsight_service.reflect_lessons(query=query)
                if reflection:
                    recalled_lessons = [reflection]
                    memory_context_str = f"HINDSIGHT HISTORICAL REFLECTION:\n{reflection}"

        # 2. Build ML Context Section
        ml_section = ""
        if ml_analysis:
            ml_section = f"""
TABULAR MACHINE LEARNING MODELS OUTPUT (Scikit-Learn Random Forest & Gradient Boosting):
- Direction Prediction: {ml_analysis.direction.direction} (Confidence: {ml_analysis.direction.confidence * 100:.1f}%)
- Direction Probabilities: {json.dumps(ml_analysis.direction.probabilities)}
- Forecasted Volatility: {ml_analysis.volatility.predicted_volatility_pct}% (Regime: {ml_analysis.volatility.volatility_regime})
- Projected ATR Move: ₹{ml_analysis.volatility.atr_forecast:,.2f}
- Price-Action & Flow Sentiment Score: {ml_analysis.sentiment.sentiment_score} ({ml_analysis.sentiment.sentiment_label})
- Buying Pressure Estimate: {ml_analysis.sentiment.buying_pressure_pct}%
- Top Driving Features: {', '.join([f"{f['feature']} (val={f['current_value']:.3f})" for f in ml_analysis.direction.top_features])}
"""

        # 3. Build verified prompt
        system_prompt = (
            "You are TradeMind AI, an institutional-grade quantitative trading strategist and explanation engine.\n\n"
            "CRITICAL ARCHITECTURAL ROLES:\n"
            "1. You are NOT trained on stock data and do NOT fabricate indicator or price values.\n"
            "2. Specialized smaller tabular ML models provide the Direction probabilities, Volatility forecast, and Sentiment.\n"
            "3. Your exclusive role is REASONING and EXPLANATION: synthesize the ML predictions, deterministic technical indicators, "
            "and historical Hindsight memories into a clear, reasoned trading thesis.\n"
            "4. Always output strictly valid JSON conforming exactly to the requested schema.\n"
            "5. Specify clear numerical levels for entry, stop_loss, target, support_level, and resistance_level that respect the ML volatility forecast.\n"
            "6. If historical Hindsight memories are provided, integrate them to avoid repeating past mistakes."
        )

        user_prompt = f"""
INSTRUMENT: {snapshot.instrument_name} ({snapshot.symbol})
CURRENT MARKET CLOSE: ₹{current_price:,.2f}
LATEST TIMESTAMP: {snapshot.last_timestamp}
DATA SOURCE: {snapshot.data_source} (Synthetic: {snapshot.is_synthetic})

{ml_section}

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

Please provide reasoning and explanation for this market setup. You MUST respond with a JSON object containing EXACTLY these keys:
{{
  "instrument": "{snapshot.symbol}",
  "market_direction": "{ml_analysis.direction.direction if ml_analysis else 'BULLISH'}",
  "hypothesis": "Detailed quantitative thesis explaining the reasoning behind the ML model forecast and indicator alignment",
  "supporting_evidence": ["Evidence 1 referencing actual ML probability and indicator", "Evidence 2", "Evidence 3"],
  "confidence": {ml_analysis.direction.confidence if ml_analysis else 0.72},
  "entry_condition": "e.g., Pullback confirmation to EMA 20 or breakout above resistance",
  "entry_assumption": {current_price},
  "stop_loss_assumption": {round(current_price * 0.985, 2)},
  "target_assumption": {round(current_price * 1.035, 2)},
  "support_level": {round(indicators.bb_lower or current_price * 0.98, 2)},
  "resistance_level": {round(indicators.bb_upper or current_price * 1.02, 2)},
  "invalidation_conditions": ["Condition 1 breaking key support/resistance", "Condition 2 volume or volatility anomaly"],
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
            
            if "instrument" not in parsed:
                parsed["instrument"] = snapshot.symbol
                
            hypothesis = TradingHypothesis(**parsed)
            hypothesis.data_source = snapshot.data_source
            hypothesis.data_timestamp = snapshot.last_timestamp
            hypothesis.memory_applied = include_memory and len(recalled_lessons) > 0
            hypothesis.recalled_lessons = recalled_lessons
            hypothesis.created_at = datetime.now().isoformat()
            
            # Retain newly generated decision context into Hindsight
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
                    metadata={"instrument": str(snapshot.symbol), "timestamp": str(snapshot.last_timestamp)}
                )
                
            return hypothesis
            
        except ValidationError as ve:
            logger.error(f"Pydantic validation error from LLM response: {ve}")
            return self._build_deterministic_fallback_hypothesis(snapshot, include_memory, recalled_lessons, str(ve))
        except Exception as e:
            logger.error(f"Groq LLM generation error: {e}")
            raise RuntimeError(f"Groq LLM generation failed: {e}")

    def chat_analysis(
        self,
        message: str,
        snapshot: MarketSnapshot,
        portfolio: Optional[PortfolioState] = None,
        include_memory: bool = True
    ) -> MarketChatResponse:
        """
        Answers user market queries using Groq LLM integrated with real market data,
        indicators, portfolio history, and Hindsight long-term memories.
        """
        if not self.client:
            raise RuntimeError("Groq LLM Client is not initialized.")

        ind = snapshot.indicators
        recalled_memories = []
        if include_memory:
            query = f"{snapshot.symbol} {message} {ind.trend_summary} RSI={ind.rsi}"
            items = hindsight_service.recall_memories(query=query, tags=[snapshot.symbol], limit=3)
            recalled_memories = [m.content for m in items]

        portfolio_info = "No active portfolio info provided."
        if portfolio:
            portfolio_info = (
                f"Virtual Cash: ₹{portfolio.available_cash:,.2f}, Total Equity: ₹{portfolio.total_equity:,.2f}, "
                f"Realized P&L: ₹{portfolio.total_realized_pnl:,.2f}, Win Rate: {portfolio.win_rate}%, "
                f"Open Positions: {len(portfolio.open_positions)}, Max Drawdown: {portfolio.max_drawdown_pct}%"
            )

        system_prompt = (
            "You are TradeMind AI, an institutional-grade quantitative market analyst. "
            "You answer queries regarding market trends, support/resistance, indicator divergence, "
            "paper-trading risk management, and past trade lessons. "
            "Base your answer strictly on the provided real data and Hindsight memories. "
            "Do not fabricate prices or promise guaranteed profits."
        )

        user_content = f"""
USER QUERY: {message}

CURRENT MARKET DATA:
- Instrument: {snapshot.instrument_name} ({snapshot.symbol})
- Current Price: ₹{snapshot.current_price:,.2f}
- Data Source: {snapshot.data_source} (Timestamp: {snapshot.last_timestamp})
- Day Change: {snapshot.change_pct}%
- OHLC: O=₹{snapshot.open or snapshot.current_price:,.2f}, H=₹{snapshot.high or snapshot.current_price:,.2f}, L=₹{snapshot.low or snapshot.current_price:,.2f}, C=₹{snapshot.current_price:,.2f}
- Volume: {snapshot.volume or 'N/A'}

TECHNICAL INDICATORS:
- Trend: {ind.trend_summary}
- Volatility: {ind.volatility_summary}
- RSI (14): {ind.rsi}
- EMA 20: ₹{ind.ema20:,.2f} | EMA 50: ₹{ind.ema50:,.2f} | EMA 200: {f"₹{ind.ema200:,.2f}" if ind.ema200 else 'N/A'}
- MACD Line: {ind.macd} | Signal: {ind.macd_signal} | Histogram: {ind.macd_hist}
- Bollinger Upper: ₹{ind.bb_upper:,.2f} | Middle: ₹{ind.bb_middle:,.2f} | Lower: ₹{ind.bb_lower:,.2f}
- ATR (14): ₹{ind.atr:,.2f}

PORTFOLIO & PAPER TRADING STATE:
{portfolio_info}

RECALLED HINDSIGHT MEMORIES:
{chr(10).join([f"- {m}" for m in recalled_memories]) if recalled_memories else "None"}

Provide a direct, insightful, quantitative answer formatted in clean Markdown.
Highlight key support/resistance levels, indicator readings, and risk considerations.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content

        return MarketChatResponse(
            answer=answer,
            instrument=snapshot.symbol,
            current_price=snapshot.current_price,
            data_source=snapshot.data_source,
            data_timestamp=snapshot.last_timestamp,
            recalled_memories=recalled_memories
        )


    def general_chat(self, message: str, session_id: Optional[str] = None) -> MarketChatResponse:
        """General assistant responses that do not require market snapshot construction."""
        if not self.client:
            raise RuntimeError("Groq LLM Client is not initialized. Please set GROQ_API_KEY.")
        recalled_memories = []
        try:
            items = hindsight_service.recall_memories(query=message, tags=["trademind_session_" + session_id] if session_id else None, limit=3)
            recalled_memories = [item.content for item in items]
        except Exception:
            pass
        system_prompt = (
            "You are TradeMind, a helpful conversational AI assistant. "
            "Answer greetings, general knowledge, explanations, and everyday questions naturally. "
            "Do not force every conversation into stock-market analysis. "
            "If a question needs current information you do not have, say so clearly. "
            "Never claim a personal fact was saved unless the memory service confirms it."
        )
        memory_context = "\\n".join(f"- {item}" for item in recalled_memories) or "No relevant memories."
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt + "\\nRelevant recalled context:\\n" + memory_context},
                {"role": "user", "content": message}
            ],
            temperature=0.4
        )
        return MarketChatResponse(
            answer=response.choices[0].message.content or "I couldn't generate a response. Please try again.",
            instrument="GENERAL",
            current_price=0.0,
            data_source="TradeMind AI",
            data_timestamp=datetime.now().astimezone().isoformat(),
            recalled_memories=recalled_memories
        )

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
            entry_condition="Test and hold of 20-period exponential moving average",
            entry_assumption=entry,
            stop_loss_assumption=sl,
            target_assumption=target,
            support_level=round(ind.bb_lower or cp * 0.98, 2),
            resistance_level=round(ind.bb_upper or cp * 1.02, 2),
            invalidation_conditions=[
                f"Price crosses stop-loss level of ₹{sl:,.2f}",
                "Opposing volume expansion"
            ],
            risk_explanation=f"Calculated using deterministic fallback due to formatting constraint: {err_msg[:60]}",
            data_source=snapshot.data_source,
            data_timestamp=snapshot.last_timestamp,
            memory_applied=include_memory and len(recalled_lessons) > 0,
            recalled_lessons=recalled_lessons,
            created_at=datetime.now().isoformat()
        )

llm_service = LLMService()
