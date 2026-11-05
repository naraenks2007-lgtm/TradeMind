import React, { useState } from 'react';
import { 
  Send, 
  Sparkles, 
  Brain, 
  TrendingUp, 
  ShieldAlert, 
  HelpCircle,
  Clock,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { MarketChatResponse } from '../types';

interface AIChatPanelProps {
  currentSymbol: string;
  currentPrice: number;
  dataSource: string;
  onSelectPrompt?: (prompt: string) => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  recalledMemories?: string[];
  dataContext?: {
    instrument: string;
    price: number;
    dataSource: string;
    dataTimestamp: string;
  };
}

export const AIChatPanel: React.FC<AIChatPanelProps> = ({
  currentSymbol,
  currentPrice,
  dataSource
}) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: 'ai',
      text: `Hello! I am TradeMind AI powered by Groq and Hindsight persistent memory. I have loaded live/historical context for **${currentSymbol}** (LTP: ₹${currentPrice.toFixed(2)}). Ask me any market question or select a quick query below!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const quickPrompts = [
    `Analyse ${currentSymbol}`,
    'Identify the current market trend',
    'Find important support and resistance levels',
    'Analyse RSI, MACD and volume',
    'Suggest a possible paper-trading setup',
    'Explain why a previous paper trade failed'
  ];

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res: MarketChatResponse = await api.chatWithGroq(currentSymbol, textToSend, true);
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        recalledMemories: res.recalled_memories,
        dataContext: {
          instrument: res.instrument,
          price: res.current_price,
          dataSource: res.data_source,
          dataTimestamp: res.data_timestamp
        }
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: `⚠️ **Analysis Error:** ${err.message || 'Unable to connect to Groq AI service.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0F141F] border border-slate-800 rounded-2xl flex flex-col h-[650px] shadow-xl overflow-hidden">
      
      {/* Panel Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#141A28] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Groq AI Market Strategist
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
                Hindsight Memory Linked
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Active Context: <span className="font-semibold text-slate-200">{currentSymbol}</span> • Source: {dataSource}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Prompt Pills */}
      <div className="px-4 py-2 border-b border-slate-800/80 bg-slate-900/60 overflow-x-auto flex items-center gap-2 scrollbar-none">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider shrink-0">
          Quick Prompts:
        </span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(p)}
            disabled={loading}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 shrink-0 transition"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/20'
                  : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none'
              }`}
            >
              {/* Message Header */}
              <div className="flex items-center space-x-2 mb-1.5 opacity-75 text-[10px] font-mono">
                {msg.sender === 'ai' ? (
                  <>
                    <Brain className="w-3 h-3 text-purple-400" />
                    <span className="text-purple-300 font-semibold">TradeMind Strategist</span>
                  </>
                ) : (
                  <span>You</span>
                )}
                <span>• {msg.timestamp}</span>
              </div>

              {/* Message Body */}
              <div className="prose prose-invert prose-xs max-w-none whitespace-pre-line">
                {msg.text}
              </div>

              {/* Recalled Hindsight Memories Badge */}
              {msg.recalledMemories && msg.recalledMemories.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-purple-500/20 bg-purple-950/20 -mx-2 px-3 py-2 rounded-lg">
                  <div className="flex items-center space-x-1.5 text-[10px] font-mono text-purple-300 mb-1">
                    <Brain className="w-3 h-3 text-purple-400" />
                    <span>Hindsight Recalled Past Lessons:</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-slate-300">
                    {msg.recalledMemories.map((mem, i) => (
                      <li key={i}>{mem}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Context Footer */}
              {msg.dataContext && (
                <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between border-t border-slate-800 pt-1.5">
                  <span>Price: ₹{msg.dataContext.price.toFixed(2)}</span>
                  <span>Source: {msg.dataContext.dataSource}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded-xl px-4 py-2.5 w-fit">
            <Sparkles className="w-3.5 h-3.5 animate-spin" />
            <span>Consulting Groq LLM & recalling Hindsight trade history...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="p-3 bg-[#141A28] border-t border-slate-800 flex items-center space-x-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask about ${currentSymbol} trend, support/resistance, RSI, or past trades...`}
          disabled={loading}
          className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white transition shadow-md shadow-blue-600/30"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
};
