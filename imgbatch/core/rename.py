#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Batch rename logic with conflict detection — no GUI dependency."""


import os
import re
from enum import Enum
from typing import Callable, Dict, List, Optional, Set

from ..infra.logger import get_logger


class ConflictResolution(Enum):
    SKIP = 'skip'
    OVERWRITE = 'overwrite'
    AUTO_NUMBER = 'auto_number'


class RenameMode(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'
    REPLACE = 'replace'
    SEQ = 'seq'
    CASE = 'case'


def sanitize_filename(name: str) -> str:
    """Remove Windows-illegal characters from a filename."""
    if not name:
        return name
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'[\x00-\x1f]', '', name)
    name = name.strip('. ')
    name = name.replace('{', '').replace('}', '').replace("'", '').replace('"', '')
    return name


def generate_rename_map(
    file_data: List[dict],
    mode: str,
    prefix: str = '',
    suffix: str = '',
    find: str = '',
    replace: str = '',
    seq_template: str = 'photo_{num}',
    seq_start: int = 1,
    seq_digits: int = 3,
    lowercase: bool = False,
    uppercase: bool = False,
) -> Dict[str, str]:
    """Generate an old_name -> new_name mapping.

    Returns mapping dict. Files with no change are excluded.
    """
    mapping: Dict[str, str] = {}
    seq = seq_start

    for d in file_data:
        name = d['name']
        base, ext = os.path.splitext(name)

        if mode == RenameMode.PREFIX.value:
            new = prefix + base + suffix + ext
        elif mode == RenameMode.SUFFIX.value:
            new = base + prefix + suffix + ext
        elif mode == RenameMode.REPLACE.value:
            if find and find in base:
                new = base.replace(find, replace) + ext
            else:
                continue
        elif mode == RenameMode.SEQ.value:
            new = seq_template.replace('{num}', str(seq).zfill(seq_digits)) + ext
            seq += 1
        elif mode == RenameMode.CASE.value:
            if lowercase:
                base = base.lower()
            if uppercase:
                base = base.upper()
            new = base + ext
        else:
            continue

        if new != name:
            mapping[name] = new

    return mapping


def resolve_conflict(
    new_name: str,
    existing_names: Set[str],
    resolution: ConflictResolution,
) -> Optional[str]:
    """Resolve a filename conflict. Returns the final name, or None to skip."""
    if new_name not in existing_names:
        return new_name

    if resolution == ConflictResolution.SKIP:
        return None
    elif resolution == ConflictResolution.OVERWRITE:
        return new_name
    elif resolution == ConflictResolution.AUTO_NUMBER:
        base, ext = os.path.splitext(new_name)
        counter = 1
        while f'{base}_{counter}{ext}' in existing_names:
            counter += 1
        return f'{base}_{counter}{ext}'
    return new_name


def run_rename_batch(
    state,
    folder: str,
    mapping: Dict[str, str],
    conflict_resolution: ConflictResolution = ConflictResolution.AUTO_NUMBER,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """Execute batch rename with conflict detection.

    Returns dict with errors, renamed_count, skipped_count.
    """
    logger = get_logger()
    errors: List[str] = []
    renamed = 0
    skipped = 0
    total = len(mapping)

    # Collect all existing files for conflict detection
    try:
        existing = set(os.listdir(folder))
    except OSError as exc:
        logger.error("Cannot list folder %s: %s", folder, exc)
        return {'errors': [str(exc)], 'renamed': 0, 'skipped': 0, 'cancelled': False}

    # Remove source names from existing (they will be freed)
    for old_name in mapping:
        existing.discard(old_name)

    used_names: Set[str] = set()

    for i, (old, new) in enumerate(mapping.items()):
        if state.cancelled:
            break

        # Sanitize the new name
        new = sanitize_filename(new)

        # Check for conflicts (against existing files AND already-used names)
        all_taken = existing | used_names
        resolved = resolve_conflict(new, all_taken, conflict_resolution)

        if resolved is None:
            skipped += 1
            logger.info("Skipped rename: %s -> %s (conflict, skip)", old, new)
        else:
            try:
                old_path = os.path.join(folder, old)
                new_path = os.path.join(folder, resolved)
                os.rename(old_path, new_path)
                renamed += 1
                used_names.add(resolved)
                if on_file_done:
                    on_file_done(old, resolved)
                logger.debug("Renamed: %s -> %s", old, resolved)
            except OSError as exc:
                errors.append(f'{old} -> {resolved}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i+1}/{total}')

    return {
        'errors': errors,
        'renamed': renamed,
        'skipped': skipped,
        'cancelled': state.cancelled,
    }
