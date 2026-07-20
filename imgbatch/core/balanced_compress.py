#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Balanced animated compression — target file size for WebP / GIF."""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageSequence, UnidentifiedImageError

from .common import ensure_parent_dir
from .gif import save_gif
from ..infra.logger import get_logger

Variant = Tuple[int, int, int]  # size_bytes, width, quality_or_colors


def _n_frames(img: Image.Image) -> int:
    return int(getattr(img, 'n_frames', 1) or 1)


def is_animated_media(path: str) -> bool:
    """True for multi-frame GIF or animated WebP."""
    ext = Path(path).suffix.lower()
    if ext not in {'.gif', '.webp'}:
        return False
    try:
        with Image.open(path) as img:
            if ext == '.gif':
                return _n_frames(img) > 1
            return bool(getattr(img, 'is_animated', False)) and _n_frames(img) > 1
    except (UnidentifiedImageError, OSError):
        return False


def load_animation(src: str) -> Tuple[List[Image.Image], List[int], int, str]:
    """Load frames, per-frame durations (ms), loop count, and format tag."""
    ext = Path(src).suffix.lower()
    frames: List[Image.Image] = []
    durations: List[int] = []
    loop = 0

    with Image.open(src) as img:
        if ext == '.gif':
            loop = int(img.info.get('loop', 0) or 0)
            count = _n_frames(img)
            for i in range(count):
                img.seek(i)
                frames.append(img.copy().convert('RGBA'))
                durations.append(max(10, int(img.info.get('duration', 100) or 100)))
            return frames, durations, loop, 'gif'

        if ext == '.webp':
            for frame in ImageSequence.Iterator(img):
                frames.append(frame.convert('RGBA').copy())
                durations.append(max(40, int(frame.info.get('duration', 83) or 83)))
            loop = int(img.info.get('loop', 0) or 0)
            return frames, durations, loop, 'webp'

    raise ValueError(f'Unsupported animation format: {ext}')


def _width_grid(orig_w: int) -> List[int]:
    """Candidate output widths, descending, always including full width."""
    ratios = (1.0, 0.95, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.75, 0.7)
    widths: List[int] = []
    for r in ratios:
        w = max(1, int(round(orig_w * r)))
        if w not in widths:
            widths.append(w)
    return sorted(widths, reverse=True)


def _resize_frames(
    frames: List[Image.Image],
    target_width: int,
    orig_w: int,
    orig_h: int,
) -> List[Image.Image]:
    if target_width >= orig_w:
        return frames
    target_h = max(1, int(round(orig_h * (target_width / orig_w))))
    return [f.resize((target_width, target_h), Image.LANCZOS) for f in frames]


def _save_webp_variant(
    frames: List[Image.Image],
    durations: List[int],
    quality: int,
) -> int:
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format='WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=quality,
        method=4,
    )
    return buf.tell()


def _save_gif_variant(
    frames: List[Image.Image],
    durations: List[int],
    loop: int,
    colors: int,
) -> int:
    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        return save_gif(frames, durations, tmp_path, loop=loop, optimize=True, colors=colors)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _encode_webp_to_path(
    frames: List[Image.Image],
    durations: List[int],
    dst: str,
    quality: int,
) -> int:
    ensure_parent_dir(dst)
    frames[0].save(
        dst,
        format='WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=quality,
        method=4,
    )
    return os.path.getsize(dst)


def _search_variants(
    frames: List[Image.Image],
    durations: List[int],
    loop: int,
    fmt: str,
    orig_w: int,
    orig_h: int,
) -> List[Variant]:
    variants: List[Variant] = []
    widths = _width_grid(orig_w)

    if fmt == 'webp':
        qualities = list(range(26, 37))
        for width in widths:
            imgs = _resize_frames(frames, width, orig_w, orig_h)
            for q in qualities:
                size = _save_webp_variant(imgs, durations, q)
                variants.append((size, width, q))
    else:
        color_steps = (256, 192, 128, 64)
        for width in widths:
            imgs = _resize_frames(frames, width, orig_w, orig_h)
            for colors in color_steps:
                size = _save_gif_variant(imgs, durations, loop, colors)
                variants.append((size, width, colors))

    return variants


def pick_best_variant(variants: List[Variant], target_bytes: int) -> Variant:
    """Choose variant closest to target without exceeding when possible."""
    if not variants:
        raise ValueError('No compression variants produced')

    under = [v for v in variants if v[0] <= target_bytes]
    if under:
        return max(under, key=lambda v: (v[2], v[1]))
    return min(variants, key=lambda v: (abs(v[0] - target_bytes), -v[2], -v[1]))


def compress_anim_to_target(
    src: str,
    dst: str,
    target_bytes: int,
) -> Dict[str, object]:
    """Compress animated WebP/GIF toward target_bytes. Returns metadata dict."""
    frames, durations, loop, fmt = load_animation(src)
    if not frames:
        raise ValueError('No animation frames')

    orig_w, orig_h = frames[0].size
    variants = _search_variants(frames, durations, loop, fmt, orig_w, orig_h)
    best = pick_best_variant(variants, target_bytes)
    best_size, best_width, best_param = best
    best_frames = _resize_frames(frames, best_width, orig_w, orig_h)

    if fmt == 'webp':
        final_size = _encode_webp_to_path(best_frames, durations, dst, best_param)
        return {
            'format': 'webp',
            'size': final_size,
            'width': best_width,
            'quality': best_param,
            'target_bytes': target_bytes,
            'under_target': final_size <= target_bytes,
        }

    final_size = save_gif(
        best_frames, durations, dst, loop=loop, optimize=True, colors=best_param,
    )
    return {
        'format': 'gif',
        'size': final_size,
        'width': best_width,
        'colors': best_param,
        'target_bytes': target_bytes,
        'under_target': final_size <= target_bytes,
    }


def run_balanced_compress_batch(
    state,
    folder: str,
    file_list: List[str],
    target_mb: float,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Batch balanced compress for animated WebP / GIF only."""
    logger = get_logger()
    errors: List[str] = []
    skipped: List[str] = []
    results: List[dict] = []
    total_before = 0
    total_after = 0
    target_bytes = int(max(0.01, target_mb) * 1024 * 1024)

    eligible = [f for f in file_list if is_animated_media(os.path.join(folder, f))]
    for f in file_list:
        if f not in eligible:
            skipped.append(f)

    total = len(eligible)
    if total == 0:
        return {
            'total_before': 0,
            'total_after': 0,
            'errors': errors,
            'skipped': skipped,
            'results': results,
            'cancelled': False,
        }

    backup_dir = None
    if do_backup and backup_fn:
        try:
            backup_dir = backup_fn(folder, file_list)
        except OSError as exc:
            logger.error("Backup failed: %s", exc)
            return {
                'total_before': 0,
                'total_after': 0,
                'errors': [f'Backup failed: {exc}'],
                'skipped': skipped,
                'results': [],
                'cancelled': False,
                'backup_dir': None,
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    for i, fname in enumerate(eligible):
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
            meta = compress_anim_to_target(src, dst, target_bytes)
            sa = int(meta['size'])
            total_after += sa
            results.append({'name': fname, **meta})
            if on_file_done:
                on_file_done(fname, sa)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i + 1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'skipped': skipped,
        'results': results,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
