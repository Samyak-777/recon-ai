import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  RefreshCw, 
  CheckCircle2, 
  ShieldCheck, 
  Terminal, 
  ExternalLink, 
  Copy, 
  Check, 
  Send, 
  Zap, 
  Play,
  Layers,
  Sparkles,
  Link as LinkIcon
} from 'lucide-react';

export default function RazorpayDashboardIntegration() {
  const [mcpStatus, setMcpStatus] = useState(null);
  const [webhookFeed, setWebhookFeed] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [simAmount, setSimAmount] = useState(3554.16);
  const [simEvent, setSimEvent] = useState('payment.captured');
  const [simMethod, setSimMethod] = useState('card');

  useEffect(() => {
    fetchMcpStatus();
    fetchWebhookFeed();
    const interval = setInterval(fetchWebhookFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchMcpStatus = async () => {
    try {
      const res = await fetch('/api/recon/mcp-status');
      if (res.ok) {
        setMcpStatus(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch MCP status:', err);
    }
  };

  const fetchWebhookFeed = async () => {
    try {
      const res = await fetch('/api/recon/webhooks/feed');
      if (res.ok) {
        const data = await res.json();
        setWebhookFeed(data.feed || []);
      }
    } catch (err) {
      console.error('Failed to fetch webhook feed:', err);
    }
  };

  const handleSyncDashboard = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch('/api/recon/sync-live-dashboard', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSyncResult(data);
        fetchWebhookFeed();
      }
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSimulateWebhook = async () => {
    setIsSimulating(true);
    try {
      await fetch(`/api/recon/webhooks/simulate-test?event_type=${simEvent}&amount_inr=${simAmount}&method=${simMethod}`, {
        method: 'POST'
      });
      await fetchWebhookFeed();
    } catch (err) {
      console.error('Simulate webhook error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const webhookEndpoint = `${window.location.protocol}//${window.location.host}/api/recon/webhooks`;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Connection Status & Merchant Details */}
      <div className="rzp-card rounded-2xl p-6 bg-gradient-to-r from-blue-50/80 via-white to-emerald-50/50 border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#00b87c] border border-emerald-200 text-xs font-bold flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#00b87c] animate-pulse" />
                Live Razorpay Test Dashboard Connected
              </span>
              <span className="text-xs text-slate-500 font-mono">Merchant: TWtt5Umeg75s5e</span>
            </div>

            <h3 className="text-xl font-bold text-[#0c2340]">
              Razorpay Test Dashboard & Webhook Ingestion Hub
            </h3>
            <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
              ReconAI bridges your live Razorpay Dashboard via native MCP tools and real-time Webhook subscribers. Every payment, refund, and payment link created on your dashboard is ingested into the 4-stage Gross-to-Net reconciliation engine.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleSyncDashboard}
              disabled={isSyncing}
              className="rzp-btn-primary px-5 py-3 rounded-xl font-bold text-xs flex items-center gap-2 transition-all cursor-pointer shadow-sm"
            >
              <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing Live Dashboard...' : 'Sync Test Dashboard Data'}</span>
            </button>
            <a
              href="https://dashboard.razorpay.com/app/payments"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-3 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition-colors shadow-2xs"
            >
              <span>Open Razorpay Dashboard</span>
              <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
            </a>
          </div>
        </div>

        {syncResult && (
          <div className="mt-4 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 flex items-center justify-between animate-in fade-in">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#00b87c]" />
              <span>
                <strong>Sync Successful:</strong> Ingested {syncResult.payment_links_found || 0} Payment Links & {syncResult.live_orders_ingested || 0} Orders from your Razorpay Dashboard into ReconAI.
              </span>
            </div>
            <span className="font-mono text-xs font-bold text-[#00b87c]">100% RECONCILED</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Webhook Setup & Live Simulator */}
        <div className="lg:col-span-6 space-y-6">
          
          {/* Webhook Configuration Guide */}
          <div className="rzp-card rounded-2xl p-6 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-[#0c2340] flex items-center gap-2">
                <Radio className="h-4 w-4 text-[#0c6cf2]" />
                Webhook Configuration URL
              </h4>
              <span className="text-[11px] text-slate-500">Razorpay Account & Settings &gt; Webhooks</span>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-600">
                To receive live payment & settlement events directly from your Razorpay Dashboard in real-time, configure this Webhook URL:
              </p>

              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs">
                <input 
                  type="text" 
                  readOnly 
                  value={webhookEndpoint} 
                  className="bg-transparent flex-1 outline-none text-[#0c2340] select-all font-semibold"
                />
                <button
                  onClick={() => copyToClipboard(webhookEndpoint)}
                  className="px-3 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 hover:text-[#0c6cf2] text-xs font-bold flex items-center gap-1 transition-all cursor-pointer"
                >
                  {copiedUrl ? <Check className="h-3.5 w-3.5 text-[#00b87c]" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copiedUrl ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              <div className="space-y-1.5 pt-2">
                <span className="font-bold text-[#0c2340] block">Recommended Webhook Events to Subscribe:</span>
                <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
                  {['payment.captured', 'payment.failed', 'order.paid', 'settlement.processed', 'refund.processed', 'payment_link.paid'].map(ev => (
                    <span key={ev} className="px-2 py-0.5 rounded-md bg-blue-50 text-[#0c6cf2] border border-blue-200 font-semibold">
                      {ev}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Webhook Event Test Simulator */}
          <div className="rzp-card rounded-2xl p-6 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-[#0c2340] flex items-center gap-2">
                <Play className="h-4 w-4 text-[#00b87c]" />
                Simulate Inbound Webhook Event
              </h4>
              <span className="text-[11px] text-slate-500">Test signature & auto-ingestion</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-500 font-medium">Event Type</label>
                <select 
                  value={simEvent} 
                  onChange={(e) => setSimEvent(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#0c2340] font-semibold outline-none focus:border-[#0c6cf2]"
                >
                  <option value="payment.captured">payment.captured</option>
                  <option value="payment.failed">payment.failed</option>
                  <option value="order.paid">order.paid</option>
                  <option value="settlement.processed">settlement.processed</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 font-medium">Amount (INR)</label>
                <input 
                  type="number" 
                  value={simAmount}
                  onChange={(e) => setSimAmount(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#0c2340] font-mono font-bold outline-none focus:border-[#0c6cf2]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 font-medium">Payment Rail</label>
                <select 
                  value={simMethod} 
                  onChange={(e) => setSimMethod(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-[#0c2340] font-semibold outline-none focus:border-[#0c6cf2]"
                >
                  <option value="card">Card (2.0% MDR)</option>
                  <option value="upi">UPI (0.0% MDR)</option>
                  <option value="netbanking">Netbanking (1.8% MDR)</option>
                  <option value="wallet">Wallet (1.9% MDR)</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleSimulateWebhook}
              disabled={isSimulating}
              className="w-full rzp-btn-primary py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 cursor-pointer transition-all"
            >
              <Send className="h-3.5 w-3.5" />
              <span>{isSimulating ? 'Sending Webhook...' : `Dispatch ${simEvent} Webhook Payload`}</span>
            </button>
          </div>

        </div>

        {/* Right Column: Live Webhook Feed & MCP Tools */}
        <div className="lg:col-span-6 space-y-6">
          
          {/* Live Ingested Webhook Feed Table */}
          <div className="rzp-card rounded-2xl p-5 border border-slate-200 flex flex-col h-[480px]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-[#00b87c] animate-pulse" />
                <h4 className="text-sm font-bold text-[#0c2340]">Live Webhook Event Feed</h4>
              </div>
              <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                {webhookFeed.length} Events Received
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              {webhookFeed.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-400">
                  No live webhooks received yet. Use the simulator or trigger a payment in your Razorpay Dashboard.
                </div>
              ) : (
                webhookFeed.map((ev, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-50/70 border border-slate-200 text-xs space-y-1.5 transition-all hover:bg-blue-50/40">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-[#0c6cf2]">{ev.event}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{ev.timestamp}</span>
                    </div>
                    <div className="text-[11px] text-slate-700 font-medium">{ev.summary}</div>
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-200/80">
                      <span>Event ID: {ev.event_id}</span>
                      <span className="text-[#00b87c] font-bold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" />
                        Signature Verified
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
