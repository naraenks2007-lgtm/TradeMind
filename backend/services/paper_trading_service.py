import os
import sqlite3
import json
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from backend.config import settings
from backend.models.paper_trading import (
    PaperOrder,
    OrderSide,
    OrderType,
    OrderStatus,
    PortfolioState,
    NewOrderRequest
)
from backend.services.hindsight_service import hindsight_service

DB_PATH = settings.BASE_DIR / "data" / "paper_trading.db"

class PaperTradingService:
    """
    Independent Paper-Trading Engine.
    
    SAFETY ASSURANCE:
    This engine executes trades strictly in-memory and in a local SQLite database.
    It NEVER invokes any broker order-placement API or real financial transaction.
    """
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.brokerage_rate = 0.0003  # 0.03% (Brokerage + STT + Turnover + GST)
        self.slippage_rate = 0.0002   # 0.02% (Simulated fill friction)
        self.peak_equity = initial_capital
        self.max_drawdown_pct = 0.0
        
        self.open_orders: Dict[str, PaperOrder] = {}
        self.pending_limit_orders: Dict[str, PaperOrder] = {}
        self.closed_orders: List[PaperOrder] = []
        
        self._init_db()
        self._load_from_db()

    def _init_db(self):
        """Initializes SQLite schema for robust persistence."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    instrument TEXT,
                    side TEXT,
                    order_type TEXT,
                    quantity INTEGER,
                    entry_price REAL,
                    limit_price REAL,
                    current_price REAL,
                    stop_loss REAL,
                    target REAL,
                    status TEXT,
                    realized_pnl REAL,
                    unrealized_pnl REAL,
                    fee_incurred REAL,
                    slippage_incurred REAL,
                    created_at TEXT,
                    closed_at TEXT,
                    notes TEXT
                )
            """)
            conn.commit()

    def _save_order_to_db(self, order: PaperOrder):
        """Persists or updates an individual order in SQLite."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO orders VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                order.order_id,
                order.instrument,
                order.side.value,
                order.order_type.value,
                order.quantity,
                order.entry_price,
                order.limit_price,
                order.current_price,
                order.stop_loss,
                order.target,
                order.status.value,
                order.realized_pnl,
                order.unrealized_pnl,
                order.fee_incurred,
                order.slippage_incurred,
                order.created_at,
                order.closed_at,
                order.notes
            ))
            cursor.execute("INSERT OR REPLACE INTO portfolio_meta VALUES ('available_cash', ?)", (str(self.available_cash),))
            cursor.execute("INSERT OR REPLACE INTO portfolio_meta VALUES ('peak_equity', ?)", (str(self.peak_equity),))
            cursor.execute("INSERT OR REPLACE INTO portfolio_meta VALUES ('max_drawdown_pct', ?)", (str(self.max_drawdown_pct),))
            conn.commit()

    def _load_from_db(self):
        """Restores orders and cash balance on engine startup."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM portfolio_meta")
                meta = dict(cursor.fetchall())
                if "available_cash" in meta:
                    self.available_cash = float(meta["available_cash"])
                if "peak_equity" in meta:
                    self.peak_equity = float(meta["peak_equity"])
                if "max_drawdown_pct" in meta:
                    self.max_drawdown_pct = float(meta["max_drawdown_pct"])

                cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
                rows = cursor.fetchall()
                for r in rows:
                    order = PaperOrder(
                        order_id=r[0],
                        instrument=r[1],
                        side=OrderSide(r[2]),
                        order_type=OrderType(r[3]),
                        quantity=r[4],
                        entry_price=r[5],
                        limit_price=r[6],
                        current_price=r[7],
                        stop_loss=r[8],
                        target=r[9],
                        status=OrderStatus(r[10]),
                        realized_pnl=r[11],
                        unrealized_pnl=r[12],
                        fee_incurred=r[13],
                        slippage_incurred=r[14],
                        created_at=r[15],
                        closed_at=r[16],
                        notes=r[17]
                    )
                    if order.status in (OrderStatus.OPEN, OrderStatus.FILLED):
                        self.open_orders[order.order_id] = order
                    elif order.status == OrderStatus.OPEN and order.order_type == OrderType.LIMIT and order.entry_price == 0:
                        self.pending_limit_orders[order.order_id] = order
                    else:
                        self.closed_orders.append(order)
        except Exception:
            pass

    def get_portfolio_state(self, current_prices: Optional[Dict[str, float]] = None) -> PortfolioState:
        """Calculates current portfolio state, unrealized P&L, win rate, and max drawdown."""
        current_prices = current_prices or {}
        
        # 1. Check pending limit orders against current prices
        for order_id, order in list(self.pending_limit_orders.items()):
            cur_price = current_prices.get(order.instrument)
            if cur_price is not None and order.limit_price is not None:
                is_triggered = (order.side == OrderSide.BUY and cur_price <= order.limit_price) or \
                               (order.side == OrderSide.SELL and cur_price >= order.limit_price)
                if is_triggered:
                    self.pending_limit_orders.pop(order_id)
                    order.entry_price = order.limit_price
                    order.current_price = cur_price
                    order.status = OrderStatus.OPEN
                    self.open_orders[order_id] = order
                    self._save_order_to_db(order)

        # 2. Recalculate unrealized P&L and check stop/target triggers
        total_unrealized = 0.0
        positions_to_close = []
        
        for order_id, order in list(self.open_orders.items()):
            cur_price = current_prices.get(order.instrument, order.current_price)
            order.current_price = cur_price
            
            if order.side == OrderSide.BUY:
                pnl = (cur_price - order.entry_price) * order.quantity
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

        # 3. Execute auto exits
        for order_id, exit_status, exit_price in positions_to_close:
            self.close_order(order_id, exit_price=exit_price, reason_status=exit_status)

        total_realized = sum(o.realized_pnl for o in self.closed_orders)
        total_fees = sum(o.fee_incurred for o in self.closed_orders) + sum(o.fee_incurred for o in self.open_orders.values())
        
        invested_capital = sum(o.entry_price * o.quantity for o in self.open_orders.values())
        equity = round(self.available_cash + invested_capital + total_unrealized, 2)
        
        # Track Peak Equity & Max Drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity > 0:
            current_drawdown = round(((self.peak_equity - equity) / self.peak_equity) * 100, 2)
            if current_drawdown > self.max_drawdown_pct:
                self.max_drawdown_pct = current_drawdown

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
            max_drawdown_pct=self.max_drawdown_pct,
            total_return_pct=return_pct,
            open_positions=list(self.open_orders.values()),
            closed_positions=self.closed_orders
        )

    def execute_order(self, req: NewOrderRequest, current_market_price: float) -> PaperOrder:
        """Executes a paper order against current simulated or live market price."""
        order_type = req.order_type or OrderType.MARKET
        
        # If LIMIT order specified and not immediately marketable
        if order_type == OrderType.LIMIT and req.limit_price is not None:
            is_immediate = (req.side == OrderSide.BUY and current_market_price <= req.limit_price) or \
                           (req.side == OrderSide.SELL and current_market_price >= req.limit_price)
            if not is_immediate:
                order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
                order = PaperOrder(
                    order_id=order_id,
                    instrument=req.instrument,
                    side=req.side,
                    order_type=OrderType.LIMIT,
                    quantity=req.quantity,
                    entry_price=0.0,
                    limit_price=req.limit_price,
                    current_price=current_market_price,
                    stop_loss=req.stop_loss or (req.limit_price * 0.98 if req.side == OrderSide.BUY else req.limit_price * 1.02),
                    target=req.target or (req.limit_price * 1.04 if req.side == OrderSide.BUY else req.limit_price * 0.96),
                    status=OrderStatus.OPEN,
                    fee_incurred=0.0,
                    slippage_incurred=0.0,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    notes=f"Limit Order pending trigger @ ₹{req.limit_price}"
                )
                self.pending_limit_orders[order_id] = order
                self._save_order_to_db(order)
                return order

        # Market order or immediately triggered limit order
        base_price = req.limit_price if (order_type == OrderType.LIMIT and req.limit_price) else current_market_price
        
        # Apply simulated slippage
        if req.side == OrderSide.BUY:
            fill_price = base_price * (1.0 + self.slippage_rate)
        else:
            fill_price = base_price * (1.0 - self.slippage_rate)
            
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
            order_type=order_type,
            quantity=req.quantity,
            entry_price=fill_price,
            limit_price=req.limit_price,
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
        self._save_order_to_db(order)
        return order

    def close_order(self, order_id: str, exit_price: Optional[float] = None, reason_status: OrderStatus = OrderStatus.CLOSED) -> PaperOrder:
        """Closes an open position, computes net P&L, saves to DB, and retains learning in Hindsight."""
        if order_id not in self.open_orders:
            if order_id in self.pending_limit_orders:
                order = self.pending_limit_orders.pop(order_id)
                order.status = OrderStatus.CANCELLED
                order.closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_orders.insert(0, order)
                self._save_order_to_db(order)
                return order
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
        self._save_order_to_db(order)
        
        # Retain trade outcome into Hindsight Long-Term Memory
        outcome_lesson = (
            f"Paper Trade Completed on {order.instrument} ({order.side.value}): "
            f"Entry=₹{order.entry_price}, Exit=₹{final_price}, Net PnL=₹{net_pnl} ({order.status.value}). "
            f"Result: {'WIN' if net_pnl > 0 else 'LOSS'}. "
            f"{'Target achieved.' if order.status == OrderStatus.TARGET_HIT else 'Stopped out to protect capital.' if order.status == OrderStatus.STOPPED_OUT else 'Manually closed.'} "
            f"Notes: {order.notes or 'No user notes'}"
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
        """Resets the paper trading account to ₹1,00,000 virtual capital."""
        self.available_cash = self.initial_capital
        self.peak_equity = self.initial_capital
        self.max_drawdown_pct = 0.0
        self.open_orders.clear()
        self.pending_limit_orders.clear()
        self.closed_orders.clear()
        
        if DB_PATH.exists():
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM orders")
                cursor.execute("DELETE FROM portfolio_meta")
                conn.commit()

paper_trading_service = PaperTradingService()
