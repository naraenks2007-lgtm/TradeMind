from fastapi import APIRouter
from typing import Dict, Any

from backend.services.llm_service import llm_service
from backend.services.hindsight_service import hindsight_service
from backend.services.data_loader import data_loader_service
from backend.services.upstox_service import upstox_service
from backend.services.replay_service import replay_service

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def get_system_health() -> Dict[str, Any]:
    # 1. Groq connection
    groq_status = llm_service.check_connection()
    
    # 2. Hindsight connection
    hindsight_stat = hindsight_service.get_status()
    
    # 3. Upstox connection
    upstox_stat = upstox_service.get_connection_status()
    
    # 4. Market data availability
    instruments = data_loader_service.list_available_instruments()
    historical_count = sum(1 for i in instruments if not i.is_synthetic and "Historical" in i.source)
    synthetic_count = sum(1 for i in instruments if i.is_synthetic)
    uploads_count = sum(1 for i in instruments if "User" in i.source)
    
    overall_status = "operational" if (groq_status.get("connected") and historical_count > 0) else "degraded"
    
    return {
        "status": overall_status,
        "backend": {
            "status": "online",
            "version": "1.0.0"
        },
        "groq": groq_status,
        "hindsight": {
            "connected": hindsight_stat.connected,
            "bank_id": hindsight_stat.bank_id,
            "status_message": hindsight_stat.status_message,
            "service_url": hindsight_stat.service_url
        },
        "upstox": upstox_stat,
        "replay": replay_service.get_state(),
        "market_data": {
            "available": len(instruments) > 0,
            "total_instruments": len(instruments),
            "historical_instruments_count": historical_count,
            "synthetic_fallback_count": synthetic_count,
            "user_uploads_count": uploads_count
        }
    }
