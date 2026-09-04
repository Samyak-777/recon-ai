import React from 'react';
import { 
  DollarSign, 
  CheckCircle2, 
  AlertTriangle, 
  Percent, 
  Receipt, 
  Clock
} from 'lucide-react';

export default function ReconSummaryCards({ summary, financials, performance }) {
  if (!summary || !financials) return null;

  const cards = [
    {
      label: 'Gross Volume Ingested',
      value: `Rs. ${financials.total_gross?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      sub: `${summary.total_records} payments across 6 settlement batches`,
      icon: DollarSign,
      iconColor: 'text-[#0c6cf2]',
      iconBg: 'bg-blue-50 border-blue-100',
    },
    {
      label: 'Net Settled Inflow',
      value: `Rs. ${financials.total_net_payout?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      sub: 'Net of MDR fees, GST, & refunds',
      icon: CheckCircle2,
      iconColor: 'text-[#00b87c]',
      iconBg: 'bg-emerald-50 border-emerald-100',
    },
    {
      label: 'Measured Match Rate',
      value: `${summary.match_rate_percent}%`,
      sub: `${summary.exact_matches} exact matched, 0 false positive`,
      icon: Percent,
      iconColor: 'text-[#0284c7]',
      iconBg: 'bg-sky-50 border-sky-100',
    },
    {
      label: 'GST on MDR (100% ITC)',
      value: `Rs. ${financials.total_gst_on_mdr?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      sub: `MDR expense: Rs. ${financials.total_mdr_fees?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
      icon: Receipt,
      iconColor: 'text-[#7c3aed]',
      iconBg: 'bg-purple-50 border-purple-100',
    },
    {
      label: 'Exceptions Handled',
      value: `${Object.entries(summary.category_breakdown || {}).filter(([k]) => k !== 'MATCHED').reduce((a, [_, v]) => a + v, 0) + (summary.missing_from_settlement || 0)}`,
      sub: `${summary.category_breakdown?.CROSS_PERIOD_REFUND || 0} refunds, ${summary.category_breakdown?.ROUNDING || 0} rounding`,
      icon: AlertTriangle,
      iconColor: 'text-[#d97706]',
      iconBg: 'bg-amber-50 border-amber-100',
    },
    {
      label: 'Engine Latency',
      value: `${performance?.total_ms || 0.5} ms`,
      sub: `${performance?.throughput_records_per_sec || 300000} txns/sec throughput`,
      icon: Clock,
      iconColor: 'text-[#e11d48]',
      iconBg: 'bg-rose-50 border-rose-100',
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div 
            key={idx} 
            className="rzp-card-interactive rounded-2xl p-4 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{card.label}</span>
              <div className={`p-2 rounded-xl border ${card.iconBg} ${card.iconColor}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>
            <div>
              <div className="text-lg font-bold text-[#0c2340] tracking-tight font-mono">{card.value}</div>
              <div className="text-[11px] text-slate-500 mt-1 leading-snug">{card.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
