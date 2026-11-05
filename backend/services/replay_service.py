import os
import logging
from typing import Dict, Any, Optional, List
import pandas as pd

from backend.models.market import CandleData, MarketSnapshot, IndicatorSummary
from backend.services.data_loader import data_loader_service
from backend.services.technical_indicators import technical_indicator_service
from backend.services.paper_trading_service import paper_trading_service

logger = logging.getLogger(__name__)

class ReplayService:
    """
    Historical Replay Engine with strict look-ahead bias prevention.
    
    CRITICAL RULE:
    Candles and indicators are strictly bounded to the simulated current time.
    Future data points are completely hidden from the AI models and the paper trading engine.
    """
    def __init__(self):
        self.is_active: bool = False
        self.is_playing: bool = False
        self.instrument_id: str = "NIFTY_50"
        self.speed: int = 1  # 1x, 2x, 5x, 10x, 20x, 50x
        self.current_index: int = 50  # Start with enough historical bars for indicators
        self._df: Optional[pd.DataFrame] = None
        self._info: Optional[Dict[str, str]] = None

    def _ensure_loaded(self, instrument_id: str):
        if self._df is None or self.instrument_id != instrument_id:
            df, info = data_loader_service.load_ohlcv_dataframe(instrument_id)
            self._df = df.copy()
            self._info = info
            self.instrument_id = instrument_id
            # Set initial index to min(50, len(df) - 1)
            self.current_index = min(50, len(df) - 1)

    def start_replay(self, instrument_id: str = "NIFTY_50", start_date: Optional[str] = None) -> Dict[str, Any]:
        """Initializes replay mode for an instrument."""
        self._ensure_loaded(instrument_id)
        if start_date and self._df is not None:
            matches = self._df.index[self._df["Date"] >= start_date].tolist()
            if matches:
                self.current_index = max(30, matches[0])
            else:
                self.current_index = 50
        else:
            self.current_index = min(50, len(self._df) - 1) if self._df is not None else 0

        self.is_active = True
        self.is_playing = False
        return self.get_state()

    def stop_replay(self) -> Dict[str, Any]:
        """Stops replay and returns to live/standard mode."""
        self.is_active = False
        self.is_playing = False
        return {"is_active": False, "status": "STOPPED"}

    def set_speed(self, speed: int) -> int:
        """Sets playback speed multiplier (1, 2, 5, 10, 20, 50)."""
        valid_speeds = [1, 2, 5, 10, 20, 50]
        if speed in valid_speeds:
            self.speed = speed
        return self.speed

    def step(self, steps: int = 1) -> Dict[str, Any]:
        """
        Advances the replay by 1 or more candles.
        Updates paper trading positions against the newly revealed candle price.
        """
        if not self.is_active:
            self.start_replay(self.instrument_id)

        if self._df is not None:
            max_idx = len(self._df) - 1
            self.current_index = min(max_idx, self.current_index + steps)
            
            # Current price for paper trading
            cur_candle = self._df.iloc[self.current_index]
            cur_price = float(cur_candle["Close"])
            
            # Check stops and targets against current replay candle
            paper_trading_service.get_portfolio_state({self.instrument_id: cur_price})

        return self.get_state()

    def jump_to_date(self, target_date: str) -> Dict[str, Any]:
        """Jumps directly to a specific historical date."""
        self._ensure_loaded(self.instrument_id)
        if self._df is not None:
            matches = self._df.index[self._df["Date"] >= target_date].tolist()
            if matches:
                self.current_index = max(30, matches[0])
        return self.get_state()

    def get_snapshot(self, limit: int = 180) -> MarketSnapshot:
        """
        Builds a strictly look-ahead-free MarketSnapshot up to the current simulated candle.
        Future data is completely omitted.
        """
        self._ensure_loaded(self.instrument_id)
        if self._df is None or len(self._df) == 0:
            raise ValueError(f"No data available for {self.instrument_id}")

        # Strict look-ahead prevention: slice dataframe ONLY up to current_index
        visible_df = self._df.iloc[:self.current_index + 1].copy()
        
        # Calculate technical indicators strictly on visible data
        df_with_ind, ind_summary = technical_indicator_service.calculate_indicators(visible_df)
        
        # Slice for chart rendering
        display_slice = df_with_ind.tail(limit)
        
        candles = [
            CandleData(
                date=str(row["Date"]),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"])
            )
            for _, row in display_slice.iterrows()
        ]
        
        latest_row = visible_df.iloc[-1]
        last_close = float(latest_row["Close"])
        prev_close = float(visible_df["Close"].iloc[-2]) if len(visible_df) > 1 else last_close
        change_pct = round(((last_close - prev_close) / prev_close * 100), 2)

        def clean_val(v):
            if v is None or pd.isna(v):
                return None
            return round(float(v), 2)

        raw_series = {
            "rsi": [clean_val(v) for v in display_slice["RSI"]] if "RSI" in display_slice.columns else [],
            "ema20": [clean_val(v) for v in display_slice["EMA_20"]] if "EMA_20" in display_slice.columns else [],
            "ema50": [clean_val(v) for v in display_slice["EMA_50"]] if "EMA_50" in display_slice.columns else [],
            "macd": [clean_val(v) for v in display_slice["MACD"]] if "MACD" in display_slice.columns else [],
            "macd_signal": [clean_val(v) for v in display_slice["MACD_SIGNAL"]] if "MACD_SIGNAL" in display_slice.columns else [],
            "macd_hist": [clean_val(v) for v in display_slice["MACD_HIST"]] if "MACD_HIST" in display_slice.columns else [],
            "bb_upper": [clean_val(v) for v in display_slice["BB_UPPER"]] if "BB_UPPER" in display_slice.columns else [],
            "bb_lower": [clean_val(v) for v in display_slice["BB_LOWER"]] if "BB_LOWER" in display_slice.columns else []
        }

        return MarketSnapshot(
            symbol=self.instrument_id,
            instrument_name=self.instrument_id.replace("_", " "),
            timeframe="1D",
            data_source="HISTORICAL REPLAY (No Look-Ahead)",
            is_synthetic=False,
            is_live=False,
            is_replay=True,
            connection_status="REPLAY_SIMULATION",
            last_timestamp=str(latest_row["Date"]),
            candle_count=len(candles),
            current_price=last_close,
            change_pct=change_pct,
            open=float(latest_row["Open"]),
            high=float(latest_row["High"]),
            low=float(latest_row["Low"]),
            close=last_close,
            volume=float(latest_row["Volume"]),
            candles=candles,
            indicators=ind_summary,
            raw_indicator_series=raw_series
        )

    def get_state(self) -> Dict[str, Any]:
        """Returns the current replay operational status and progress."""
        if self._df is None:
            self._ensure_loaded(self.instrument_id)

        total = len(self._df) if self._df is not None else 0
        cur_row = self._df.iloc[self.current_index] if self._df is not None and len(self._df) > 0 else None
        
        return {
            "is_active": self.is_active,
            "is_playing": self.is_playing,
            "instrument_id": self.instrument_id,
            "speed": self.speed,
            "current_index": self.current_index,
            "total_candles": total,
            "current_date": str(cur_row["Date"]) if cur_row is not None else None,
            "current_price": float(cur_row["Close"]) if cur_row is not None else 0.0,
            "progress_pct": round(((self.current_index + 1) / total * 100), 1) if total > 0 else 0.0
        }

replay_service = ReplayService()
