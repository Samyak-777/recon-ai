import React from 'react';
import { 
  RefreshCw, 
  CheckCircle2, 
  Layers, 
  X
} from 'lucide-react';

export default function BatchRunModal({ isOpen, onClose, progress, batchSize = 150 }) {
  if (!isOpen) return null;

  const estimatedBatches = Math.max(1, Math.ceil(batchSize / 25));

  const steps = [
    { label: `Ingesting ${batchSize} Orders & ${estimatedBatches} Settlement Batches from Storage Engine`, done: progress >= 20 },
    { label: 'Executing Stage 1: Exact ID & Bank UTR Join Matching', done: progress >= 40 },
    { label: 'Executing Stage 2: Net-to-Gross Waterfall Unpacker', done: progress >= 60 },
    { label: 'Executing Stage 3: Deterministic Variance Classification', done: progress >= 80 },
    { label: 'Executing Stage 4: AI-Assisted Fuzzy Match Proposal', done: progress >= 100 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 max-w-lg w-full shadow-2xl">
        
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0c6cf2]">
              <Layers className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#0c2340]">4-Stage Batch Reconciliation</h3>
              <p className="text-xs text-slate-500">Processing {batchSize} payments across {estimatedBatches} settlement batches</p>
            </div>
          </div>
          
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="my-6">
          <div className="flex justify-between text-xs font-mono mb-2">
            <span className="text-slate-500">BATCH CLEARANCE</span>
            <span className="text-[#0c6cf2] font-bold">{progress}%</span>
          </div>
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div 
              className="h-full bg-gradient-to-r from-[#0c6cf2] via-[#0284c7] to-[#00b87c] transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step List */}
        <div className="space-y-3 font-sans">
          {steps.map((step, idx) => (
            <div 
              key={idx}
              className={`p-3 rounded-xl border flex items-center space-x-3 transition-all ${
                step.done 
                  ? 'bg-emerald-50 border-emerald-200 text-[#00b87c]' 
                  : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}
            >
              {step.done ? (
                <CheckCircle2 className="h-4 w-4 text-[#00b87c] shrink-0" />
              ) : (
                <RefreshCw className="h-4 w-4 animate-spin text-[#0c6cf2] shrink-0" />
              )}
              <span className={`text-xs font-medium leading-snug ${step.done ? 'text-[#0c2340] font-semibold' : 'text-slate-500'}`}>{step.label}</span>
            </div>
          ))}
        </div>

        {/* Complete Action Button */}
        {progress >= 100 && (
          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <button
              onClick={onClose}
              className="rzp-btn-primary w-full py-3 rounded-xl font-bold text-xs shadow-md transition-all cursor-pointer"
            >
              View Complete Reconciliation Dashboard
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
