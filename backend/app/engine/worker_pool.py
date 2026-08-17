import asyncio
import time
import json
import random
import logging
from typing import Dict, List, Optional, Any
from app.redis_client import redis_client
from app.engine.queue_engine import RedisQueueEngine, KEY_ACTIVE_HASH, KEY_WORKERS
from app.engine.task_registry import TaskRegistry, TaskExecutionError
from app.engine.dag_engine import DAGEngine
from app.schemas.task import TaskState, TaskExecutionRecord, WorkflowRun

logger = logging.getLogger("chronos.workers")

active_workflow_runs: Dict[str, WorkflowRun] = {}

class Worker:
    def __init__(self, worker_id: str, name: str, concurrency: int = 1):
        self.worker_id = worker_id
        self.name = name
        self.concurrency = concurrency
        self.is_running = True
        self.current_task_id: Optional[str] = None
        self.tasks_processed = 0
        self.tasks_failed = 0
        self.last_heartbeat = time.time()
        self.cpu_load = 4
        self.memory_mb = 128

    def to_dict(self) -> Dict[str, Any]:
        # Dynamic telemetry: higher CPU/RAM when actively processing
        if self.is_running and self.current_task_id:
            self.cpu_load = random.randint(62, 89)
            self.memory_mb = random.randint(280, 420)
        elif self.is_running:
            self.cpu_load = random.randint(3, 12)
            self.memory_mb = random.randint(110, 140)
        else:
            self.cpu_load = 0
            self.memory_mb = 0

        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "is_running": self.is_running,
            "current_task_id": self.current_task_id,
            "tasks_processed": self.tasks_processed,
            "tasks_failed": self.tasks_failed,
            "cpu_load": self.cpu_load,
            "memory_mb": self.memory_mb,
            "last_heartbeat": self.last_heartbeat,
            "is_healthy": self.is_running and (time.time() - self.last_heartbeat < 10.0)
        }

class WorkerPool:
    workers: Dict[str, Worker] = {}
    _pool_task: Optional[asyncio.Task] = None
    _reaper_task: Optional[asyncio.Task] = None

    @classmethod
    def initialize(cls, num_workers: int = 4):
        cls.workers.clear()
        for i in range(1, num_workers + 1):
            w_id = f"worker_{i}"
            cls.workers[w_id] = Worker(
                worker_id=w_id,
                name=f"Worker Node #{i}"
            )

    @classmethod
    async def start(cls):
        if not cls.workers:
            cls.initialize(4)
        cls._pool_task = asyncio.create_task(cls._worker_loop())
        cls._reaper_task = asyncio.create_task(cls._reaper_loop())

    @classmethod
    async def stop(cls):
        if cls._pool_task:
            cls._pool_task.cancel()
        if cls._reaper_task:
            cls._reaper_task.cancel()

    @classmethod
    async def _worker_loop(cls):
        while True:
            try:
                for worker in cls.workers.values():
                    if worker.is_running and worker.current_task_id is None:
                        task = RedisQueueEngine.lease_next_task(worker.worker_id)
                        if task:
                            worker.current_task_id = f"{task.workflow_run_id}:{task.task_id}"
                            asyncio.create_task(cls._execute_task_async(worker, task))

                    if worker.is_running:
                        worker.last_heartbeat = time.time()
                        redis_client.hset(KEY_WORKERS, key_arg=worker.worker_id, val_arg=json.dumps(worker.to_dict()))

                await asyncio.sleep(0.12)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(0.5)

    @classmethod
    async def _execute_task_async(cls, worker: Worker, task: TaskExecutionRecord):
        task_key = f"{task.workflow_run_id}:{task.task_id}"
        run = active_workflow_runs.get(task.workflow_run_id)

        try:
            attempt = task.attempt + 1
            result = await asyncio.to_thread(TaskRegistry.execute, task.handler, task.payload, attempt)

            RedisQueueEngine.complete_task(task, result)
            worker.tasks_processed += 1
            worker.current_task_id = None

            if run and task.task_id in run.tasks:
                run.tasks[task.task_id] = task
                cls._advance_dag_workflow(run)

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Task {task_key} failed: {error_msg}")
            worker.tasks_failed += 1
            worker.current_task_id = None

            RedisQueueEngine.schedule_delayed_retry(task, error_msg)

            if run and task.task_id in run.tasks:
                run.tasks[task.task_id] = task
                if task.state == TaskState.FAILED:
                    DAGEngine.cascade_cancellations(task.task_id, run.tasks)
                    cls._check_workflow_completion(run)

    @classmethod
    def _advance_dag_workflow(cls, run: WorkflowRun):
        ready_tasks = DAGEngine.get_ready_tasks(run.tasks)
        for ready in ready_tasks:
            ready.state = TaskState.READY
            RedisQueueEngine.enqueue_task(ready)

        cls._check_workflow_completion(run)

    @classmethod
    def _check_workflow_completion(cls, run: WorkflowRun):
        all_terminal = True
        has_failure = False

        for t in run.tasks.values():
            if t.state not in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED_UPSTREAM):
                all_terminal = False
                break
            if t.state in (TaskState.FAILED, TaskState.CANCELLED_UPSTREAM):
                has_failure = True

        if all_terminal:
            now = time.time()
            run.finished_at = now
            run.duration_ms = round((now - (run.started_at or now)) * 1000, 2)
            run.status = "COMPLETED_WITH_FAILURES" if has_failure else "COMPLETED"
            RedisQueueEngine.emit_event("WORKFLOW_COMPLETED", run.model_dump())

    @classmethod
    async def _reaper_loop(cls):
        while True:
            try:
                now = time.time()
                active_leases = redis_client.hgetall(KEY_ACTIVE_HASH)

                for task_key, lease_info in active_leases.items():
                    try:
                        worker_id, leased_at_str = lease_info.split(":", 1)
                        worker = cls.workers.get(worker_id)

                        if not worker or not worker.is_running or (now - worker.last_heartbeat > 10.0):
                            parts = task_key.split(":", 1)
                            if len(parts) == 2:
                                wf_id, tid = parts
                                task = RedisQueueEngine.get_task_record(wf_id, tid)
                                if task:
                                    redis_client.hdel(KEY_ACTIVE_HASH, task_key)
                                    task.attempt += 1
                                    task.worker_id = None
                                    task.error = f"Auto-reassigned by Orphan Reaper after worker '{worker_id}' crashed."
                                    RedisQueueEngine.enqueue_task(task)

                                    RedisQueueEngine.emit_event("TASK_REASSIGNED_AFTER_WORKER_CRASH", {
                                        "task_id": tid,
                                        "workflow_run_id": wf_id,
                                        "crashed_worker": worker_id,
                                        "new_attempt": task.attempt
                                    })
                    except Exception as ex:
                        logger.error(f"Error in reaper lease check: {ex}")

                await asyncio.sleep(1.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reaper loop: {e}")
                await asyncio.sleep(1.5)

    @classmethod
    def kill_worker(cls, worker_id: str):
        if worker_id in cls.workers:
            cls.workers[worker_id].is_running = False
            cls.workers[worker_id].last_heartbeat = time.time() - 25.0
            RedisQueueEngine.emit_event("WORKER_CRASHED", {"worker_id": worker_id})

    @classmethod
    def revive_worker(cls, worker_id: str):
        if worker_id in cls.workers:
            cls.workers[worker_id].is_running = True
            cls.workers[worker_id].last_heartbeat = time.time()
            cls.workers[worker_id].current_task_id = None
            RedisQueueEngine.emit_event("WORKER_REVIVED", {"worker_id": worker_id})
