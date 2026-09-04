import React, { useState } from 'react';
import { 
  ArrowDownRight, 
  ArrowUpRight, 
  CreditCard, 
  Receipt, 
  CheckCircle2, 
  Sparkles,
  Info
} from 'lucide-react';

export default function GrossNetWaterfall({ waterfalls, financials }) {
  const [selectedTxn, setSelectedTxn] = useState(waterfalls?.[0] || null);

  if (!waterfalls || waterfalls.length === 0) {
    return (
      <div className="rzp-card rounded-2xl p-8 text-center text-slate-500">
        No waterfall data available. Run a reconciliation batch first.
      </div>
    );
  }

  const current = selectedTxn || waterfalls[0];

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Aggregate Waterfall Formula */}
      <div className="rzp-card rounded-2xl p-6 bg-slate-50/80 border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#0c6cf2]">Accounting Invariant</span>
            <h3 className="text-lg font-bold text-[#0c2340] mt-0.5">Multi-Rail Gross-to-Net Reconciliation Formula</h3>
            <p className="text-xs text-slate-500 mt-1">
              Every Razorpay settlement is unpacked into constituent Order IDs with discrete MDR fee schedules and ITC tax buckets.
            </p>
          </div>
          
          <div className="flex items-center gap-2 overflow-x-auto py-2 font-mono text-xs">
            <div className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-[#0c2340] shadow-2xs">
              <span className="text-[10px] text-slate-500 block font-sans">GROSS AMOUNT</span>
              Rs. {financials?.total_gross?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <span className="text-rose-500 font-bold">−</span>
            <div className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-rose-600 shadow-2xs">
              <span className="text-[10px] text-slate-500 block font-sans">MDR FEES</span>
              Rs. {financials?.total_mdr_fees?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <span className="text-rose-500 font-bold">−</span>
            <div className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-purple-600 shadow-2xs">
              <span className="text-[10px] text-slate-500 block font-sans">GST (18%)</span>
              Rs. {financials?.total_gst_on_mdr?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <span className="text-rose-500 font-bold">−</span>
            <div className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-amber-600 shadow-2xs">
              <span className="text-[10px] text-slate-500 block font-sans">REFUNDS</span>
              Rs. {financials?.total_refunds_deducted?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <span className="text-[#00b87c] font-bold">=</span>
            <div className="px-3.5 py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-[#00b87c] font-bold shadow-2xs">
              <span className="text-[10px] text-[#00b87c] block font-sans">NET SETTLED</span>
              Rs. {financials?.total_net_payout?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Transaction Selector List */}
        <div className="lg:col-span-5 rzp-card rounded-2xl p-4 flex flex-col h-[550px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <h4 className="text-sm font-bold text-[#0c2340] flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-[#0c6cf2]" />
              Reconciled Transactions ({waterfalls.length})
            </h4>
            <span className="text-[11px] text-slate-500 font-sans">Click to inspect waterfall</span>
          </div>

          <div className="overflow-y-auto space-y-2 pr-1 flex-1">
            {waterfalls.map((wf, idx) => {
              const isSelected = current?.payment_id === wf.payment_id;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedTxn(wf)}
                  className={`p-3 rounded-xl cursor-pointer transition-all border text-left ${
                    isSelected
                      ? 'bg-blue-50/80 border-blue-300 shadow-xs'
                      : 'bg-slate-50/60 border-slate-200/80 hover:bg-slate-100/80 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#0c2340]">{wf.payment_id}</span>
                    <span className="text-xs font-bold text-[#00b87c] font-mono">
                      Rs. {wf.net_payout?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                    <div className="flex items-center gap-2">
                      <span className="uppercase px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-semibold text-slate-700">
                        {wf.method}
                      </span>
                      <span>Gross: Rs. {wf.gross_amount?.toLocaleString('en-IN')}</span>
                    </div>
                    {wf.refund_deducted > 0 && (
                      <span className="text-amber-700 text-[10px] font-semibold bg-amber-50 px-1 rounded border border-amber-200">
                        Refund: Rs. {wf.refund_deducted}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Detailed Visual Waterfall for Selected Txn */}
        <div className="lg:col-span-7 rzp-card rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
              <div>
                <span className="text-[11px] font-mono font-bold text-[#0c6cf2]">ORDER: {current?.order_id || 'N/A'}</span>
                <h4 className="text-lg font-bold text-[#0c2340] flex items-center gap-2 mt-0.5">
                  Waterfall for {current?.payment_id}
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-[#00b87c] border border-emerald-200 text-xs font-semibold flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  100% Reconciled
                </span>
              </div>
            </div>

            {/* Visual Step-by-Step Waterfall */}
            <div className="space-y-3 font-mono">
              {current?.waterfall_steps?.map((step, sIdx) => {
                const isDebit = step.type === 'debit';
                const isNet = step.type === 'net';

                return (
                  <div 
                    key={sIdx}
                    className={`p-4 rounded-xl border flex items-center justify-between ${
                      isNet 
                        ? 'bg-emerald-50 border-emerald-200 font-bold' 
                        : isDebit 
                        ? 'bg-rose-50/50 border-rose-100' 
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        isNet ? 'bg-emerald-100 text-[#00b87c]' :
                        isDebit ? 'bg-rose-100 text-rose-600' : 'bg-blue-100 text-[#0c6cf2]'
                      }`}>
                        {isDebit ? <ArrowDownRight className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                      </div>
                      <div>
                        <div className={`text-sm font-semibold font-sans ${isNet ? 'text-[#00b87c]' : 'text-slate-800'}`}>
                          {step.label}
                        </div>
                        {step.label.includes('GST') && (
                          <div className="text-[11px] text-purple-700 flex items-center gap-1 mt-0.5 font-sans font-medium">
                            <Sparkles className="h-3 w-3 text-purple-600" />
                            Input Tax Credit (ITC) Eligible
                          </div>
                        )}
                      </div>
                    </div>

                    <div className={`text-base font-bold ${
                      isNet ? 'text-[#00b87c] text-lg' :
                      isDebit ? 'text-rose-600' : 'text-[#0c2340]'
                    }`}>
                      {step.amount > 0 && !isNet ? `+Rs. ${step.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 
                       step.amount < 0 ? `-Rs. ${Math.abs(step.amount)?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` :
                       `Rs. ${step.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tax Note Footer */}
          <div className="mt-6 p-3.5 rounded-xl bg-purple-50/70 border border-purple-200 flex items-start gap-3">
            <Info className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
            <div className="text-xs text-purple-950 leading-relaxed font-sans">
              <strong className="text-purple-700">Input Tax Credit Compliance:</strong> The GST of Rs. {current?.gst_on_mdr?.toFixed(2)} on this transaction is recorded with Razorpay PA GSTIN metadata for automated filing on GSTR-2B.
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
