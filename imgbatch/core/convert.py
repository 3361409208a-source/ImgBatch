#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Format conversion logic — no GUI dependency."""


import os
from typing import Callable, List, Optional

from PIL import Image, UnidentifiedImageError

from .common import convert_to_rgb_if_needed, get_save_format
from ..infra.logger import get_logger


def convert_image(src: str, dst: str, target_fmt: str) -> int:
    """Convert a single image to a new format.

    Returns new file size in bytes.
    """
    target_ext_l = target_fmt.lower()
    with Image.open(src) as img:
        img = convert_to_rgb_if_needed(img, target_ext_l)
        save_fmt = get_save_format(target_ext_l)
        if save_fmt:
            img.save(dst, format=save_fmt, optimize=True)
        else:
            img.save(dst, optimize=True)
    return os.path.getsize(dst)


def run_convert_batch(
    state,
    folder: str,
    file_list: List[str],
    target_fmt: str,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch format conversion.

    Returns dict with total_before, total_after, errors, cancelled.
    """
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0
    total = len(file_list)

    if do_backup and backup_fn:
        try:
            backup_fn(folder, file_list)
        except OSError as exc:
            logger.error("Backup failed: %s", exc)
            return {
                'total_before': 0, 'total_after': 0,
                'errors': [f'Backup failed: {exc}'], 'cancelled': False,
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    for i, fname in enumerate(file_list):
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
        base = os.path.splitext(fname)[0]
        new_name = base + target_fmt
        current_ext = os.path.splitext(fname)[1].lower()
        dst = src if (replace and target_fmt.lower() == current_ext) else (
            os.path.join(folder, new_name) if replace else os.path.join(out, new_name)
        )

        try:
            sa = convert_image(src, dst, target_fmt)
            total_after += sa

            if replace and target_fmt.lower() != current_ext and os.path.exists(src):
                try:
                    os.remove(src)
                except OSError:
                    pass

            if on_file_done:
                on_file_done(fname, new_name, sa)

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
    }
