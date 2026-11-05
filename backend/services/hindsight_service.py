import os
import json
import logging
import concurrent.futures
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
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="hindsight_worker")
        self._init_client()

    def _execute_sync(self, func, *args, **kwargs):
        """Executes client call in isolated thread to prevent Python 3.13 event loop conflicts."""
        future = self._thread_pool.submit(func, *args, **kwargs)
        return future.result(timeout=15.0)

    def _init_client(self):
        try:
            from hindsight_client import Hindsight
            if self.base_url:
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key if self.api_key else None,
                    timeout=12.0,
                    max_attempts=2
                )
        except Exception as e:
            logger.warning(f"Could not initialize Hindsight client: {e}")
            self.client = None

    def _ensure_bank_exists(self):
        """Ensures the TradeMind bank is created in Hindsight."""
        if not self.client:
            return
        try:
            self._execute_sync(self.client.get_bank_config, bank_id=self.bank_id)
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                try:
                    self._execute_sync(
                        self.client.create_bank,
                        bank_id=self.bank_id,
                        name="TradeMind Bank",
                        mission="Persistent memory and learning for TradeMind trading hypotheses and trade outcomes."
                    )
                except Exception as ce:
                    logger.warning(f"Could not create Hindsight bank: {ce}")

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
            self._ensure_bank_exists()
            config = self._execute_sync(self.client.get_bank_config, bank_id=self.bank_id)
            return MemoryStatus(
                connected=True,
                service_url=self.base_url,
                bank_id=self.bank_id,
                status_message="Online: Connected to Vectorize Hindsight Engine",
                memory_count=1
            )
        except Exception as e:
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
            self._ensure_bank_exists()
            res = self._execute_sync(
                self.client.retain,
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
            self._ensure_bank_exists()
            res = self._execute_sync(
                self.client.recall,
                bank_id=self.bank_id,
                query=query,
                tags=tags,
                budget="mid"
            )
            
            items: List[MemoryItem] = []
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
            self._ensure_bank_exists()
            res = self._execute_sync(
                self.client.reflect,
                bank_id=self.bank_id,
                query=query,
                budget="low"
            )
            return getattr(res, "response", None) or getattr(res, "text", str(res))
        except Exception as e:
            logger.warning(f"Hindsight reflect error: {e}")
            return None

    def reflect_and_learn_from_trade(
        self,
        instrument: str,
        hypothesis_text: str,
        entry_price: float,
        exit_price: float,
        net_pnl: float,
        exit_reason: str
    ) -> Dict[str, Any]:
        """
        Reflects on the outcome of a completed paper trade against the original hypothesis,
        synthesizes a qualified lesson, and retains it into Hindsight.
        """
        outcome_str = "WIN" if net_pnl > 0 else "LOSS"
        query = (
            f"Compare hypothesis for {instrument} with final trade result: "
            f"Original Thesis: '{hypothesis_text}'. "
            f"Executed: Entry=₹{entry_price}, Exit=₹{exit_price}, Net PnL=₹{net_pnl} ({outcome_str}, {exit_reason}). "
            f"What worked or failed? What is the verified lesson for future setups?"
        )
        lesson = self.reflect_lessons(query)
        if not lesson:
            lesson = (
                f"Trade on {instrument} resulted in {outcome_str} (PnL: ₹{net_pnl}). "
                f"Reason: {exit_reason}. "
                f"Lesson: Adhere strictly to stop loss and avoid chasing extended moves beyond Bollinger Bands."
            )

        retain_res = self.retain_memory(
            content=f"QUALIFIED LESSON ({instrument}): {lesson}",
            tags=[instrument, "verified_lesson", outcome_str],
            metadata={
                "instrument": instrument,
                "net_pnl": str(net_pnl),
                "outcome": outcome_str,
                "learned_at": datetime.now().isoformat()
            }
        )
        return {
            "outcome": outcome_str,
            "lesson": lesson,
            "retained": retain_res.get("success", False)
        }

hindsight_service = HindsightService()
