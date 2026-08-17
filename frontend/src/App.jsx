import React from 'react';
import { EngineProvider } from './context/EngineContext';
import Navbar from './components/layout/Navbar';
import QueueTelemetry from './components/queue/QueueTelemetry';
import DagVisualizer from './components/dag/DagVisualizer';
import WorkerFleet from './components/workers/WorkerFleet';
import DlqInspector from './components/queue/DlqInspector';
import TriggerPanel from './components/controls/TriggerPanel';
import RedisGuideModal from './components/redis/RedisGuideModal';

function Dashboard() {
  return (
    <div className="min-h-screen bg-[#080c16] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Top Queue Telemetry Cards */}
        <QueueTelemetry />

        {/* Visual DAG Pipeline Graph */}
        <DagVisualizer />

        {/* Trigger Panel for Launching Pipelines */}
        <TriggerPanel />

        {/* Worker Fleet Telemetry & Chaos Controls */}
        <WorkerFleet />

        {/* Dead-Letter Queue (DLQ) Inspector */}
        <DlqInspector />
      </main>

      {/* Redis Mastery Curriculum Modal */}
      <RedisGuideModal />
    </div>
  );
}

export default function App() {
  return (
    <EngineProvider>
      <Dashboard />
    </EngineProvider>
  );
}
