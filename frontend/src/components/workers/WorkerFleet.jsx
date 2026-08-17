import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function WorkerFleet() {
  const { workers, handleKillWorker, handleReviveWorker } = useEngine();

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-base">🤖</span>
          <h3 className="text-sm font-black uppercase tracking-wider text-white">
            Distributed Worker Fleet & Heartbeats
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Cluster Size: <span className="text-emerald-400 font-bold">{workers.length} Nodes</span>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {workers.map((worker) => (
          <div
            key={worker.worker_id}
            className={`p-4 rounded-2xl border transition-all ${
              !worker.is_running || !worker.is_healthy
                ? 'bg-red-950/20 border-red-500/40 shadow-[0_0_20px_rgba(239,68,68,0.15)]'
                : worker.current_task_id
                ? 'bg-indigo-950/25 border-indigo-500/40 shadow-[0_0_20px_rgba(99,102,241,0.15)]'
                : 'bg-slate-950/60 border-slate-800'
            }`}
          >
            {/* Top Badge */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  worker.is_running && worker.is_healthy ? 'bg-emerald-400 animate-ping' : 'bg-red-500'
                }`} />
                <span className="text-xs font-mono font-bold text-white">
                  {worker.worker_id}
                </span>
              </div>
              <span className={`text-[10px] font-mono font-black px-1.5 py-0.5 rounded ${
                worker.is_running && worker.is_healthy ? 'bg-emerald-950 text-emerald-300' : 'bg-red-950 text-red-300'
              }`}>
                {worker.is_running && worker.is_healthy ? 'HEALTHY' : 'CRASHED'}
              </span>
            </div>

            {/* Current Lease */}
            <div className="text-[11px] font-mono text-slate-400 mb-3 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              <span className="text-[9px] uppercase font-bold text-slate-500 block">Current Lease:</span>
              <span className={worker.current_task_id ? 'text-indigo-300 font-bold truncate block' : 'text-slate-600 italic block'}>
                {worker.current_task_id ? `⚡ ${worker.current_task_id.split(':').pop()}` : 'Idle (Waiting)'}
              </span>
            </div>

            {/* Live CPU & Memory Load Gauges */}
            <div className="space-y-2 text-[10px] font-mono mb-3">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>CPU Load:</span>
                  <span className="font-bold text-cyan-300">{worker.cpu_load || 0}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, worker.cpu_load || 0)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>RAM Usage:</span>
                  <span className="font-bold text-purple-300">{worker.memory_mb || 0} MB</span>
                </div>
                <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, ((worker.memory_mb || 0) / 512) * 100)}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800/60">
                <span>Jobs (OK / Fail):</span>
                <span className="text-emerald-400 font-bold">
                  {worker.tasks_processed} <span className="text-slate-600">/</span> <span className="text-red-400">{worker.tasks_failed}</span>
                </span>
              </div>
            </div>

            {/* Chaos Crash / Revive Button */}
            {worker.is_running && worker.is_healthy ? (
              <button
                onClick={() => handleKillWorker(worker.worker_id)}
                className="w-full py-1.5 bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-300 hover:text-white rounded-lg text-[10px] font-mono font-bold uppercase transition-colors cursor-pointer"
              >
                💥 Crash Worker (Chaos)
              </button>
            ) : (
              <button
                onClick={() => handleReviveWorker(worker.worker_id)}
                className="w-full py-1.5 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-300 hover:text-white rounded-lg text-[10px] font-mono font-bold uppercase transition-colors cursor-pointer"
              >
                🔄 Revive Worker
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
