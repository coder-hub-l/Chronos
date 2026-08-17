import sys
sys.path.insert(0, '.')

import asyncio
import time
from app.engine.workflows import trigger_workflow_run
from app.engine.worker_pool import WorkerPool, active_workflow_runs
from app.engine.queue_engine import RedisQueueEngine
from app.schemas.task import TaskState

async def run_tests():
    print("=== CHRONOS ENGINE AUTOMATED VERIFICATION ===")
    
    # 1. Start worker pool
    WorkerPool.initialize(4)
    await WorkerPool.start()

    # 2. Trigger Ecommerce v1
    run_v1 = trigger_workflow_run("ecommerce_fulfillment", version=1)
    print(f"[Test 1] Triggered Workflow: {run_v1.name} (Version: {run_v1.workflow_version}, Run ID: {run_v1.run_id})")

    timeout = 10.0
    start = time.time()
    while time.time() - start < timeout:
        current_run = active_workflow_runs.get(run_v1.run_id)
        if current_run and current_run.status in ("COMPLETED", "COMPLETED_WITH_FAILURES"):
            break
        await asyncio.sleep(0.3)

    finished_v1 = active_workflow_runs.get(run_v1.run_id)
    print(f"[Test 1 Result] Status: {finished_v1.status}, Version Pinned: v{finished_v1.workflow_version}, Duration: {finished_v1.duration_ms}ms")
    assert finished_v1.status == "COMPLETED"
    assert len(finished_v1.tasks) == 5

    # 3. Trigger Ecommerce v2 (Workflow Versioning Test)
    run_v2 = trigger_workflow_run("ecommerce_fulfillment", version=2)
    print(f"\n[Test 2] Triggered Workflow: {run_v2.name} (Version: {run_v2.workflow_version}, Run ID: {run_v2.run_id})")
    start = time.time()
    while time.time() - start < timeout:
        current_v2 = active_workflow_runs.get(run_v2.run_id)
        if current_v2 and current_v2.status in ("COMPLETED", "COMPLETED_WITH_FAILURES"):
            break
        await asyncio.sleep(0.3)

    finished_v2 = active_workflow_runs.get(run_v2.run_id)
    print(f"[Test 2 Result] Status: {finished_v2.status}, Version Pinned: v{finished_v2.workflow_version}, Duration: {finished_v2.duration_ms}ms")
    assert finished_v2.status == "COMPLETED"
    assert len(finished_v2.tasks) == 6  # v2 has 6 tasks with 3PL step

    # 4. Trigger Chaos Transient Retry Test
    print("\n[Test 3] Triggering Chaos Transient Failure & Exponential Backoff...")
    chaos_run = trigger_workflow_run("chaos_recovery_demo", version=1)
    start = time.time()
    while time.time() - start < timeout:
        current_chaos = active_workflow_runs.get(chaos_run.run_id)
        if current_chaos and current_chaos.status in ("COMPLETED", "COMPLETED_WITH_FAILURES"):
            break
        await asyncio.sleep(0.3)

    finished_chaos = active_workflow_runs.get(chaos_run.run_id)
    print(f"[Test 3 Result] Chaos Workflow Status: {finished_chaos.status}")
    assert finished_chaos.status == "COMPLETED"

    await WorkerPool.stop()
    print("\n[PASS] ALL CHRONOS BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
