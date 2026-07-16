# -*- coding: utf-8 -*-
"""Shared dependencies for API routes.

Singletons that bridge core business logic to the HTTP layer.
"""

from imgbatch.history import HistoryManager
from imgbatch.infra.settings import load_config, save_config

from .tasks import task_manager

# History is process-wide — one manager instance
_history_manager: HistoryManager | None = None


def get_task_manager():
    return task_manager


def get_history() -> HistoryManager:
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


def get_config() -> dict:
    return load_config()


def save_config_dict(config: dict) -> None:
    save_config(config)
