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
    if not conversation_store.get_conversation(session_id, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")

    try:
        learned_memory = adaptive_learning_service.learn_from_user_reply(
            req.message.strip(), session_id, req.instrument_id
        )
        response = process_personal_memory(session_id, req.message.strip())
        if response is None:
            response = process_greeting(req.message.strip())
        if response is None:
            if is_market_question(req.message):
                snapshot = _get_active_snapshot(req.instrument_id)
                portfolio = paper_trading_service.get_portfolio_state({snapshot.symbol: snapshot.current_price})
                headlines = adaptive_learning_service.fetch_and_remember_market_news(snapshot.symbol)
                news_context = "\n".join(
                    f"- {item['title']} (source: {item['source']}; published: {item['published']}; link: {item['link']})"
                    for item in headlines
                ) or "No fresh public news headlines were available."
                response = llm_service.chat_analysis(
                    message=req.message.strip(),
                    snapshot=snapshot,
                    portfolio=portfolio,
                    include_memory=req.include_memory,
                    external_context=news_context
                )
            else:
                response = llm_service.general_chat(req.message.strip(), session_id=session_id)

        if learned_memory:
            response.answer += "\n\n🧠 **Hindsight learned:** " + learned_memory + "\nI'll use this preference or lesson when relevant in future analysis."
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
