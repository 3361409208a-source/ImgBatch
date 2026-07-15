#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional, Set, Tuple
"""Shared constants and helpers for image processing."""


import os
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico'}
QUALITY_FORMATS = {'.jpg', '.jpeg', '.webp'}
# Formats that do not store an alpha channel — flatten onto white when needed.
NO_ALPHA_EXT = {'.jpg', '.jpeg', '.bmp'}
CONVERT_TARGETS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico']

SAVE_FORMAT_MAP = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
    '.bmp': 'BMP',
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.gif': 'GIF',
    '.ico': 'ICO',
}


def is_supported(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXT


def ensure_parent_dir(file_path: str) -> None:
    """Create parent directories for a file path when needed."""
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def scan_folder(folder: str, recursive: bool = False) -> List[dict]:
    """Scan a folder for supported images. Returns list of file info dicts.

    Each dict: {name, path, size, size_str, dimensions, format}
    ``name`` is relative to ``folder`` (e.g. ``assets/logo.png``) so batch
    operations can resolve files in subdirectories when recursive scan is on.
    """
    result = []
    folder_path = Path(folder)
    if not folder_path.is_dir():
        return result

    if recursive:
        files = sorted(folder_path.rglob('*'))
    else:
        files = sorted(folder_path.iterdir())

    for f in files:
        if not f.is_file():
            continue
        if f.suffix.lower() not in SUPPORTED_EXT:
            continue
        try:
            size = f.stat().st_size
        except OSError:
            continue
        try:
            with Image.open(f) as img:
                dims = f'{img.width}x{img.height}'
                fmt = img.format or f.suffix[1:]
        except (UnidentifiedImageError, OSError):
            dims = '?'
            fmt = f.suffix[1:]
        result.append({
            'name': str(f.relative_to(folder_path)),
            'path': str(f),
            'size': size,
            'size_str': fmt_size(size),
            'dimensions': dims,
            'format': fmt,
        })
    return result


def fmt_size(size: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


# Size filter presets: key -> (min_bytes, max_bytes); None means unbounded.
SIZE_PRESETS = {
    'all': (None, None),
    'lt_50kb': (None, 50 * 1024 - 1),
    'lt_100kb': (None, 100 * 1024 - 1),
    'lt_500kb': (None, 500 * 1024 - 1),
    'lt_1mb': (None, 1024 * 1024 - 1),
    '100kb_1mb': (100 * 1024, 1024 * 1024 - 1),
    'gt_500kb': (500 * 1024, None),
    'gt_1mb': (1024 * 1024, None),
    'custom': (None, None),  # bounds come from custom min/max fields
}

FILTER_FORMATS = ('ALL', 'PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'GIF', 'ICO')


def parse_dimensions(dim_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse ``WxH`` dimension string into ``(width, height)``."""
    if not dim_str or dim_str == '?':
        return (None, None)
    m = re.match(r'^(\d+)\s*[xX×]\s*(\d+)$', dim_str.strip())
    if not m:
        return (None, None)
    return (int(m.group(1)), int(m.group(2)))


def _normalize_format(fmt: str) -> str:
    """Normalize format/extension to uppercase family name (JPEG, PNG, …)."""
    f = (fmt or '').strip().upper().lstrip('.')
    if f in ('JPG', 'JPEG'):
        return 'JPEG'
    if f in ('TIF', 'TIFF'):
        return 'TIFF'
    return f


def filter_files(
    files: List[dict],
    *,
    name_query: str = '',
    formats: Optional[Set[str]] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    min_width: Optional[int] = None,
    min_height: Optional[int] = None,
) -> List[dict]:
    """Filter image file-info dicts by name, format, size, and dimensions.

    Args:
        files: Items with keys ``name``, ``size``, ``dimensions``, ``format``.
        name_query: Case-insensitive substring match on filename.
        formats: Allowed format names (e.g. ``{'PNG','JPEG'}``). Empty/None = all.
        min_size / max_size: Inclusive byte bounds; ``None`` = unbounded.
        min_width / min_height: Minimum pixel size; skipped when dimensions unknown.
    """
    q = (name_query or '').strip().lower()
    fmt_set: Optional[Set[str]] = None
    if formats:
        fmt_set = {_normalize_format(f) for f in formats if f and f.upper() != 'ALL'}
        if not fmt_set:
            fmt_set = None

    result = []
    for d in files:
        if q and q not in d.get('name', '').lower():
            continue

        if fmt_set is not None:
            file_fmt = _normalize_format(d.get('format', ''))
            if not file_fmt:
                file_fmt = _normalize_format(Path(d.get('name', '')).suffix)
            if file_fmt not in fmt_set:
                continue

        size = d.get('size', 0) or 0
        if min_size is not None and size < min_size:
            continue
        if max_size is not None and size > max_size:
            continue

        if min_width is not None or min_height is not None:
            w, h = parse_dimensions(d.get('dimensions', ''))
            if w is None or h is None:
                continue
            if min_width is not None and w < min_width:
                continue
            if min_height is not None and h < min_height:
                continue

        result.append(d)
    return result


def parse_kb_to_bytes(value: str) -> Optional[int]:
    """Parse a KB number string to bytes. Empty/invalid → None."""
    s = (value or '').strip()
    if not s:
        return None
    try:
        kb = float(s)
    except ValueError:
        return None
    if kb < 0:
        return None
    return int(kb * 1024)


def convert_to_rgb_if_needed(img: Image.Image, target_ext: str) -> Image.Image:
    """Prepare image mode for the target format.

    - JPEG/BMP: flatten RGBA/P/LA onto a white background → RGB
    - PNG/WebP/TIFF/GIF/ICO: keep alpha (RGBA/LA/P); only convert exotic modes
    """
    ext = target_ext.lower()
    om = img.mode
    if om in ('RGBA', 'P', 'LA') and ext in NO_ALPHA_EXT:
        if om in ('P', 'LA'):
            img = img.convert('RGBA')
        rgb = Image.new('RGB', img.size, (255, 255, 255))
        rgb.paste(img, mask=img.split()[-1])
        return rgb
    # Preserve alpha-capable modes for formats that support transparency
    if om in ('RGBA', 'LA', 'PA', 'RGB', 'L', 'P'):
        return img
    return img.convert('RGB')


def get_save_format(ext: str) -> Optional[str]:
    """Map file extension to Pillow save format string."""
    return SAVE_FORMAT_MAP.get(ext.lower())


def hex_to_rgba(hex_color: str, alpha: int) -> Tuple[int, int, int, int]:
    """Convert #RRGGBB + alpha to (R, G, B, A) tuple."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def calc_position(img_size: Tuple[int, int], elem_size: Tuple[int, int],
                  pos: str, margin: int = 20) -> Tuple[int, int]:
    """Calculate top-left (x, y) for placing an element at a given position."""
    iw, ih = img_size
    ew, eh = elem_size
    pos_map = {
        'top-left': (margin, margin),
        'top-right': (iw - ew - margin, margin),
        'center': ((iw - ew) // 2, (ih - eh) // 2),
        'bottom-left': (margin, ih - eh - margin),
        'bottom-right': (iw - ew - margin, ih - eh - margin),
    }
    return pos_map.get(pos, pos_map['bottom-right'])
