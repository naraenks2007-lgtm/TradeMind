import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import ta

from backend.models.market import IndicatorSummary

class TechnicalIndicatorService:
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> Tuple[pd.DataFrame, IndicatorSummary]:
        if len(df) < 15:
            # Not enough data for robust indicators
            return df, IndicatorSummary()
            
        res_df = df.copy()
        
        # 1. RSI (14)
        rsi_series = ta.momentum.RSIIndicator(close=res_df["Close"], window=14).rsi()
        res_df["RSI"] = rsi_series
        
        # 2. EMAs
        res_df["EMA_20"] = ta.trend.EMAIndicator(close=res_df["Close"], window=20).ema_indicator()
        res_df["EMA_50"] = ta.trend.EMAIndicator(close=res_df["Close"], window=min(50, len(res_df)-1)).ema_indicator()
        if len(res_df) >= 200:
            res_df["EMA_200"] = ta.trend.EMAIndicator(close=res_df["Close"], window=200).ema_indicator()
        else:
            res_df["EMA_200"] = None
            
        # 3. MACD (12, 26, 9)
        macd_indicator = ta.trend.MACD(close=res_df["Close"], window_slow=26, window_fast=12, window_sign=9)
        res_df["MACD"] = macd_indicator.macd()
        res_df["MACD_SIGNAL"] = macd_indicator.macd_signal()
        res_df["MACD_HIST"] = macd_indicator.macd_diff()
        
        # 4. Bollinger Bands (20, 2)
        bb = ta.volatility.BollingerBands(close=res_df["Close"], window=20, window_dev=2)
        res_df["BB_UPPER"] = bb.bollinger_hband()
        res_df["BB_MIDDLE"] = bb.bollinger_mavg()
        res_df["BB_LOWER"] = bb.bollinger_lband()
        
        # 5. ATR (14)
        atr = ta.volatility.AverageTrueRange(high=res_df["High"], low=res_df["Low"], close=res_df["Close"], window=14)
        res_df["ATR"] = atr.average_true_range()
        
        # Extract latest non-null values for summary
        latest = res_df.iloc[-1]
        
        def safe_float(val):
            if val is None or pd.isna(val):
                return None
            return round(float(val), 2)
            
        rsi_val = safe_float(latest.get("RSI"))
        ema20_val = safe_float(latest.get("EMA_20"))
        ema50_val = safe_float(latest.get("EMA_50"))
        ema200_val = safe_float(latest.get("EMA_200"))
        macd_val = safe_float(latest.get("MACD"))
        macd_sig_val = safe_float(latest.get("MACD_SIGNAL"))
        macd_hist_val = safe_float(latest.get("MACD_HIST"))
        bb_upper_val = safe_float(latest.get("BB_UPPER"))
        bb_middle_val = safe_float(latest.get("BB_MIDDLE"))
        bb_lower_val = safe_float(latest.get("BB_LOWER"))
        atr_val = safe_float(latest.get("ATR"))
        
        # Trend summary
        close = float(latest["Close"])
        trend = "NEUTRAL"
        if ema20_val and ema50_val:
            if close > ema20_val and ema20_val > ema50_val:
                trend = "STRONG_BULLISH" if (ema200_val is None or close > ema200_val) else "BULLISH"
            elif close < ema20_val and ema20_val < ema50_val:
                trend = "STRONG_BEARISH" if (ema200_val is None or close < ema200_val) else "BEARISH"
                
        # Volatility summary
        vol = "NORMAL"
        if bb_upper_val and bb_lower_val and bb_middle_val and bb_middle_val > 0:
            bandwidth = (bb_upper_val - bb_lower_val) / bb_middle_val
            if bandwidth > 0.08:
                vol = "HIGH"
            elif bandwidth < 0.03:
                vol = "LOW (SQUEEZE)"
                
        summary = IndicatorSummary(
            rsi=rsi_val,
            ema20=ema20_val,
            ema50=ema50_val,
            ema200=ema200_val,
            macd=macd_val,
            macd_signal=macd_sig_val,
            macd_hist=macd_hist_val,
            bb_upper=bb_upper_val,
            bb_middle=bb_middle_val,
            bb_lower=bb_lower_val,
            atr=atr_val,
            trend_summary=trend,
            volatility_summary=vol
        )
        
        return res_df, summary

technical_indicator_service = TechnicalIndicatorService()
