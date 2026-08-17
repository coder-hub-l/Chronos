# Chronos — Distributed Workflow Queue & DAG Execution Engine

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Redis](https://img.shields.io/badge/Redis-Sorted%20Sets-red?logo=redis)
![WebSockets](https://img.shields.io/badge/WebSockets-Live%20Dashboard-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

A production-grade **distributed asynchronous task queue and DAG-based workflow execution engine** backed by Redis Sorted Sets. Supports priority scheduling, DAG dependency resolution, fault-tolerant workers, and a real-time mission control dashboard.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Chronos Engine                        │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  FastAPI      │    │     Redis Sorted Sets         │  │
│  │  REST API     │───►│  Priority Queue (O(log N))    │  │
│  │  /api/v1/     │    │  Scheduled Delayed Tasks       │  │
│  └──────────────┘    └──────────────────────────────┘  │
│                                │                         │
│  ┌─────────────────────────────▼──────────────────────┐ │
│  │              DAG Execution Engine                    │ │
│  │   Kahn's Algorithm  •  Cycle Detection              │ │
│  │   Dynamic Dependency Gating  •  Multi-stage         │ │
│  └─────────────────────────────┬──────────────────────┘ │
│                                │                         │
│  ┌─────────────────────────────▼──────────────────────┐ │
│  │              Fault-Tolerant Worker Fleet             │ │
│  │   Heartbeat Monitor  •  Orphan-Task Reaper          │ │
│  │   Exponential Backoff  •  Dead-Letter Queue         │ │
│  └─────────────────────────────┬──────────────────────┘ │
│                                │                         │
│  ┌─────────────────────────────▼──────────────────────┐ │
│  │         Real-Time Mission Control Dashboard          │ │
│  │   React + WebSockets  •  Live DAG Status            │ │
│  │   Worker Health  •  Queue Depth Metrics             │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Features

| Feature | Details |
|---|---|
| **Priority Queue** | Redis Sorted Sets with O(log N) enqueue/dequeue |
| **Delayed Tasks** | Schedule tasks up to any future timestamp |
| **DAG Execution** | Topological sort via Kahn's algorithm |
| **Cycle Detection** | Rejects invalid dependency graphs at submission |
| **Fault Tolerance** | Heartbeat-based worker health, orphan-task reaper |
| **Dead-Letter Queue** | Terminal failures captured with one-click replay |
| **Retry Policy** | Configurable exponential backoff per task |
| **Live Dashboard** | React UI with WebSocket real-time updates |

## Quick Start

### Prerequisites
- Python 3.11+
- Redis (local or [Upstash](https://upstash.com) free tier)
- Node.js 18+ (for frontend dashboard)

```bash
git clone https://github.com/coder-hub-l/chronos.git
cd chronos/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env: set REDIS_URL=redis://localhost:6379

# Start the engine
uvicorn main:app --reload --port 8001
```

### Dashboard (Frontend)
```bash
cd ../frontend
npm install
npm run dev
# Open http://localhost:5173
```

### API Docs
Open `http://localhost:8001/docs` for interactive Swagger UI.

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/queue/enqueue` | POST | Submit a task to the priority queue |
| `/api/v1/queue/dequeue` | POST | Claim next available task (worker) |
| `/api/v1/workflows/trigger` | POST | Submit a full DAG workflow |
| `/api/v1/workers/` | GET | List active workers + heartbeats |
| `/api/v1/queue/dlq` | GET | View dead-letter queue |
| `/api/v1/queue/dlq/replay` | POST | Replay failed tasks |
| `/ws/stream` | WS | Live event stream for dashboard |
| `/health` | GET | Engine health + metrics snapshot |

## Environment Variables

```env
REDIS_URL=redis://localhost:6379
PROJECT_NAME=Chronos
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Redis (Sorted Sets), WebSockets
- **Frontend**: React, Vite, WebSocket client
- **Queue**: Redis Sorted Sets (score = priority + timestamp)
- **Scheduler**: DAG topological ordering (Kahn'\''s algorithm)
- **Resilience**: Heartbeat monitor + exponential backoff retries
