#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Thread management with cancellation, progress, and ETA support.

Provides a cancellable task runner that replaces bare ``threading.Thread``
calls throughout the codebase.
"""


import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Optional

from .logger import get_logger


class TaskState:
    """Thread-safe task state flags."""

    def __init__(self):
        self._cancelled = threading.Event()
        self._running = False
        self._lock = threading.Lock()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> None:
        self._cancelled.set()

    def reset(self) -> None:
        self._cancelled.clear()

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def set_running(self, value: bool) -> None:
        with self._lock:
            self._running = value


class TaskRunner:
    """Single-worker task executor with cancellation support.

    Usage::

        runner = TaskRunner()
        runner.start(my_function, arg1, arg2,
                     on_progress=callback,
                     on_complete=callback,
                     on_error=callback)
        # Later:
        runner.cancel()
    """

    def __init__(self):
        self._state = TaskState()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Optional[Future] = None

    @property
    def is_running(self) -> bool:
        return self._state.running

    @property
    def is_cancelled(self) -> bool:
        return self._state.cancelled

    def start(
        self,
        func: Callable,
        *args,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs,
    ) -> bool:
        """Start a task. Returns False if one is already running."""
        if self._state.running:
            return False

        self._state.reset()
        self._state.set_running(True)

        def _wrapper():
            try:
                result = func(
                    self._state,
                    *args,
                    on_progress=on_progress,
                    **kwargs,
                )
                if not self._state.cancelled and on_complete:
                    on_complete(result)
            except Exception as exc:
                get_logger().error("Task error: %s", exc, exc_info=True)
                if on_error:
                    on_error(exc)
            finally:
                self._state.set_running(False)

        self._future = self._executor.submit(_wrapper)
        return True

    def cancel(self) -> None:
        """Request cancellation. The running task must check ``state.cancelled``."""
        self._state.cancel()
        get_logger().info("Task cancellation requested")

    def wait(self, timeout: Optional[float] = None) -> None:
        if self._future is not None:
            self._future.result(timeout=timeout)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


def compute_eta(elapsed: float, done: int, total: int) -> Optional[float]:
    """Estimate remaining seconds based on current progress."""
    if done <= 0 or total <= 0 or done >= total:
        return None
    per_item = elapsed / done
    remaining = total - done
    return max(0.0, per_item * remaining)


class ProgressTracker:
    """Track progress with ETA computation."""

    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self._start_time = time.time()

    def advance(self, n: int = 1) -> None:
        self.done += n

    @property
    def fraction(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(1.0, self.done / self.total)

    @property
    def percent(self) -> float:
        return self.fraction * 100

    @property
    def elapsed(self) -> float:
        return time.time() - self._start_time

    @property
    def eta(self) -> Optional[float]:
        return compute_eta(self.elapsed, self.done, self.total)
