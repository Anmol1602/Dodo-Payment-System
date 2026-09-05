import React from 'react';
import { DollarSign, CheckCircle2, RotateCw } from 'lucide-react';

interface MetricsCardsProps {
  totalVolume: string;
  successRate: string;
  webhookStatus: string;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  totalVolume,
  successRate,
  webhookStatus,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {/* Total Volume */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-5 hover:border-white/20 transition-colors">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Total Settled Volume</span>
          <DollarSign className="w-4 h-4 text-indigo-400 opacity-60" />
        </div>
        <div className="text-2xl font-bold text-white font-mono tracking-tight">{totalVolume}</div>
        <div className="text-[11px] text-slate-500 mt-1">USD (settled)</div>
      </div>

      {/* Success Rate */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-5 hover:border-white/20 transition-colors">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Success Rate</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400 opacity-60" />
        </div>
        <div className="text-2xl font-bold text-emerald-400 font-mono tracking-tight">{successRate}</div>
        <div className="text-[11px] text-slate-500 mt-1">Payment completions</div>
      </div>

      {/* Webhook Delivery */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-5 hover:border-white/20 transition-colors">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Webhook Delivery</span>
          <RotateCw className="w-4 h-4 text-blue-400 opacity-60 animate-spin-slow" />
        </div>
        <div className="text-2xl font-bold text-blue-400 tracking-tight">{webhookStatus}</div>
        <div className="text-[11px] text-slate-500 mt-1">Signed event deliveries</div>
      </div>
    </div>
  );
};
