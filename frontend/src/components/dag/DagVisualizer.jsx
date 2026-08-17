import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function DagVisualizer() {
  const { selectedRun, activeRuns, setSelectedRunId } = useEngine();

  if (!selectedRun) {
    return (
      <div className="w-full bg-slate-900/60 border border-slate-800 rounded-3xl p-10 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-2xl bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-2xl mb-3 text-indigo-400">
          ⚡
        </div>
        <h3 className="text-base font-bold text-white uppercase tracking-wider">No Pipeline Execution Active</h3>
        <p className="text-slate-400 text-xs mt-1 max-w-md">
          Launch one of the pipelines below to observe real-time task leasing, Redis Sorted Set scheduling, and worker execution.
        </p>
      </div>
    );
  }

  const tasksList = Object.values(selectedRun.tasks || {});

  const stateStyles = {
    BLOCKED: { bg: 'bg-slate-950/60', border: 'border-slate-800', badge: 'bg-slate-800 text-slate-400', label: 'BLOCKED (WAITING)' },
    READY: { bg: 'bg-cyan-950/30', border: 'border-cyan-500/40', badge: 'bg-cyan-900/60 text-cyan-300', label: 'READY' },
    QUEUED: { bg: 'bg-blue-950/30', border: 'border-blue-500/50', badge: 'bg-blue-900/60 text-blue-300', label: 'IN REDIS ZSET' },
    DELAYED: { bg: 'bg-amber-950/30', border: 'border-amber-500/50', badge: 'bg-amber-900/60 text-amber-300', label: 'DELAYED RETRY' },
    RETRYING: { bg: 'bg-amber-950/40', border: 'border-amber-500 animate-pulse', badge: 'bg-amber-900 text-amber-200', label: 'BACKOFF RETRY' },
    RUNNING: { bg: 'bg-indigo-950/50', border: 'border-indigo-500 shadow-[0_0_25px_rgba(99,102,241,0.35)] animate-pulse', badge: 'bg-indigo-600 text-white', label: 'RUNNING (LEASED)' },
    COMPLETED: { bg: 'bg-emerald-950/30', border: 'border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.2)]', badge: 'bg-emerald-900/60 text-emerald-300', label: 'COMPLETED' },
    FAILED: { bg: 'bg-red-950/40', border: 'border-red-500/60 shadow-[0_0_25px_rgba(239,68,68,0.25)]', badge: 'bg-red-900 text-red-200', label: 'FAILED -> DLQ' },
    CANCELLED: { bg: 'bg-rose-950/20', border: 'border-rose-900/40', badge: 'bg-rose-950 text-rose-400', label: 'CANCELLED' },
  };

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-xl">
      {/* Workflow Header & Run Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            <h2 className="text-base font-black text-white uppercase tracking-wider">
              {selectedRun.name}
            </h2>
            {/* Version Badge */}
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-500/40">
              v{selectedRun.workflow_version || 1}
            </span>
            <span className={`text-[10px] font-mono font-black px-2 py-0.5 rounded-full uppercase ${
              selectedRun.status === 'COMPLETED' ? 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-300' :
              selectedRun.status === 'RUNNING' ? 'bg-indigo-950/80 border border-indigo-500/40 text-indigo-300 animate-pulse' :
              'bg-red-950/80 border border-red-500/40 text-red-300'
            }`}>
              {selectedRun.status}
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Run ID: <span className="text-indigo-400">{selectedRun.run_id}</span> • Duration: {selectedRun.duration_ms ? `${selectedRun.duration_ms}ms` : 'In Flight...'}
          </p>
        </div>

        {/* Run Selector Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto max-w-full pb-1">
          <span className="text-[11px] font-mono text-slate-500 uppercase mr-1">History:</span>
          {activeRuns.slice(-6).map((r) => (
            <button
              key={r.run_id}
              onClick={() => setSelectedRunId(r.run_id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                r.run_id === selectedRun.run_id
                  ? 'bg-indigo-600 text-white font-bold shadow-md'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {r.run_id.slice(-6)} (v{r.workflow_version || 1})
            </button>
          ))}
        </div>
      </div>

      {/* DAG Visual Node Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tasksList.map((task) => {
          const style = stateStyles[task.state] || stateStyles.BLOCKED;

          return (
            <div
              key={task.task_id}
              className={`p-4 rounded-2xl border transition-all duration-300 flex flex-col justify-between ${style.bg} ${style.border}`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className={`text-[10px] font-mono font-black px-2 py-0.5 rounded-md ${style.badge}`}>
                    {style.label}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800">
                    P{task.priority}
                  </span>
                </div>

                <h4 className="text-sm font-extrabold text-white tracking-wide mb-1">
                  {task.name}
                </h4>
                <div className="text-[11px] font-mono text-indigo-400 mb-2">
                  handler: {task.handler}()
                </div>
              </div>

              {task.dependencies && task.dependencies.length > 0 && (
                <div className="text-[10px] font-mono text-slate-500 mb-2 bg-slate-950/50 p-1.5 rounded border border-slate-800/60">
                  <span>Upstream: </span>
                  <span className="text-slate-300">{task.dependencies.join(', ')}</span>
                </div>
              )}

              <div className="border-t border-slate-800/80 pt-2 mt-2 flex items-center justify-between text-[11px] font-mono">
                <span className="text-slate-400">
                  {task.worker_id ? `⚡ ${task.worker_id}` : 'Unassigned'}
                </span>
                <span className="font-bold text-emerald-400">
                  {task.duration_ms ? `${task.duration_ms}ms` : task.state === 'RUNNING' ? 'Running...' : '-'}
                </span>
              </div>

              {task.error && (
                <div className="mt-2 text-[10px] font-mono text-red-300 bg-red-950/60 border border-red-500/30 p-1.5 rounded break-all">
                  {task.error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
