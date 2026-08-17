import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.engine.queue_engine import RedisQueueEngine
from app.engine.worker_pool import WorkerPool, active_workflow_runs

logger = logging.getLogger("taskforge.ws")
router = APIRouter()

active_connections: List[WebSocket] = []

@router.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"Dashboard client connected to telemetry stream. Active clients: {len(active_connections)}")

    try:
        while True:
            # Broadcast high-frequency telemetry snapshot every 300ms
            snapshot = {
                "type": "TELEMETRY_SNAPSHOT",
                "metrics": RedisQueueEngine.get_metrics_snapshot(),
                "workers": [w.to_dict() for w in WorkerPool.workers.values()],
                "active_runs": [run.model_dump() for run in list(active_workflow_runs.values())[-6:]],
                "dlq": [item.model_dump() for item in RedisQueueEngine.get_dlq_records()[:10]],
            }
            await websocket.send_text(json.dumps(snapshot))
            await asyncio.sleep(0.35)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info("Dashboard client disconnected.")
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
