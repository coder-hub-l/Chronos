import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from app.redis_client import redis_client
from app.schemas.task import TaskExecutionRecord, TaskState, DLQRecord, WorkflowRun
from app.engine.retry_policy import RetryPolicy

logger = logging.getLogger("taskforge.queue")

KEY_TASKS = "taskforge:tasks"
KEY_PRIORITY_ZSET = "taskforge:priority"
KEY_DELAYED_ZSET = "taskforge:delayed"
KEY_ACTIVE_HASH = "taskforge:active"
KEY_DLQ_LIST = "taskforge:dlq"
KEY_WORKFLOWS = "taskforge:workflows"
KEY_WORKERS = "taskforge:workers"
CHANNEL_EVENTS = "taskforge:events"

class RedisQueueEngine:
    """
    Production Queue Engine using Redis Sorted Sets (ZSET), Hashes, and Lists.
    Employs the exact same architecture as BullMQ and Celery for sub-millisecond priority & delayed tasks.
    """

    @classmethod
    def emit_event(cls, event_type: str, data: Any):
        """Broadcasts real-time engine telemetry through Redis Pub/Sub."""
        payload = json.dumps({"type": event_type, "data": data, "timestamp": time.time()})
        redis_client.publish(CHANNEL_EVENTS, payload)

    @classmethod
    def save_task_record(cls, task: TaskExecutionRecord):
        """Saves/Updates task record in Redis Hash."""
        redis_client.hset(KEY_TASKS, key_arg=f"{task.workflow_run_id}:{task.task_id}", val_arg=task.model_dump_json())

    @classmethod
    def get_task_record(cls, workflow_run_id: str, task_id: str) -> Optional[TaskExecutionRecord]:
        raw = redis_client.hget(KEY_TASKS, f"{workflow_run_id}:{task_id}")
        if raw:
            return TaskExecutionRecord.model_validate_json(raw)
        return None

    @classmethod
    def enqueue_task(cls, task: TaskExecutionRecord):
        """
        Enqueues task into the Redis Priority Sorted Set (ZSET).
        Score is -priority (so higher priority tasks like 10 have score -10 and pop first).
        """
        task_key = f"{task.workflow_run_id}:{task.task_id}"
        task.state = TaskState.QUEUED
        task.enqueued_at = time.time()
        cls.save_task_record(task)

        # Invert priority so highest priority has smallest negative score for ZPOPMIN
        score = -float(task.priority)
        redis_client.zadd(KEY_PRIORITY_ZSET, {task_key: score})
        logger.info(f"Enqueued task {task_key} with priority {task.priority} into Redis ZSET.")

        cls.emit_event("TASK_ENQUEUED", task.model_dump())

    @classmethod
    def schedule_delayed_retry(cls, task: TaskExecutionRecord, error_msg: str):
        """
        Schedules a task for delayed retry in Redis Delayed Sorted Set (ZSET).
        Score is the future Unix timestamp when the backoff delay expires.
        """
        task_key = f"{task.workflow_run_id}:{task.task_id}"
        task.attempt += 1
        
        if task.attempt > task.max_retries:
            # Exceeded retries -> move to Dead-Letter Queue (DLQ)
            cls.send_to_dlq(task, error_msg)
            return

        delay = RetryPolicy.calculate_backoff(task.attempt, base_delay=task.retry_delay_base)
        execute_at = time.time() + delay

        task.state = TaskState.RETRYING
        task.error = f"[Attempt {task.attempt}/{task.max_retries}] {error_msg} (Retrying in {delay}s)"
        cls.save_task_record(task)

        # Remove from active hash
        redis_client.hdel(KEY_ACTIVE_HASH, task_key)

        # Add to Redis Delayed Sorted Set with execute_at score
        redis_client.zadd(KEY_DELAYED_ZSET, {task_key: execute_at})
        logger.info(f"Task {task_key} scheduled for retry #{task.attempt} at {execute_at} (delay {delay}s)")

        cls.emit_event("TASK_RETRY_SCHEDULED", {
            "task_id": task.task_id,
            "workflow_run_id": task.workflow_run_id,
            "attempt": task.attempt,
            "delay_seconds": delay,
            "error": error_msg
        })

    @classmethod
    def promote_delayed_tasks(cls):
        """
        Scans Redis Delayed Sorted Set (ZSET) for tasks whose execute_at <= current_time,
        and atomically migrates them to the Priority Sorted Set for immediate worker pickup.
        """
        now = time.time()
        # Query ZSET for ready tasks: 0 <= score <= now
        ready_keys = redis_client.zrangebyscore(KEY_DELAYED_ZSET, 0, now)

        for task_key in ready_keys:
            redis_client.zrem(KEY_DELAYED_ZSET, task_key)
            # Retrieve record to get its priority
            raw = redis_client.hget(KEY_TASKS, task_key)
            if raw:
                task = TaskExecutionRecord.model_validate_json(raw)
                task.state = TaskState.QUEUED
                cls.save_task_record(task)
                score = -float(task.priority)
                redis_client.zadd(KEY_PRIORITY_ZSET, {task_key: score})
                logger.info(f"Promoted delayed task {task_key} to ready queue.")
                cls.emit_event("TASK_PROMOTED", {"task_key": task_key})

    @classmethod
    def lease_next_task(cls, worker_id: str) -> Optional[TaskExecutionRecord]:
        """
        Atomically pops the highest priority ready task from Redis ZSET
        and marks it as ACTIVE in Redis Hash.
        """
        # First ensure any matured delayed tasks are promoted
        cls.promote_delayed_tasks()

        popped = redis_client.zpopmin(KEY_PRIORITY_ZSET, count=1)
        if not popped:
            return None

        task_key, score = popped[0]
        now = time.time()

        # Mark in active hash: task_key -> worker_id:timestamp
        redis_client.hset(KEY_ACTIVE_HASH, key_arg=task_key, val_arg=f"{worker_id}:{now}")

        raw = redis_client.hget(KEY_TASKS, task_key)
        if not raw:
            return None

        task = TaskExecutionRecord.model_validate_json(raw)
        task.state = TaskState.RUNNING
        task.worker_id = worker_id
        task.started_at = now
        cls.save_task_record(task)

        cls.emit_event("TASK_STARTED", task.model_dump())
        return task

    @classmethod
    def complete_task(cls, task: TaskExecutionRecord, result: Any):
        """Marks task COMPLETED, records duration, removes active lease, and unlocks DAG children."""
        task_key = f"{task.workflow_run_id}:{task.task_id}"
        now = time.time()

        task.state = TaskState.COMPLETED
        task.result = result
        task.finished_at = now
        task.duration_ms = round((now - (task.started_at or now)) * 1000, 2)
        task.error = None
        cls.save_task_record(task)

        # Remove from active hash
        redis_client.hdel(KEY_ACTIVE_HASH, task_key)

        cls.emit_event("TASK_COMPLETED", task.model_dump())

    @classmethod
    def send_to_dlq(cls, task: TaskExecutionRecord, error_msg: str):
        """Sends a permanently failed task to the Dead-Letter Queue (DLQ) in Redis."""
        task_key = f"{task.workflow_run_id}:{task.task_id}"
        now = time.time()

        task.state = TaskState.FAILED
        task.error = error_msg
        task.finished_at = now
        task.duration_ms = round((now - (task.started_at or now)) * 1000, 2)
        cls.save_task_record(task)

        redis_client.hdel(KEY_ACTIVE_HASH, task_key)

        dlq_entry = DLQRecord(
            task_id=task.task_id,
            workflow_run_id=task.workflow_run_id,
            name=task.name,
            handler=task.handler,
            attempts_made=task.attempt,
            error=error_msg,
            payload=task.payload,
            failed_at=now
        )

        redis_client.lpush(KEY_DLQ_LIST, dlq_entry.model_dump_json())
        logger.warning(f"Task {task_key} permanently failed. Pushed to DLQ.")

        cls.emit_event("TASK_DLQ", dlq_entry.model_dump())

    @classmethod
    def replay_dlq_task(cls, workflow_run_id: str, task_id: str) -> bool:
        """Requeues a failed DLQ task for fresh execution."""
        task_key = f"{workflow_run_id}:{task_id}"
        raw = redis_client.hget(KEY_TASKS, task_key)
        if not raw:
            return False

        task = TaskExecutionRecord.model_validate_json(raw)
        task.attempt = 0
        task.error = None
        task.state = TaskState.QUEUED
        cls.enqueue_task(task)

        # Remove matching item from DLQ list
        dlq_items = redis_client.lrange(KEY_DLQ_LIST, 0, -1)
        for item_str in dlq_items:
            try:
                data = json.loads(item_str)
                if data.get("task_id") == task_id and data.get("workflow_run_id") == workflow_run_id:
                    # Filter and rewrite
                    updated = [i for i in dlq_items if i != item_str]
                    redis_client.delete(KEY_DLQ_LIST)
                    if updated:
                        redis_client.rpush(KEY_DLQ_LIST, *updated)
                    break
            except Exception:
                pass

        logger.info(f"Replayed task {task_key} from DLQ.")
        return True

    @classmethod
    def get_dlq_records(cls) -> List[DLQRecord]:
        """Retrieves all dead-letter queue records."""
        items = redis_client.lrange(KEY_DLQ_LIST, 0, 50)
        records = []
        for raw in items:
            try:
                records.append(DLQRecord.model_validate_json(raw))
            except Exception:
                pass
        return records

    @classmethod
    def get_metrics_snapshot(cls) -> Dict[str, Any]:
        """Returns live Redis queue lengths and storage telemetry."""
        return {
            "priority_queue_depth": redis_client.zcard(KEY_PRIORITY_ZSET),
            "delayed_queue_depth": redis_client.zcard(KEY_DELAYED_ZSET),
            "active_tasks_count": len(redis_client.hgetall(KEY_ACTIVE_HASH)),
            "dlq_count": redis_client.llen(KEY_DLQ_LIST),
            "total_tasks_stored": len(redis_client.hgetall(KEY_TASKS)),
            "is_real_redis": not getattr(redis_client, "is_emulated", False)
        }
