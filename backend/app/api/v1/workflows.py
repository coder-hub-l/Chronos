from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.schemas.task import WorkflowDefinition, WorkflowRun
from app.engine.workflows import VERSIONED_TEMPLATES, trigger_workflow_run
from app.engine.worker_pool import active_workflow_runs

router = APIRouter()

@router.get("/templates", response_model=List[WorkflowDefinition])
def list_templates():
    """List all versioned workflow templates."""
    return list(VERSIONED_TEMPLATES.values())

@router.post("/trigger/{workflow_id}", response_model=WorkflowRun)
def trigger_workflow(
    workflow_id: str,
    version: int = Query(default=1, ge=1),
    custom_payload: Dict[str, Any] = None
):
    """Trigger an execution run of a specific workflow version."""
    try:
        run = trigger_workflow_run(workflow_id, version=version, custom_payload=custom_payload or {})
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/runs", response_model=List[WorkflowRun])
def list_runs():
    """List all recent workflow runs."""
    return list(active_workflow_runs.values())

@router.get("/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: str):
    """Get the live DAG state and task records of a run."""
    run = active_workflow_runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Workflow run '{run_id}' not found.")
    return run
