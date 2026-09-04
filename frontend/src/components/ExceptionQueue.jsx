import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Filter
} from 'lucide-react';

export default function ExceptionQueue({ exceptionsData }) {
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [resolvedIds, setResolvedIds] = useState(new Set());

  const exceptions = exceptionsData?.exceptions || [];
  const missing = exceptionsData?.missing_from_settlement || [];

  const allItems = [
    ...exceptions.map(e => ({ ...e, source: 'VARIANCE' })),
    ...missing.map(m => ({ 
      payment_id: m.payment_id, 
      category: 'MISSING_FROM_SETTLEMENT', 
      amount_diff: -m.amount, 
      explanation: `Payment of Rs. ${m.amount} captured at gateway but missing from settlement batch. Pending bank transfer.`,
      source: 'MISSING',
      confidence: 1.0
    }))
  ];

  const categories = ['ALL', 'CROSS_PERIOD_REFUND', 'ROUNDING', 'FEE_DEDUCTION', 'MISSING_FROM_SETTLEMENT', 'UNEXPLAINED'];

  const filtered = allItems.filter(item => {
    if (activeFilter === 'ALL') return true;
    return item.category === activeFilter;
  });

  const handleResolve = (id) => {
    setResolvedIds(prev => new Set([...prev, id]));
  };

  const getBadgeStyle = (cat) => {
    switch (cat) {
      case 'CROSS_PERIOD_REFUND':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'ROUNDING':
        return 'bg-blue-50 text-[#0c6cf2] border-blue-200';
      case 'FEE_DEDUCTION':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'MISSING_FROM_SETTLEMENT':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-[#0c2340] uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-[#d97706]" />
            Exception & Variance Management Queue
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Deterministic categorization of non-exact matches with AI root-cause diagnostics and 1-click verification
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all border cursor-pointer ${
                activeFilter === cat
                  ? 'bg-[#0c6cf2] text-white border-[#0c6cf2] shadow-sm shadow-[#0c6cf2]/30'
                  : 'bg-white text-slate-600 border-slate-200 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              {cat.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Exception Table */}
      <div className="rzp-card rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase tracking-wider text-[11px] font-semibold">
              <tr>
                <th className="py-3.5 px-4 font-sans">Payment ID</th>
                <th className="py-3.5 px-4 font-sans">Classification</th>
                <th className="py-3.5 px-4 font-sans">Variance Amount</th>
                <th className="py-3.5 px-4 font-sans">Confidence</th>
                <th className="py-3.5 px-4 font-sans">Deterministic Explanation</th>
                <th className="py-3.5 px-4 font-sans text-right">Human Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                    No exceptions found for this filter.
                  </td>
                </tr>
              ) : (
                filtered.map((item, idx) => {
                  const isResolved = resolvedIds.has(item.payment_id);
                  return (
                    <tr 
                      key={idx} 
                      className={`hover:bg-blue-50/30 transition-colors ${
                        isResolved ? 'opacity-60 bg-emerald-50/40' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-bold text-[#0c2340]">
                        {item.payment_id}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <span className={`px-2 py-0.5 rounded-md border text-[11px] font-bold ${getBadgeStyle(item.category)}`}>
                          {item.category.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className={`py-3.5 px-4 font-bold ${
                        item.amount_diff < 0 ? 'text-rose-600' : 'text-[#00b87c]'
                      }`}>
                        {item.amount_diff > 0 ? `+Rs. ${item.amount_diff}` : `Rs. ${item.amount_diff}`}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <span className="text-[#00b87c] font-bold font-mono">
                          {((item.confidence || 0.95) * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-sans text-slate-700 max-w-md truncate" title={item.explanation}>
                        {item.explanation}
                      </td>
                      <td className="py-3.5 px-4 text-right font-sans">
                        {isResolved ? (
                          <span className="inline-flex items-center gap-1 text-[#00b87c] text-xs font-bold">
                            <CheckCircle2 className="h-4 w-4" />
                            Verified
                          </span>
                        ) : (
                          <button
                            onClick={() => handleResolve(item.payment_id)}
                            className="px-3 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#0c6cf2] border border-blue-200 text-xs font-bold transition-all cursor-pointer"
                          >
                            Approve & Close
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
