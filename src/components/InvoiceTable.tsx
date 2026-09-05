import React, { useState } from 'react';
import { Invoice } from '../types';
import { Loader2, ArrowRight } from 'lucide-react';

interface InvoiceTableProps {
  invoices: Invoice[];
  onSelectInvoice: (invoice: Invoice) => void;
  onOpenCreateModal: () => void;
}

export const InvoiceTable: React.FC<InvoiceTableProps> = ({
  invoices,
  onSelectInvoice,
}) => {
  const [filterState, setFilterState] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);

  const filteredInvoices = invoices.filter((inv) => {
    if (filterState === 'all') return true;
    return inv.state === filterState;
  });

  const formatCentsToCurrency = (cents: number): string => {
    return (cents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  return (
    <div className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col overflow-hidden min-h-[460px]">
      {/* Table Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight">
            Invoices
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitor real-time invoices and settlement activity.
          </p>
        </div>

        <div className="flex items-center gap-2 relative">
          <button
            onClick={() => setTimeRange(timeRange === '24h' ? '7d' : timeRange === '7d' ? '30d' : '24h')}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs text-slate-200 border border-white/10 transition-colors font-mono cursor-pointer"
            title="Toggle time filter"
          >
            Last {timeRange}
          </button>

          <div className="relative">
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              className={`px-3 py-1.5 rounded-lg text-xs border transition-colors cursor-pointer flex items-center gap-1.5 ${
                filterState !== 'all'
                  ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                  : 'bg-white/10 hover:bg-white/20 text-slate-200 border-white/10'
              }`}
            >
              <span>Filter: {filterState.toUpperCase()}</span>
            </button>

            {showFilterDropdown && (
              <div className="absolute right-0 mt-2 w-36 bg-slate-900/95 backdrop-blur-xl border border-white/15 rounded-xl shadow-2xl z-30 py-1.5 text-xs">
                {['all', 'open', 'paid', 'draft'].map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setFilterState(s);
                      setShowFilterDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 hover:bg-white/10 transition-colors ${
                      filterState === s ? 'text-indigo-400 font-semibold' : 'text-slate-300'
                    }`}
                  >
                    {s === 'all' ? 'All Invoices' : s.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="text-[11px] uppercase tracking-widest text-slate-500 border-b border-white/5">
            <tr>
              <th className="pb-3 font-semibold">Invoice / Customer</th>
              <th className="pb-3 font-semibold">Amount</th>
              <th className="pb-3 font-semibold">Last Token</th>
              <th className="pb-3 font-semibold">Processor Result</th>
              <th className="pb-3 font-semibold">Status</th>
              <th className="pb-3 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="text-sm divide-y divide-white/5">
            {filteredInvoices.map((invoice) => {
              const hasAttempt = invoice.attempts && invoice.attempts.length > 0;
              const lastAttempt = hasAttempt ? invoice.attempts[invoice.attempts.length - 1] : null;
              const tokenUsed = invoice.lastToken || (lastAttempt ? lastAttempt.tokenUsed : '—');
              const isTimeout = tokenUsed === 'tok_timeout';
              const isCardDeclined = tokenUsed === 'tok_card_declined';

              return (
                <tr
                  key={invoice.id}
                  onClick={() => onSelectInvoice(invoice)}
                  className="group hover:bg-white/[0.03] transition-colors cursor-pointer"
                >
                  {/* Invoice ID / Customer */}
                  <td className="py-4 pr-4">
                    <div className="font-mono text-indigo-300 font-medium group-hover:text-indigo-200 flex items-center gap-1.5">
                      {invoice.displayNumber}
                      <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="text-xs opacity-50 text-white truncate max-w-[220px]">
                      {invoice.customerName} ({invoice.customerEmail})
                    </div>
                  </td>

                  {/* Amount */}
                  <td className="py-4 pr-4 font-mono font-medium text-slate-100">
                    {formatCentsToCurrency(invoice.totalAmountCents)}
                  </td>

                  {/* Last Attempt */}
                  <td className="py-4 pr-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-mono ${
                          isTimeout
                            ? 'text-amber-400 opacity-90'
                            : isCardDeclined
                            ? 'text-rose-400 opacity-90'
                            : 'text-slate-400'
                        }`}
                      >
                        {tokenUsed}
                      </span>
                      {isTimeout && (
                        <Loader2 className="w-3 h-3 animate-spin text-amber-400 shrink-0" />
                      )}
                    </div>
                  </td>

                  {/* PSP Result */}
                  <td className="py-4 pr-4">
                    {invoice.lastPspResult === 'Succeeded' ? (
                      <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-[10px] font-bold uppercase tracking-wider">
                        Succeeded
                      </span>
                    ) : invoice.lastPspResult === 'Declined' ? (
                      <span className="px-2 py-1 bg-rose-500/20 text-rose-400 rounded text-[10px] font-bold uppercase tracking-wider">
                        Declined
                      </span>
                    ) : invoice.lastPspResult === 'Pending' ? (
                      <span className="px-2 py-1 bg-slate-500/20 text-slate-400 rounded text-[10px] font-bold uppercase tracking-wider">
                        Pending
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">—</span>
                    )}
                  </td>

                  {/* State */}
                  <td className="py-4 pr-4">
                    <span className="flex items-center gap-1.5 text-white capitalize text-xs">
                      {invoice.state === 'paid' && (
                        <>
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                          <span>Paid</span>
                        </>
                      )}
                      {invoice.state === 'open' && (
                        <>
                          <span className={`w-1.5 h-1.5 rounded-full ${isCardDeclined ? 'bg-rose-400' : 'bg-blue-400'}`}></span>
                          <span>Open</span>
                        </>
                      )}
                      {invoice.state === 'draft' && (
                        <>
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                          <span>Draft</span>
                        </>
                      )}
                      {invoice.state === 'void' && (
                        <>
                          <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                          <span>Void</span>
                        </>
                      )}
                    </span>
                  </td>

                  {/* Action link */}
                  <td className="py-4 text-right">
                    <span className="text-xs text-indigo-400 opacity-80 group-hover:opacity-100">
                      View &rarr;
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Status Footer */}
      <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap gap-4 justify-between items-center text-[10px] font-mono text-slate-500">
        <div className="flex flex-wrap gap-4 sm:gap-6">
          <div>
            Database: <span className="text-emerald-400 font-semibold">Connected</span>
          </div>
          <div>
            Gateway: <span className="text-emerald-400 font-semibold">Online</span>
          </div>
          <div>
            Worker: <span className="text-blue-400 font-semibold">Active</span>
          </div>
        </div>
        <div>
          Environment: <span className="text-slate-300 font-semibold">Sandbox</span>
        </div>
      </div>
    </div>
  );
};
