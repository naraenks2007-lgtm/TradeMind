from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend.services.replay_service import replay_service
from backend.models.market import MarketSnapshot

router = APIRouter(prefix="/api/replay", tags=["Historical Replay"])

class StartReplayRequest(BaseModel):
    instrument: str = "NIFTY_50"
    start_date: Optional[str] = None

class StepReplayRequest(BaseModel):
    steps: int = 1

class SpeedRequest(BaseModel):
    speed: int

class JumpRequest(BaseModel):
    target_date: str

@router.post("/start")
def start_replay(req: StartReplayRequest):
    """Starts historical replay mode for an instrument without look-ahead bias."""
    return replay_service.start_replay(req.instrument, req.start_date)

@router.post("/stop")
def stop_replay():
    """Stops replay simulation mode."""
    return replay_service.stop_replay()

@router.post("/step")
def step_replay(req: StepReplayRequest = StepReplayRequest()):
    """Advances replay by specified number of candles and checks pending orders."""
    return replay_service.step(req.steps)

@router.post("/speed")
def set_speed(req: SpeedRequest):
    """Sets playback speed multiplier (1, 2, 5, 10, 20, 50)."""
    spd = replay_service.set_speed(req.speed)
    return {"speed": spd}

@router.post("/jump")
def jump_to_date(req: JumpRequest):
    """Jumps simulation to a specific date."""
    return replay_service.jump_to_date(req.target_date)

@router.get("/state")
def get_replay_state():
    """Returns current replay state."""
    return replay_service.get_state()

@router.get("/snapshot", response_model=MarketSnapshot)
def get_replay_snapshot(limit: int = 180):
    """Returns the look-ahead-free market snapshot at the current replay position."""
    try:
        return replay_service.get_snapshot(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
