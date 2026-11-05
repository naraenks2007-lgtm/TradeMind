import os
import json
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import requests

from backend.config import settings
from backend.models.market import CandleData, MarketSnapshot, IndicatorSummary, InstrumentMetadata
from backend.services.technical_indicators import technical_indicator_service

logger = logging.getLogger(__name__)

# Valid, verified Upstox instrument keys
UPSTOX_INSTRUMENTS: Dict[str, Dict[str, str]] = {
    "NIFTY_50": {
        "symbol": "NIFTY_50",
        "display_name": "NIFTY 50 Index",
        "instrument_key": "NSE_INDEX|Nifty 50",
        "exchange": "NSE_INDEX",
        "type": "INDEX"
    },
    "BANK_NIFTY": {
        "symbol": "BANK_NIFTY",
        "display_name": "NIFTY Bank Index",
        "instrument_key": "NSE_INDEX|Nifty Bank",
        "exchange": "NSE_INDEX",
        "type": "INDEX"
    },
    "RELIANCE": {
        "symbol": "RELIANCE",
        "display_name": "Reliance Industries Ltd",
        "instrument_key": "NSE_EQ|INE002A01018",
        "exchange": "NSE_EQ",
        "type": "EQUITY"
    },
    "TCS": {
        "symbol": "TCS",
        "display_name": "Tata Consultancy Services Ltd",
        "instrument_key": "NSE_EQ|INE467B01029",
        "exchange": "NSE_EQ",
        "type": "EQUITY"
    },
    "INFY": {
        "symbol": "INFY",
        "display_name": "Infosys Ltd",
        "instrument_key": "NSE_EQ|INE009A01021",
        "exchange": "NSE_EQ",
        "type": "EQUITY"
    },
    "HDFCBANK": {
        "symbol": "HDFCBANK",
        "display_name": "HDFC Bank Ltd",
        "instrument_key": "NSE_EQ|INE040A01034",
        "exchange": "NSE_EQ",
        "type": "EQUITY"
    },
    "ICICIBANK": {
        "symbol": "ICICIBANK",
        "display_name": "ICICI Bank Ltd",
        "instrument_key": "NSE_EQ|INE090A01021",
        "exchange": "NSE_EQ",
        "type": "EQUITY"
    }
}

TOKEN_STORAGE_PATH = settings.BASE_DIR / "data" / ".upstox_token.json"

class UpstoxService:
    """
    Upstox Service strictly for authorized market-data retrieval and OAuth lifecycle.
    
    SAFETY ENFORCEMENT:
    This service NEVER implements broker order placement. Upstox is strictly used for
    market quotes, candles, and streaming data feeds.
    """
    def __init__(self):
        self.client_id = settings.UPSTOX_CLIENT_ID
        self.client_secret = settings.UPSTOX_CLIENT_SECRET
        self.redirect_uri = settings.UPSTOX_REDIRECT_URI
        self.token_file = TOKEN_STORAGE_PATH
        self.token: Optional[str] = self._load_token()
        self.user_profile: Optional[Dict[str, Any]] = None
        self._cached_quotes: Dict[str, Dict[str, Any]] = {}

    def _load_token(self) -> Optional[str]:
        # Priority 1: Stored session token in secure local JSON
        if self.token_file.exists():
            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tok = data.get("access_token")
                    if tok:
                        return tok
            except Exception as e:
                logger.error(f"Error loading stored Upstox token: {e}")

        # Priority 2: Configured environment variable
        if settings.UPSTOX_ACCESS_TOKEN and settings.UPSTOX_ACCESS_TOKEN.strip():
            return settings.UPSTOX_ACCESS_TOKEN.strip()

        return None

    def save_token(self, token_data: Dict[str, Any]):
        """Persists access token and user metadata safely in data/.upstox_token.json."""
        self.token = token_data.get("access_token")
        self.user_profile = {
            "user_name": token_data.get("user_name"),
            "user_id": token_data.get("user_id"),
            "email": token_data.get("email"),
            "is_active": token_data.get("is_active", True),
            "updated_at": datetime.now().isoformat()
        }
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump({
                    "access_token": self.token,
                    "profile": self.user_profile
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist Upstox token: {e}")

    def clear_token(self):
        """Clears stored access token and user profile."""
        self.token = None
        self.user_profile = None
        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove token file: {e}")

    def get_auth_url(self) -> str:
        """Constructs the official Upstox OAuth 2.0 authorization dialog URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri
        }
        return f"https://api.upstox.com/v2/login/authorization/dialog?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for an access token via Upstox API v2.
        POST https://api.upstox.com/v2/login/authorization/token
        """
        url = "https://api.upstox.com/v2/login/authorization/token"
        headers = {
            "accept": "application/json",
            "Api-Version": "2.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        if response.status_code != 200:
            error_detail = response.text
            try:
                err_json = response.json()
                error_detail = err_json.get("errors", [{}])[0].get("message", error_detail)
            except Exception:
                pass
            raise ValueError(f"Upstox Token Exchange Failed ({response.status_code}): {error_detail}")

        data = response.json()
        self.save_token(data)
        return data

    def get_connection_status(self) -> Dict[str, Any]:
        """Checks configuration and validates access token against Upstox profile endpoint."""
        is_configured = bool(self.client_id and self.client_secret and self.redirect_uri)
        if not is_configured:
            return {
                "configured": False,
                "authenticated": False,
                "status": "UNCONFIGURED",
                "message": "UPSTOX_CLIENT_ID or UPSTOX_CLIENT_SECRET missing in .env"
            }

        if not self.token:
            return {
                "configured": True,
                "authenticated": False,
                "status": "NOT_CONNECTED",
                "message": "No active Upstox access token. Click 'Connect Upstox' to authenticate.",
                "auth_url": self.get_auth_url()
            }

        # Validate token with Upstox User Profile
        try:
            url = "https://api.upstox.com/v2/user/profile"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                profile_data = res.json().get("data", {})
                self.user_profile = profile_data
                return {
                    "configured": True,
                    "authenticated": True,
                    "status": "CONNECTED",
                    "user_name": profile_data.get("user_name", "Authorized User"),
                    "user_id": profile_data.get("user_id"),
                    "email": profile_data.get("email"),
                    "message": "Connected to Upstox Market Data Feed (Authorized)"
                }
            elif res.status_code in (401, 403):
                return {
                    "configured": True,
                    "authenticated": False,
                    "status": "TOKEN_EXPIRED",
                    "message": "Upstox token expired or invalid. Please re-authenticate.",
                    "auth_url": self.get_auth_url()
                }
            else:
                return {
                    "configured": True,
                    "authenticated": False,
                    "status": "ERROR",
                    "message": f"Upstox status check returned {res.status_code}: {res.text[:100]}",
                    "auth_url": self.get_auth_url()
                }
        except Exception as e:
            return {
                "configured": True,
                "authenticated": False,
                "status": "NETWORK_ERROR",
                "message": f"Failed reaching Upstox API: {str(e)[:120]}",
                "auth_url": self.get_auth_url()
            }

    def get_supported_instruments(self) -> List[Dict[str, Any]]:
        """Returns the list of verified instruments supported by TradeMind."""
        return list(UPSTOX_INSTRUMENTS.values())

    def get_market_quote(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Fetches live market quote for an instrument using Upstox v2 API."""
        if not self.token:
            return None
        url = f"https://api.upstox.com/v2/market-quote/quotes"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        params = {"instrument_key": instrument_key}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", {})
                # Format is usually { "EXCHANGE:SYMBOL": { ... } }
                if data:
                    val = next(iter(data.values()))
                    self._cached_quotes[instrument_key] = val
                    return val
            return None
        except Exception as e:
            logger.error(f"Error fetching quote for {instrument_key}: {e}")
            return None

    def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None
    ) -> List[CandleData]:
        """
        Fetches historical candles from Upstox v2 API.
        GET /v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        """
        if not self.token:
            raise RuntimeError("Upstox token not available.")

        now = datetime.now()
        to_d = to_date or now.strftime("%Y-%m-%d")
        from_d = from_date or (now - timedelta(days=365)).strftime("%Y-%m-%d")

        encoded_key = urllib.parse.quote(instrument_key)
        url = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/{interval}/{to_d}/{from_d}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            raise RuntimeError(f"Upstox candle fetch failed ({res.status_code}): {res.text}")

        candles_raw = res.json().get("data", {}).get("candles", [])
        candles: List[CandleData] = []
        for c in reversed(candles_raw):  # Upstox returns newest first; reverse to chronological
            candles.append(
                CandleData(
                    date=c[0][:10] if "T" in c[0] else c[0],
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[5])
                )
            )
        return candles

    def get_intraday_candles(self, instrument_key: str, interval: str = "1minute") -> List[CandleData]:
        """
        Fetches intraday candles for the current trading day.
        GET /v2/historical-candle/intraday/{instrument_key}/{interval}
        """
        if not self.token:
            raise RuntimeError("Upstox token not available.")

        encoded_key = urllib.parse.quote(instrument_key)
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/{interval}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            raise RuntimeError(f"Upstox intraday fetch failed ({res.status_code}): {res.text}")

        candles_raw = res.json().get("data", {}).get("candles", [])
        candles: List[CandleData] = []
        for c in reversed(candles_raw):
            candles.append(
                CandleData(
                    date=c[0],
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[5])
                )
            )
        return candles

    def get_ws_auth_url(self) -> Optional[str]:
        """
        Fetches an authorized WebSocket connection URL from Upstox.
        GET /v2/feed/market-data-feed/authorize
        """
        if not self.token:
            return None
        url = "https://api.upstox.com/v2/feed/market-data-feed/authorize"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                return res.json().get("data", {}).get("authorizedRedirectUri")
            return None
        except Exception as e:
            logger.error(f"WebSocket auth failed: {e}")
            return None

upstox_service = UpstoxService()
