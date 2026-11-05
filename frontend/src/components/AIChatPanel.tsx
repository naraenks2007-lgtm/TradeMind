import React, { useEffect, useRef, useState } from 'react';
import {
  Send, Sparkles, Brain, Plus, MessageSquare, Trash2, PanelLeftClose,
  PanelLeftOpen, Activity, ArrowUpRight, Command, Loader2, Paperclip, X, FileText
} from 'lucide-react';
import { api } from '../services/api';

interface AIChatPanelProps {
  currentSymbol: string;
  currentPrice: number;
  dataSource: string;
  isLightTheme: boolean;
}

interface Conversation {
  id: string;
  title: string;
  instrument: string;
  updated_at: string;
  message_count?: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  instrument?: string;
  current_price?: number;
  data_source?: string;
  data_timestamp?: string;
  recalled_memories?: string[];
}

const formatTime = (value: string) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const formatDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const today = new Date();
  return date.toDateString() === today.toDateString()
    ? 'Today'
    : date.toLocaleDateString([], { month: 'short', day: 'numeric' });
};

export const AIChatPanel: React.FC<AIChatPanelProps> = ({
  currentSymbol,
  currentPrice,
  dataSource,
  isLightTheme
}) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    `Analyse ${currentSymbol}`,
    'Identify the current market trend',
    'Find important support and resistance levels',
    'Analyse RSI, MACD and volume',
    'Suggest a possible paper-trading setup'
  ];

  const refreshHistory = async () => {
    const rows = await api.listConversations();
    setConversations(rows);
    return rows as Conversation[];
  };

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const rows = await api.listConversations();
        if (!alive) return;
        setConversations(rows);
        if (rows.length) {
          const latest = await api.getConversation(rows[0].id);
          if (!alive) return;
          setActiveId(latest.id);
          setMessages(latest.messages || []);
        }
      } catch (err: any) {
        if (alive) setError(err.message || 'Could not load chat history.');
      } finally {
        if (alive) setHistoryLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  const startNewConversation = async () => {
    if (loading) return;
    setError('');
    try {
      const conversation = await api.createConversation(currentSymbol);
      setConversations((prev) => [conversation, ...prev]);
      setActiveId(conversation.id);
      setMessages([]);
      setInput('');
    } catch (err: any) {
      setError(err.message || 'Could not create a new conversation.');
    }
  };

  const openConversation = async (id: string) => {
    if (loading || id === activeId) return;
    setError('');
    setActiveId(id);
    setMessages([]);
    try {
      const conversation = await api.getConversation(id);
      setMessages(conversation.messages || []);
    } catch (err: any) {
      setError(err.message || 'Could not open this conversation.');
    }
  };

  const removeConversation = async (id: string) => {
    if (loading) return;
    try {
      await api.deleteConversation(id);
      const remaining = conversations.filter((item) => item.id !== id);
      setConversations(remaining);
      if (activeId === id) {
        setActiveId(null);
        setMessages([]);
        if (remaining.length) {
          const next = await api.getConversation(remaining[0].id);
          setActiveId(next.id);
          setMessages(next.messages || []);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Could not delete conversation.');
    }
  };

  const ensureConversation = async () => {
    if (activeId) return activeId;
    const created = await api.createConversation(currentSymbol);
    setConversations((prev) => [created, ...prev]);
    setActiveId(created.id);
    return created.id as string;
  };

  const handleAnalyzeFile = async (promptText: string) => {
    if (!selectedFile || loading) return;
    setError('');
    setLoading(true);
    try {
      const conversationId = await ensureConversation();
      const result = await api.analyseChatFile(conversationId, selectedFile, promptText || 'Analyse this file and explain the key findings.');
      setMessages(result.messages || []);
      setSelectedFile(null);
      setInput('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      await refreshHistory();
    } catch (err: any) {
      setError(err.message || 'File analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText ?? input).trim();
    if (selectedFile) {
      await handleAnalyzeFile(textToSend);
      return;
    }
    if (!textToSend || loading) return;
    setError('');
    setInput('');
    setLoading(true);
    try {
      const conversationId = await ensureConversation();
      const result = await api.sendConversationMessage(conversationId, currentSymbol, textToSend, true);
      setMessages(result.messages || []);
      await refreshHistory();
    } catch (err: any) {
      setError(err.message || 'Unable to send message. Please try again.');
      setInput(textToSend);
    } finally {
      setLoading(false);
    }
  };

  const activeConversation = conversations.find((item) => item.id === activeId);

  return (
    <div className={`tm-chat-shell ${isLightTheme ? "tm-light-theme" : ""} flex h-[min(780px,calc(100vh-190px))] min-h-[560px] overflow-hidden rounded-3xl border border-slate-800/90 bg-[#080d18] shadow-2xl shadow-black/30`}>
      {sidebarOpen && (
        <aside className="tm-chat-sidebar flex w-[270px] shrink-0 flex-col border-r border-slate-800/80 bg-[#0b1120]">
          <div className="flex items-center justify-between px-4 py-5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200">
                <Brain size={18} />
              </div>
              <div>
                <p className="text-sm font-bold tracking-wide text-white">TradeMind</p>
                <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">AI workspace</p>
              </div>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-800 hover:text-white" title="Collapse history">
              <PanelLeftClose size={16} />
            </button>
          </div>
          <button onClick={startNewConversation} className="mx-3 mb-5 flex items-center justify-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-3 py-3 text-xs font-semibold text-cyan-100 transition hover:border-cyan-200/50 hover:bg-cyan-300/15">
            <Plus size={15} /> New conversation <span className="ml-auto text-[10px] text-cyan-200/50">⌘ K</span>
          </button>
          <div className="mb-2 flex items-center justify-between px-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">Recent history</span>
            <span className="text-[10px] text-slate-600">{conversations.length}</span>
          </div>
          <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-3">
            {historyLoading ? (
              <div className="flex items-center gap-2 px-3 py-5 text-xs text-slate-500"><Loader2 size={14} className="animate-spin" /> Loading history…</div>
            ) : conversations.length === 0 ? (
              <div className="px-3 py-8 text-center text-xs leading-5 text-slate-600">Your conversations will appear here. Start a new chat to begin.</div>
            ) : conversations.map((conversation) => (
              <div key={conversation.id} className={`group flex items-center gap-1 rounded-xl px-2 py-1.5 transition ${activeId === conversation.id ? 'bg-slate-800/90 ring-1 ring-cyan-300/15' : 'hover:bg-slate-800/50'}`}>
                <button onClick={() => openConversation(conversation.id)} className="min-w-0 flex-1 py-1 text-left">
                  <div className="flex items-center gap-2">
                    <MessageSquare size={13} className={activeId === conversation.id ? 'shrink-0 text-cyan-200' : 'shrink-0 text-slate-500'} />
                    <span className={`truncate text-xs ${activeId === conversation.id ? 'text-white' : 'text-slate-300'}`}>{conversation.title}</span>
                  </div>
                  <div className="ml-5 mt-1 flex gap-2 text-[10px] text-slate-600">
                    <span>{conversation.instrument}</span><span>·</span><span>{formatDate(conversation.updated_at)}</span>
                  </div>
                </button>
                <button onClick={() => removeConversation(conversation.id)} title="Delete conversation" className="rounded-md p-1.5 text-slate-600 opacity-0 transition hover:bg-rose-500/10 hover:text-rose-300 group-hover:opacity-100">
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-800/80 px-4 py-3">
            <div className="flex items-center gap-2 text-[10px] text-slate-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_#34d399]" /> Local conversation sync enabled</div>
            <p className="mt-1 text-[9px] leading-4 text-slate-600">History is saved on this TradeMind server and scoped to this browser session.</p>
          </div>
        </aside>
      )}

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800/80 bg-[#0c1322]/90 px-5 py-3.5">
          <div className="flex min-w-0 items-center gap-3">
            {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" title="Show history"><PanelLeftOpen size={17} /></button>}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-sm font-semibold text-white">{activeConversation?.title || 'New conversation'}</h2>
                <span className="rounded-full border border-purple-400/20 bg-purple-400/10 px-2 py-0.5 text-[9px] font-medium tracking-wide text-purple-200">HINDSIGHT ON</span>
              </div>
              <p className="mt-0.5 truncate text-[10px] text-slate-500">Groq market strategist <span className="px-1">·</span> {currentSymbol} <span className="px-1">·</span> {dataSource}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-full border border-slate-700/70 bg-slate-900/80 px-3 py-1.5 sm:flex">
              <Activity size={12} className="text-emerald-400" />
              <span className="text-[10px] text-slate-400">Market context active</span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
          {messages.length === 0 && !historyLoading ? (
            <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center text-center">
              <div className="tm-orb-scene mb-7">
                <div className="tm-orb-ring tm-orb-ring-one" />
                <div className="tm-orb-ring tm-orb-ring-two" />
                <div className="tm-orb-core"><div className="tm-orb-shine" /><Sparkles size={35} strokeWidth={1.3} /></div>
                <div className="tm-orb-particle tm-particle-one" /><div className="tm-orb-particle tm-particle-two" /><div className="tm-orb-particle tm-particle-three" />
              </div>
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.32em] text-cyan-200/70">Your market intelligence copilot</p>
              <h3 className="max-w-lg text-2xl font-semibold tracking-tight text-white sm:text-3xl">Think deeper about the market.</h3>
              <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">Ask TradeMind to interpret market structure, explain indicators, and review trade decisions. Tell it what worked, what failed, or how you prefer to trade; it can retain those lessons in Hindsight and apply them in later analysis.</p>
              <div className="mt-8 grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
                {quickPrompts.slice(0, 4).map((prompt) => (
                  <button key={prompt} onClick={() => handleSendMessage(prompt)} className="group flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-left text-xs text-slate-300 transition hover:border-cyan-300/30 hover:bg-cyan-300/5 hover:text-white">
                    <span>{prompt}</span><ArrowUpRight size={14} className="text-slate-600 transition group-hover:text-cyan-200" />
                  </button>
                ))}
              </div>
              <p className="mt-6 text-[10px] text-slate-600">Current reference · {currentSymbol} · ₹{currentPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-7">
              {messages.map((message) => (
                <div key={message.id} className={`flex gap-3 sm:gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${message.role === 'assistant' ? 'border border-cyan-300/20 bg-cyan-300/10 text-cyan-100' : 'bg-slate-700 text-slate-200'}`}>
                    {message.role === 'assistant' ? <Sparkles size={15} /> : <span className="text-[10px] font-bold">YOU</span>}
                  </div>
                  <div className={`min-w-0 max-w-[88%] ${message.role === 'user' ? 'text-right' : ''}`}>
                    <div className="mb-1.5 flex items-center gap-2 text-[10px] text-slate-500">
                      <span className="font-semibold text-slate-300">{message.role === 'assistant' ? 'TradeMind' : 'You'}</span>
                      <span>{formatTime(message.created_at)}</span>
                    </div>
                    <div className={`whitespace-pre-wrap break-words rounded-2xl px-4 py-3 text-[13px] leading-6 ${message.role === 'user' ? 'rounded-tr-sm border border-blue-400/20 bg-blue-500/15 text-blue-50' : 'rounded-tl-sm border border-slate-800 bg-slate-900/75 text-slate-200'}`}>
                      {message.content}
                    </div>
                    {message.role === 'assistant' && message.recalled_memories && message.recalled_memories.length > 0 && (
                      <div className="mt-2 rounded-xl border border-purple-400/15 bg-purple-400/5 p-3">
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-purple-200"><Brain size={12} /> Recalled from Hindsight</div>
                        {message.recalled_memories.map((memory, index) => <p key={index} className="mb-1 text-xs leading-5 text-slate-400">• {memory}</p>)}
                      </div>
                    )}
                    {message.role === 'assistant' && message.data_source && message.data_source !== 'TradeMind AI' && (
                      <p className="mt-1.5 text-[9px] text-slate-600">{message.instrument} · ₹{(message.current_price || 0).toLocaleString('en-IN')} · {message.data_source}</p>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-100"><Sparkles size={15} className="animate-pulse" /></div>
                  <div className="rounded-2xl rounded-tl-sm border border-slate-800 bg-slate-900/70 px-4 py-3 text-xs text-slate-400">
                    <span className="tm-thinking-dots">Thinking with market context and Hindsight memory</span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {error && <div className="mx-5 mb-2 rounded-lg border border-rose-400/20 bg-rose-400/5 px-3 py-2 text-xs text-rose-200">{error}</div>}
        <div className="border-t border-slate-800/80 bg-[#0b1120] px-4 py-4 sm:px-7">
          <div className="mx-auto max-w-3xl">
            {messages.length > 0 && messages.length < 3 && (
              <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
                {quickPrompts.slice(1, 4).map((prompt) => <button key={prompt} onClick={() => handleSendMessage(prompt)} disabled={loading} className="shrink-0 rounded-full border border-slate-800 px-3 py-1.5 text-[10px] text-slate-400 transition hover:border-cyan-300/30 hover:text-cyan-100">{prompt}</button>)}
              </div>
            )}
            {selectedFile && (
              <div className="mb-2 flex items-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-300/5 px-3 py-2 text-xs text-cyan-100">
                <FileText size={14} />
                <span className="min-w-0 flex-1 truncate">{selectedFile.name}</span>
                <span className="text-[10px] text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                <button type="button" onClick={() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }} className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white" title="Remove file"><X size={14} /></button>
              </div>
            )}
            <form onSubmit={(event) => { event.preventDefault(); handleSendMessage(); }} className="flex items-end gap-2 rounded-2xl border border-slate-700/80 bg-slate-900/90 p-2 shadow-[0_12px_50px_rgba(0,0,0,0.25)] transition focus-within:border-cyan-300/40">
              <input ref={fileInputRef} type="file" accept=".pdf,.csv,.png,.jpg,.jpeg,.webp,application/pdf,text/csv,image/png,image/jpeg,image/webp" className="hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) setSelectedFile(file); }} />
              <button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading} className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-slate-400 transition hover:bg-slate-800 hover:text-cyan-200 disabled:opacity-40" title="Attach PDF, image, or CSV">
                <Paperclip size={17} />
              </button>
              <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); } }} placeholder={selectedFile ? 'Add an instruction for the file analysis (optional)…' : `Ask anything about ${currentSymbol}…`} rows={1} disabled={loading} className="max-h-32 min-h-[42px] flex-1 resize-y bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-slate-600 disabled:opacity-50" />
              <button type="submit" disabled={loading || (!input.trim() && !selectedFile)} className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-300 text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-30" title={selectedFile ? 'Analyse file' : 'Send message'}>
                {loading ? <Loader2 size={17} className="animate-spin" /> : <Send size={16} />}
              </button>
            </form>
            <div className="mt-2 flex items-center justify-between px-1 text-[9px] text-slate-600"><span>TradeMind can make mistakes. Verify market decisions independently.</span><span className="hidden sm:inline"><Command size={9} className="mr-1 inline" /> Enter to send · Shift + Enter for new line</span></div>
          </div>
        </div>
      </section>
    </div>
  );
};
