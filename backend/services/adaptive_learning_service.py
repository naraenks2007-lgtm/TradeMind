import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests

from backend.services.hindsight_service import hindsight_service

logger = logging.getLogger(__name__)
SESSION_TAG_PREFIX = "trademind_session_"


class AdaptiveLearningService:
    """Turns explicit user feedback and public market headlines into Hindsight experiences."""

    def __init__(self) -> None:
        self._news_cache: Dict[str, Dict[str, Any]] = {}
        self._news_ttl_seconds = 15 * 60

    @staticmethod
    def _feedback_candidate(message: str) -> bool:
        text = message.lower()
        signals = (
            "i prefer", "i usually", "i always", "i never", "i avoid", "my risk",
            "my strategy", "my trading", "my mistake", "i lost", "i won", "trade closed",
            "trade hit", "stop loss hit", "target hit", "that analysis was", "you were wrong",
            "you were right", "that was wrong", "that was incorrect", "this worked", "this failed", "it worked", "it failed", "should have", "my preferred", "risk appetite", "risk tolerance", "i trade", "i usually enter", "i usually exit", "next time", "from now on", "i want you to",
            "i don't want", "i do not want", "because i entered", "because i exited"
        )
        return len(message.strip()) >= 18 and any(term in text for term in signals)

    def learn_from_user_reply(self, message: str, session_id: str, instrument: str) -> Optional[str]:
        """Extract only durable preferences, corrections or trade lessons explicitly shared by the user."""
        if not self._feedback_candidate(message):
            return None
        try:
            # Local import avoids coupling the learning service to LLM initialization at import time.
            from backend.services.llm_service import llm_service
            if not llm_service.client:
                return None
            result = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": (
                        "Extract durable trading preferences, user corrections, or lessons from this message. "
                        "Do not infer facts. Return JSON with keys: should_remember (boolean), category "
                        "(preference|lesson|correction|outcome|none), memory (string). Set should_remember=false "
                        "for casual chat, one-off questions, unsupported claims, or content that is not useful later. "
                        "Keep memory concise and preserve uncertainty."
                    )},
                    {"role": "user", "content": f"Instrument context: {instrument}\nUser message: {message}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            payload = json.loads(result.choices[0].message.content or "{}")
            memory = str(payload.get("memory") or "").strip()
            if not payload.get("should_remember") or len(memory) < 12:
                return None
            category = str(payload.get("category") or "lesson").lower()
            if category not in {"preference", "lesson", "correction", "outcome"}:
                category = "lesson"
            now = datetime.now(timezone.utc).isoformat()
            retained = hindsight_service.retain_memory(
                content=(
                    f"USER-TAUGHT TRADING {category.upper()} (instrument context: {instrument}): {memory}. "
                    f"Source: explicit user reply. Recorded at {now}."
                ),
                tags=["user_taught", "trading_" + category, SESSION_TAG_PREFIX + session_id],
                metadata={"type": "user_feedback", "category": category, "instrument": instrument,
                          "session_id": session_id, "recorded_at": now}
            )
            return memory if retained.get("success") else None
        except Exception as exc:
            logger.warning("Could not learn from user reply: %s", exc)
            return None

    @staticmethod
    def _news_query(instrument: str) -> str:
        mapping = {
            "NIFTY_50": "Nifty 50 India stock market",
            "BANK_NIFTY": "Nifty Bank India banking stocks",
            "SENSEX": "BSE Sensex India stock market",
            "RELIANCE": "Reliance Industries stock India",
            "TCS": "TCS stock India",
            "INFY": "Infosys stock India",
            "HDFCBANK": "HDFC Bank stock India",
            "ICICIBANK": "ICICI Bank stock India",
        }
        return mapping.get(instrument.upper(), f"{instrument} India stock market")

    def fetch_and_remember_market_news(self, instrument: str) -> List[Dict[str, str]]:
        """Read public Google News RSS headlines; no login, paywall or broker endpoints are scraped."""
        key = instrument.upper()
        cached = self._news_cache.get(key)
        now = time.time()
        if cached and now - cached["fetched_at"] < self._news_ttl_seconds:
            return cached["items"]
        query = quote_plus(self._news_query(key))
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            response = requests.get(url, timeout=8, headers={"User-Agent": "TradeMind/1.0 (market research)"})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            items: List[Dict[str, str]] = []
            for node in root.findall(".//item")[:6]:
                title = (node.findtext("title") or "").strip()
                link = (node.findtext("link") or "").strip()
                pub_date = (node.findtext("pubDate") or "").strip()
                source = node.findtext("source") or "Google News RSS"
                if not title:
                    continue
                item = {"title": title, "link": link, "published": pub_date, "source": source}
                items.append(item)
                hindsight_service.retain_memory(
                    content=(
                        f"PUBLIC MARKET NEWS HEADLINE for {key}: {title}. Source: {source}. "
                        f"Published: {pub_date or 'not provided'}. Link: {link}. "
                        "Treat this as a reported headline, not verified market fact."
                    ),
                    tags=[key, "market_news", "external_context"],
                    metadata={"instrument": key, "source": source, "url": link, "published": pub_date}
                )
            self._news_cache[key] = {"fetched_at": now, "items": items}
            return items
        except Exception as exc:
            logger.info("Market RSS context unavailable for %s: %s", key, exc)
            return cached["items"] if cached else []


adaptive_learning_service = AdaptiveLearningService()
