from fastapi import APIRouter, HTTPException, Query

from backend.models.experiment import ExperimentReport
from backend.services.experiment_service import experiment_service

router = APIRouter(prefix="/api/experiment", tags=["Comparison Lab"])

@router.get("/comparison", response_model=ExperimentReport)
def get_memory_comparison(
    instrument: str = Query(default="NIFTY_50", description="Instrument ID for the backtest scenarios"),
    scenarios: int = Query(default=6, ge=3, le=12, description="Number of historical evaluation slices")
):
    try:
        report = experiment_service.run_comparison_experiment(
            instrument_id=instrument,
            num_scenarios=scenarios
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison experiment failed: {e}")
