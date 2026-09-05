import React from 'react';
import { Customer } from '../types';
import { Users, Mail, DollarSign, FileText } from 'lucide-react';

interface CustomersViewProps {
  customers: Customer[];
}

export const CustomersView: React.FC<CustomersViewProps> = ({ customers }) => {
  const formatCents = (cents: number) => {
    return (cents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  return (
    <div className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col overflow-hidden min-h-[460px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            <span>Customers</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage business customers and billing profiles.
          </p>
        </div>
        <div className="px-3 py-1 bg-white/10 rounded-lg text-xs font-mono text-slate-300 border border-white/10">
          Total: {customers.length} Customers
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="text-[11px] uppercase tracking-widest text-slate-500 border-b border-white/5">
            <tr>
              <th className="pb-3 font-semibold">Customer</th>
              <th className="pb-3 font-semibold">Customer ID</th>
              <th className="pb-3 font-semibold">Invoices</th>
              <th className="pb-3 font-semibold">Total Paid</th>
              <th className="pb-3 font-semibold">Created</th>
            </tr>
          </thead>
          <tbody className="text-sm divide-y divide-white/5">
            {customers.map((c) => (
              <tr key={c.id} className="group hover:bg-white/[0.03] transition-colors">
                <td className="py-4 pr-4">
                  <div className="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                    {c.name}
                  </div>
                  <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                    <Mail className="w-3 h-3 opacity-60" />
                    <span className="font-mono">{c.email}</span>
                  </div>
                </td>

                <td className="py-4 pr-4 font-mono text-xs text-slate-400">
                  {c.id}
                </td>

                <td className="py-4 pr-4 font-mono text-xs text-slate-200">
                  <div className="flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{c.invoiceCount} invoices</span>
                  </div>
                </td>

                <td className="py-4 pr-4 font-mono font-medium text-slate-100">
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{formatCents(c.totalSpentCents)}</span>
                  </div>
                </td>

                <td className="py-4 text-xs font-mono text-slate-400">
                  {new Date(c.createdAt).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-slate-500">
        <div>Registry Status: Active</div>
        <div>Scope: Tenant Account</div>
      </div>
    </div>
  );
};
