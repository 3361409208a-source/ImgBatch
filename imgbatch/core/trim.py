#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trim transparent edges logic — no GUI dependency."""


import os
from typing import Callable, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError

from .common import QUALITY_FORMATS, TRIM_SUPPORTED_EXT, ensure_parent_dir, get_save_format
from ..infra.logger import get_logger


def _pixel_is_background(
    pixel: Tuple[int, int, int, int],
    bg: Tuple[int, int, int, int],
    alpha_threshold: int,
    color_tolerance: int,
) -> bool:
    r, g, b, a = pixel
    br, bg_c, bb, ba = bg
    if a < alpha_threshold:
        return True
    if ba < alpha_threshold:
        return False
    return (
        abs(r - br) <= color_tolerance
        and abs(g - bg_c) <= color_tolerance
        and abs(b - bb) <= color_tolerance
    )


def _background_bbox(
    rgba: Image.Image,
    alpha_threshold: int = 28,
    color_tolerance: int = 10,
) -> Optional[Tuple[int, int, int, int]]:
    """Trim uniform border color sampled from the top-left pixel."""
    w, h = rgba.size
    if w == 0 or h == 0:
        return None

    bg = rgba.getpixel((0, 0))
    px = rgba.load()

    def row_is_bg(y: int) -> bool:
        return all(
            _pixel_is_background(px[x, y], bg, alpha_threshold, color_tolerance)
            for x in range(w)
        )

    def col_is_bg(x: int, y0: int, y1: int) -> bool:
        return all(
            _pixel_is_background(px[x, y], bg, alpha_threshold, color_tolerance)
            for y in range(y0, y1 + 1)
        )

    top = 0
    while top < h and row_is_bg(top):
        top += 1
    if top >= h:
        return None

    bottom = h - 1
    while bottom > top and row_is_bg(bottom):
        bottom -= 1

    left = 0
    while left < w and col_is_bg(left, top, bottom):
        left += 1

    right = w - 1
    while right > left and col_is_bg(right, top, bottom):
        right -= 1

    return (left, top, right + 1, bottom + 1)


def find_content_bbox(
    img: Image.Image,
    alpha_threshold: int = 28,
    color_tolerance: int = 10,
) -> Optional[Tuple[int, int, int, int]]:
    """Find content bounds using alpha, then uniform background color."""
    rgba = img.convert('RGBA')
    w, h = rgba.size
    alpha = rgba.getchannel('A')
    alpha_min, _ = alpha.getextrema()
    mask = alpha.point(lambda a: 255 if a >= alpha_threshold else 0)
    alpha_bbox = mask.getbbox()

    if alpha_bbox and alpha_min < alpha_threshold:
        aw = alpha_bbox[2] - alpha_bbox[0]
        ah = alpha_bbox[3] - alpha_bbox[1]
        if aw * ah < w * h * 0.98:
            return alpha_bbox

    return _background_bbox(rgba, alpha_threshold, color_tolerance)


def _save_trimmed(img: Image.Image, dst: str) -> None:
    """Save trimmed image using the destination file's format."""
    ext = os.path.splitext(dst)[1].lower()
    save_kw: dict = {}
    if ext == '.png':
        save_kw['optimize'] = True
    elif ext == '.webp':
        if img.mode in ('RGBA', 'LA') and 'A' in img.getbands():
            lo, _ = img.getchannel('A').getextrema()
            if lo < 255:
                save_kw['lossless'] = True
            else:
                save_kw['quality'] = 85
        else:
            save_kw['quality'] = 85
    elif ext in QUALITY_FORMATS:
        save_kw['quality'] = 85
    save_fmt = get_save_format(ext)
    if save_fmt:
        img.save(dst, format=save_fmt, **save_kw)
    else:
        img.save(dst, **save_kw)


def trim_image(
    src: str,
    dst: str,
    padding: int = 4,
    alpha_threshold: int = 28,
    color_tolerance: int = 10,
) -> int:
    """Trim blank edges from an image, adding optional padding.

    Uses alpha channel when present; otherwise trims a uniform border color.
    Returns new file size in bytes.
    """
    with Image.open(src) as img:
        bbox = find_content_bbox(img, alpha_threshold, color_tolerance)
        rgba = img.convert('RGBA')
        if not bbox:
            _save_trimmed(rgba, dst)
            return os.path.getsize(dst)

        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(rgba.width, bbox[2] + padding)
        bottom = min(rgba.height, bbox[3] + padding)
        cropped = rgba.crop((left, top, right, bottom))
        _save_trimmed(cropped, dst)

    return os.path.getsize(dst)


def _is_trim_supported(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in TRIM_SUPPORTED_EXT


def run_trim_batch(
    state,
    folder: str,
    file_list: List[str],
    padding: int,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    alpha_threshold: int = 28,
    color_tolerance: int = 10,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch transparent-edge trimming."""
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0

    trim_list = [f for f in file_list if _is_trim_supported(f)]
    if not trim_list:
        return {
            'total_before': 0, 'total_after': 0,
            'errors': [], 'cancelled': False,
        }

    total = len(trim_list)

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

    for i, fname in enumerate(trim_list):
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
            sa = trim_image(
                src, dst, padding,
                alpha_threshold=alpha_threshold,
                color_tolerance=color_tolerance,
            )
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
