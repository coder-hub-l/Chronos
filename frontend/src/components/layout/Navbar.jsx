import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function Navbar() {
  const { wsConnected, metrics, setShowRedisGuide, handleFlush } = useEngine();

  return (
    <header className="w-full bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)]">
          <span className="text-white font-black text-lg tracking-tighter">⚡</span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-white font-black tracking-wider text-base uppercase">
              Chronos Engine
            </h1>
            <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono border border-indigo-500/30">
              v1.0 DISTRIBUTED
            </span>
          </div>
          <p className="text-slate-400 text-xs tracking-tight hidden sm:block">
            Asynchronous DAG Workflow Queue backed by Redis Sorted Sets
          </p>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Storage Mode Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg">
          <span className="text-[10px] text-slate-400 font-mono uppercase">Storage:</span>
          <span className="text-xs font-mono font-bold text-cyan-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            {metrics.is_real_redis ? 'Redis Server (6379)' : 'Redis Engine (Embedded)'}
          </span>
        </div>

        {/* Live Stream Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
          <span className="text-xs font-mono text-slate-300">
            {wsConnected ? 'LIVE STREAM' : 'CONNECTING...'}
          </span>
        </div>

        {/* Redis Guide */}
        <button
          onClick={() => setShowRedisGuide(true)}
          className="px-3 py-1.5 bg-red-950/40 hover:bg-red-900/60 border border-red-500/40 text-red-300 hover:text-white rounded-lg text-xs font-mono font-bold tracking-wider transition-colors flex items-center gap-1.5"
        >
          <span>🔥</span>
          <span className="hidden sm:inline">Why Redis? (Guide)</span>
        </button>

        {/* Flush */}
        <button
          onClick={handleFlush}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs font-mono font-semibold transition-colors"
          title="Flush all Redis queues"
        >
          Flush
        </button>
      </div>
    </header>
  );
}
