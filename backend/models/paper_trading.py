from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED_OUT = "STOPPED_OUT"
    TARGET_HIT = "TARGET_HIT"
    CANCELLED = "CANCELLED"

class PaperOrder(BaseModel):
    order_id: str
    instrument: str
    side: OrderSide
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    target: float
    status: OrderStatus
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    fee_incurred: float = 0.0
    slippage_incurred: float = 0.0
    created_at: str
    closed_at: Optional[str] = None
    notes: Optional[str] = None

class NewOrderRequest(BaseModel):
    instrument: str
    side: OrderSide
    quantity: int = Field(gt=0)
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    notes: Optional[str] = None

class PortfolioState(BaseModel):
    initial_capital: float = 100000.0  # ₹1,00,000
    available_cash: float = 100000.0
    total_equity: float = 100000.0
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_fees_paid: float = 0.0
    total_trades_count: int = 0
    winning_trades_count: int = 0
    losing_trades_count: int = 0
    win_rate: float = 0.0
    total_return_pct: float = 0.0
    open_positions: List[PaperOrder] = []
    closed_positions: List[PaperOrder] = []
