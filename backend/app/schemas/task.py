from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class TaskState(str, Enum):
    BLOCKED = "BLOCKED"                   # Waiting on parent DAG dependencies
    READY = "READY"                       # All parents completed; ready to be queued
    QUEUED = "QUEUED"                     # In Redis Priority Queue / Sorted Set
    DELAYED = "DELAYED"                   # In Redis Delayed ZSET (waiting for retry backoff time)
    RUNNING = "RUNNING"                   # Leased by a worker
    COMPLETED = "COMPLETED"               # Finished successfully
    FAILED = "FAILED"                     # Failed permanently -> Dead-Letter Queue (DLQ)
    RETRYING = "RETRYING"                 # Transient failure -> scheduled for retry
    CANCELLED_UPSTREAM = "CANCELLED"      # Cancelled because an upstream parent task failed

class TaskDefinition(BaseModel):
    task_id: str
    name: str
    handler: str                          # e.g., "inventory_reserve", "payment_charge", "data_clean"
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10, description="1 (Lowest) to 10 (Highest)")
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_base: float = Field(default=2.0, description="Base seconds for exponential backoff")
    dependencies: List[str] = Field(default_factory=list, description="Parent task IDs that must finish first")

class TaskExecutionRecord(BaseModel):
    task_id: str
    workflow_run_id: str
    name: str
    handler: str
    state: TaskState = TaskState.BLOCKED
    priority: int = 5
    attempt: int = 0
    max_retries: int = 3
    retry_delay_base: float = 2.0
    dependencies: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    worker_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    enqueued_at: Optional[float] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    duration_ms: Optional[float] = None

class WorkflowDefinition(BaseModel):
    workflow_id: str                      # e.g., "ecommerce_fulfillment"
    version: int = 1                      # Temporal-style Workflow Versioning (v1, v2, v3)
    name: str
    description: str
    tasks: List[TaskDefinition]

class WorkflowRun(BaseModel):
    run_id: str
    workflow_id: str
    workflow_version: int = 1             # Pinned version snapshot that in-flight run executes against
    name: str
    status: str = "RUNNING"               # "RUNNING", "COMPLETED", "FAILED", "PARTIAL"
    created_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    duration_ms: Optional[float] = None
    tasks: Dict[str, TaskExecutionRecord] = Field(default_factory=dict)

class DLQRecord(BaseModel):
    task_id: str
    workflow_run_id: str
    name: str
    handler: str
    attempts_made: int
    error: str
    payload: Dict[str, Any]
    failed_at: float
