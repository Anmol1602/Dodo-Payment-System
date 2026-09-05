import React, { useState } from 'react';
import { WebhookDelivery } from '../types';
import { Webhook, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react';

interface WebhooksViewProps {
  webhooks: WebhookDelivery[];
}

export const WebhooksView: React.FC<WebhooksViewProps> = ({ webhooks }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col overflow-hidden min-h-[460px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
            <Webhook className="w-5 h-5 text-indigo-400" />
            <span>Webhooks</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            View real-time event deliveries and payload signatures.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
          <span className="px-3 py-1 bg-white/10 rounded-lg border border-white/10">Active</span>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <div className="space-y-3">
          {webhooks.map((wh) => {
            const isExpanded = expandedId === wh.id;

            return (
              <div
                key={wh.id}
                className="bg-white/5 border border-white/5 rounded-2xl p-4 transition-all hover:border-white/10"
              >
                <div
                  onClick={() => setExpandedId(isExpanded ? null : wh.id)}
                  className="flex flex-wrap items-center justify-between gap-3 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-1 rounded text-[10px] font-mono font-bold uppercase ${
                        wh.status === 'delivered'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : wh.status === 'retrying'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {wh.eventType}
                    </span>

                    <span className="font-mono text-xs text-slate-300 truncate max-w-xs">
                      {wh.targetUrl}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono">
                    <div className="flex items-center gap-1 text-slate-400">
                      <span>HTTP</span>
                      <span
                        className={
                          wh.statusCode === 200
                            ? 'text-emerald-400 font-semibold'
                            : 'text-amber-400 font-semibold'
                        }
                      >
                        {wh.statusCode}
                      </span>
                    </div>

                    <div className="text-slate-400 text-[11px]">
                      {wh.attempts} {wh.attempts === 1 ? 'attempt' : 'attempts'}
                    </div>

                    <div className="text-slate-500 text-[10px]">
                      {new Date(wh.timestamp).toLocaleTimeString()}
                    </div>

                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-white/5 space-y-3 animate-in fade-in duration-150">
                    <div className="bg-slate-900/60 p-3 rounded-xl border border-white/5">
                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                        <span className="flex items-center gap-1.5 text-indigo-300">
                          <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Signature Header</span>
                        </span>
                      </div>
                      <div className="font-mono text-xs text-slate-300 break-all select-all bg-black/40 p-2 rounded-lg">
                        {wh.signature}
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] font-mono text-slate-400 mb-1">
                        Payload:
                      </div>
                      <pre className="p-3 bg-black/40 rounded-xl border border-white/5 text-xs font-mono text-emerald-300 overflow-x-auto">
                        {JSON.stringify(wh.payload, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-slate-500">
        <div>Worker: Active</div>
        <div>Retry Policy: Exponential</div>
      </div>
    </div>
  );
};
