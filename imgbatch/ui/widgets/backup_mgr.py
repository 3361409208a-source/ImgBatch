#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List
"""Backup manager dialog widget."""


import os
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

from ...core.common import ensure_parent_dir
from ...infra.logger import get_logger


def find_backups(folder: str) -> List[str]:
    """Find all backup directories for a given folder."""
    folder_name = os.path.basename(folder.rstrip(os.sep))
    backup_root = os.path.join(os.path.dirname(folder), 'backup')
    if not os.path.isdir(backup_root):
        return []
    backups = []
    for name in sorted(os.listdir(backup_root), reverse=True):
        if name.startswith(folder_name + '_'):
            backups.append(os.path.join(backup_root, name))
    return backups


def do_backup(folder: str, file_names: List[str]) -> str:
    """Create a timestamped backup of the given files.

    Returns the backup directory path.
    """
    folder_name = os.path.basename(folder.rstrip(os.sep))
    backup_root = os.path.join(os.path.dirname(folder), 'backup')
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(backup_root, f'{folder_name}_{ts}')
    os.makedirs(backup_dir, exist_ok=True)
    for f in file_names:
        src = os.path.join(folder, f)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, f)
            ensure_parent_dir(dst)
            shutil.copy2(src, dst)
    get_logger().info("Backup created: %s (%d files)", backup_dir, len(file_names))
    return backup_dir


def do_restore(backup_dir: str, folder: str) -> int:
    """Restore files from a backup directory.

    Returns count of restored files.
    """
    count = 0
    for f in os.listdir(backup_dir):
        src = os.path.join(backup_dir, f)
        dst = os.path.join(folder, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            count += 1
    return count


def do_clear_backups(backups: List[str]) -> int:
    """Delete all backup directories. Returns count deleted."""
    count = 0
    for d in backups:
        try:
            shutil.rmtree(d)
            count += 1
        except OSError as exc:
            get_logger().error("Failed to remove backup %s: %s", d, exc)
    return count
