import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function RedisGuideModal() {
  const { showRedisGuide, setShowRedisGuide } = useEngine();

  if (!showRedisGuide) return null;

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 z-50 animate-fadeIn">
      <div className="w-full max-w-4xl bg-slate-900 border-2 border-red-500/40 rounded-3xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto shadow-[0_0_80px_rgba(239,68,68,0.2)] relative text-left">
        <button
          onClick={() => setShowRedisGuide(false)}
          className="absolute top-6 right-6 text-slate-500 hover:text-white font-bold"
        >
          ✕
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🔥</span>
          <div>
            <h2 className="text-2xl font-black uppercase tracking-wider text-white">
              Why Redis Sorted Sets & The Mastery Curriculum
            </h2>
            <p className="text-xs font-mono text-red-400">
              Why BullMQ, Celery, & RQ use Redis Sorted Sets for Queues
            </p>
          </div>
        </div>

        {/* Section 1: The Core Explanation */}
        <div className="mt-6 space-y-4">
          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wide mb-1">
              1. The Score = Timestamp Trick for Delayed & Priority Queues
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Standard FIFO queues (Lists: `LPUSH`/`RPOP`) cannot handle delayed execution or priority sorting without scanning all elements. 
              <strong> Redis Sorted Sets (ZSET)</strong> store items ordered by an O(log N) 64-bit floating-point score:
            </p>
            <ul className="text-xs text-slate-400 mt-2 space-y-1 font-mono list-disc list-inside">
              <li><strong className="text-cyan-300">Delayed Queue:</strong> Set score = current_unix_timestamp + delay_seconds. Fetch ready tasks via ZRANGEBYSCORE queue:delayed 0 [current_time].</li>
              <li><strong className="text-cyan-300">Priority Queue:</strong> Set score = -priority (Priority 10 is score -10). Fetch highest priority via ZPOPMIN queue:priority 1.</li>
            </ul>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wide mb-1">
              2. Atomic Pop & Lease with Single-Threaded Lua Scripts
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              When 50 workers compete for jobs simultaneously, standard SQL databases suffer from row-lock contention. Redis executes commands and Lua scripts atomically in a single event loop, guaranteeing <strong>zero race conditions</strong> and eliminating distributed locking overhead.
            </p>
          </div>
        </div>

        {/* Section 2: Curated Problem-Based Curriculum */}
        <h3 className="text-lg font-black text-white uppercase tracking-wider mt-8 mb-4 flex items-center gap-2">
          <span>📚</span>
          <span>Curated Redis Problem Module (Easy to Extreme Hard)</span>
        </h3>

        <div className="space-y-3">
          {/* Level 1 */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 uppercase font-mono">Level 1: Foundations (Easy)</span>
              <span className="text-[10px] font-mono text-slate-500">Strings, TTL, & Hashes</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              • <strong>Problem 1.1:</strong> Build a Rate Limiter using INCR and EXPIRE (Fixed Window).<br />
              • <strong>Problem 1.2:</strong> Implement User Session storage using HSET and HEXPIRE.
            </p>
          </div>

          {/* Level 2 */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400 uppercase font-mono">Level 2: Queueing & Leaderboards (Medium)</span>
              <span className="text-[10px] font-mono text-slate-500">Sorted Sets & Reliable Lists</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              • <strong>Problem 2.1:</strong> Build a Real-Time Gaming Leaderboard with ZADD, ZINCRBY, and ZREVRANGE.<br />
              • <strong>Problem 2.2:</strong> Implement a Reliable Message Queue using RPOPLPUSH (or LMOVE) to prevent message loss on worker crash.
            </p>
          </div>

          {/* Level 3 */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-400 uppercase font-mono">Level 3: Distributed State & Sliding Windows (Hard)</span>
              <span className="text-[10px] font-mono text-slate-500">Sliding Window Rate Limiters & Bitmaps</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              • <strong>Problem 3.1:</strong> Implement a Sliding Window Log Rate Limiter using ZREMRANGEBYSCORE and ZCARD.<br />
              • <strong>Problem 3.2:</strong> Track 100 Million Daily Active Users (DAU) using Redis BITCOUNT and BITOP with less than 12 MB RAM.
            </p>
          </div>

          {/* Level 4 */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-400 uppercase font-mono">Level 4: Atomicity & Streams (Very Hard)</span>
              <span className="text-[10px] font-mono text-slate-500">Lua Scripting & Consumer Groups</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              • <strong>Problem 4.1:</strong> Write an atomic Lua script for a Flash Sale inventory checkout preventing overselling.<br />
              • <strong>Problem 4.2:</strong> Build an Event-Driven Message Broker with Redis Streams (XADD, XREADGROUP, XACK, XPENDING).
            </p>
          </div>

          {/* Level 5 */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-red-400 uppercase font-mono">Level 5: Distributed Systems & Consensus (Extreme Hard)</span>
              <span className="text-[10px] font-mono text-slate-500">Redlock, Replication & Sharding</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              • <strong>Problem 5.1:</strong> Implement the <strong>Redlock Algorithm</strong> across 5 independent Redis master instances.<br />
              • <strong>Problem 5.2:</strong> Analyze Redis Sentinel automatic failover and Redis Cluster Hash Slot CRC16 sharding under network partition.
            </p>
          </div>
        </div>

        {/* Section 3: Recommended Learning Sites */}
        <div className="mt-6 p-4 bg-slate-950 border border-slate-800 rounded-2xl">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
            Top Official Learning Sites:
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300">
              🎓 <strong>Redis University:</strong> official free courses (RU101, RU204 Streams)
            </div>
            <div className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300">
              💻 <strong>try.redis.io:</strong> interactive browser REPL tutorial
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowRedisGuide(false)}
          className="w-full mt-6 py-3.5 bg-gradient-to-r from-red-600 to-indigo-600 hover:from-red-500 hover:to-indigo-500 text-white font-black uppercase tracking-wider rounded-xl transition-all cursor-pointer"
        >
          Close & Return to Dashboard
        </button>
      </div>
    </div>
  );
}
