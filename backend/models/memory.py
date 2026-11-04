from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    id: Optional[str] = None
    bank_id: str
    content: str
    timestamp: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

class RecallRequest(BaseModel):
    query: str
    bank_id: Optional[str] = None
    tags: Optional[List[str]] = None
    budget: str = "mid"
    limit: int = 5

class RetainRequest(BaseModel):
    content: str
    bank_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ReflectRequest(BaseModel):
    query: str
    bank_id: Optional[str] = None
    tags: Optional[List[str]] = None

class MemoryStatus(BaseModel):
    connected: bool
    service_url: str
    bank_id: str
    status_message: str
    memory_count: int = 0
