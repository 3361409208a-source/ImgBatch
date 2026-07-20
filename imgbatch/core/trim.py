#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trim transparent / blank edges — no GUI dependency."""


import os
from typing import Callable, List, Optional, Tuple

from PIL import Image, ImageChops, UnidentifiedImageError

from .common import QUALITY_FORMATS, TRIM_SUPPORTED_EXT, ensure_parent_dir, get_save_format
from ..infra.logger import get_logger


def _sample_corner_color(rgba: Image.Image) -> Tuple[int, int, int, int]:
    """Pick a representative border color from the four corners."""
    w, h = rgba.size
    corners = [
        rgba.getpixel((0, 0)),
        rgba.getpixel((w - 1, 0)),
        rgba.getpixel((0, h - 1)),
        rgba.getpixel((w - 1, h - 1)),
    ]
    # Prefer a fully-opaque corner if any (typical solid canvas).
    opaque = [c for c in corners if c[3] >= 250]
    pool = opaque or corners
    # Median-ish: average then clamp — stable against single noisy corner.
    r = sum(c[0] for c in pool) // len(pool)
    g = sum(c[1] for c in pool) // len(pool)
    b = sum(c[2] for c in pool) // len(pool)
    a = sum(c[3] for c in pool) // len(pool)
    return (r, g, b, a)


def _alpha_bbox(
    rgba: Image.Image,
    alpha_threshold: int,
) -> Optional[Tuple[int, int, int, int]]:
    alpha = rgba.getchannel('A')
    alpha_min, _ = alpha.getextrema()
    if alpha_min >= alpha_threshold:
        return None
    mask = alpha.point(lambda a: 255 if a >= alpha_threshold else 0)
    return mask.getbbox()


def _color_bbox(
    rgba: Image.Image,
    color_tolerance: int,
) -> Optional[Tuple[int, int, int, int]]:
    """BBox of pixels that differ from the corner background color.

    Uses channel-wise absolute difference so lossy WebP / JPEG border noise
    still trims when most of the border matches the canvas color.
    """
    w, h = rgba.size
    if w == 0 or h == 0:
        return None

    bg = _sample_corner_color(rgba)
    rgb = rgba.convert('RGB')
    bg_img = Image.new('RGB', (w, h), bg[:3])
    diff = ImageChops.difference(rgb, bg_img)
    # Max of R/G/B channel deltas → single-channel distance map.
    r, g, b = diff.split()
    distance = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = distance.point(lambda d: 255 if d > color_tolerance else 0)

    # Also treat near-transparent pixels as background when alpha exists.
    alpha = rgba.getchannel('A')
    a_min, _ = alpha.getextrema()
    if a_min < 255:
        alpha_mask = alpha.point(lambda a: 255 if a >= 28 else 0)
        mask = ImageChops.multiply(mask, alpha_mask)

    return mask.getbbox()


def find_content_bbox(
    img: Image.Image,
    alpha_threshold: int = 28,
    color_tolerance: int = 24,
) -> Optional[Tuple[int, int, int, int]]:
    """Find content bounds: alpha first, then solid/lossy background color."""
    rgba = img.convert('RGBA')
    w, h = rgba.size

    alpha_box = _alpha_bbox(rgba, alpha_threshold)
    if alpha_box:
        aw = alpha_box[2] - alpha_box[0]
        ah = alpha_box[3] - alpha_box[1]
        # Meaningful shrink vs full canvas.
        if aw * ah < w * h * 0.98:
            return alpha_box

    color_box = _color_bbox(rgba, color_tolerance)
    if color_box:
        cw = color_box[2] - color_box[0]
        ch = color_box[3] - color_box[1]
        if cw * ch < w * h * 0.98:
            return color_box

    return None


def _save_trimmed(img: Image.Image, dst: str) -> None:
    """Save trimmed image using the destination file's format."""
    ext = os.path.splitext(dst)[1].lower()
    save_kw: dict = {}
    if ext == '.png':
        save_kw['optimize'] = True
    elif ext == '.webp':
        # Keep RGB WebP without forcing an unused alpha plane.
        if img.mode == 'RGBA':
            lo, _ = img.getchannel('A').getextrema()
            if lo >= 255:
                img = img.convert('RGB')
                save_kw['quality'] = 90
            else:
                save_kw['lossless'] = True
        else:
            save_kw['quality'] = 90
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
    color_tolerance: int = 24,
) -> int:
    """Trim blank edges from an image, adding optional padding.

    Uses alpha channel when present; otherwise trims a uniform border color
    (including lossy WebP white / solid canvases).
    Returns new file size in bytes.
    """
    with Image.open(src) as img:
        # Animated WebP / GIF: trim the first frame canvas only for still trim.
        if getattr(img, 'is_animated', False) and getattr(img, 'n_frames', 1) > 1:
            img.seek(0)
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
    color_tolerance: int = 24,
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
