#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Operation history and undo system.

Records each operation so the user can undo it later.
History is persisted to ``~/.imgbatch/history.json``.
"""


import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .infra.logger import get_logger
from .infra.settings import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.json"
MAX_HISTORY = 20


class OperationRecord:
    """A single operation record for undo."""

    def __init__(
        self,
        op_type: str,
        timestamp: Optional[str] = None,
        folder: str = '',
        files: Optional[List[str]] = None,
        rename_map: Optional[Dict[str, str]] = None,
        backup_dir: Optional[str] = None,
        params: Optional[dict] = None,
    ):
        self.op_type = op_type
        self.timestamp = timestamp or datetime.now().isoformat()
        self.folder = folder
        self.files = files or []
        self.rename_map = rename_map or {}
        self.backup_dir = backup_dir
        self.params = params or {}

    def to_dict(self) -> dict:
        return {
            'op_type': self.op_type,
            'timestamp': self.timestamp,
            'folder': self.folder,
            'files': self.files,
            'rename_map': self.rename_map,
            'backup_dir': self.backup_dir,
            'params': self.params,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'OperationRecord':
        return cls(
            op_type=d.get('op_type', ''),
            timestamp=d.get('timestamp'),
            folder=d.get('folder', ''),
            files=d.get('files', []),
            rename_map=d.get('rename_map', {}),
            backup_dir=d.get('backup_dir'),
            params=d.get('params', {}),
        )

    @property
    def label(self) -> str:
        """Human-readable label for UI display."""
        n = len(self.files) or len(self.rename_map)
        return f"{self.op_type} ({n} files) - {self.timestamp[:19]}"


class HistoryManager:
    """Manages operation history with persistence."""

    def __init__(self):
        self._records: List[OperationRecord] = []
        self._load()

    def _load(self) -> None:
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
                if isinstance(data, list):
                    self._records = [OperationRecord.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError) as exc:
                get_logger().warning("Failed to load history: %s", exc)

    def _save(self) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            data = [r.to_dict() for r in self._records[-MAX_HISTORY:]]
            HISTORY_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )
        except OSError as exc:
            get_logger().error("Failed to save history: %s", exc)

    def push(self, record: OperationRecord) -> None:
        """Add a new operation record."""
        self._records.append(record)
        if len(self._records) > MAX_HISTORY:
            self._records = self._records[-MAX_HISTORY:]
        self._save()
        get_logger().info("History: recorded %s", record.label)

    def pop(self) -> Optional[OperationRecord]:
        """Pop the most recent operation and return it for undo."""
        if not self._records:
            return None
        record = self._records.pop()
        self._save()
        return record

    def peek(self) -> Optional[OperationRecord]:
        """Return the most recent operation without removing it."""
        return self._records[-1] if self._records else None

    @property
    def can_undo(self) -> bool:
        return bool(self._records)

    @property
    def records(self) -> List[OperationRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
        self._save()


def undo_operation(record: OperationRecord) -> dict:
    """Undo a recorded operation.

    Returns dict with success bool and message string.
    """
    logger = get_logger()

    if record.op_type == 'rename' and record.rename_map:
        # Reverse the rename: new_name -> old_name
        reversed_map = {v: k for k, v in record.rename_map.items()}
        errors: List[str] = []
        for new_name, old_name in reversed_map.items():
            try:
                new_path = os.path.join(record.folder, new_name)
                old_path = os.path.join(record.folder, old_name)
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
            except OSError as exc:
                errors.append(f'{new_name} -> {old_name}: {exc}')
        if errors:
            return {'success': False, 'message': f'Undo partially failed: {errors[:3]}'}
        return {'success': True, 'message': f'Undid rename of {len(reversed_map)} files'}

    if record.backup_dir and os.path.isdir(record.backup_dir):
        # Restore from backup
        restored = 0
        for fname in os.listdir(record.backup_dir):
            src = os.path.join(record.backup_dir, fname)
            dst = os.path.join(record.folder, fname)
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                    restored += 1
                except OSError as exc:
                    logger.error("Undo restore failed for %s: %s", fname, exc)
        return {'success': True, 'message': f'Restored {restored} files from backup'}

    return {'success': False, 'message': 'No undo method available for this operation'}
