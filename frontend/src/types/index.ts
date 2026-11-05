export type MarketDirection = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

export interface InstrumentMetadata {
  id: string;
  symbol: string;
  name: string;
  instrument_key?: string;
  file_name?: string;
  source: string;
  is_synthetic: boolean;
  last_timestamp: string;
  row_count: number;
  latest_close: number;
}

export interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSummary {
  rsi?: number;
  ema20?: number;
  ema50?: number;
  ema200?: number;
  macd?: number;
  macd_signal?: number;
  macd_hist?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  atr?: number;
  trend_summary?: string;
  volatility_summary?: string;
}

export interface MarketSnapshot {
  symbol: string;
  instrument_name: string;
  instrument_key?: string;
  timeframe: string;
  data_source: string;
  is_synthetic: boolean;
  is_live?: boolean;
  is_replay?: boolean;
  connection_status?: string;
  last_timestamp: string;
  candle_count: number;
  current_price: number;
  change_pct: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  candles: CandleData[];
  indicators: IndicatorSummary;
  raw_indicator_series?: {
    rsi: (number | null)[];
    ema20: (number | null)[];
    ema50: (number | null)[];
    macd: (number | null)[];
    macd_signal: (number | null)[];
    macd_hist: (number | null)[];
    bb_upper: (number | null)[];
    bb_lower: (number | null)[];
  };
}

export interface TradingHypothesis {
  instrument: string;
  market_direction: MarketDirection;
  hypothesis: string;
  supporting_evidence: string[];
  confidence: number;
  entry_condition?: string;
  entry_assumption: number;
  stop_loss_assumption: number;
  target_assumption: number;
  support_level?: number;
  resistance_level?: number;
  invalidation_conditions: string[];
  risk_explanation: string;
  data_source?: string;
  data_timestamp?: string;
  memory_applied: boolean;
  recalled_lessons?: string[];
  created_at?: string;
}

export interface MarketChatResponse {
  answer: string;
  instrument: string;
  current_price: number;
  data_source: string;
  data_timestamp: string;
  recalled_memories: string[];
  hypothesis?: TradingHypothesis;
}

export interface UpstoxStatus {
  configured: boolean;
  authenticated: boolean;
  status: string;
  user_name?: string;
  user_id?: string;
  email?: string;
  message: string;
  auth_url?: string;
}

export interface ReplayState {
  is_active: boolean;
  is_playing: boolean;
  instrument_id: string;
  speed: number;
  current_index: number;
  total_candles: number;
  current_date?: string;
  current_price: number;
  progress_pct: number;
}

export interface DirectionPrediction {
  direction: string;
  confidence: number;
  probabilities: Record<string, number>;
  top_features: Array<{ feature: string; importance: number; current_value: number }>;
}

export interface VolatilityPrediction {
  predicted_volatility_pct: number;
  volatility_regime: string;
  atr_forecast: number;
}

export interface SentimentPrediction {
  sentiment_score: number;
  sentiment_label: string;
  buying_pressure_pct: number;
}

export interface MLAnalysisResult {
  instrument: string;
  timestamp: string;
  current_price: number;
  direction: DirectionPrediction;
  volatility: VolatilityPrediction;
  sentiment: SentimentPrediction;
  model_metadata: Record<string, any>;
}

export interface CompellingLoopResponse {
  loop_id: string;
  instrument: string;
  timestamp: string;
  step1_market_data: {
    status: string;
    instrument: string;
    data_source: string;
    is_synthetic: boolean;
    timestamp: string;
    current_price: number;
    change_pct: number;
    total_bars_available: number;
    indicators: Record<string, any>;
  };
  step2_ml_analysis: MLAnalysisResult;
  step3_hindsight_recall: {
    status: string;
    hindsight_connected: boolean;
    query_used: string;
    recalled_items_count: number;
    recalled_lessons: string[];
  };
  step4_groq_explanation: TradingHypothesis;
  step5_paper_trading_result: {
    status: string;
    order_id: string;
    side: string;
    quantity: number;
    entry_price: number;
    exit_price: number;
    gross_return_pct: number;
    net_realized_pnl: number;
    fees_and_slippage: number;
    verdict: string;
    portfolio_equity: number;
  };
  step6_hindsight_lesson_reply: {
    status: string;
    learned_lesson: string;
    hindsight_reply: string;
    memory_bank: string;
    timestamp: string;
  };
  summary_verdict: string;
  execution_time_seconds: number;
}

export interface SystemHealth {
  status: 'operational' | 'degraded';
  backend: {
    status: string;
    version: string;
  };
  groq: {
    connected: boolean;
    model?: string;
    is_model_available?: boolean;
    error?: string;
  };
  hindsight: {
    connected: boolean;
    bank_id: string;
    status_message: string;
    service_url: string;
  };
  upstox?: UpstoxStatus;
  replay?: ReplayState;
  market_data: {
    available: boolean;
    total_instruments: number;
    historical_instruments_count: number;
    synthetic_fallback_count: number;
    user_uploads_count: number;
  };
}

export interface PaperOrder {
  order_id: string;
  instrument: string;
  side: 'BUY' | 'SELL';
  order_type?: 'MARKET' | 'LIMIT';
  quantity: number;
  entry_price: number;
  limit_price?: number;
  current_price: number;
  stop_loss: number;
  target: number;
  status: 'OPEN' | 'FILLED' | 'CLOSED' | 'STOPPED_OUT' | 'TARGET_HIT' | 'CANCELLED';
  realized_pnl: number;
  unrealized_pnl: number;
  fee_incurred: number;
  slippage_incurred: number;
  created_at: string;
  closed_at?: string;
  notes?: string;
}

export interface PortfolioState {
  initial_capital: number;
  available_cash: number;
  total_equity: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_fees_paid: number;
  total_trades_count: number;
  winning_trades_count: number;
  losing_trades_count: number;
  win_rate: number;
  max_drawdown_pct?: number;
  total_return_pct: number;
  open_positions: PaperOrder[];
  closed_positions: PaperOrder[];
}

export interface AgentExperimentResult {
  agent_id: string;
  agent_name: string;
  has_memory: boolean;
  market_direction: string;
  hypothesis_summary: string;
  confidence: number;
  entry_price: number;
  stop_loss: number;
  target: number;
  supporting_factors: string[];
  recalled_lessons_used: string[];
  trade_outcome?: string;
  realized_pnl_pct?: number;
  was_direction_correct?: boolean;
  repeated_known_mistake: boolean;
}

export interface ScenarioEvaluation {
  scenario_id: string;
  instrument: string;
  decision_date: string;
  evaluation_date: string;
  decision_close_price: number;
  future_close_price: number;
  actual_return_pct: number;
  actual_market_trend: string;
  agent_a_no_memory: AgentExperimentResult;
  agent_b_with_memory: AgentExperimentResult;
}

export interface ExperimentReport {
  total_scenarios_evaluated: number;
  agent_a_metrics: {
    directional_accuracy_pct: number;
    win_rate_pct: number;
    total_return_pct: number;
    repeated_mistakes_count: number;
    average_confidence: number;
  };
  agent_b_metrics: {
    directional_accuracy_pct: number;
    win_rate_pct: number;
    total_return_pct: number;
    repeated_mistakes_count: number;
    average_confidence: number;
  };
  scenarios: ScenarioEvaluation[];
  summary_analysis: string;
  disclaimer: string;
}
