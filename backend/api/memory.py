from fastapi import APIRouter, Header
from typing import Optional
from typing import List, Dict, Any

from backend.models.memory import MemoryItem, MemoryStatus, RecallRequest, RetainRequest, ReflectRequest
from backend.services.hindsight_service import hindsight_service

router = APIRouter(prefix="/api/memory", tags=["Hindsight Long-Term Memory"])

@router.get("/status", response_model=MemoryStatus)
def get_memory_status():
    return hindsight_service.get_status()

@router.post("/recall", response_model=List[MemoryItem])
def recall_memory_items(req: RecallRequest, x_trademind_session: Optional[str] = Header(default=None)):
    # Never run an unscoped recall from the personal Memory Explorer: user-taught
    # memories live in a shared Hindsight bank but carry a browser-session tag.
    tags = req.tags or []
    if not tags:
        query = req.query.lower()
        instrument_tags = {
            "nifty": "NIFTY_50", "banknifty": "BANK_NIFTY", "bank nifty": "BANK_NIFTY",
            "sensex": "SENSEX", "reliance": "RELIANCE", "tcs": "TCS",
            "infosys": "INFY", "infy": "INFY", "hdfc": "HDFCBANK", "icici": "ICICIBANK"
        }
        tags = [tag for token, tag in instrument_tags.items() if token in query]
    results = []
    if tags:
        for tag in tags:
            results.extend(hindsight_service.recall_memories(query=req.query, tags=[tag], limit=req.limit))
    if x_trademind_session:
        results.extend(hindsight_service.recall_memories(
            query=req.query, tags=["trademind_session_" + x_trademind_session], limit=req.limit
        ))
    unique = []
    seen = set()
    for item in results:
        if item.content not in seen:
            seen.add(item.content)
            unique.append(item)
    return unique[:req.limit]

@router.post("/retain")
def retain_memory_item(req: RetainRequest) -> Dict[str, Any]:
    return hindsight_service.retain_memory(
        content=req.content,
        tags=req.tags,
        metadata=req.metadata
    )

@router.post("/reflect")
def reflect_memory_reasoning(req: ReflectRequest) -> Dict[str, Any]:
    reflection = hindsight_service.reflect_lessons(query=req.query)
    return {
        "query": req.query,
        "reflection": reflection,
        "connected": hindsight_service.get_status().connected
    }
