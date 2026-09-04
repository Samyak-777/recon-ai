import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  Info
} from 'lucide-react';

export default function CashForecastChart() {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/recon/forecast')
      .then(res => res.json())
      .then(data => {
        setForecast(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rzp-card rounded-2xl p-8 text-center text-slate-500">
        Generating 7-day forward cash forecast...
      </div>
    );
  }

  if (!forecast || !forecast.predictions) {
    return (
      <div className="rzp-card rounded-2xl p-8 text-center text-slate-500">
        No forecast data available. Run a reconciliation batch first.
      </div>
    );
  }

  const maxNet = Math.max(...forecast.predictions.map(p => p.predicted_net));

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Forecast Summary */}
      <div className="rzp-card rounded-2xl p-6 bg-emerald-50/70 border border-emerald-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#00b87c]">Forward Liquidity Planning</span>
            <h3 className="text-lg font-bold text-[#0c2340] mt-0.5">7-Day Forward Cash Position & Settlement Forecast</h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              {forecast.summary}
            </p>
          </div>
          
          <div className="text-right">
            <span className="text-xs text-slate-500 block font-medium">TOTAL 7-DAY PROJECTED INFLOW</span>
            <span className="text-2xl font-bold text-[#00b87c] font-mono tracking-tight">
              Rs. {forecast.total_predicted_net?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      {/* 7-Day Visual Bar/Timeline Cards */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
        {forecast.predictions.map((p, idx) => {
          const heightPercent = Math.max(20, Math.round((p.predicted_net / maxNet) * 100));
          const isWeekend = p.day_of_week === 'Saturday' || p.day_of_week === 'Sunday';

          return (
            <div 
              key={idx}
              className={`rzp-card-interactive rounded-2xl p-4 flex flex-col justify-between transition-all ${
                isWeekend 
                  ? 'border-slate-200 bg-slate-50/60 opacity-85' 
                  : 'border-slate-200 bg-white hover:border-emerald-300'
              }`}
            >
              {/* Day Header */}
              <div>
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 mb-1 font-mono">
                  <span>{p.date.slice(5)}</span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                    isWeekend ? 'bg-slate-200 text-slate-600' : 'bg-emerald-50 text-[#00b87c] border border-emerald-200'
                  }`}>
                    {p.confidence * 100}% Conf.
                  </span>
                </div>
                <div className="text-sm font-bold text-[#0c2340]">{p.day_of_week}</div>
              </div>

              {/* Visual Bar Height */}
              <div className="my-4 h-32 flex items-end justify-center">
                <div 
                  className="w-full rounded-xl bg-gradient-to-t from-emerald-100 to-[#00b87c] border border-[#00b87c] transition-all flex items-center justify-center shadow-xs"
                  style={{ height: `${heightPercent}%` }}
                >
                  <span className="text-[10px] font-mono text-white font-bold px-1 text-center truncate">
                    {(p.predicted_net / 1000).toFixed(0)}k
                  </span>
                </div>
              </div>

              {/* Amounts Breakdown */}
              <div className="pt-2 border-t border-slate-100 space-y-1 text-[11px] font-mono">
                <div className="flex justify-between text-slate-500">
                  <span>Gross:</span>
                  <span>Rs. {(p.predicted_gross / 1000).toFixed(1)}k</span>
                </div>
                <div className="flex justify-between font-bold text-[#00b87c]">
                  <span>Net:</span>
                  <span>Rs. {(p.predicted_net / 1000).toFixed(1)}k</span>
                </div>
              </div>

            </div>
          );
        })}
      </div>

      {/* Methodology Card */}
      <div className="rzp-card rounded-2xl p-5 border border-slate-200 flex items-start gap-4">
        <Info className="h-5 w-5 text-[#00b87c] shrink-0 mt-0.5" />
        <div className="text-xs text-slate-600 leading-relaxed font-sans">
          <strong className="text-[#0c2340]">Forecasting Methodology:</strong> Uses dynamic day-of-week settlement velocity coefficients calibrated against historical Razorpay settlement cycles (Monday batch accumulations for weekend checkout spikes, bank holiday shifts, and instrument settlement schedules T+1 for UPI, T+2 for Credit Cards).
        </div>
      </div>

    </div>
  );
}
