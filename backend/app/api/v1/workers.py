from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.engine.worker_pool import WorkerPool

router = APIRouter()

@router.get("/")
def list_workers() -> List[Dict[str, Any]]:
    """List active workers, CPU/memory loads, and assigned jobs."""
    return [w.to_dict() for w in WorkerPool.workers.values()]

@router.post("/{worker_id}/kill")
def kill_worker(worker_id: str):
    """Simulate a worker crash (chaos injection) to demonstrate orphan task recovery."""
    if worker_id not in WorkerPool.workers:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    WorkerPool.kill_worker(worker_id)
    return {"status": "success", "message": f"Worker '{worker_id}' crashed."}

@router.post("/{worker_id}/revive")
def revive_worker(worker_id: str):
    """Revives a stopped worker."""
    if worker_id not in WorkerPool.workers:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    WorkerPool.revive_worker(worker_id)
    return {"status": "success", "message": f"Worker '{worker_id}' revived."}
