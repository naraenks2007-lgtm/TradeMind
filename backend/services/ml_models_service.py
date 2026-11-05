import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import ta

from backend.models.ml import (
    DirectionPrediction,
    VolatilityPrediction,
    SentimentPrediction,
    MLAnalysisResult
)

logger = logging.getLogger(__name__)

class TabularMLService:
    def __init__(self):
        # In-memory cache for trained models per instrument
        self._models_cache: Dict[str, Dict[str, Any]] = {}

    def extract_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extracts robust quantitative tabular features without lookahead bias.
        """
        data = df.copy()
        
        # 1. Price Returns
        data["ret_1d"] = data["Close"].pct_change(1)
        data["ret_3d"] = data["Close"].pct_change(3)
        data["ret_5d"] = data["Close"].pct_change(5)

        # 2. RSI & RSI Momentum
        rsi = ta.momentum.RSIIndicator(close=data["Close"], window=14).rsi()
        data["rsi"] = rsi
        data["rsi_delta"] = rsi.diff(3)

        # 3. Moving Average Alignments
        ema20 = ta.trend.EMAIndicator(close=data["Close"], window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close=data["Close"], window=min(50, len(data)-1)).ema_indicator()
        data["ema20_ratio"] = (data["Close"] / ema20) - 1.0
        data["ema_cross"] = (ema20 / ema50) - 1.0

        # 4. Bollinger Bands features
        bb = ta.volatility.BollingerBands(close=data["Close"], window=20, window_dev=2)
        upper = bb.bollinger_hband()
        lower = bb.bollinger_lband()
        mid = bb.bollinger_mavg()
        data["bb_pct_b"] = (data["Close"] - lower) / (upper - lower + 1e-8)
        data["bb_bandwidth"] = (upper - lower) / (mid + 1e-8)

        # 5. Volume dynamics
        vol_ma = data["Volume"].rolling(20).mean()
        data["vol_ratio"] = data["Volume"] / (vol_ma + 1e-8)

        # 6. Volatility (ATR Normalized)
        atr = ta.volatility.AverageTrueRange(high=data["High"], low=data["Low"], close=data["Close"], window=14).average_true_range()
        data["atr_norm"] = atr / data["Close"]

        # 7. Close Location Value (Intraday Sentiment Proxy: -1 to +1)
        hl_range = data["High"] - data["Low"]
        data["clv"] = np.where(hl_range > 0, ((data["Close"] - data["Low"]) - (data["High"] - data["Close"])) / hl_range, 0.0)

        # Forward Targets for Training
        # 3-day forward return
        data["target_ret_3d"] = data["Close"].pct_change(3).shift(-3)
        # 5-day forward realized volatility
        data["target_vol_5d"] = (data["ret_1d"].rolling(5).std() * np.sqrt(252)).shift(-5)

        feature_cols = [
            "ret_1d", "ret_3d", "ret_5d", "rsi", "rsi_delta",
            "ema20_ratio", "ema_cross", "bb_pct_b", "bb_bandwidth",
            "vol_ratio", "atr_norm", "clv"
        ]

        return data, data[feature_cols]

    def train_and_analyze(self, instrument_id: str, df: pd.DataFrame) -> MLAnalysisResult:
        if len(df) < 40:
            raise ValueError(f"Insufficient data for ML training ({len(df)} bars; requires at least 40)")

        full_df, X_features = self.extract_features(df)
        
        # Prepare training dataset (exclude rows with NaN in features or targets)
        train_mask = (
            X_features.notna().all(axis=1) & 
            full_df["target_ret_3d"].notna() & 
            full_df["target_vol_5d"].notna()
        )
        
        X_train = X_features[train_mask]
        
        # Target classes: BULLISH (> +0.65%), BEARISH (< -0.65%), NEUTRAL
        ret_3d = full_df.loc[train_mask, "target_ret_3d"]
        y_dir = np.where(ret_3d > 0.0065, "BULLISH", np.where(ret_3d < -0.0065, "BEARISH", "NEUTRAL"))
        
        # Target volatility (annualized %)
        y_vol = full_df.loc[train_mask, "target_vol_5d"] * 100

        # Standard scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        # 1. Train Direction Model (Random Forest Classifier)
        clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
        clf.fit(X_train_scaled, y_dir)

        # 2. Train Volatility Model (Gradient Boosting Regressor)
        reg = GradientBoostingRegressor(n_estimators=35, max_depth=3, random_state=42)
        reg.fit(X_train_scaled, y_vol)

        # 3. Analyze Current Bar (latest timestamp)
        current_X = X_features.iloc[[-1]]
        current_X_clean = current_X.fillna(0.0)
        current_X_scaled = scaler.transform(current_X_clean)

        # Direction Prediction
        probs = clf.predict_proba(current_X_scaled)[0]
        classes = clf.classes_
        prob_dict = {str(c): round(float(p), 3) for c, p in zip(classes, probs)}
        
        # Ensure all classes are present
        for c in ["BULLISH", "BEARISH", "NEUTRAL"]:
            if c not in prob_dict:
                prob_dict[c] = 0.0

        best_dir = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[best_dir]

        # Top driving features
        importances = clf.feature_importances_
        feature_names = X_features.columns
        top_indices = np.argsort(importances)[::-1][:4]
        top_features = [
            {
                "feature": str(feature_names[i]),
                "importance": round(float(importances[i]), 3),
                "current_value": round(float(current_X.iloc[0, i]), 4)
            }
            for i in top_indices
        ]

        # Volatility Prediction
        pred_vol = max(5.0, round(float(reg.predict(current_X_scaled)[0]), 2))
        vol_regime = (
            "HIGH_EXPANSION" if pred_vol > 24.0 else
            "LOW_COMPRESSION" if pred_vol < 12.0 else
            "NORMAL"
        )
        current_close = float(df["Close"].iloc[-1])
        daily_vol_pct = (pred_vol / 100.0) / np.sqrt(252)
        atr_forecast = round(current_close * daily_vol_pct * 1.5, 2)

        # Sentiment Composite (-1.0 to +1.0)
        clv_val = float(current_X_clean["clv"].iloc[0])
        rsi_val = float(current_X_clean["rsi"].iloc[0])
        ret1d_val = float(current_X_clean["ret_1d"].iloc[0])
        vol_rat = float(current_X_clean["vol_ratio"].iloc[0])

        # Composite score
        sentiment_score = (clv_val * 0.4) + ((rsi_val - 50.0) / 50.0 * 0.4) + (np.clip(ret1d_val * 20.0, -1.0, 1.0) * 0.2)
        sentiment_score = round(float(np.clip(sentiment_score, -1.0, 1.0)), 3)

        if sentiment_score >= 0.35:
            sentiment_label = "STRONG_BULLISH"
        elif sentiment_score >= 0.10:
            sentiment_label = "MODERATE_BULLISH"
        elif sentiment_score <= -0.35:
            sentiment_label = "STRONG_BEARISH"
        elif sentiment_score <= -0.10:
            sentiment_label = "MODERATE_BEARISH"
        else:
            sentiment_label = "NEUTRAL"

        buying_pressure = round(float(np.clip((sentiment_score + 1.0) / 2.0 * 100, 5.0, 95.0)), 1)

        result = MLAnalysisResult(
            instrument=instrument_id,
            timestamp=str(df["Date"].iloc[-1]),
            current_price=current_close,
            direction=DirectionPrediction(
                direction=best_dir,
                confidence=confidence,
                probabilities=prob_dict,
                top_features=top_features
            ),
            volatility=VolatilityPrediction(
                predicted_volatility_pct=pred_vol,
                volatility_regime=vol_regime,
                atr_forecast=atr_forecast
            ),
            sentiment=SentimentPrediction(
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                buying_pressure_pct=buying_pressure
            ),
            model_metadata={
                "direction_model": "RandomForestClassifier(n_estimators=50, max_depth=4)",
                "volatility_model": "GradientBoostingRegressor(n_estimators=35, max_depth=3)",
                "training_samples": len(X_train),
                "feature_count": len(feature_names),
                "target_horizon": "3-day forward price change & 5-day realized volatility"
            }
        )

        return result

tabular_ml_service = TabularMLService()
