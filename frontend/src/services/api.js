const API_BASE = 'http://localhost:8001';

class ChronosApi {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || 'API request failed');
    }
    return response.json();
  }

  getTemplates() {
    return this.request('/api/v1/workflows/templates');
  }

  triggerWorkflow(workflowId, customPayload = {}, version = 1) {
    return this.request(`/api/v1/workflows/trigger/${workflowId}?version=${version}`, {
      method: 'POST',
      body: JSON.stringify(customPayload),
    });
  }

  getRuns() {
    return this.request('/api/v1/workflows/runs');
  }

  getMetrics() {
    return this.request('/api/v1/queue/metrics');
  }

  getDlq() {
    return this.request('/api/v1/queue/dlq');
  }

  replayDlq(workflowRunId, taskId) {
    return this.request('/api/v1/queue/dlq/replay', {
      method: 'POST',
      body: JSON.stringify({ workflow_run_id: workflowRunId, task_id: taskId }),
    });
  }

  flushQueue() {
    return this.request('/api/v1/queue/flush', { method: 'POST' });
  }

  getWorkers() {
    return this.request('/api/v1/workers/');
  }

  killWorker(workerId) {
    return this.request(`/api/v1/workers/${workerId}/kill`, { method: 'POST' });
  }

  reviveWorker(workerId) {
    return this.request(`/api/v1/workers/${workerId}/revive`, { method: 'POST' });
  }
}

export const api = new ChronosApi();
