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
    """Extracts user-taught trading lessons and retains sourced market context."""

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
            "you were right", "that was wrong", "that was incorrect", "this worked", "this failed",
            "it worked", "it failed", "should have", "my preferred", "risk appetite", "risk tolerance",
            "i trade", "i usually enter", "i usually exit", "next time", "from now on", "i want you to",
            "i don't want", "i do not want", "because i entered", "because i exited", "wrong price",
            "price is", "price was", "actual price", "market price", "that price", "not correct",
            "incorrect price", "your output", "you said", "current price", "the value is"
        )
        return len(message.strip()) >= 8 and any(term in text for term in signals)

    def learn_from_user_reply(
        self,
        message: str,
        session_id: str,
        instrument: str,
        previous_assistant_message: str = "",
        market_evidence: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Interpret feedback in its conversational context; preserve unverified price claims as claims."""
        if not self._feedback_candidate(message):
            return None
        try:
            from backend.services.llm_service import llm_service
            if not llm_service.client:
                return None
            evidence = market_evidence or {}
            result = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": (
                        "You are a careful trading-conversation memory extractor. Read the previous assistant "
                        "claim and the user's reply together. Identify whether the user is correcting a quoted "
                        "price/data point, stating a durable preference, reporting a trade outcome, or teaching "
                        "a strategy lesson. Never assume the user's price is true merely because they said it. "
                        "For price corrections, compare only with the supplied market evidence and classify "
                        "verification as verified, contradicted, or unverified. A historical/stale snapshot is "
                        "not proof of a live price. Return JSON keys: should_remember (boolean), category "
                        "(preference|lesson|correction|outcome|none), memory (string), verification "
                        "(verified|contradicted|unverified|not_applicable), response_guidance (string). "
                        "Save useful corrections even when unverified, but explicitly label them as user-reported "
                        "and include instrument/time context. Do not save a one-off price as a permanent current "
                        "price. Do not invent missing details. If the message is ambiguous, do not create a "
                        "durable memory; response_guidance should ask a concise clarification."
                    )},
                    {"role": "user", "content": (
                        f"Instrument: {instrument}\nPrevious assistant message: {previous_assistant_message[-2500:]}\n"
                        f"User reply: {message}\nMarket evidence available now: {json.dumps(evidence, default=str)}"
                    )}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            payload = json.loads(result.choices[0].message.content or "{}")
            memory = str(payload.get("memory") or "").strip()
            if not payload.get("should_remember") or len(memory) < 8:
                return None
            category = str(payload.get("category") or "lesson").lower()
            if category not in {"preference", "lesson", "correction", "outcome"}:
                category = "lesson"
            verification = str(payload.get("verification") or "not_applicable").lower()
            if verification not in {"verified", "contradicted", "unverified", "not_applicable"}:
                verification = "unverified"
            now = datetime.now(timezone.utc).isoformat()
            content = (
                f"USER-TAUGHT TRADING {category.upper()} (instrument: {instrument}): {memory}. "
                f"Verification: {verification}. Market evidence at capture: {json.dumps(evidence, default=str)}. "
                f"Source: explicit user reply in conversation; previous assistant claim: "
                f"{previous_assistant_message[-1200:]}. Recorded at {now}. "
                "Do not treat user-reported price values as current market quotes."
            )
            retained = hindsight_service.retain_memory(
                content=content,
                tags=["user_taught", "trading_" + category, SESSION_TAG_PREFIX + session_id, instrument.upper()],
                metadata={
                    "type": "conversation_feedback", "category": category, "verification": verification,
                    "instrument": instrument, "session_id": session_id, "recorded_at": now,
                    "market_evidence": evidence
                }
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
