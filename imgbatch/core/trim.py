#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trim transparent edges logic — no GUI dependency."""


import os
from typing import Callable, List, Optional

from PIL import Image, UnidentifiedImageError

from .common import ensure_parent_dir
from ..infra.logger import get_logger


def trim_image(src: str, dst: str, padding: int = 4) -> int:
    """Trim transparent edges from a PNG, adding optional padding.

    Returns new file size in bytes.
    """
    with Image.open(src) as img:
        img = img.convert('RGBA')
        bbox = img.getbbox()
        if not bbox:
            # Fully transparent image, save as-is
            img.save(dst, optimize=True)
            return os.path.getsize(dst)

        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(img.width, bbox[2] + padding)
        bottom = min(img.height, bbox[3] + padding)
        cropped = img.crop((left, top, right, bottom))
        cropped.save(dst, optimize=True)

    return os.path.getsize(dst)


def run_trim_batch(
    state,
    folder: str,
    file_list: List[str],
    padding: int,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch transparent-edge trimming."""
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0

    png_list = [f for f in file_list if f.lower().endswith('.png')]
    if not png_list:
        return {
            'total_before': 0, 'total_after': 0,
            'errors': [], 'cancelled': False,
        }

    total = len(png_list)

    backup_dir = None
    if do_backup and backup_fn:
        try:
            backup_dir = backup_fn(folder, file_list)
        except OSError as exc:
            logger.error("Backup failed: %s", exc)
            return {
                'total_before': 0, 'total_after': 0,
                'errors': [f'Backup failed: {exc}'], 'cancelled': False,
                'backup_dir': None,
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    for i, fname in enumerate(png_list):
        if state.cancelled:
            break

        src = os.path.join(folder, fname)
        if not os.path.exists(src):
            errors.append(f'{fname}: source not found')
            continue

        try:
            sb = os.path.getsize(src)
        except OSError as exc:
            errors.append(f'{fname}: {exc}')
            continue

        total_before += sb
        dst = src if replace else os.path.join(out, fname)
        if not replace:
            ensure_parent_dir(dst)

        try:
            sa = trim_image(src, dst, padding)
            total_after += sa
            if on_file_done:
                on_file_done(fname, sa)
        except (UnidentifiedImageError, OSError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i+1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
