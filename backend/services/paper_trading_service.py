import uuid
from typing import List, Dict, Optional
from datetime import datetime

from backend.models.paper_trading import (
    PaperOrder,
    OrderSide,
    OrderStatus,
    PortfolioState,
    NewOrderRequest
)
from backend.services.hindsight_service import hindsight_service

class PaperTradingService:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.brokerage_rate = 0.0003  # 0.03%
        self.slippage_rate = 0.0002   # 0.02%
        self.open_orders: Dict[str, PaperOrder] = {}
        self.closed_orders: List[PaperOrder] = []

    def get_portfolio_state(self, current_prices: Optional[Dict[str, float]] = None) -> PortfolioState:
        current_prices = current_prices or {}
        
        # Recalculate unrealized P&L and check stop/target triggers
        total_unrealized = 0.0
        positions_to_close = []
        
        for order_id, order in list(self.open_orders.items()):
            cur_price = current_prices.get(order.instrument, order.current_price)
            order.current_price = cur_price
            
            if order.side == OrderSide.BUY:
                pnl = (cur_price - order.entry_price) * order.quantity
                # Trigger checks
                if order.stop_loss and cur_price <= order.stop_loss:
                    positions_to_close.append((order_id, OrderStatus.STOPPED_OUT, order.stop_loss))
                elif order.target and cur_price >= order.target:
                    positions_to_close.append((order_id, OrderStatus.TARGET_HIT, order.target))
            else:  # SELL (short)
                pnl = (order.entry_price - cur_price) * order.quantity
                if order.stop_loss and cur_price >= order.stop_loss:
                    positions_to_close.append((order_id, OrderStatus.STOPPED_OUT, order.stop_loss))
                elif order.target and cur_price <= order.target:
                    positions_to_close.append((order_id, OrderStatus.TARGET_HIT, order.target))
                    
            order.unrealized_pnl = round(pnl, 2)
            total_unrealized += order.unrealized_pnl

        # Execute auto exits
        for order_id, exit_status, exit_price in positions_to_close:
            self.close_order(order_id, exit_price=exit_price, reason_status=exit_status)

        total_realized = sum(o.realized_pnl for o in self.closed_orders)
        total_fees = sum(o.fee_incurred for o in self.closed_orders) + sum(o.fee_incurred for o in self.open_orders.values())
        
        equity = round(self.available_cash + sum(o.entry_price * o.quantity for o in self.open_orders.values()) + total_unrealized, 2)
        total_trades = len(self.closed_orders)
        winning_trades = sum(1 for o in self.closed_orders if o.realized_pnl > 0)
        losing_trades = sum(1 for o in self.closed_orders if o.realized_pnl < 0)
        win_rate = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0.0
        return_pct = round(((equity - self.initial_capital) / self.initial_capital * 100), 2)

        return PortfolioState(
            initial_capital=self.initial_capital,
            available_cash=round(self.available_cash, 2),
            total_equity=equity,
            total_realized_pnl=round(total_realized, 2),
            total_unrealized_pnl=round(total_unrealized, 2),
            total_fees_paid=round(total_fees, 2),
            total_trades_count=total_trades,
            winning_trades_count=winning_trades,
            losing_trades_count=losing_trades,
            win_rate=win_rate,
            total_return_pct=return_pct,
            open_positions=list(self.open_orders.values()),
            closed_positions=self.closed_orders
        )

    def execute_order(self, req: NewOrderRequest, current_market_price: float) -> PaperOrder:
        # Apply simulated slippage
        if req.side == OrderSide.BUY:
            fill_price = current_market_price * (1.0 + self.slippage_rate)
        else:
            fill_price = current_market_price * (1.0 - self.slippage_rate)
            
        fill_price = round(fill_price, 2)
        order_value = fill_price * req.quantity
        fee = round(order_value * self.brokerage_rate, 2)
        
        required_capital = order_value + fee
        if required_capital > self.available_cash:
            raise ValueError(
                f"Insufficient funds: Required ₹{required_capital:,.2f}, Available ₹{self.available_cash:,.2f}"
            )
            
        self.available_cash -= required_capital
        
        order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
        order = PaperOrder(
            order_id=order_id,
            instrument=req.instrument,
            side=req.side,
            quantity=req.quantity,
            entry_price=fill_price,
            current_price=fill_price,
            stop_loss=req.stop_loss or (fill_price * 0.98 if req.side == OrderSide.BUY else fill_price * 1.02),
            target=req.target or (fill_price * 1.04 if req.side == OrderSide.BUY else fill_price * 0.96),
            status=OrderStatus.OPEN,
            fee_incurred=fee,
            slippage_incurred=round(abs(fill_price - current_market_price) * req.quantity, 2),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            notes=req.notes
        )
        
        self.open_orders[order_id] = order
        return order

    def close_order(self, order_id: str, exit_price: Optional[float] = None, reason_status: OrderStatus = OrderStatus.CLOSED) -> PaperOrder:
        if order_id not in self.open_orders:
            raise KeyError(f"Order {order_id} not found in open positions.")
            
        order = self.open_orders.pop(order_id)
        final_price = exit_price if exit_price is not None else order.current_price
        
        # Calculate exit fees
        exit_value = final_price * order.quantity
        exit_fee = round(exit_value * self.brokerage_rate, 2)
        
        if order.side == OrderSide.BUY:
            gross_pnl = (final_price - order.entry_price) * order.quantity
        else:
            gross_pnl = (order.entry_price - final_price) * order.quantity
            
        net_pnl = round(gross_pnl - (order.fee_incurred + exit_fee), 2)
        
        order.current_price = final_price
        order.realized_pnl = net_pnl
        order.unrealized_pnl = 0.0
        order.fee_incurred += exit_fee
        order.status = reason_status
        order.closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.available_cash += (order.entry_price * order.quantity) + net_pnl
        self.closed_orders.insert(0, order)
        
        # Retain trade outcome into Hindsight Long-Term Memory
        outcome_lesson = (
            f"Paper Trade Completed on {order.instrument} ({order.side.value}): "
            f"Entry=₹{order.entry_price}, Exit=₹{final_price}, Net PnL=₹{net_pnl} ({order.status.value}). "
            f"Result: {'WIN' if net_pnl > 0 else 'LOSS'}. "
            f"{'Target achieved.' if order.status == OrderStatus.TARGET_HIT else 'Stopped out to protect capital.' if order.status == OrderStatus.STOPPED_OUT else 'Manually closed.'}"
        )
        hindsight_service.retain_memory(
            content=outcome_lesson,
            tags=[order.instrument, "trade_outcome", "WIN" if net_pnl > 0 else "LOSS"],
            metadata={
                "order_id": str(order.order_id),
                "instrument": str(order.instrument),
                "pnl": str(net_pnl),
                "status": str(order.status.value)
            }
        )
        
        return order

    def reset_account(self):
        self.available_cash = self.initial_capital
        self.open_orders.clear()
        self.closed_orders.clear()

paper_trading_service = PaperTradingService()
