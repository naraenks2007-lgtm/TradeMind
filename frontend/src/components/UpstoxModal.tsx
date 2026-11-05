import React, { useState } from 'react';
import { X, ExternalLink, Key, CheckCircle, AlertTriangle, Shield, RefreshCw } from 'lucide-react';
import { UpstoxStatus } from '../types';
import { api } from '../services/api';

interface UpstoxModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: UpstoxStatus | null;
  onStatusUpdated: () => void;
}

export const UpstoxModal: React.FC<UpstoxModalProps> = ({
  isOpen,
  onClose,
  status,
  onStatusUpdated
}) => {
  const [manualToken, setManualToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleOAuthConnect = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getUpstoxAuthUrl();
      if (res.auth_url) {
        // Open OAuth dialog in a popup window
        const width = 600;
        const height = 750;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;
        
        const popup = window.open(
          res.auth_url,
          'Upstox_OAuth',
          `width=${width},height=${height},top=${top},left=${left}`
        );

        // Listen for postMessage from callback HTML
        const messageListener = (event: MessageEvent) => {
          if (event.data?.type === 'UPSTOX_AUTH_SUCCESS') {
            window.removeEventListener('message', messageListener);
            onStatusUpdated();
            setLoading(false);
          }
        };
        window.addEventListener('message', messageListener);

        // Fallback polling if popup closes
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            window.removeEventListener('message', messageListener);
            onStatusUpdated();
            setLoading(false);
          }
        }, 1500);
      }
    } catch (err: any) {
      setError(err.message || 'Failed generating authorization link');
      setLoading(false);
    }
  };

  const handleManualTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualToken.trim()) return;
    try {
      setLoading(true);
      setError(null);
      await api.setManualUpstoxToken(manualToken.trim());
      setManualToken('');
      onStatusUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed saving access token');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      await api.disconnectUpstox();
      onStatusUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed disconnecting');
    } finally {
      setLoading(false);
    }
  };

  const isConnected = status?.authenticated;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0F141F] border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#141A28]">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center font-bold">
              U
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Upstox Market Data Feed</h2>
              <p className="text-xs text-slate-400">Official OAuth 2.0 & Live Quotes Integration</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          
          {/* Status Banner */}
          <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
            isConnected
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            {isConnected ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            )}
            <div className="text-xs">
              <p className="font-semibold text-sm">
                {isConnected ? 'Upstox Feed Connected (Authorized)' : 'Upstox Not Authorized'}
              </p>
              <p className="mt-1 text-slate-300">
                {status?.message || (isConnected ? `Authenticated as ${status?.user_name}` : 'Click Connect Upstox to login and authorize live data.')}
              </p>
            </div>
          </div>

          {/* Safety Rule Note */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3 text-xs text-slate-400 flex items-start space-x-2">
            <Shield className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <span>
              <b>Safety Guarantee:</b> Upstox is used exclusively for authorized market quotes and streaming candles. Real orders are NEVER placed on your broker account. All trading is strictly simulated in TradeMind's paper engine.
            </span>
          </div>

          {/* OAuth Action */}
          <div>
            {isConnected ? (
              <div className="flex items-center justify-between bg-slate-900 p-3 rounded-xl border border-slate-800">
                <div>
                  <span className="text-xs text-slate-400">Account:</span>
                  <p className="text-sm font-semibold text-white">{status?.user_name || 'Authorized User'}</p>
                  <p className="text-[11px] text-slate-500">{status?.email || status?.user_id}</p>
                </div>
                <button
                  onClick={handleDisconnect}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 border border-red-500/30 text-xs font-semibold"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <button
                onClick={handleOAuthConnect}
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-purple-600/25 flex items-center justify-center space-x-2 transition"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <ExternalLink className="w-4 h-4" />
                )}
                <span>Connect Upstox via OAuth 2.0</span>
              </button>
            )}
          </div>

          {/* Manual Token Option */}
          <div className="pt-2 border-t border-slate-800">
            <details className="group">
              <summary className="text-xs text-slate-400 cursor-pointer hover:text-white flex items-center justify-between list-none">
                <span className="flex items-center space-x-1.5">
                  <Key className="w-3.5 h-3.5" />
                  <span>Manual Access Token Override</span>
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">Advanced</span>
              </summary>
              <form onSubmit={handleManualTokenSubmit} className="mt-3 space-y-2">
                <input
                  type="password"
                  placeholder="Paste Upstox Access Token (starts with ey...)"
                  value={manualToken}
                  onChange={(e) => setManualToken(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
                <button
                  type="submit"
                  disabled={loading || !manualToken.trim()}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-medium rounded-lg"
                >
                  Apply Manual Token
                </button>
              </form>
            </details>
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 p-2.5 rounded-lg border border-red-500/20">
              {error}
            </p>
          )}

        </div>

      </div>
    </div>
  );
};
