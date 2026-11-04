from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models.paper_trading import PortfolioState, NewOrderRequest, PaperOrder
from backend.services.paper_trading_service import paper_trading_service
from backend.services.data_loader import data_loader_service

router = APIRouter(prefix="/api/paper-trading", tags=["Paper Trading"])

@router.get("/portfolio", response_model=PortfolioState)
def get_portfolio():
    # Build current price mapping from available instruments
    instruments = data_loader_service.list_available_instruments()
    price_map = {inst.id: inst.latest_close for inst in instruments}
    return paper_trading_service.get_portfolio_state(current_prices=price_map)

@router.post("/order", response_model=PaperOrder)
def place_order(req: NewOrderRequest):
    # Lookup current price
    try:
        df, _ = data_loader_service.load_ohlcv_dataframe(req.instrument)
        current_price = float(df["Close"].iloc[-1])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot resolve market price for {req.instrument}: {e}")

    try:
        order = paper_trading_service.execute_order(req, current_market_price=current_price)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/order/{order_id}/close", response_model=PaperOrder)
def close_order(order_id: str):
    try:
        # Get order to find its instrument
        if order_id not in paper_trading_service.open_orders:
            raise HTTPException(status_code=404, detail="Open order not found.")
        inst = paper_trading_service.open_orders[order_id].instrument
        df, _ = data_loader_service.load_ohlcv_dataframe(inst)
        current_price = float(df["Close"].iloc[-1])
        
        return paper_trading_service.close_order(order_id, exit_price=current_price)
    except KeyError:
        raise HTTPException(status_code=404, detail="Order not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
def reset_account() -> Dict[str, str]:
    paper_trading_service.reset_account()
    return {"status": "success", "message": "Simulated capital reset to ₹1,00,000."}
