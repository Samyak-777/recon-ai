import React from 'react';
import { 
  Layers, 
  Activity, 
  Play, 
  RefreshCw, 
  Sparkles, 
  ArrowUpRight,
  Receipt,
  TrendingUp,
  Radio
} from 'lucide-react';

export default function Header({ 
  onTriggerBatch, 
  isReconciling, 
  activeTab, 
  setActiveTab, 
  summaryData,
  batchSize = 150,
  onBatchSizeChange
}) {
  const tabs = [
    { id: 'recon', label: 'Reconciliation Ledger', icon: Layers },
    { id: 'waterfall', label: 'Gross-to-Net Waterfall', icon: ArrowUpRight },
    { id: 'exceptions', label: 'Exception Queue', icon: Activity, badge: summaryData?.summary?.missing_from_settlement || 0 },
    { id: 'qa', label: 'Settlement Q&A Copilot', icon: Sparkles },
    { id: 'forecast', label: '7-Day Cash Forecast', icon: TrendingUp },
    { id: 'tax', label: 'GST & ITC Optimization', icon: Receipt },
    { id: 'webhooks', label: 'Test Dashboard & Webhooks', icon: Radio },
  ];

  return (
    <header className="border-b border-slate-200/80 bg-white/95 sticky top-0 z-40 backdrop-blur-md shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Top Navbar Row */}
        <div className="flex items-center justify-between h-20">
          
          {/* Razorpay Brand Mark & Logo */}
          <div className="flex items-center space-x-4">
            <div className="h-10 w-10 rounded-xl bg-[#0c6cf2] flex items-center justify-center shadow-md shadow-[#0c6cf2]/20">
              <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.7 2L5 13.5h5.5L8.5 22 19 10.5h-5.5L15.3 2z" />
              </svg>
            </div>

            <div>
              <div className="flex items-center space-x-2.5">
                <span className="text-xl font-black tracking-tight text-[#0c2340] flex items-center gap-1.5 font-sans">
                  Recon<span className="text-[#0c6cf2]">AI</span>
                </span>
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-[#f0f7ff] text-[#0c6cf2] border border-[#d0e4ff] uppercase tracking-wide">
                  Track 04 • AI Finance Controller
                </span>
              </div>
              <div className="flex items-center space-x-3 text-xs text-slate-500 mt-0.5 font-medium">
                <span>Autonomous Multi-Rail Settlement Reconciliation</span>
                <span className="text-slate-300">•</span>
                <span className="text-[#00b87c] font-mono font-semibold flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-[#00b87c] animate-pulse" />
                  Razorpay MCP Connected
                </span>
              </div>
            </div>
          </div>

            {/* Batch Size Selector & Run Batch CTA */}
            <div className="flex items-center space-x-2 bg-slate-50 p-1 rounded-xl border border-slate-200">
              <div className="flex items-center pl-2 pr-1 text-xs font-semibold text-slate-600">
                <span className="hidden sm:inline mr-1.5 text-slate-400">Batch:</span>
                <select
                  value={batchSize}
                  onChange={(e) => onBatchSizeChange(Number(e.target.value))}
                  disabled={isReconciling}
                  className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-bold text-[#0c2340] focus:outline-none focus:ring-2 focus:ring-[#0c6cf2] cursor-pointer"
                >
                  <option value={50}>50 Txns</option>
                  <option value={100}>100 Txns</option>
                  <option value={150}>150 Txns (Standard)</option>
                  <option value={250}>250 Txns</option>
                  <option value={500}>500 Txns</option>
                  <option value={1000}>1000 Txns (Heavy)</option>
                </select>
              </div>

              <button
                onClick={() => onTriggerBatch(batchSize)}
                disabled={isReconciling}
                className={`rzp-btn-primary px-4 py-2 rounded-lg font-bold text-xs flex items-center gap-2 transition-all cursor-pointer ${
                  isReconciling ? 'opacity-70 cursor-not-allowed' : ''
                }`}
              >
                {isReconciling ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Reconciling...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-current" />
                    <span>Run {batchSize}-Txn Recon</span>
                  </>
                )}
              </button>
            </div>
          </div>

        {/* Razorpay Green-Underline Navigation Tabs */}
        <div className="flex space-x-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold whitespace-nowrap transition-all border-b-2 cursor-pointer ${
                  isActive
                    ? 'border-[#00b87c] text-[#0c2340] font-extrabold'
                    : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-[#00b87c]' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
                {tab.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full bg-amber-50 text-amber-700 text-[10px] font-mono border border-amber-200">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

      </div>
    </header>
  );
}
