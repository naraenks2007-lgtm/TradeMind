import {
  InstrumentMetadata,
  MarketSnapshot,
  TradingHypothesis,
  SystemHealth,
  PortfolioState,
  PaperOrder,
  ExperimentReport,
  UpstoxStatus,
  ReplayState,
  MarketChatResponse
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

  // Upstox OAuth & Market Data
  getUpstoxStatus: async (): Promise<UpstoxStatus> => {
    const res = await fetch(`${API_BASE}/upstox/status`);
    if (!res.ok) throw new Error('Failed fetching Upstox status');
    return res.json();
  },

  getUpstoxAuthUrl: async (): Promise<{ auth_url: string }> => {
    const res = await fetch(`${API_BASE}/upstox/auth-url`);
    if (!res.ok) throw new Error('Failed fetching Upstox auth URL');
    return res.json();
  },

  disconnectUpstox: async (): Promise<{ status: string; message: string }> => {
    const res = await fetch(`${API_BASE}/upstox/disconnect`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed disconnecting Upstox');
    return res.json();
  },

  setManualUpstoxToken: async (access_token: string): Promise<UpstoxStatus> => {
    const res = await fetch(`${API_BASE}/upstox/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token })
    });
    if (!res.ok) throw new Error('Failed updating Upstox token');
    return res.json();
  },

  // Historical Replay
  startReplay: async (instrument: string = 'NIFTY_50', startDate?: string): Promise<ReplayState> => {
    const res = await fetch(`${API_BASE}/replay/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instrument, start_date: startDate })
    });
    if (!res.ok) throw new Error('Failed starting replay mode');
    return res.json();
  },

  stopReplay: async (): Promise<{ is_active: boolean; status: string }> => {
    const res = await fetch(`${API_BASE}/replay/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed stopping replay mode');
    return res.json();
  },

  stepReplay: async (steps: number = 1): Promise<ReplayState> => {
    const res = await fetch(`${API_BASE}/replay/step`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps })
    });
    if (!res.ok) throw new Error('Failed advancing replay');
    return res.json();
  },

  setReplaySpeed: async (speed: number): Promise<{ speed: number }> => {
    const res = await fetch(`${API_BASE}/replay/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed })
    });
    if (!res.ok) throw new Error('Failed setting replay speed');
    return res.json();
  },

  getReplayState: async (): Promise<ReplayState> => {
    const res = await fetch(`${API_BASE}/replay/state`);
    if (!res.ok) throw new Error('Failed fetching replay state');
    return res.json();
  },

  getReplaySnapshot: async (limit: number = 180): Promise<MarketSnapshot> => {
    const res = await fetch(`${API_BASE}/replay/snapshot?limit=${limit}`);
    if (!res.ok) throw new Error('Failed fetching replay snapshot');
    return res.json();
  },

  // Groq AI Hypothesis & Chat
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

  chatWithGroq: async (
    instrumentId: string,
    message: string,
    includeMemory: boolean = true
  ): Promise<MarketChatResponse> => {
    const res = await fetch(`${API_BASE}/hypothesis/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instrument_id: instrumentId,
        message,
        include_memory: includeMemory
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Chat query failed');
    }
    return res.json();
  },

  // Persistent conversations (browser-session scoped until account auth is added)
  getChatSessionId: (): string => {
    const key = 'trademind.chat.session.v1';
    let id = localStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID().replace(/-/g, '');
      localStorage.setItem(key, id);
    }
    return id;
  },

  chatSessionHeaders: (): Record<string, string> => ({
    'X-TradeMind-Session': api.getChatSessionId()
  }),

  listConversations: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/conversations`, { headers: api.chatSessionHeaders() });
    if (!res.ok) throw new Error('Failed loading conversation history');
    return res.json();
  },

  createConversation: async (instrument: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { ...api.chatSessionHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ instrument })
    });
    if (!res.ok) throw new Error('Failed creating conversation');
    return res.json();
  },

  getConversation: async (id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/conversations/${id}`, { headers: api.chatSessionHeaders() });
    if (!res.ok) throw new Error('Failed loading conversation');
    return res.json();
  },

  sendConversationMessage: async (id: string, instrument: string, message: string, includeMemory = true): Promise<any> => {
    const res = await fetch(`${API_BASE}/conversations/${id}/messages`, {
      method: 'POST',
      headers: { ...api.chatSessionHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ instrument_id: instrument, message, include_memory: includeMemory })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Chat query failed');
    }
    return res.json();
  },

  deleteConversation: async (id: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
      headers: api.chatSessionHeaders()
    });
    if (!res.ok) throw new Error('Failed deleting conversation');
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
    order_type?: 'MARKET' | 'LIMIT';
    quantity: number;
    limit_price?: number;
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

  // Compelling Loop Workflow
  runCompellingLoop: async (instrument: string = "NIFTY_50"): Promise<any> => {
    const res = await fetch(`${API_BASE}/loop/run?instrument=${instrument}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Loop execution failed');
    }
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
