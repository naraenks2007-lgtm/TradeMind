import React, { useState } from 'react';
import { api } from '../services/api';
import { InstrumentMetadata } from '../types';
import { X, Upload, CheckCircle2, AlertTriangle, FileSpreadsheet } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newInst: InstrumentMetadata) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const result = await api.uploadCsv(file);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-[#121824] border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              Upload Custom OHLCV CSV
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Requirements description */}
        <div className="text-xs text-slate-400 space-y-2 leading-relaxed">
          <p>
            Upload any Indian or global market dataset in CSV format. The backend data loader validates column headers, deduplicates timestamps, and checks price consistency.
          </p>
          <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300">
            <strong>Required Columns:</strong> Date, Open, High, Low, Close, Volume
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-2">
            <Upload className="w-8 h-8 text-slate-500" />
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setFile(e.target.files[0]);
                }
              }}
              className="text-xs text-slate-400 file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"
            />
            {file && (
              <span className="text-xs text-emerald-400 font-mono font-medium">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </span>
            )}
          </div>

          {error && (
            <div className="bg-rose-950/40 border border-rose-800/40 p-2.5 rounded-xl text-xs text-rose-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs text-slate-300 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || uploading}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-600/30 transition disabled:opacity-50"
            >
              {uploading ? 'Validating & Ingesting...' : 'Upload & Process'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
