from fastapi import APIRouter, HTTPException, Query
from backend.models.loop import CompellingLoopResponse
from backend.services.workflow_loop_service import workflow_loop_service

router = APIRouter(prefix="/api/loop", tags=["Core Loop Workflow"])

@router.post("/run", response_model=CompellingLoopResponse)
def run_compelling_loop(
    instrument: str = Query(default="NIFTY_50", description="Target instrument for the complete loop")
):
    try:
        result = workflow_loop_service.execute_complete_loop(instrument_id=instrument)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loop execution failed: {e}")
