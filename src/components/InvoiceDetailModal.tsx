import React, { useState } from 'react';
import { Invoice, PaymentAttempt } from '../types';
import { X, KeyRound, Play, RefreshCw } from 'lucide-react';

interface InvoiceDetailModalProps {
  invoice: Invoice | null;
  onClose: () => void;
  onSimulatePayment: (
    invoiceId: string,
    token: 'tok_success' | 'tok_timeout' | 'tok_card_declined' | 'tok_insufficient_funds',
    idempotencyKey: string
  ) => void;
  onVoidInvoice: (invoiceId: string) => void;
}

export const InvoiceDetailModal: React.FC<InvoiceDetailModalProps> = ({
  invoice,
  onClose,
  onSimulatePayment,
  onVoidInvoice,
}) => {
  if (!invoice) return null;

  const [selectedToken, setSelectedToken] = useState<
    'tok_success' | 'tok_timeout' | 'tok_card_declined' | 'tok_insufficient_funds'
  >('tok_success');
  const [customKey, setCustomKey] = useState<string>(
    () => `idem_${Math.random().toString(36).substring(2, 9)}-${Date.now().toString().slice(-4)}`
  );
  const [isProcessing, setIsProcessing] = useState(false);

  const formatCents = (cents: number) => {
    return (cents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  const handleTriggerPayment = () => {
    if (invoice.state === 'paid' || invoice.state === 'void') return;
    setIsProcessing(true);
    setTimeout(() => {
      onSimulatePayment(invoice.id, selectedToken, customKey);
      setIsProcessing(false);
      // Generate fresh next key
      setCustomKey(`idem_${Math.random().toString(36).substring(2, 9)}-${Date.now().toString().slice(-4)}`);
    }, selectedToken === 'tok_timeout' ? 1200 : 400);
  };

  const isTerminal = invoice.state === 'paid' || invoice.state === 'void';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-md">
      <div className="relative w-full max-w-2xl max-h-[90vh] bg-slate-900/90 border border-white/15 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="font-mono text-xl font-bold text-white tracking-tight">
              {invoice.displayNumber}
            </div>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full uppercase font-mono font-semibold border ${
                invoice.state === 'paid'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                  : invoice.state === 'open'
                  ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
                  : invoice.state === 'void'
                  ? 'bg-red-500/20 text-red-300 border-red-500/30'
                  : 'bg-slate-500/20 text-slate-300 border-slate-500/30'
              }`}
            >
              {invoice.state}
            </span>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto py-5 space-y-6">
          {/* Customer & Overview */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-slate-400 uppercase tracking-wider block text-[10px] mb-1">Customer</span>
              <div className="font-medium text-white">{invoice.customerName}</div>
              <div className="text-slate-400 font-mono text-[11px]">{invoice.customerEmail}</div>
            </div>
            <div className="p-3 bg-white/5 rounded-xl border border-white/5">
              <span className="text-slate-400 uppercase tracking-wider block text-[10px] mb-1">Total Amount Due</span>
              <div className="font-mono text-lg font-bold text-white">
                {formatCents(invoice.totalAmountCents)}
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                USD
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400">
                Line Items
              </h4>
            </div>
            <div className="bg-white/5 rounded-xl border border-white/5 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/5 text-slate-400 text-[10px] uppercase font-mono">
                  <tr>
                    <th className="p-3">Description</th>
                    <th className="p-3 text-center">Qty</th>
                    <th className="p-3 text-right">Unit Price</th>
                    <th className="p-3 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {invoice.lineItems.map((item) => (
                    <tr key={item.id} className="text-slate-200">
                      <td className="p-3">{item.description}</td>
                      <td className="p-3 text-center font-mono">{item.quantity}</td>
                      <td className="p-3 text-right font-mono text-slate-400">
                        {formatCents(item.unitAmountCents)}
                      </td>
                      <td className="p-3 text-right font-mono font-medium text-white">
                        {formatCents(item.totalAmountCents)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Payment Simulation Section */}
          <div className="p-4 bg-indigo-950/30 border border-indigo-500/20 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Play className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Simulate Payment Flow
                </span>
              </div>
              {isTerminal && (
                <span className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded font-mono">
                  Status: {invoice.state.toUpperCase()}
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Select a payment test token and submit to simulate invoice processing.
            </p>

            {/* Token Selector */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {(
                [
                  { token: 'tok_success', label: 'Success', color: 'emerald' },
                  { token: 'tok_timeout', label: 'Timeout', color: 'amber' },
                  { token: 'tok_card_declined', label: 'Declined', color: 'rose' },
                  { token: 'tok_insufficient_funds', label: 'No Funds', color: 'rose' },
                ] as const
              ).map((t) => (
                <button
                  key={t.token}
                  type="button"
                  disabled={isTerminal}
                  onClick={() => setSelectedToken(t.token)}
                  className={`p-2 rounded-xl border text-center transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                    selectedToken === t.token
                      ? 'bg-indigo-500/30 border-indigo-400 text-white font-medium shadow-sm'
                      : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  <div className="font-mono text-[11px]">{t.token}</div>
                  <div className="text-[10px] opacity-70 mt-0.5">{t.label}</div>
                </button>
              ))}
            </div>

            {/* Idempotency Key Input */}
            <div className="flex items-center gap-2 pt-1">
              <div className="flex-1 relative">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-slate-500">
                  <KeyRound className="w-3.5 h-3.5" />
                </div>
                <input
                  type="text"
                  value={customKey}
                  onChange={(e) => setCustomKey(e.target.value)}
                  placeholder="Idempotency-Key"
                  className="w-full bg-slate-900/80 border border-white/15 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="button"
                onClick={() =>
                  setCustomKey(`idem_${Math.random().toString(36).substring(2, 9)}-${Date.now().toString().slice(-4)}`)
                }
                title="Regenerate Key"
                className="p-2 bg-white/10 hover:bg-white/15 border border-white/10 rounded-xl text-slate-300 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end pt-2">
              <button
                onClick={handleTriggerPayment}
                disabled={isTerminal || isProcessing || !customKey.trim()}
                className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>Submit Payment</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Payment Attempts History */}
          <div>
            <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-400 mb-2">
              Payment Attempts
            </h4>
            {invoice.attempts.length === 0 ? (
              <div className="p-4 bg-white/5 rounded-xl border border-white/5 text-center text-xs text-slate-500 italic">
                No payment attempts recorded yet for this invoice.
              </div>
            ) : (
              <div className="space-y-2">
                {invoice.attempts.map((att: PaymentAttempt) => (
                  <div
                    key={att.id}
                    className="p-3 bg-white/5 rounded-xl border border-white/5 text-xs flex flex-wrap items-center justify-between gap-3 font-mono"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">{att.tokenUsed}</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                            att.status === 'succeeded'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : att.status === 'pending'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-rose-500/20 text-rose-400'
                          }`}
                        >
                          {att.pspResult}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1">
                        Key: {att.idempotencyKey}
                      </div>
                      {att.failureMessage && (
                        <div className="text-[10px] text-rose-400 mt-0.5">
                          {att.failureMessage}
                        </div>
                      )}
                    </div>

                    <div className="text-right text-[11px] text-slate-400">
                      <div>{formatCents(att.amountCents)}</div>
                      <div className="text-[10px] opacity-60">
                        {new Date(att.createdAt).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-white/10 flex items-center justify-between">
          <div>
            {invoice.state === 'draft' || invoice.state === 'open' ? (
              <button
                onClick={() => onVoidInvoice(invoice.id)}
                className="px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 border border-red-500/20 rounded-xl transition-colors cursor-pointer"
              >
                Void Invoice
              </button>
            ) : null}
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-white/10 hover:bg-white/20 text-slate-200 text-xs font-medium rounded-xl transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
