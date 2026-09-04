import React from 'react';
import { FileText, Users, Webhook, Terminal, Info } from 'lucide-react';

export type NavTab = 'invoices' | 'customers' | 'webhooks' | 'logs';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  openAiUsageModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, openAiUsageModal }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    {
      id: 'invoices',
      label: 'Invoices',
      icon: <FileText className="w-5 h-5" />,
    },
    {
      id: 'customers',
      label: 'Customers',
      icon: <Users className="w-5 h-5" />,
    },
    {
      id: 'webhooks',
      label: 'Webhooks',
      icon: <Webhook className="w-5 h-5" />,
    },
    {
      id: 'logs',
      label: 'Logs',
      icon: <Terminal className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="col-span-12 lg:col-span-3 flex flex-col gap-4">
      {/* Navigation list */}
      <nav className="flex flex-col gap-1.5">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full px-4 py-3 rounded-xl font-medium flex items-center gap-3 transition-all cursor-pointer text-left ${
                isActive
                  ? 'bg-indigo-500/20 border border-indigo-500/30 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* AI_USAGE disclosure callout */}
      <div
        onClick={openAiUsageModal}
        className="mt-auto p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl hover:bg-amber-500/15 transition-all cursor-pointer group"
      >
        <div className="flex items-center gap-2 mb-2">
          <Info className="w-4 h-4 text-amber-500 shrink-0" />
          <span className="text-xs font-bold text-amber-500 uppercase tracking-widest">
            Required: AI_USAGE.md
          </span>
        </div>
        <p className="text-[11px] text-amber-200/70 leading-relaxed italic group-hover:text-amber-200/90 transition-colors">
          &ldquo;Claude corrected my DB schema normalization for Invoice line items to ensure client-supplied totals are never trusted.&rdquo;
        </p>
        <div className="mt-2.5 text-[10px] text-amber-400 font-mono flex items-center justify-between opacity-80 group-hover:opacity-100">
          <span>View 3 Independent Architectural Decisions</span>
          <span>&rarr;</span>
        </div>
      </div>
    </aside>
  );
};
