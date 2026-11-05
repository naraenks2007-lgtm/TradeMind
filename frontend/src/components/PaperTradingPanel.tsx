import React, { useState, useEffect } from 'react';
import { PortfolioState, PaperOrder } from '../types';
import { api } from '../services/api';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  RotateCcw, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  Clock, 
  Percent,
  Plus,
  ShieldAlert
} from 'lucide-react';

interface PaperTradingPanelProps {
  currentSymbol: string;
  currentPrice: number;
}

export const PaperTradingPanel: React.FC<PaperTradingPanelProps> = ({ currentSymbol, currentPrice }) => {
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [orderQuantity, setOrderQuantity] = useState(10);
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState<number>(0);
  const [stopLoss, setStopLoss] = useState<number>(0);
  const [target, setTarget] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const fetchPortfolio = async () => {
    try {
      const data = await api.getPortfolio();
      setPortfolio(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    if (currentPrice > 0) {
      setLimitPrice(currentPrice);
      setStopLoss(orderSide === 'BUY' ? Math.round(currentPrice * 0.985) : Math.round(currentPrice * 1.015));
      setTarget(orderSide === 'BUY' ? Math.round(currentPrice * 1.035) : Math.round(currentPrice * 0.965));
    }
  }, [currentSymbol, currentPrice, orderSide]);

  const handleOpenConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    setShowConfirmModal(true);
  };

  const handleConfirmOrder = async () => {
    setShowConfirmModal(false);
    setSubmitting(true);
    setActionMsg(null);
    try {
      const order = await api.placeOrder({
        instrument: currentSymbol,
        side: orderSide,
        order_type: orderType,
        quantity: orderQuantity,
        limit_price: orderType === 'LIMIT' ? limitPrice : undefined,
        stop_loss: stopLoss,
        target: target,
        notes: `Manual virtual ${orderType} order placed from Trading Terminal`
      });
      setActionMsg(`Order ${order.order_id} executed @ ₹${order.entry_price || limitPrice}`);
      fetchPortfolio();
    } catch (err: any) {
      setActionMsg(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseOrder = async (orderId: string) => {
    try {
      await api.closeOrder(orderId);
      fetchPortfolio();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = async () => {
    if (window.confirm("Are you sure you want to reset simulated capital back to ₹1,00,000?")) {
      await api.resetPortfolio();
      fetchPortfolio();
    }
  };

  const effectivePrice = orderType === 'LIMIT' ? limitPrice : currentPrice;
  const estimatedValue = orderQuantity * effectivePrice;
  const estimatedCharges = estimatedValue * 0.0003;
  const estimatedSlippage = estimatedValue * 0.0002;

  return (
    <div className="flex flex-col space-y-5 max-w-7xl mx-auto">
      
      {/* Portfolio Top Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        
        {/* Total Equity */}
        <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>TOTAL EQUITY</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white mt-2">
            ₹{portfolio ? portfolio.total_equity.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '1,00,000.00'}
          </div>
          <div className="text-xs font-mono text-slate-500 mt-1 flex items-center justify-between">
            <span>Starting: ₹1,00,000</span>
            <span className={portfolio && portfolio.total_return_pct >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
              {portfolio && portfolio.total_return_pct >= 0 ? '+' : ''}{portfolio?.total_return_pct || 0}%
            </span>
          </div>
        </div>

        {/* Available Cash */}
        <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>AVAILABLE CASH</span>
            <span className="text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">Virtual</span>
          </div>
          <div className="text-xl font-bold font-mono text-slate-200 mt-2">
            ₹{portfolio ? portfolio.available_cash.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '1,00,000.00'}
          </div>
          <div className="text-xs font-mono text-slate-500 mt-1">
            Simulated Balance
          </div>
        </div>

        {/* Realized & Unrealized PnL */}
        <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>P&L BREAKDOWN</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline justify-between mt-2 font-mono">
            <div>
              <div className="text-[10px] text-slate-500">Realized</div>
              <div className={`text-base font-bold ${portfolio && portfolio.total_realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                ₹{portfolio?.total_realized_pnl || 0}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500">Unrealized</div>
              <div className={`text-base font-bold ${portfolio && portfolio.total_unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                ₹{portfolio?.total_unrealized_pnl || 0}
              </div>
            </div>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-1">
            Fees: ₹{portfolio?.total_fees_paid || 0}
          </div>
        </div>

        {/* Win Rate */}
        <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>WIN RATE</span>
            <span className="text-[10px] text-emerald-400 font-mono">Accuracy</span>
          </div>
          <div className="text-xl font-bold font-mono text-white mt-2">
            {portfolio?.win_rate || 0}%
          </div>
          <div className="text-xs font-mono text-slate-500 mt-1">
            {portfolio?.winning_trades_count || 0}W / {portfolio?.losing_trades_count || 0}L ({portfolio?.total_trades_count || 0} closed)
          </div>
        </div>

        {/* Max Drawdown & Reset */}
        <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>MAX DRAWDOWN</span>
            <button
              onClick={handleReset}
              title="Reset portfolio to ₹1,00,000"
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="text-xl font-bold font-mono text-rose-400 mt-2">
            {portfolio?.max_drawdown_pct || 0}%
          </div>
          <div className="text-xs font-mono text-slate-500 mt-1">
            Peak Risk Metric
          </div>
        </div>

      </div>

      {/* Place Order & Positions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Order Ticket */}
        <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Virtual Order Ticket
            </h3>
            <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              {currentSymbol} @ ₹{currentPrice.toFixed(2)}
            </span>
          </div>

          <form onSubmit={handleOpenConfirm} className="space-y-3 text-xs font-mono">
            {/* Side Tabs */}
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setOrderSide('BUY')}
                className={`py-2 rounded-xl font-bold transition ${
                  orderSide === 'BUY'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                    : 'bg-slate-900 text-slate-400 border border-slate-800'
                }`}
              >
                BUY (Long)
              </button>
              <button
                type="button"
                onClick={() => setOrderSide('SELL')}
                className={`py-2 rounded-xl font-bold transition ${
                  orderSide === 'SELL'
                    ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                    : 'bg-slate-900 text-slate-400 border border-slate-800'
                }`}
              >
                SELL (Short)
              </button>
            </div>

            {/* Order Type */}
            <div>
              <label className="text-slate-400 block mb-1">Order Execution Type</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setOrderType('MARKET')}
                  className={`py-1.5 rounded-lg font-medium transition ${
                    orderType === 'MARKET'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}
                >
                  MARKET
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('LIMIT')}
                  className={`py-1.5 rounded-lg font-medium transition ${
                    orderType === 'LIMIT'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}
                >
                  LIMIT
                </button>
              </div>
            </div>

            {/* Limit Price if LIMIT */}
            {orderType === 'LIMIT' && (
              <div>
                <label className="text-slate-400 block mb-1">Limit Price (₹)</label>
                <input
                  type="number"
                  step="0.1"
                  value={limitPrice}
                  onChange={(e) => setLimitPrice(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white font-bold outline-none focus:border-blue-500 transition"
                />
              </div>
            )}

            {/* Quantity */}
            <div>
              <label className="text-slate-400 block mb-1">Quantity (Units)</label>
              <input
                type="number"
                min="1"
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(Math.max(1, Number(e.target.value)))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white font-bold outline-none focus:border-blue-500 transition"
              />
            </div>

            {/* Stop Loss */}
            <div>
              <label className="text-slate-400 block mb-1">Stop Loss (₹)</label>
              <input
                type="number"
                step="0.5"
                value={stopLoss}
                onChange={(e) => setStopLoss(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-rose-400 font-bold outline-none focus:border-rose-500 transition"
              />
            </div>

            {/* Target */}
            <div>
              <label className="text-slate-400 block mb-1">Target Price (₹)</label>
              <input
                type="number"
                step="0.5"
                value={target}
                onChange={(e) => setTarget(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-emerald-400 font-bold outline-none focus:border-emerald-500 transition"
              />
            </div>

            {/* Order Cost & Fees breakdown */}
            <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Estimated Value:</span>
                <span className="text-slate-200">₹{estimatedValue.toLocaleString('en-IN', { maximumFractionDigits: 1 })}</span>
              </div>
              <div className="flex justify-between">
                <span>Transaction Charges (0.03%):</span>
                <span>₹{estimatedCharges.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Simulated Slippage (0.02%):</span>
                <span>±₹{estimatedSlippage.toFixed(2)}</span>
              </div>
            </div>

            {actionMsg && (
              <div className={`p-2 rounded-lg text-xs ${actionMsg.startsWith('Error') ? 'bg-rose-950/40 text-rose-300' : 'bg-emerald-950/40 text-emerald-300'}`}>
                {actionMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className={`w-full py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider text-white transition ${
                orderSide === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'
              }`}
            >
              {submitting ? 'Executing...' : `Review & Place ${orderType} ${orderSide} Order`}
            </button>
          </form>
        </div>

        {/* Positions & Trade History */}
        <div className="lg:col-span-2 flex flex-col space-y-4">
          
          {/* Open Positions */}
          <div className="bg-[#121824] border border-slate-800 rounded-2xl p-4 shadow-xl">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono mb-3">
              Open Positions ({portfolio?.open_positions.length || 0})
            </h3>
            {!portfolio?.open_positions.length ? (
              <div className="text-center py-6 text-xs text-slate-500 font-mono">
                No active open positions.
              </div>
            ) : (
              <div className="space-y-2">
                {portfolio.open_positions.map((pos) => (
                  <div key={pos.order_id} className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex items-center justify-between text-xs font-mono">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          pos.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {pos.side}
                        </span>
                        <span className="font-bold text-white">{pos.instrument}</span>
                        <span className="text-slate-400">{pos.quantity} Qty</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Entry: ₹{pos.entry_price} | Current: ₹{pos.current_price} | SL: ₹{pos.stop_loss} | Tgt: ₹{pos.target}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className={`text-right font-bold ${pos.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {pos.unrealized_pnl >= 0 ? '+' : ''}₹{pos.unrealized_pnl}
                      </div>
                      <button
                        onClick={() => handleCloseOrder(pos.order_id)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] border border-slate-700 transition"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Trade History */}
          <div className="bg-[#121824] border border-slate-800 rounded-2xl p-4 shadow-xl">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono mb-3">
              Closed Trade History ({portfolio?.closed_positions.length || 0})
            </h3>
            {!portfolio?.closed_positions.length ? (
              <div className="text-center py-6 text-xs text-slate-500 font-mono">
                No closed trades yet. Closed trades retain lessons directly into Hindsight.
              </div>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {portfolio.closed_positions.map((tr) => (
                  <div key={tr.order_id} className="bg-slate-900/60 border border-slate-800/80 p-2.5 rounded-xl flex items-center justify-between text-xs font-mono">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white">{tr.instrument}</span>
                        <span className="text-slate-400">{tr.side} {tr.quantity} Qty</span>
                        <span className="text-slate-500 text-[10px]">{tr.closed_at}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Entry ₹{tr.entry_price} → Exit ₹{tr.current_price} ({tr.status})
                      </div>
                    </div>
                    <div className={`font-bold ${tr.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {tr.realized_pnl >= 0 ? '+' : ''}₹{tr.realized_pnl}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Explicit Order Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0F141F] border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl font-mono">
            <div className="flex items-center space-x-2 text-amber-400 border-b border-slate-800 pb-3">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="text-sm font-bold text-white">Confirm Paper Order</h3>
            </div>

            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Instrument:</span>
                <span className="font-bold text-white">{currentSymbol}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Order Side:</span>
                <span className={orderSide === 'BUY' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                  {orderSide}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Type:</span>
                <span className="text-blue-400 font-bold">{orderType}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Quantity:</span>
                <span className="font-bold text-white">{orderQuantity} Units</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Reference Price:</span>
                <span className="font-bold text-white">₹{effectivePrice.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Stop Loss:</span>
                <span className="text-rose-400 font-bold">₹{stopLoss.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Target:</span>
                <span className="text-emerald-400 font-bold">₹{target.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Estimated Value:</span>
                <span className="font-bold text-white">₹{estimatedValue.toFixed(2)}</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
              * Paper order executed strictly internally in TradeMind. Upstox is NEVER sent any order.
            </p>

            <div className="flex items-center space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmOrder}
                className="flex-1 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/30"
              >
                Confirm & Place
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
