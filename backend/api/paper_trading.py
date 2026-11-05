from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.models.paper_trading import PortfolioState, NewOrderRequest, PaperOrder
from backend.services.paper_trading_service import paper_trading_service
from backend.services.data_loader import data_loader_service
from backend.services.replay_service import replay_service
from backend.services.upstox_service import upstox_service, UPSTOX_INSTRUMENTS

router = APIRouter(prefix="/api/paper-trading", tags=["Paper Trading Engine"])

def _resolve_current_price(instrument: str) -> float:
    # 1. If Replay is active for this instrument
    if replay_service.is_active and replay_service.instrument_id == instrument:
        return replay_service.get_state().get("current_price", 0.0)

    # 2. If Upstox is authenticated and online
    if upstox_service.get_connection_status().get("authenticated"):
        inst_info = UPSTOX_INSTRUMENTS.get(instrument.upper())
        if inst_info:
            quote = upstox_service.get_market_quote(inst_info["instrument_key"])
            if quote and "last_price" in quote:
                return float(quote["last_price"])

    # 3. Fallback to latest local historical dataset
    df, _ = data_loader_service.load_ohlcv_dataframe(instrument)
    return float(df["Close"].iloc[-1])

@router.get("/portfolio", response_model=PortfolioState)
def get_portfolio():
    """Returns current portfolio state with real-time unrealized P&L and drawdown."""
    instruments = data_loader_service.list_available_instruments()
    price_map = {}
    for inst in instruments:
        try:
            price_map[inst.id] = _resolve_current_price(inst.id)
        except Exception:
            price_map[inst.id] = inst.latest_close

    return paper_trading_service.get_portfolio_state(current_prices=price_map)

@router.post("/order", response_model=PaperOrder)
def place_order(req: NewOrderRequest):
    """
    Executes an internal simulated paper-trading order.
    
    SAFETY ENFORCEMENT:
    Paper orders are NEVER sent to Upstox or any live broker. Execution is strictly internal.
    """
    try:
        current_price = _resolve_current_price(req.instrument)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot resolve market price for {req.instrument}: {e}")

    try:
        order = paper_trading_service.execute_order(req, current_market_price=current_price)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/order/{order_id}/close", response_model=PaperOrder)
def close_order(order_id: str):
    """Closes an open position and retains the outcome/lesson into Hindsight."""
    try:
        if order_id in paper_trading_service.open_orders:
            inst = paper_trading_service.open_orders[order_id].instrument
        elif order_id in paper_trading_service.pending_limit_orders:
            inst = paper_trading_service.pending_limit_orders[order_id].instrument
        else:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")

        current_price = _resolve_current_price(inst)
        return paper_trading_service.close_order(order_id, exit_price=current_price)
    except KeyError:
        raise HTTPException(status_code=404, detail="Order not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders", response_model=Dict[str, List[PaperOrder]])
def get_all_orders():
    """Returns all open positions, pending limits, and closed trade history."""
    return {
        "open_orders": list(paper_trading_service.open_orders.values()),
        "pending_limit_orders": list(paper_trading_service.pending_limit_orders.values()),
        "closed_orders": paper_trading_service.closed_orders
    }

@router.post("/reset")
def reset_account() -> Dict[str, str]:
    """Resets paper-trading account balance to ₹1,00,000 virtual capital."""
    paper_trading_service.reset_account()
    return {"status": "success", "message": "Simulated capital reset to ₹1,00,000."}
