import React from 'react';
import { Zap, Plus } from 'lucide-react';

interface HeaderProps {
  onNewInvoice: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNewInvoice }) => {
  return (
    <header className="relative z-10 flex flex-wrap items-center justify-between gap-4 px-6 lg:px-8 py-4 bg-white/5 border-b border-white/10 backdrop-blur-xl">
      {/* Brand & Badge */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white">
          <Zap className="w-5 h-5 fill-white text-white" />
        </div>
        <div className="flex items-center">
          <span className="text-xl font-bold tracking-tight text-white">Dodo Payments</span>
          <span className="text-xs font-mono bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded ml-2.5 border border-indigo-500/30">
            Console
          </span>
        </div>
      </div>

      {/* Engine Status & API Key */}
      <div className="flex items-center flex-wrap gap-4 sm:gap-6">
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-400">API:</span>
          <span className="font-mono text-emerald-400">Online</span>
        </div>

        <div className="px-3.5 py-1.5 bg-white/10 rounded-full border border-white/10 text-xs font-medium flex items-center gap-2">
          <span className="opacity-60 uppercase tracking-widest text-[10px]">Key:</span>
          <span className="font-mono text-slate-200">sk_test_...89a2</span>
        </div>

        <button
          onClick={onNewInvoice}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium rounded-xl transition-all shadow-md shadow-indigo-500/25 active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Invoice</span>
        </button>
      </div>
    </header>
  );
};
