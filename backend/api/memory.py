from fastapi import APIRouter
from typing import List, Dict, Any

from backend.models.memory import MemoryItem, MemoryStatus, RecallRequest, RetainRequest, ReflectRequest
from backend.services.hindsight_service import hindsight_service

router = APIRouter(prefix="/api/memory", tags=["Hindsight Long-Term Memory"])

@router.get("/status", response_model=MemoryStatus)
def get_memory_status():
    return hindsight_service.get_status()

@router.post("/recall", response_model=List[MemoryItem])
def recall_memory_items(req: RecallRequest):
    return hindsight_service.recall_memories(
        query=req.query,
        tags=req.tags,
        limit=req.limit
    )

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
