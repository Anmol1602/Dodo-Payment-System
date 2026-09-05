import React from 'react';
import { FileText, Users, Webhook, Terminal } from 'lucide-react';

export type NavTab = 'invoices' | 'customers' | 'webhooks' | 'logs';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
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

      {/* Account Info */}
      <div className="mt-auto p-4 bg-white/5 border border-white/10 rounded-2xl">
        <div className="text-xs font-medium text-white mb-0.5">Dodo Live Tenant</div>
        <div className="text-[11px] font-mono text-slate-400">biz_dodo_live</div>
      </div>
    </aside>
  );
};
