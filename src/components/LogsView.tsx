import React, { useState } from 'react';
import { SystemLog } from '../types';
import { Terminal, Shield, Filter } from 'lucide-react';

interface LogsViewProps {
  logs: SystemLog[];
  onClearLogs: () => void;
}

export const LogsView: React.FC<LogsViewProps> = ({ logs, onClearLogs }) => {
  const [filterLevel, setFilterLevel] = useState<string>('ALL');

  const filteredLogs = logs.filter((log) => {
    if (filterLevel === 'ALL') return true;
    return log.level === filterLevel;
  });

  return (
    <div className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col overflow-hidden min-h-[460px]">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
            <Terminal className="w-5 h-5 text-indigo-400" />
            <span>FastAPI Async Engine Logs</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Non-blocking Uvicorn event loop &bull; Database locks &bull; State validation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/10 text-xs font-mono">
            {['ALL', 'INFO', 'WARN', 'ERROR'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                  filterLevel === lvl
                    ? 'bg-indigo-500/30 text-white font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <button
            onClick={onClearLogs}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/15 rounded-xl text-xs text-slate-300 transition-colors cursor-pointer border border-white/10"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-black/40 border border-white/5 rounded-2xl p-4 font-mono text-xs space-y-2">
        {filteredLogs.map((l) => (
          <div key={l.id} className="flex items-start gap-2.5 hover:bg-white/5 p-1.5 rounded transition-colors">
            <span className="text-slate-500 text-[10px] shrink-0 mt-0.5">
              {new Date(l.timestamp).toLocaleTimeString()}
            </span>

            <span
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0 ${
                l.level === 'INFO'
                  ? 'bg-indigo-500/20 text-indigo-300'
                  : l.level === 'WARN'
                  ? 'bg-amber-500/20 text-amber-300'
                  : l.level === 'ERROR'
                  ? 'bg-rose-500/20 text-rose-300'
                  : 'bg-slate-500/20 text-slate-300'
              }`}
            >
              {l.level}
            </span>

            <span className="text-[10px] text-slate-400 font-semibold shrink-0">
              [{l.component}]
            </span>

            <span className="text-slate-200 break-all">{l.message}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-slate-500">
        <div>STREAM: STDOUT/STDERR CAPTURE</div>
        <div>WORKERS: 4 ASYNC EVENT LOOPS</div>
      </div>
    </div>
  );
};
