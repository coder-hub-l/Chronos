import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function DlqInspector() {
  const { dlq, handleReplayDlq } = useEngine();

  if (!dlq || dlq.length === 0) return null;

  return (
    <div className="w-full bg-slate-900/80 border-2 border-rose-500/40 rounded-3xl p-6 shadow-[0_0_50px_rgba(244,63,94,0.15)] backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
          <h3 className="text-sm font-black uppercase tracking-wider text-rose-400">
            Dead-Letter Queue (DLQ) Inspector
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-500/30">
            {dlq.length} Failed Tasks
          </span>
        </div>
        <p className="text-[11px] font-mono text-slate-400">
          Terminal execution failures trapped for manual investigation and replay.
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
              <th className="p-3">Task ID</th>
              <th className="p-3">Handler</th>
              <th className="p-3">Attempts Made</th>
              <th className="p-3">Terminal Error Reason</th>
              <th className="p-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {dlq.map((item, idx) => (
              <tr key={idx} className="border-b border-slate-800/60 bg-slate-900/40 hover:bg-slate-800/30">
                <td className="p-3 font-bold text-white">
                  {item.task_id}
                  <div className="text-[9px] text-slate-500">{item.workflow_run_id}</div>
                </td>
                <td className="p-3 text-indigo-300">{item.handler}</td>
                <td className="p-3 text-amber-400 font-bold">{item.attempts_made} Retries</td>
                <td className="p-3 text-rose-300 max-w-xs truncate" title={item.error}>
                  {item.error}
                </td>
                <td className="p-3 text-right">
                  <button
                    onClick={() => handleReplayDlq(item.workflow_run_id, item.task_id)}
                    className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg text-[10px] uppercase transition-colors"
                  >
                    ↺ Replay Job
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
