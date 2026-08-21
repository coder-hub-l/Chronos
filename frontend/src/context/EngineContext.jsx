import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

const EngineContext = createContext(null);

export function EngineProvider({ children }) {
  const [metrics, setMetrics] = useState({
    priority_queue_depth: 0,
    delayed_queue_depth: 0,
    active_tasks_count: 0,
    dlq_count: 0,
    total_tasks_stored: 0,
    is_real_redis: false,
  });

  const [workers, setWorkers] = useState([]);
  const [activeRuns, setActiveRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [dlq, setDlq] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [showRedisGuide, setShowRedisGuide] = useState(false);

  const wsRef = useRef(null);

  // Load Templates initially
  useEffect(() => {
    api.getTemplates().then(setTemplates).catch(console.error);
  }, []);

  // Connect to WebSocket Telemetry Stream
  useEffect(() => {
    let reconnectTimeout = null;

    const getWsUrl = () => {
      if (typeof window === 'undefined') return 'ws://localhost:8001/ws/telemetry';
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return `${protocol}//${window.location.hostname}:8001/ws/telemetry`;
      }
      return `${protocol}//${window.location.host}/ws/telemetry`;
    };

    const connectWs = () => {
      try {
        const ws = new WebSocket(getWsUrl());
        ws.onopen = () => {
          setWsConnected(true);
        };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'TELEMETRY_SNAPSHOT') {
              if (data.metrics) setMetrics(data.metrics);
              if (data.workers) setWorkers(data.workers);
              if (data.active_runs) {
                setActiveRuns(data.active_runs);
                if (!selectedRunId && data.active_runs.length > 0) {
                  setSelectedRunId(data.active_runs[data.active_runs.length - 1].run_id);
                }
              }
              if (data.dlq) setDlq(data.dlq);
            }
          } catch (e) {}
        };
        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWs, 2000);
        };
        ws.onerror = () => {
          ws.close();
        };
        wsRef.current = ws;
      } catch (e) {
        reconnectTimeout = setTimeout(connectWs, 2000);
      }
    };

    connectWs();

    const interval = setInterval(async () => {
      if (!wsConnected) {
        try {
          const m = await api.getMetrics();
          setMetrics(m);
          const w = await api.getWorkers();
          setWorkers(w);
          const r = await api.getRuns();
          setActiveRuns(r);
          const d = await api.getDlq();
          setDlq(d);
        } catch (e) {}
      }
    }, 2000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(interval);
    };
  }, [wsConnected, selectedRunId]);

  const selectedRun = activeRuns.find((r) => r.run_id === selectedRunId) || (activeRuns.length > 0 ? activeRuns[activeRuns.length - 1] : null);

  const handleTrigger = async (workflowId, customPayload = {}, version = 1) => {
    try {
      const run = await api.triggerWorkflow(workflowId, customPayload, version);
      setSelectedRunId(run.run_id);
    } catch (err) {
      alert(`Failed to trigger workflow: ${err.message}`);
    }
  };

  const handleReplayDlq = async (wfId, taskId) => {
    try {
      await api.replayDlq(wfId, taskId);
    } catch (err) {
      alert(`Replay failed: ${err.message}`);
    }
  };

  const handleKillWorker = async (workerId) => {
    try {
      await api.killWorker(workerId);
    } catch (err) {
      alert(`Kill failed: ${err.message}`);
    }
  };

  const handleReviveWorker = async (workerId) => {
    try {
      await api.reviveWorker(workerId);
    } catch (err) {
      alert(`Revive failed: ${err.message}`);
    }
  };

  const handleFlush = async () => {
    if (confirm('Flush all Redis queues and clear history?')) {
      await api.flushQueue();
      setActiveRuns([]);
      setDlq([]);
      setSelectedRunId(null);
    }
  };

  return (
    <EngineContext.Provider
      value={{
        metrics,
        workers,
        activeRuns,
        selectedRun,
        selectedRunId,
        setSelectedRunId,
        dlq,
        templates,
        wsConnected,
        showRedisGuide,
        setShowRedisGuide,
        handleTrigger,
        handleReplayDlq,
        handleKillWorker,
        handleReviveWorker,
        handleFlush,
      }}
    >
      {children}
    </EngineContext.Provider>
  );
}

export function useEngine() {
  const context = useContext(EngineContext);
  if (!context) {
    throw new Error('useEngine must be used within an EngineProvider');
  }
  return context;
}
