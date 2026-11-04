import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.config import settings
from backend.models.memory import MemoryItem, MemoryStatus

logger = logging.getLogger(__name__)

class HindsightService:
    def __init__(self):
        self.base_url = settings.HINDSIGHT_BASE_URL
        self.api_key = settings.HINDSIGHT_API_KEY
        self.bank_id = settings.HINDSIGHT_BANK_ID
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from hindsight_client import Hindsight
            if self.base_url:
                # Initialize real Hindsight SDK client
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key if self.api_key else None,
                    timeout=10.0,
                    max_attempts=2
                )
        except Exception as e:
            logger.warning(f"Could not initialize Hindsight client: {e}")
            self.client = None

    def get_status(self) -> MemoryStatus:
        if not self.api_key and not ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
            return MemoryStatus(
                connected=False,
                service_url=self.base_url,
                bank_id=self.bank_id,
                status_message="Offline: HINDSIGHT_API_KEY not configured in .env",
                memory_count=0
            )
            
        if not self.client:
            return MemoryStatus(
                connected=False,
                service_url=self.base_url,
                bank_id=self.bank_id,
                status_message="Offline: Hindsight SDK not connected",
                memory_count=0
            )
            
        try:
            # Probe actual Hindsight connection via get_bank_config or get_version
            config = self.client.get_bank_config(bank_id=self.bank_id)
            return MemoryStatus(
                connected=True,
                service_url=self.base_url,
                bank_id=self.bank_id,
                status_message="Online: Connected to Vectorize Hindsight Engine",
                memory_count=1  # Connected
            )
        except Exception as e:
            # Honest degradation without fake success
            return MemoryStatus(
                connected=False,
                service_url=self.base_url,
                bank_id=self.bank_id,
                status_message=f"Disconnected: {str(e)[:120]}",
                memory_count=0
            )

    def retain_memory(self, content: str, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retains experience/market context/trade outcome into Hindsight memory bank.
        """
        if not self.client:
            return {
                "success": False,
                "error": "Hindsight service unavailable. Configure HINDSIGHT_API_KEY.",
                "bank_id": self.bank_id
            }
            
        try:
            res = self.client.retain(
                bank_id=self.bank_id,
                content=content,
                tags=tags or ["trade_decision"],
                metadata=metadata or {}
            )
            return {
                "success": True,
                "operation_id": getattr(res, "operation_id", "completed"),
                "bank_id": self.bank_id
            }
        except Exception as e:
            logger.error(f"Hindsight retain error: {e}")
            return {
                "success": False,
                "error": str(e),
                "bank_id": self.bank_id
            }

    def recall_memories(self, query: str, tags: Optional[List[str]] = None, limit: int = 5) -> List[MemoryItem]:
        """
        Executes sub-second hybrid memory search (semantic + BM25 + entity) in Hindsight.
        """
        if not self.client:
            return []
            
        try:
            res = self.client.recall(
                bank_id=self.bank_id,
                query=query,
                tags=tags,
                budget="mid"
            )
            
            items: List[MemoryItem] = []
            # Parse RecallResponse
            results = getattr(res, "results", []) or []
            for item in results[:limit]:
                content = getattr(item, "text", "") or getattr(item, "content", str(item))
                score = getattr(item, "score", None)
                item_tags = getattr(item, "tags", [])
                items.append(MemoryItem(
                    bank_id=self.bank_id,
                    content=content,
                    tags=item_tags,
                    score=score
                ))
            return items
        except Exception as e:
            logger.warning(f"Hindsight recall error: {e}")
            return []

    def reflect_lessons(self, query: str) -> Optional[str]:
        """
        Invokes Hindsight's reflect analytical reasoning loop across past experiences.
        """
        if not self.client:
            return None
            
        try:
            res = self.client.reflect(
                bank_id=self.bank_id,
                query=query,
                budget="low"
            )
            return getattr(res, "response", None) or getattr(res, "text", str(res))
        except Exception as e:
            logger.warning(f"Hindsight reflect error: {e}")
            return None

hindsight_service = HindsightService()
