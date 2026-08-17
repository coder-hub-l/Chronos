import React, { useState } from 'react';
import { useEngine } from '../../context/EngineContext';

export default function TriggerPanel() {
  const { handleTrigger } = useEngine();
  const [ecomVersion, setEcomVersion] = useState(1);

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-base">🚀</span>
          <h3 className="text-sm font-black uppercase tracking-wider text-white">
            Trigger Real-World DAG Pipelines
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Redis Sorted Set Orchestration
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Pipeline 1: E-Commerce (With Versioning Switcher) */}
        <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-indigo-500/40 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">🛒</span>
              {/* Temporal-style Version Switcher */}
              <div className="flex items-center gap-1 bg-slate-950 px-2 py-0.5 rounded border border-indigo-500/40">
                <span className="text-[9px] font-mono text-slate-400">VER:</span>
                <button
                  onClick={() => setEcomVersion(1)}
                  className={`text-[10px] font-mono font-black px-1.5 py-0.5 rounded ${
                    ecomVersion === 1 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  v1
                </button>
                <button
                  onClick={() => setEcomVersion(2)}
                  className={`text-[10px] font-mono font-black px-1.5 py-0.5 rounded ${
                    ecomVersion === 2 ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  v2
                </button>
              </div>
            </div>
            <h4 className="text-sm font-extrabold text-white">
              E-Commerce Fulfillment
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Inventory → [Payment + Fraud Check] → Invoice → Email {ecomVersion === 2 ? '→ 3PL Logistics' : ''}.
            </p>
          </div>
          <button
            onClick={() => handleTrigger('ecommerce_fulfillment', {}, ecomVersion)}
            className="mt-4 w-full py-2 bg-indigo-600/30 hover:bg-indigo-600 border border-indigo-500/40 text-indigo-300 hover:text-white rounded-xl text-xs font-mono font-bold transition-all flex items-center justify-center gap-1"
          >
            <span>Launch (v{ecomVersion})</span>
            <span>→</span>
          </button>
        </div>

        {/* Pipeline 2: Data ETL */}
        <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-cyan-500/40 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">📊</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40">
                4 STEPS
              </span>
            </div>
            <h4 className="text-sm font-extrabold text-white">
              Distributed Data ETL
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Extract DB Replica → Clean & Deduplicate → Transform Aggregates → Load Snowflake.
            </p>
          </div>
          <button
            onClick={() => handleTrigger('data_etl_pipeline', {}, 1)}
            className="mt-4 w-full py-2 bg-cyan-600/30 hover:bg-cyan-600 border border-cyan-500/40 text-cyan-300 hover:text-white rounded-xl text-xs font-mono font-bold transition-all flex items-center justify-center gap-1"
          >
            <span>Launch ETL</span>
            <span>→</span>
          </button>
        </div>

        {/* Pipeline 3: Media / AI Pipeline */}
        <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-purple-500/40 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">🤖</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-500/40">
                5 STEPS
              </span>
            </div>
            <h4 className="text-sm font-extrabold text-white">
              Media & AI Inference
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Download S3 → [Resize + ResNet Inference] → Upload Processed → Post Slack.
            </p>
          </div>
          <button
            onClick={() => handleTrigger('media_ai_pipeline', {}, 1)}
            className="mt-4 w-full py-2 bg-purple-600/30 hover:bg-purple-600 border border-purple-500/40 text-purple-300 hover:text-white rounded-xl text-xs font-mono font-bold transition-all flex items-center justify-center gap-1"
          >
            <span>Launch Pipeline</span>
            <span>→</span>
          </button>
        </div>

        {/* Pipeline 4: Chaos Exponential Retry Demo */}
        <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-amber-500/40 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">⚡</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/40">
                SELF-HEALING
              </span>
            </div>
            <h4 className="text-sm font-extrabold text-white">
              Chaos Retry & Backoff
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Injects transient glitch on Step 2. Watch Redis Delayed ZSET backoff & auto-recover on attempt 3.
            </p>
          </div>
          <button
            onClick={() => handleTrigger('chaos_recovery_demo', {}, 1)}
            className="mt-4 w-full py-2 bg-amber-600/30 hover:bg-amber-600 border border-amber-500/40 text-amber-300 hover:text-white rounded-xl text-xs font-mono font-bold transition-all flex items-center justify-center gap-1"
          >
            <span>Test Retry</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
