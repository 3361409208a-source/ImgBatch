#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Normalize PNG title images to uniform glyph height — no GUI dependency."""


import os
from typing import Callable, List, Optional

from PIL import Image, UnidentifiedImageError

from ..infra.logger import get_logger


def normalize_image(
    src: str,
    dst: str,
    alpha_threshold: int = 28,
    target_height: int = 280,
    padding: int = 6,
) -> int:
    """Normalize a PNG so its visible content has a uniform height.

    1. Crop to opaque content (alpha >= threshold)
    2. Scale so content height == target_height
    3. Wrap with uniform transparent padding

    Returns new file size in bytes.
    """
    with Image.open(src) as img:
        img = img.convert('RGBA')
        alpha = img.getchannel('A')
        mask = alpha.point(lambda a: 255 if a >= alpha_threshold else 0)
        bbox = mask.getbbox()
        if not bbox:
            img.save(dst, optimize=True)
            return os.path.getsize(dst)

        content = img.crop(bbox)
        cw, ch = content.size
        if ch <= 0:
            img.save(dst, optimize=True)
            return os.path.getsize(dst)

        scale = target_height / ch
        new_w = max(1, round(cw * scale))
        scaled = content.resize((new_w, target_height), Image.LANCZOS)

        # Re-crop soft fringe after scale, then force exact height again
        alpha2 = scaled.getchannel('A')
        mask2 = alpha2.point(lambda a: 255 if a >= alpha_threshold else 0)
        bbox2 = mask2.getbbox()
        if bbox2:
            scaled = scaled.crop(bbox2)
            sw, sh = scaled.size
            if sh != target_height and sh > 0:
                scaled = scaled.resize(
                    (max(1, round(sw * target_height / sh)), target_height),
                    Image.LANCZOS,
                )

        canvas = Image.new(
            'RGBA',
            (scaled.width + padding * 2, target_height + padding * 2),
            (0, 0, 0, 0),
        )
        canvas.paste(scaled, (padding, padding), scaled)
        canvas.save(dst, optimize=True)

    return os.path.getsize(dst)


def run_normalize_batch(
    state,
    folder: str,
    file_list: List[str],
    alpha_threshold: int,
    target_height: int,
    padding: int,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch normalization."""
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

        try:
            sa = normalize_image(src, dst, alpha_threshold, target_height, padding)
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
    }
