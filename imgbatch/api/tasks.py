# -*- coding: utf-8 -*-
"""Async task manager for batch operations.

Enforces single-concurrent-task semantics (matching the old Tkinter
TaskRunner) and bridges thread-to-async progress reporting via a
thread-safe ``queue.Queue`` consumed by the SSE endpoint.
"""

import asyncio
import queue
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from imgbatch.infra.threading import TaskState


@dataclass
class TaskRecord:
    """Runtime state for a single task."""

    id: str
    state: TaskState
    queue: "queue.Queue[dict]" = field(default_factory=queue.Queue)
    result: Optional[dict] = None
    error: Optional[str] = None
    done: bool = False
    thread: Optional[threading.Thread] = None

    def put(self, msg: dict) -> None:
        """Non-blocking put onto the thread-safe queue."""
        try:
            self.queue.put_nowait(msg)
        except queue.Full:
            pass


class TaskManager:
    """Singleton task manager — at most one running task at a time."""

    def __init__(self) -> None:
        self._current: Optional[TaskRecord] = None
        self._lock = threading.Lock()

    @property
    def current(self) -> Optional[TaskRecord]:
        return self._current

    def get(self, task_id: str) -> Optional[TaskRecord]:
        if self._current and self._current.id == task_id:
            return self._current
        return None

    async def start(
        self,
        fn: Callable,
        *args,
        **kwargs,
    ) -> str:
        """Start *fn* in a background thread.

        *fn* signature: ``fn(state, *args, on_progress=callback, **kwargs)``
        Returns the task_id.
        """
        with self._lock:
            if self._current and not self._current.done:
                raise RuntimeError("task_already_running")

            task_id = str(uuid.uuid4())
            state = TaskState()
            record = TaskRecord(id=task_id, state=state)
            self._current = record

        def on_progress(pct: float, msg: str) -> None:
            record.put({
                "type": "progress",
                "pct": pct,
                "message": msg,
            })

        def run_in_thread() -> None:
            try:
                result = fn(state, *args, on_progress=on_progress, **kwargs)
                record.result = result
                record.put({
                    "type": "done",
                    "status": "done",
                    "result": result,
                })
            except Exception as exc:
                record.error = str(exc)
                record.put({
                    "type": "done",
                    "status": "error",
                    "result": {"error": str(exc)},
                })
            finally:
                state.set_running(False)
                record.done = True

        state.set_running(True)
        thread = threading.Thread(target=run_in_thread, daemon=True)
        record.thread = thread
        thread.start()

        return task_id

    def cancel(self, task_id: str) -> bool:
        """Request cancellation for the given task."""
        with self._lock:
            if self._current and self._current.id == task_id and not self._current.done:
                self._current.state.cancel()
                return True
            return False


# Singleton
task_manager = TaskManager()
