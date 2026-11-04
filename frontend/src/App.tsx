import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import { 
  InstrumentMetadata, 
  MarketSnapshot, 
  TradingHypothesis, 
  SystemHealth 
} from './types';
import { Header } from './components/Header';
import { MarketChart } from './components/MarketChart';
import { IndicatorControls } from './components/IndicatorControls';
import { HypothesisCard } from './components/HypothesisCard';
import { ComparisonLab } from './components/ComparisonLab';
import { PaperTradingPanel } from './components/PaperTradingPanel';
import { MemoryExplorer } from './components/MemoryExplorer';
import { CompellingLoop } from './components/CompellingLoop';
import { UploadModal } from './components/UploadModal';
import { 
  TrendingUp, 
  Sparkles, 
  Clock, 
  ShieldCheck, 
  Database,
  ChevronRight,
  Flame
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'loop' | 'terminal' | 'experiment' | 'portfolio' | 'memory'>('loop');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [instruments, setInstruments] = useState<InstrumentMetadata[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('NIFTY_50');
  const [snapshot, setSnapshot] = useState<MarketSnapshot | null>(null);
  const [hypothesis, setHypothesis] = useState<TradingHypothesis | null>(null);
  const [loadingMarket, setLoadingMarket] = useState(false);
  const [loadingHypothesis, setLoadingHypothesis] = useState(false);
  const [includeMemory, setIncludeMemory] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Load initial health and instruments
  const loadInitialData = async () => {
    try {
      const [healthData, instData] = await Promise.all([
        api.getHealth(),
        api.getInstruments()
      ]);
      setHealth(healthData);
      setInstruments(instData);
      if (instData.length > 0 && !selectedSymbol) {
        setSelectedSymbol(instData[0].id);
      }
    } catch (err) {
      console.error('Initial load error:', err);
    }
  };

  // Load market data for selected symbol
  const loadMarketData = async (symbol: string) => {
    setLoadingMarket(true);
    setHypothesis(null); // Clear previous hypothesis on symbol change
    try {
      const data = await api.getMarketData(symbol);
      setSnapshot(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMarket(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      loadMarketData(selectedSymbol);
    }
  }, [selectedSymbol]);

  // Generate Hypothesis via Groq
  const handleGenerateHypothesis = async () => {
    if (!selectedSymbol) return;
    setLoadingHypothesis(true);
    try {
      const hypo = await api.generateHypothesis(selectedSymbol, includeMemory);
      setHypothesis(hypo);
    } catch (err: any) {
      alert(`Hypothesis Generation Error: ${err.message}`);
    } finally {
      setLoadingHypothesis(false);
    }
  };

  // Execute Paper Trade directly from Hypothesis
  const handleExecutePaperTrade = async (hypo: TradingHypothesis) => {
    try {
      const side = hypo.market_direction === 'BEARISH' ? 'SELL' : 'BUY';
      const order = await api.placeOrder({
        instrument: hypo.instrument,
        side: side,
        quantity: 10,
        stop_loss: hypo.stop_loss_assumption,
        target: hypo.target_assumption,
        notes: `Executed from AI Hypothesis (Confidence: ${(hypo.confidence * 100).toFixed(0)}%)`
      });
      setNotification(`Paper order ${order.order_id} filled @ ₹${order.entry_price}`);
      setTimeout(() => setNotification(null), 5000);
      setActiveTab('portfolio');
    } catch (err: any) {
      alert(`Order Execution Error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-100 flex flex-col font-sans">
      
      {/* Header */}
      <Header
        health={health}
        onOpenUpload={() => setUploadModalOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRefresh={() => {
          loadInitialData();
          if (selectedSymbol) loadMarketData(selectedSymbol);
        }}
        loading={loadingMarket}
      />

      {/* Floating Notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-emerald-500 text-white font-mono text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-2 animate-bounce">
          <ShieldCheck className="w-4 h-4" />
          <span>{notification}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 space-y-5">
        
        {/* Compelling AI Loop Tab */}
        {activeTab === 'loop' && (
          <div className="flex flex-col space-y-4">
            {/* Instrument Bar */}
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-xs font-mono text-slate-500 uppercase tracking-wider shrink-0 mr-1">
                Select Instrument:
              </span>
              {instruments.map((inst) => {
                const isSelected = inst.id === selectedSymbol;
                return (
                  <button
                    key={inst.id}
                    onClick={() => setSelectedSymbol(inst.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-mono font-medium transition flex items-center space-x-2 shrink-0 ${
                      isSelected
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                        : 'bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span>{inst.symbol}</span>
                    <span className="text-[10px] opacity-75">₹{inst.latest_close.toFixed(1)}</span>
                    {inst.is_synthetic && (
                      <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300">DEMO</span>
                    )}
                  </button>
                );
              })}
            </div>

            <CompellingLoop currentSymbol={selectedSymbol} />
          </div>
        )}
        
        {/* Terminal View */}
        {activeTab === 'terminal' && (
          <div className="flex flex-col space-y-4">
            
            {/* Instrument Bar */}
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-xs font-mono text-slate-500 uppercase tracking-wider shrink-0 mr-1">
                Supported Instruments:
              </span>
              {instruments.map((inst) => {
                const isSelected = inst.id === selectedSymbol;
                return (
                  <button
                    key={inst.id}
                    onClick={() => setSelectedSymbol(inst.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-mono font-medium transition flex items-center space-x-2 shrink-0 ${
                      isSelected
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                        : 'bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span>{inst.symbol}</span>
                    <span className="text-[10px] opacity-75">₹{inst.latest_close.toFixed(1)}</span>
                    {inst.is_synthetic && (
                      <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300">DEMO</span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Layout: Chart & Indicators on Left, Hypothesis on Right */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              
              {/* Left Column: Candlestick Chart & Indicator Controls */}
              <div className="lg:col-span-7 xl:col-span-8 flex flex-col space-y-4">
                <MarketChart 
                  snapshot={snapshot} 
                  loading={loadingMarket} 
                />

                <IndicatorControls 
                  indicators={snapshot?.indicators} 
                  currentPrice={snapshot?.current_price || 0} 
                />
              </div>

              {/* Right Column: AI Hypothesis Generator Card */}
              <div className="lg:col-span-5 xl:col-span-4">
                <HypothesisCard
                  hypothesis={hypothesis}
                  loading={loadingHypothesis}
                  onGenerate={handleGenerateHypothesis}
                  onExecutePaperTrade={handleExecutePaperTrade}
                  includeMemory={includeMemory}
                  setIncludeMemory={setIncludeMemory}
                />
              </div>

            </div>

          </div>
        )}

        {/* Experiment Tab */}
        {activeTab === 'experiment' && (
          <ComparisonLab currentSymbol={selectedSymbol} />
        )}

        {/* Portfolio Tab */}
        {activeTab === 'portfolio' && (
          <PaperTradingPanel 
            currentSymbol={selectedSymbol} 
            currentPrice={snapshot?.current_price || 0} 
          />
        )}

        {/* Memory Tab */}
        {activeTab === 'memory' && (
          <MemoryExplorer />
        )}

      </main>

      {/* Upload CSV Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={(newInst) => {
          setInstruments((prev) => [newInst, ...prev]);
          setSelectedSymbol(newInst.id);
          setNotification(`Uploaded & indexed ${newInst.name}!`);
          setTimeout(() => setNotification(null), 5000);
        }}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0F141F] py-4 px-6 text-xs text-slate-500 text-center font-mono">
        TradeMind AI • Hackathon Edition • Developed with Band Desktop Multi-Agent Collaboration • Real Historical Indian Market Data
      </footer>

    </div>
  );
};
