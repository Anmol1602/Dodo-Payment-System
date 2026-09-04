import React from 'react';
import { X, ShieldCheck, CheckCircle2, AlertOctagon, Database, Lock, Clock } from 'lucide-react';

interface AiUsageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AiUsageModal: React.FC<AiUsageModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-md">
      <div className="relative w-full max-w-2xl max-h-[85vh] bg-slate-900/90 border border-amber-500/30 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                AI_USAGE.md Disclosure
              </h3>
              <p className="text-xs text-amber-300/80">
                3 Independent Architectural Decisions Made Beyond AI Suggestions
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
          {/* Decision 1 */}
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl space-y-2">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold uppercase tracking-wider text-[11px]">
              <Database className="w-4 h-4" />
              <span>Decision 1: Relational 3NF Normalization vs. AI JSONB</span>
            </div>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-white">AI Proposed:</strong> Storing invoice line items as a denormalized JSONB array inside the invoices table.
            </p>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-emerald-400">Engineering Choice:</strong> Implemented a fully normalized <code className="text-amber-300 font-mono">invoice_line_items</code> table with check constraints (<code className="text-amber-300 font-mono">quantity &gt; 0</code>, <code className="text-amber-300 font-mono">unit_amount_cents &gt;= 0</code>) and composite indexes on <code className="text-amber-300 font-mono">(business_id, state)</code>. Client-supplied totals are never trusted.
            </p>
          </div>

          {/* Decision 2 */}
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl space-y-2">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold uppercase tracking-wider text-[11px]">
              <Lock className="w-4 h-4" />
              <span>Decision 2: Transaction Idempotency Table vs. Advisory Locks</span>
            </div>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-white">AI Proposed:</strong> Using PostgreSQL session advisory locks (<code className="text-amber-300 font-mono">pg_advisory_xact_lock</code>) based on key hash.
            </p>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-emerald-400">Engineering Choice:</strong> Created a dedicated <code className="text-amber-300 font-mono">idempotency_records</code> table with unique constraint on <code className="text-amber-300 font-mono">(business_id, idempotency_key)</code> and row-level locking. Eliminates PgBouncer transaction-mode connection leakage, avoids 32-bit hash collisions, and durably caches response payloads.
            </p>
          </div>

          {/* Decision 3 */}
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl space-y-2">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold uppercase tracking-wider text-[11px]">
              <Clock className="w-4 h-4" />
              <span>Decision 3: Indeterminate Pending State for PSP Timeouts</span>
            </div>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-white">AI Proposed:</strong> Marking payment attempt and invoice as immediately failed upon reaching upstream 5s timeout.
            </p>
            <p className="text-slate-300 leading-relaxed">
              <strong className="text-emerald-400">Engineering Choice:</strong> Kept payment attempt in indeterminate <code className="text-amber-300 font-mono">pending</code> status and invoice in <code className="text-amber-300 font-mono">open</code>. Upstream card networks may have debited the customer during network latency; premature failure leads to double billing.
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-white/10 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-slate-200 text-xs font-medium rounded-xl transition-colors cursor-pointer"
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
};
