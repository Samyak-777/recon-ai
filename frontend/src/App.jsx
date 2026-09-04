import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ReconSummaryCards from './components/ReconSummaryCards';
import GrossNetWaterfall from './components/GrossNetWaterfall';
import ExceptionQueue from './components/ExceptionQueue';
import SettlementQAChat from './components/SettlementQAChat';
import CashForecastChart from './components/CashForecastChart';
import TaxGstDashboard from './components/TaxGstDashboard';
import RazorpayDashboardIntegration from './components/RazorpayDashboardIntegration';
import BatchRunModal from './components/BatchRunModal';
import { 
  ShieldCheck, 
  CheckCircle2,
  Sparkles
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('recon');
  const [reconData, setReconData] = useState(null);
  const [exceptionsData, setExceptionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isReconciling, setIsReconciling] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchSize, setBatchSize] = useState(150);

  useEffect(() => {
    fetchReconData();
  }, []);

  const fetchReconData = async () => {
    try {
      setLoading(true);
      let res = await fetch('/api/recon/results');
      if (!res.ok) {
        await fetch('/api/recon/seed?num_transactions=150', { method: 'POST' });
        res = await fetch('/api/recon/run', { method: 'POST' });
      }
      const data = await res.json();
      setReconData(data);

      const excRes = await fetch('/api/recon/exceptions');
      if (excRes.ok) {
        const excData = await excRes.json();
        setExceptionsData(excData);
      }
    } catch (err) {
      console.error('Failed to load reconciliation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerBatch = async (sizeToRun) => {
    const size = sizeToRun || batchSize || 150;
    setIsReconciling(true);
    setShowBatchModal(true);
    setBatchProgress(10);

    try {
      setBatchProgress(25);
      await fetch(`/api/recon/seed?num_transactions=${size}`, { method: 'POST' });
      
      setBatchProgress(65);
      const res = await fetch('/api/recon/run', { method: 'POST' });
      const data = await res.json();
      setBatchProgress(90);

      setReconData(data);

      const excRes = await fetch('/api/recon/exceptions');
      if (excRes.ok) {
        const excData = await excRes.json();
        setExceptionsData(excData);
      }

      setBatchProgress(100);
    } catch (err) {
      console.error('Batch run error:', err);
    } finally {
      setIsReconciling(false);
    }
  };

  if (loading && !reconData) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center text-[#0c2340]">
        <div className="text-center space-y-4">
          <div className="h-14 w-14 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto text-[#0c6cf2] animate-pulse shadow-lg shadow-[#0c6cf2]/10">
            <ShieldCheck className="h-8 w-8" />
          </div>
          <h2 className="text-lg font-bold text-[#0c2340]">Connecting to ReconAI...</h2>
          <p className="text-xs text-slate-500">Loading synthetic orders, settlement batches, and MCP tools</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-[#0c2340] flex flex-col selection:bg-[#0c6cf2]/20">
      
      {/* Razorpay Brand Header with Green-Underline Nav Tabs */}
      <Header 
        onTriggerBatch={handleTriggerBatch}
        isReconciling={isReconciling}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        summaryData={reconData}
        batchSize={batchSize}
        onBatchSizeChange={setBatchSize}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Top Metric Cards — Visible on all tabs for financial situational awareness */}
        <ReconSummaryCards 
          summary={reconData?.summary} 
          financials={reconData?.financials} 
          performance={reconData?.performance} 
        />

        {/* Tab 1: Reconciliation Ledger */}
        {activeTab === 'recon' && (
          <div className="space-y-8">
            <GrossNetWaterfall 
              waterfalls={reconData?.waterfalls} 
              financials={reconData?.financials} 
            />
            <ExceptionQueue 
              exceptionsData={exceptionsData} 
            />
          </div>
        )}

        {/* Tab 2: Gross-to-Net Waterfall */}
        {activeTab === 'waterfall' && (
          <GrossNetWaterfall 
            waterfalls={reconData?.waterfalls} 
            financials={reconData?.financials} 
          />
        )}

        {/* Tab 3: Exception Queue */}
        {activeTab === 'exceptions' && (
          <ExceptionQueue 
            exceptionsData={exceptionsData} 
          />
        )}

        {/* Tab 4: Settlement Q&A Copilot */}
        {activeTab === 'qa' && (
          <SettlementQAChat />
        )}

        {/* Tab 5: 7-Day Cash Flow Forecast */}
        {activeTab === 'forecast' && (
          <CashForecastChart />
        )}

        {/* Tab 6: GST & ITC Optimization */}
        {activeTab === 'tax' && (
          <TaxGstDashboard />
        )}

        {/* Tab 7: Razorpay Test Dashboard & Webhooks Hub */}
        {activeTab === 'webhooks' && (
          <RazorpayDashboardIntegration />
        )}

      </main>

      {/* Floating Ask RAY Button */}
      <div className="fixed bottom-6 right-6 z-30">
        <button
          onClick={() => setActiveTab('qa')}
          className="rzp-btn-primary px-5 py-3 rounded-full text-xs font-bold flex items-center gap-2 shadow-xl shadow-[#0c6cf2]/20 hover:scale-105 transition-all cursor-pointer"
        >
          <div className="h-5 w-5 rounded-full bg-white/20 flex items-center justify-center">
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </div>
          <span>Ask RAY</span>
        </button>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50 py-6 text-center text-xs text-slate-500 font-sans mt-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ReconAI • Buildathon 2026 Submission • Track 04: AI Finance Controller</span>
          <span className="flex items-center gap-1.5 text-[#00b87c] font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            100% Deterministic Accounting Engine Active
          </span>
        </div>
      </footer>

      {/* Batch Run Progress Modal */}
      <BatchRunModal 
        isOpen={showBatchModal}
        onClose={() => setShowBatchModal(false)}
        progress={batchProgress}
        batchSize={batchSize}
      />

    </div>
  );
}
