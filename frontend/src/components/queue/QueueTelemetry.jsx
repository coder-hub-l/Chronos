import React from 'react';
import { useEngine } from '../../context/EngineContext';

export default function QueueTelemetry() {
  const { metrics } = useEngine();

  const cards = [
    {
      title: 'Priority Queue (Redis ZSET)',
      value: metrics.priority_queue_depth,
      sub: 'ZPOPMIN Ready Queue',
      color: 'text-cyan-400',
      border: 'border-cyan-500/30',
      bg: 'bg-cyan-950/20',
      icon: '⚡',
    },
    {
      title: 'Delayed Retries (Redis ZSET)',
      value: metrics.delayed_queue_depth,
      sub: 'Score = execute_at timestamp',
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-950/20',
      icon: '⏳',
    },
    {
      title: 'Active Leased Jobs',
      value: metrics.active_tasks_count,
      sub: 'Redis Hash (taskforge:active)',
      color: 'text-indigo-400',
      border: 'border-indigo-500/30',
      bg: 'bg-indigo-950/20',
      icon: '⚙️',
    },
    {
      title: 'Dead-Letter Queue (DLQ)',
      value: metrics.dlq_count,
      sub: 'Terminal failures for replay',
      color: 'text-rose-400',
      border: 'border-rose-500/30',
      bg: 'bg-rose-950/20',
      icon: '💀',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className={`p-4 rounded-2xl border ${card.border} ${card.bg} backdrop-blur-md shadow-lg flex flex-col justify-between`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-mono uppercase font-bold text-slate-400 tracking-wider">
              {card.title}
            </span>
            <span className="text-lg">{card.icon}</span>
          </div>
          <div className={`text-3xl font-mono font-black ${card.color} my-1`}>
            {card.value}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            {card.sub}
          </div>
        </div>
      ))}
    </div>
  );
}
