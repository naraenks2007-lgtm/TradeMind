import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.api.hypothesis import _get_active_snapshot
from backend.services.conversation_store import conversation_store
from backend.services.llm_service import llm_service
from backend.services.paper_trading_service import paper_trading_service
from backend.models.hypothesis import MarketChatResponse
from backend.services.chat_intelligence import process_personal_memory, process_greeting, is_market_question
from backend.services.file_analysis_service import analyze_file
from backend.services.adaptive_learning_service import adaptive_learning_service

router = APIRouter(prefix="/api/conversations", tags=["Persistent AI Conversations"])




def _extract_user_reported_price(message: str) -> Optional[float]:
    """Extract a price explicitly supplied by the user; this is not a verified quote."""
    match = re.search(
        r"\b(?:nifty(?:\s*50)?|bank\s*nifty|sensex|reliance|tcs|infy|infosys)\b.*?"
        r"(?:current\s+price|market\s+price|price\s*(?:is|=|:))\s*₹?\s*([\d,]+(?:\.\d+)?)",
        message,
        flags=re.IGNORECASE
    )
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", ""))
        return value if value > 0 else None
    except ValueError:
        return None


def _session_id(value: Optional[str]) -> str:
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", value):
        raise HTTPException(status_code=400, detail="A valid X-TradeMind-Session header is required.")
    return value


class CreateConversationRequest(BaseModel):
    instrument: str = Field(default="NIFTY_50", min_length=1, max_length=40)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    instrument_id: str = Field(default="NIFTY_50", min_length=1, max_length=40)
    include_memory: bool = True


@router.get("")
def list_conversations(x_trademind_session: Optional[str] = Header(default=None)):
    return conversation_store.list_conversations(_session_id(x_trademind_session))


@router.post("")
def create_conversation(req: CreateConversationRequest, x_trademind_session: Optional[str] = Header(default=None)):
    return conversation_store.create_conversation(_session_id(x_trademind_session), req.instrument)


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, x_trademind_session: Optional[str] = Header(default=None)):
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation id.")
    result = conversation_store.get_conversation(_session_id(x_trademind_session), conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return result


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, x_trademind_session: Optional[str] = Header(default=None)):
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation id.")
    deleted = conversation_store.delete_conversation(_session_id(x_trademind_session), conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"deleted": True, "conversation_id": conversation_id}


@router.post("/{conversation_id}/messages")
def send_message(conversation_id: str, req: ChatMessageRequest, x_trademind_session: Optional[str] = Header(default=None)):
    session_id = _session_id(x_trademind_session)
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation id.")
    conversation = conversation_store.get_conversation(session_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Feed the recent turns to both the learner and the response model. This lets it
    # resolve "that price is wrong" against the exact quote it gave earlier.
    prior_messages = (conversation.get("messages") or [])[-8:]
    previous_assistant = next(
        (item.get("content", "") for item in reversed(prior_messages) if item.get("role") == "assistant"),
        ""
    )
    history_context = "\n".join(
        f"{'USER' if item.get('role') == 'user' else 'TRADEMIND'}: {item.get('content', '')[:1800]}"
        for item in prior_messages
    )
    contextual_message = (
        f"RECENT CONVERSATION CONTEXT (for resolving follow-up references; do not repeat it):\n"
        f"{history_context or 'No previous messages.'}\n\n"
        f"CURRENT USER MESSAGE: {req.message.strip()}"
    )

    try:
        user_reported_price = _extract_user_reported_price(req.message.strip())
        # A standalone quote supplied by the user is input context, not a durable lesson.
        # Only send it to adaptive learning when it is clearly a reply to an earlier assistant claim.
        learned_memory = None
        if not (user_reported_price is not None and not previous_assistant):
            learned_memory = adaptive_learning_service.learn_from_user_reply(
                req.message.strip(), session_id, req.instrument_id,
                previous_assistant_message=previous_assistant
            )
        response = process_personal_memory(session_id, req.message.strip())
        if response is None:
            response = process_greeting(req.message.strip())
        if response is None:
            if is_market_question(req.message) or (
                previous_assistant and any(term in req.message.lower() for term in (
                    "wrong", "incorrect", "not right", "that price", "your output", "you said",
                    "actual price", "that's not", "this is not", "it should be", "this output", "output is wrong", "not matching", "does not match", "doesn't match", "you gave", "you provided", "it shows", "i got", "i am getting"
                ))
            ):
                snapshot = _get_active_snapshot(req.instrument_id)
                portfolio = paper_trading_service.get_portfolio_state({snapshot.symbol: snapshot.current_price})
                headlines = adaptive_learning_service.fetch_and_remember_market_news(snapshot.symbol)
                news_context = "\n".join(
                    f"- {item['title']} (source: {item['source']}; published: {item['published']}; link: {item['link']})"
                    for item in headlines
                ) or "No fresh public news headlines were available."
                if user_reported_price is not None:
                    news_context += (
                        f"\\n\\nUSER-REPORTED REFERENCE PRICE: ₹{user_reported_price:,.2f}. "
                        "The user supplied this number in the current message. It is unverified input, "
                        "not a broker quote and not a substitute for the market snapshot. Explicitly "
                        "acknowledge it as user-provided, compare it with the snapshot source/timestamp, "
                        "and state clearly if the available feed cannot verify it. Do not silently overwrite "
                        "the snapshot or present the supplied value as live market data."
                    )
                response = llm_service.chat_analysis(
                    message=contextual_message,
                    snapshot=snapshot,
                    portfolio=portfolio,
                    include_memory=req.include_memory,
                    external_context=news_context,
                    session_id=session_id
                )
            else:
                response = llm_service.general_chat(contextual_message, session_id=session_id)

        if learned_memory:
            response.answer += (
                "\n\n🧠 **Hindsight learned:** " + learned_memory +
                "\nI'll treat this as user feedback, not as a replacement for verified live market data, "
                "and use it when relevant in future analysis."
            )
        result = conversation_store.append_exchange(
            session_id, conversation_id, req.instrument_id, req.message.strip(), response.answer, response
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat analysis failed: {exc}")


@router.post("/{conversation_id}/files")
def analyse_chat_file(
    conversation_id: str,
    file: UploadFile = File(...),
    prompt: str = Form(default="Analyse this file and explain the key findings."),
    x_trademind_session: Optional[str] = Header(default=None)
):
    session_id = _session_id(x_trademind_session)
    try:
        UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation id.")
    conversation = conversation_store.get_conversation(session_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    try:
        payload = file.file.read(10 * 1024 * 1024 + 1)
        answer = analyze_file(file.filename or "uploaded-file", payload, prompt)
        instrument = conversation.get("instrument") or "GENERAL"
        response = MarketChatResponse(
            answer=answer,
            instrument=instrument,
            current_price=0.0,
            data_source=f"File analysis: {file.filename}",
            data_timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            recalled_memories=[]
        )
        user_text = f"📎 Analyse file: {file.filename or 'uploaded-file'}\nRequest: {prompt}"
        result = conversation_store.append_exchange(
            session_id, conversation_id, instrument, user_text, answer, response
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File analysis failed: {exc}")
