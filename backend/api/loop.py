from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
from backend.models.loop import CompellingLoopResponse
from backend.services.workflow_loop_service import workflow_loop_service

router = APIRouter(prefix="/api/loop", tags=["Core Loop Workflow"])

@router.post("/run", response_model=CompellingLoopResponse)
def run_compelling_loop(
    instrument: str = Query(default="NIFTY_50", description="Target instrument for the complete loop"),
    x_trademind_session: Optional[str] = Header(default=None)
):
    try:
        result = workflow_loop_service.execute_complete_loop(instrument_id=instrument, session_id=x_trademind_session)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loop execution failed: {e}")
