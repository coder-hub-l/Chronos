import logging
from typing import Dict, List, Set, Tuple
from app.schemas.task import TaskDefinition, TaskState, TaskExecutionRecord

logger = logging.getLogger("taskforge.dag")

class DAGCycleError(Exception):
    """Raised when a circular dependency cycle is detected in the workflow DAG."""
    pass

class DAGEngine:
    @staticmethod
    def validate_dag(tasks: List[TaskDefinition]) -> bool:
        """
        Validates the DAG using Kahn's Algorithm (Topological Sort).
        Ensures there are no cycles and all referenced dependencies exist.
        """
        task_ids = {t.task_id for t in tasks}
        in_degree: Dict[str, int] = {t.task_id: 0 for t in tasks}
        adj_list: Dict[str, List[str]] = {t.task_id: [] for t in tasks}

        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task '{task.task_id}' references non-existent parent dependency '{dep}'.")
                adj_list[dep].append(task.task_id)
                in_degree[task.task_id] += 1

        # Kahn's Algorithm: Queue of nodes with 0 incoming dependencies
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(tasks):
            raise DAGCycleError("Circular dependency cycle detected in the workflow DAG definition.")
        
        return True

    @staticmethod
    def get_ready_tasks(tasks: Dict[str, TaskExecutionRecord]) -> List[TaskExecutionRecord]:
        """
        Finds all tasks currently in BLOCKED state whose parent dependencies
        have ALL reached the COMPLETED state.
        """
        ready_tasks = []
        for task_id, task in tasks.items():
            if task.state == TaskState.BLOCKED:
                all_parents_done = True
                for dep_id in task.dependencies:
                    parent = tasks.get(dep_id)
                    if not parent or parent.state != TaskState.COMPLETED:
                        all_parents_done = False
                        break
                
                if all_parents_done:
                    ready_tasks.append(task)
        
        return ready_tasks

    @staticmethod
    def cascade_cancellations(failed_task_id: str, tasks: Dict[str, TaskExecutionRecord]) -> List[str]:
        """
        When an upstream task fails permanently, recursively cancels all downstream
        dependent child tasks, marking them as CANCELLED_UPSTREAM.
        """
        # Build children adjacency list
        children_map: Dict[str, List[str]] = {tid: [] for tid in tasks}
        for tid, t in tasks.items():
            for dep in t.dependencies:
                if dep in children_map:
                    children_map[dep].append(tid)

        cancelled_ids = []
        queue = list(children_map.get(failed_task_id, []))

        while queue:
            curr_id = queue.pop(0)
            curr_task = tasks.get(curr_id)
            if curr_task and curr_task.state in (TaskState.BLOCKED, TaskState.READY, TaskState.QUEUED):
                curr_task.state = TaskState.CANCELLED_UPSTREAM
                curr_task.error = f"Cancelled due to upstream parent '{failed_task_id}' failure."
                cancelled_ids.append(curr_id)
                # Propagate to its children
                queue.extend(children_map.get(curr_id, []))

        return cancelled_ids
