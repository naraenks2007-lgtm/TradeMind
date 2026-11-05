import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from backend.api.hypothesis import _get_active_snapshot
from backend.services.conversation_store import conversation_store
from backend.services.llm_service import llm_service
from backend.services.paper_trading_service import paper_trading_service

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
        snapshot = _get_active_snapshot(req.instrument_id)
        portfolio = paper_trading_service.get_portfolio_state({snapshot.symbol: snapshot.current_price})
        response = llm_service.chat_analysis(
            message=req.message.strip(),
            snapshot=snapshot,
            portfolio=portfolio,
            include_memory=req.include_memory
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
