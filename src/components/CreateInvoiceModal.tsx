import React, { useState } from 'react';
import { Customer, Invoice, LineItem } from '../types';
import { X, Plus, Trash2, Calculator } from 'lucide-react';

interface CreateInvoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  customers: Customer[];
  onCreateInvoice: (newInvoice: Invoice) => void;
}

export const CreateInvoiceModal: React.FC<CreateInvoiceModalProps> = ({
  isOpen,
  onClose,
  customers,
  onCreateInvoice,
}) => {
  if (!isOpen) return null;

  const [selectedCustomerId, setSelectedCustomerId] = useState<string>(
    customers[0]?.id || ''
  );
  const [dueDate, setDueDate] = useState<string>(
    new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0]
  );
  const [items, setItems] = useState<
    Array<{ description: string; quantity: number; unitPriceDollars: string }>
  >([
    { description: 'API Platform Subscription', quantity: 1, unitPriceDollars: '950.00' },
  ]);

  const handleAddItem = () => {
    setItems((prev) => [
      ...prev,
      { description: 'Consulting / Engineering Sprint', quantity: 1, unitPriceDollars: '500.00' },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    if (items.length <= 1) return;
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const totalCents = items.reduce((acc, item) => {
    const qty = Math.max(1, parseInt(String(item.quantity)) || 1);
    const priceCents = Math.round((parseFloat(item.unitPriceDollars) || 0) * 100);
    return acc + qty * priceCents;
  }, 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const customer = customers.find((c) => c.id === selectedCustomerId) || customers[0];
    const newId = `inv_${Math.floor(1000 + Math.random() * 9000)}`;
    const displayNumber = `#INV-${Math.floor(5000 + Math.random() * 1000)}`;

    const lineItems: LineItem[] = items.map((item, idx) => {
      const qty = Math.max(1, parseInt(String(item.quantity)) || 1);
      const unitCents = Math.round((parseFloat(item.unitPriceDollars) || 0) * 100);
      return {
        id: `li_${newId}_${idx + 1}`,
        description: item.description,
        quantity: qty,
        unitAmountCents: unitCents,
        totalAmountCents: qty * unitCents,
      };
    });

    const newInvoice: Invoice = {
      id: newId,
      displayNumber,
      businessId: customer?.businessId || 'biz_dodo_live',
      customerId: customer?.id || 'cust_default',
      customerName: customer?.name || 'Standard Client',
      customerEmail: customer?.email || 'client@example.com',
      state: 'open',
      currency: 'USD',
      totalAmountCents: totalCents,
      dueDate,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lineItems,
      attempts: [],
    };

    onCreateInvoice(newInvoice);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-md">
      <div className="relative w-full max-w-xl bg-slate-900/90 border border-white/15 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">Create New Invoice</h3>
            <p className="text-xs text-slate-400">
              State transitions to OPEN immediately &bull; Minor unit precision
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="py-4 space-y-4 overflow-y-auto max-h-[75vh]">
          {/* Customer Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Select Customer
            </label>
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="w-full bg-slate-800/80 border border-white/15 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                  {c.name} ({c.email})
                </option>
              ))}
            </select>
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Due Date
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full bg-slate-800/80 border border-white/15 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Line Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Line Items (Relational 3NF)
              </label>
              <button
                type="button"
                onClick={handleAddItem}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-2">
              {items.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-white/5 p-2.5 rounded-xl border border-white/5">
                  <input
                    type="text"
                    required
                    value={item.description}
                    onChange={(e) => {
                      const newItems = [...items];
                      newItems[idx].description = e.target.value;
                      setItems(newItems);
                    }}
                    placeholder="Description"
                    className="flex-1 bg-transparent border-none text-xs text-white placeholder-slate-500 focus:outline-none"
                  />
                  <input
                    type="number"
                    min="1"
                    required
                    value={item.quantity}
                    onChange={(e) => {
                      const newItems = [...items];
                      newItems[idx].quantity = parseInt(e.target.value) || 1;
                      setItems(newItems);
                    }}
                    placeholder="Qty"
                    className="w-14 bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-xs text-center text-white font-mono focus:outline-none"
                  />
                  <div className="flex items-center gap-1 text-slate-400 font-mono text-xs">
                    <span>$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={item.unitPriceDollars}
                      onChange={(e) => {
                        const newItems = [...items];
                        newItems[idx].unitPriceDollars = e.target.value;
                        setItems(newItems);
                      }}
                      placeholder="0.00"
                      className="w-20 bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-xs text-white font-mono focus:outline-none"
                    />
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(idx)}
                      className="p-1 text-slate-500 hover:text-rose-400 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Computed Summary */}
          <div className="p-4 bg-white/5 rounded-2xl border border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Calculator className="w-4 h-4 text-indigo-400" />
              <span>Calculated Total (Integer Cents):</span>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold font-mono text-white">
                {(totalCents / 100).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                {totalCents} cents
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white/10 hover:bg-white/15 text-slate-300 text-xs font-medium rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-500/20 transition-all cursor-pointer"
            >
              Create &amp; Open Invoice
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
