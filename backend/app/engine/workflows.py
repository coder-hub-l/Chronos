import time
import uuid
from typing import List, Dict, Any, Optional
from app.schemas.task import WorkflowDefinition, TaskDefinition, WorkflowRun, TaskExecutionRecord, TaskState
from app.engine.dag_engine import DAGEngine
from app.engine.queue_engine import RedisQueueEngine
from app.engine.worker_pool import active_workflow_runs

# Versioned Workflow Registry: Maps "workflow_id:version" -> WorkflowDefinition
VERSIONED_TEMPLATES: Dict[str, WorkflowDefinition] = {}

def register_workflow(definition: WorkflowDefinition):
    key = f"{definition.workflow_id}:v{definition.version}"
    VERSIONED_TEMPLATES[key] = definition

# --- 1. E-COMMERCE FULFILLMENT (v1 & v2 for Versioning Demo) ---

# Version 1 (Standard 5 steps)
register_workflow(WorkflowDefinition(
    workflow_id="ecommerce_fulfillment",
    version=1,
    name="E-Commerce Order Fulfillment (v1)",
    description="Reserve Inventory -> [Payment + Fraud Check] -> Invoice Generation -> Customer Email Dispatch.",
    tasks=[
        TaskDefinition(task_id="step_1_inventory", name="1. Reserve Warehouse Stock", handler="inventory_reserve", priority=9, dependencies=[]),
        TaskDefinition(task_id="step_2_fraud", name="2A. Fraud Risk Scoring", handler="fraud_check", priority=8, dependencies=["step_1_inventory"]),
        TaskDefinition(task_id="step_2_payment", name="2B. Process Stripe Payment", handler="payment_charge", priority=10, dependencies=["step_1_inventory"]),
        TaskDefinition(task_id="step_3_invoice", name="3. Generate PDF Invoice", handler="invoice_generate", priority=6, dependencies=["step_2_payment", "step_2_fraud"]),
        TaskDefinition(task_id="step_4_email", name="4. Dispatch Confirmation Email", handler="email_dispatch", priority=5, dependencies=["step_3_invoice"]),
    ]
))

# Version 2 (Enhanced with 3PL Logistics Dispatch step)
register_workflow(WorkflowDefinition(
    workflow_id="ecommerce_fulfillment",
    version=2,
    name="E-Commerce Order Fulfillment (v2 - with 3PL)",
    description="Adds Step 5 automated 3PL Logistics API dispatch. In-flight v1 runs stay pinned to v1.",
    tasks=[
        TaskDefinition(task_id="step_1_inventory", name="1. Reserve Warehouse Stock", handler="inventory_reserve", priority=9, dependencies=[]),
        TaskDefinition(task_id="step_2_fraud", name="2A. Fraud Risk Scoring", handler="fraud_check", priority=8, dependencies=["step_1_inventory"]),
        TaskDefinition(task_id="step_2_payment", name="2B. Process Stripe Payment", handler="payment_charge", priority=10, dependencies=["step_1_inventory"]),
        TaskDefinition(task_id="step_3_invoice", name="3. Generate PDF Invoice", handler="invoice_generate", priority=6, dependencies=["step_2_payment", "step_2_fraud"]),
        TaskDefinition(task_id="step_4_email", name="4. Dispatch Confirmation Email", handler="email_dispatch", priority=5, dependencies=["step_3_invoice"]),
        TaskDefinition(task_id="step_5_3pl", name="5. Automated 3PL Warehouse Routing", handler="s3_upload", priority=7, dependencies=["step_4_email"]),
    ]
))


# --- 2. DATA ETL PIPELINE ---

register_workflow(WorkflowDefinition(
    workflow_id="data_etl_pipeline",
    version=1,
    name="Distributed Data ETL Pipeline (v1)",
    description="Sequential data processing: Extract -> Clean -> Transform -> Load into Warehouse.",
    tasks=[
        TaskDefinition(task_id="etl_1_extract", name="1. Extract DB Replica Logs", handler="data_extract", priority=8, dependencies=[]),
        TaskDefinition(task_id="etl_2_clean", name="2. Clean Nulls & Deduplicate", handler="data_clean", priority=7, dependencies=["etl_1_extract"]),
        TaskDefinition(task_id="etl_3_transform", name="3. Compute Hourly Aggregations", handler="data_transform", priority=8, dependencies=["etl_2_clean"]),
        TaskDefinition(task_id="etl_4_load", name="4. Load Partitions to Snowflake", handler="data_load", priority=9, dependencies=["etl_3_transform"]),
    ]
))


# --- 3. MEDIA / AI PIPELINE ---

register_workflow(WorkflowDefinition(
    workflow_id="media_ai_pipeline",
    version=1,
    name="Media & AI Inference Pipeline (v1)",
    description="Download Image -> Resize Thumbnail -> Run Neural Inference -> Upload to S3 -> Notify Slack.",
    tasks=[
        TaskDefinition(task_id="ai_1_download", name="1. Ingest S3 Raw Image", handler="image_download", priority=8, dependencies=[]),
        TaskDefinition(task_id="ai_2_resize", name="2. Generate WebP Thumbnails", handler="image_resize", priority=7, dependencies=["ai_1_download"]),
        TaskDefinition(task_id="ai_3_inference", name="3. Execute ResNet Model Inference", handler="model_inference", priority=9, dependencies=["ai_1_download"]),
        TaskDefinition(task_id="ai_4_upload", name="4. Upload Processed Assets to S3", handler="s3_upload", priority=7, dependencies=["ai_2_resize", "ai_3_inference"]),
        TaskDefinition(task_id="ai_5_slack", name="5. Post Notification to Slack", handler="slack_notify", priority=4, dependencies=["ai_4_upload"]),
    ]
))


# --- 4. CHAOS SELF-HEALING DEMO ---

register_workflow(WorkflowDefinition(
    workflow_id="chaos_recovery_demo",
    version=1,
    name="Chaos Exponential Retry & Self-Healing (v1)",
    description="Step 2 injects transient gateway fault. Demonstrates Redis Delayed ZSET countdown and automatic retry recovery.",
    tasks=[
        TaskDefinition(task_id="chaos_1", name="1. Initial Request Validation", handler="inventory_reserve", priority=8, dependencies=[]),
        TaskDefinition(
            task_id="chaos_2_retry",
            name="2. Gateway Glitch (Auto-Heals on Attempt 3)",
            handler="payment_charge",
            payload={"fail_until_attempt": 2},
            priority=10,
            max_retries=3,
            retry_delay_base=2.0,
            dependencies=["chaos_1"]
        ),
        TaskDefinition(task_id="chaos_3_done", name="3. Final Workflow Resolution", handler="email_dispatch", priority=6, dependencies=["chaos_2_retry"]),
    ]
))


def trigger_workflow_run(workflow_id: str, version: int = 1, custom_payload: Dict[str, Any] = None) -> WorkflowRun:
    """Instantiates an in-flight workflow run pinned to a specific version definition."""
    key = f"{workflow_id}:v{version}"
    template = VERSIONED_TEMPLATES.get(key)
    if not template:
        # Fallback to default v1
        template = VERSIONED_TEMPLATES.get(f"{workflow_id}:v1")
        if not template:
            raise ValueError(f"Workflow template '{workflow_id}' version {version} not found.")

    DAGEngine.validate_dag(template.tasks)

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    now = time.time()

    tasks_dict: Dict[str, TaskExecutionRecord] = {}
    for t_def in template.tasks:
        payload = dict(t_def.payload)
        if custom_payload:
            payload.update(custom_payload)

        tasks_dict[t_def.task_id] = TaskExecutionRecord(
            task_id=t_def.task_id,
            workflow_run_id=run_id,
            name=t_def.name,
            handler=t_def.handler,
            state=TaskState.BLOCKED,
            priority=t_def.priority,
            max_retries=t_def.max_retries,
            retry_delay_base=t_def.retry_delay_base,
            dependencies=t_def.dependencies,
            payload=payload
        )

    run = WorkflowRun(
        run_id=run_id,
        workflow_id=template.workflow_id,
        workflow_version=template.version,
        name=template.name,
        status="RUNNING",
        created_at=now,
        started_at=now,
        tasks=tasks_dict
    )

    active_workflow_runs[run_id] = run

    # Enqueue root ready tasks
    ready_tasks = DAGEngine.get_ready_tasks(tasks_dict)
    for ready in ready_tasks:
        ready.state = TaskState.READY
        RedisQueueEngine.enqueue_task(ready)

    RedisQueueEngine.emit_event("WORKFLOW_STARTED", run.model_dump())
    return run
