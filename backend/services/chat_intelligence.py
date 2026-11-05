import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from backend.models.hypothesis import MarketChatResponse
from backend.services.conversation_store import conversation_store
from backend.services.hindsight_service import hindsight_service


IST = ZoneInfo("Asia/Kolkata")
SESSION_TAG_PREFIX = "trademind_session_"


def _response(answer: str, instrument: str = "GENERAL", memories=None) -> MarketChatResponse:
    return MarketChatResponse(
        answer=answer,
        instrument=instrument,
        current_price=0.0,
        data_source="TradeMind AI",
        data_timestamp=datetime.now(IST).isoformat(),
        recalled_memories=memories or []
    )


def _save_payload(message: str) -> Optional[str]:
    match = re.match(
        r"^\s*(?:please\s+)?(?:remember|save|store|note|keep\s+in\s+mind)\s+(?:that\s+)?(.+?)\s*[.!?]*\s*$",
        message,
        flags=re.IGNORECASE
    )
    if not match:
        return None
    fact = match.group(1).strip()
    if len(fact) < 4:
        return None
    return fact


def _memory_query(message: str) -> bool:
    text = message.lower()
    asks_recall = any(term in text for term in ("what did i say", "what was the", "what is the", "do you remember", "what did i tell", "recall"))
    asks_fact = any(term in text for term in ("price", "cost", "amount", "value", "said", "saved", "stored"))
    return asks_recall and asks_fact


def _format_saved_at(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value).astimezone(IST)
        return dt.strftime("%d %b %Y at %I:%M:%S %p IST")
    except Exception:
        return value


def process_personal_memory(session_id: str, message: str) -> Optional[MarketChatResponse]:
    fact = _save_payload(message)
    if fact:
        now = datetime.now(IST).isoformat()
        left, separator, right = re.partition(r"\s*(?:is|was|=|:)\s*", fact, flags=re.IGNORECASE)
        search_text = left if separator else fact
        saved = conversation_store.save_user_fact(session_id, fact, search_text, now)
        hindsight_result = hindsight_service.retain_memory(
            content=(
                f"USER-STATED PERSONAL FACT (not independently verified): {fact}. "
                f"Saved at {now} (Asia/Kolkata). When asked about this fact, report the saved value and this timestamp."
            ),
            tags=["user_fact", SESSION_TAG_PREFIX + session_id],
            metadata={
                "type": "user_fact",
                "session_id": session_id,
                "fact_key": search_text,
                "saved_at": now,
                "timezone": "Asia/Kolkata"
            }
        )
        if hindsight_result.get("success"):
            answer = f"Saved to Hindsight memory.\n\n**{fact}**\nSaved on {_format_saved_at(saved['saved_at'])}."
        else:
            answer = (
                f"I saved this in TradeMind's local conversation memory, but Hindsight is currently unavailable.\n\n"
                f"**{fact}**\nSaved on {_format_saved_at(saved['saved_at'])}.\n\n"
                "I'll still be able to recall it from this browser session."
            )
        return _response(answer)

    if _memory_query(message):
        facts = conversation_store.find_user_facts(session_id, message, limit=3)
        if facts:
            lines = [
                f"- **{item['fact_text']}**\n  Saved on {_format_saved_at(item['saved_at'])}"
                for item in facts
            ]
            return _response("Here's what you told me:\n\n" + "\n\n".join(lines))
        recalled = hindsight_service.recall_memories(
            query=message,
            tags=["user_fact", SESSION_TAG_PREFIX + session_id],
            limit=3
        )
        if recalled:
            return _response(
                "I found this in your saved Hindsight memories:\n\n" +
                "\n".join(f"- {item.content}" for item in recalled),
                memories=[item.content for item in recalled]
            )
        return _response("I couldn't find a saved fact matching that question in this browser session. Try asking with the subject, such as 'What petrol price did I save?'.")

    return None


def process_greeting(message: str) -> Optional[MarketChatResponse]:
    normalized = re.sub(r"[^a-z ]", "", message.lower()).strip()
    if normalized in {"hi", "hello", "hey", "hii", "heyy", "good morning", "good afternoon", "good evening", "how are you"}:
        return _response(
            "Hey! 👋 I'm TradeMind. I can help with market analysis, explain trading concepts, remember facts you ask me to save, and analyse PDF, image, or CSV files. What would you like to explore?"
        )
    if normalized in {"thanks", "thank you", "thx", "ok", "okay"}:
        return _response("You're welcome! Let me know what you'd like to work on next.")
    return None


def is_market_question(message: str) -> bool:
    terms = (
        "nifty", "sensex", "banknifty", "stock", "share", "market", "trading", "trade setup",
        "rsi", "macd", "ema", "bollinger", "support", "resistance", "candlestick", "portfolio",
        "upstox", "volume", "volatility", "bullish", "bearish", "entry", "stop loss", "target"
    )
    text = message.lower()
    return any(term in text for term in terms)
