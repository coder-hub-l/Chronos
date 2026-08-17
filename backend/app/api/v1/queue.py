from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.engine.queue_engine import RedisQueueEngine
from app.schemas.task import DLQRecord
from app.redis_client import redis_client

router = APIRouter()

@router.get("/metrics")
def get_queue_metrics():
    """Retrieve live Redis Sorted Set depths and active leases."""
    return RedisQueueEngine.get_metrics_snapshot()

@router.get("/dlq", response_model=List[DLQRecord])
def get_dlq_records():
    """List all failed tasks residing in the Dead-Letter Queue."""
    return RedisQueueEngine.get_dlq_records()

class ReplayRequest(BaseModel := type("ReplayRequest", (), {})):
    workflow_run_id: str
    task_id: str

@router.post("/dlq/replay")
def replay_dlq_task(req: Dict[str, str]):
    """Replays a failed task from the DLQ into the priority queue."""
    wf_id = req.get("workflow_run_id")
    tid = req.get("task_id")
    if not wf_id or not tid:
        raise HTTPException(status_code=400, detail="Missing workflow_run_id or task_id.")
    
    success = RedisQueueEngine.replay_dlq_task(wf_id, tid)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found in DLQ.")
    return {"status": "success", "message": f"Task '{tid}' re-enqueued for execution."}

@router.post("/flush")
def flush_queues():
    """Clear all Redis queue keys."""
    redis_client.flushdb()
    return {"status": "success", "message": "Redis queues flushed."}
