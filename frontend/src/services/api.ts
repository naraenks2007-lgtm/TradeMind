import {
  InstrumentMetadata,
  MarketSnapshot,
  TradingHypothesis,
  SystemHealth,
  PortfolioState,
  PaperOrder,
  ExperimentReport
} from '../types';

const API_BASE = '/api';

export const api = {
  // Health
  getHealth: async (): Promise<SystemHealth> => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed fetching health status');
    return res.json();
  },

  // Market Data
  getInstruments: async (): Promise<InstrumentMetadata[]> => {
    const res = await fetch(`${API_BASE}/market/instruments`);
    if (!res.ok) throw new Error('Failed fetching instruments');
    return res.json();
  },

  getMarketData: async (symbol: string): Promise<MarketSnapshot> => {
    const res = await fetch(`${API_BASE}/market/${symbol}`);
    if (!res.ok) throw new Error(`Failed fetching data for ${symbol}`);
    return res.json();
  },

  uploadCsv: async (file: File): Promise<InstrumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/market/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  // Hypothesis
  generateHypothesis: async (
    instrumentId: string,
    includeMemory: boolean = true,
    userNotes?: string
  ): Promise<TradingHypothesis> => {
    const res = await fetch(`${API_BASE}/hypothesis/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instrument_id: instrumentId,
        include_memory: includeMemory,
        user_context: userNotes
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Hypothesis generation failed');
    }
    return res.json();
  },

  // Paper Trading
  getPortfolio: async (): Promise<PortfolioState> => {
    const res = await fetch(`${API_BASE}/paper-trading/portfolio`);
    if (!res.ok) throw new Error('Failed fetching portfolio');
    return res.json();
  },

  placeOrder: async (order: {
    instrument: string;
    side: 'BUY' | 'SELL';
    quantity: number;
    stop_loss?: number;
    target?: number;
    notes?: string;
  }): Promise<PaperOrder> => {
    const res = await fetch(`${API_BASE}/paper-trading/order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Order execution failed');
    }
    return res.json();
  },

  closeOrder: async (orderId: string): Promise<PaperOrder> => {
    const res = await fetch(`${API_BASE}/paper-trading/order/${orderId}/close`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed closing order');
    return res.json();
  },

  resetPortfolio: async (): Promise<{ status: string; message: string }> => {
    const res = await fetch(`${API_BASE}/paper-trading/reset`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed resetting portfolio');
    return res.json();
  },

  // Experiment Comparison
  getComparison: async (instrument: string, scenarios: number = 6): Promise<ExperimentReport> => {
    const res = await fetch(`${API_BASE}/experiment/comparison?instrument=${instrument}&scenarios=${scenarios}`);
    if (!res.ok) throw new Error('Failed loading comparison experiment');
    return res.json();
  },

  // Memory
  getMemoryStatus: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/memory/status`);
    if (!res.ok) throw new Error('Failed fetching memory status');
    return res.json();
  },

  recallMemory: async (query: string, limit: number = 5): Promise<any> => {
    const res = await fetch(`${API_BASE}/memory/recall`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });
    if (!res.ok) throw new Error('Memory recall failed');
    return res.json();
  }
};
