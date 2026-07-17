#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional, Set, Tuple
"""Shared constants and helpers for image processing."""


import os
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

_BASE_SUPPORTED_EXT = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico',
}
_HEIF_INPUT_EXT = {'.heic', '.heif'}
_BASE_CONVERT_TARGETS = [
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico',
]
QUALITY_FORMATS = {'.jpg', '.jpeg', '.webp', '.avif'}
# Formats that do not store an alpha channel — flatten onto white when needed.
NO_ALPHA_EXT = {'.jpg', '.jpeg', '.bmp'}
# Formats supported by transparent-edge trim (must preserve alpha).
TRIM_SUPPORTED_EXT = {'.png', '.webp', '.gif', '.tiff', '.tif', '.ico', '.avif'}

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
    '.avif': 'AVIF',
}

COMMON_CONVERT_PRESETS = [
    {
        'id': 'web_jpg',
        'label': '网页 JPG',
        'target_fmt': '.jpg',
        'quality': 85,
        'hint': '通用网页与分享，体积适中',
    },
    {
        'id': 'web_webp',
        'label': 'WebP 体积小',
        'target_fmt': '.webp',
        'quality': 82,
        'hint': '现代浏览器，比 JPG 更小',
    },
    {
        'id': 'png_transparent',
        'label': 'PNG 透明',
        'target_fmt': '.png',
        'quality': None,
        'hint': '保留透明通道，无损',
    },
    {
        'id': 'avif_modern',
        'label': 'AVIF 现代',
        'target_fmt': '.avif',
        'quality': 75,
        'hint': '新一代高压缩格式',
    },
    {
        'id': 'print_tiff',
        'label': 'TIFF 打印',
        'target_fmt': '.tiff',
        'quality': None,
        'hint': '印刷与归档',
    },
    {
        'id': 'icon_ico',
        'label': '图标 ICO',
        'target_fmt': '.ico',
        'quality': None,
        'hint': 'Windows 图标',
    },
]

CONVERT_TARGET_GROUPS = {
    'common': ['.jpg', '.png', '.webp', '.avif'],
    'other': ['.jpeg', '.bmp', '.tiff', '.gif', '.ico'],
}


def _register_heif_opener() -> bool:
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        return True
    except ImportError:
        return False


def _avif_encode_supported() -> bool:
    try:
        from PIL import features
        return bool(features.check('avif'))
    except Exception:
        return False


HEIF_AVAILABLE = _register_heif_opener()
AVIF_AVAILABLE = _avif_encode_supported()

SUPPORTED_EXT = set(_BASE_SUPPORTED_EXT)
if HEIF_AVAILABLE:
    SUPPORTED_EXT |= _HEIF_INPUT_EXT

CONVERT_TARGETS = list(_BASE_CONVERT_TARGETS)
if AVIF_AVAILABLE and '.avif' not in CONVERT_TARGETS:
    CONVERT_TARGETS.insert(3, '.avif')


def get_convert_catalog() -> dict:
    """Return supported convert targets, presets, and capability flags."""
    targets = []
    for ext in CONVERT_TARGETS:
        group = 'common' if ext in CONVERT_TARGET_GROUPS.get('common', []) else 'other'
        targets.append({
            'ext': ext,
            'label': ext.lstrip('.').upper(),
            'group': group,
            'supports_quality': ext in QUALITY_FORMATS,
        })

    presets = []
    for preset in COMMON_CONVERT_PRESETS:
        target = preset['target_fmt']
        if target == '.avif' and not AVIF_AVAILABLE:
            continue
        presets.append(dict(preset))

    return {
        'targets': targets,
        'presets': presets,
        'features': {
            'heic_input': HEIF_AVAILABLE,
            'avif_output': AVIF_AVAILABLE,
        },
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
        info = _file_info(f, folder_path)
        if info:
            result.append(info)
    return result


def _file_info(f: Path, folder_path: Optional[Path]) -> Optional[dict]:
    try:
        size = f.stat().st_size
    except OSError:
        return None
    try:
        with Image.open(f) as img:
            dims = f'{img.width}x{img.height}'
            fmt = img.format or f.suffix[1:]
            if f.suffix.lower() == '.gif':
                count = int(getattr(img, 'n_frames', 1) or 1)
                if count > 1:
                    fmt = f'GIF ({count}f)'
    except (UnidentifiedImageError, OSError):
        dims = '?'
        fmt = f.suffix[1:]
    if folder_path is not None:
        name = str(f.relative_to(folder_path))
    else:
        name = f.name
    return {
        'name': name,
        'path': str(f),
        'size': size,
        'size_str': fmt_size(size),
        'dimensions': dims,
        'format': fmt,
    }


def probe_files(paths: List[str]) -> List[dict]:
    """Return metadata for explicit file paths without scanning a folder."""
    result: List[dict] = []
    seen: Set[str] = set()
    for path_str in paths:
        key = path_str.strip().strip('"').lower()
        if not key or key in seen:
            continue
        seen.add(key)
        f = Path(path_str.strip().strip('"'))
        if not f.is_file() or f.suffix.lower() not in SUPPORTED_EXT:
            continue
        info = _file_info(f, None)
        if info:
            result.append(info)
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

FILTER_FORMATS = ('ALL', 'PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'GIF', 'ICO', 'AVIF', 'HEIC')


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
    if f in ('HEIC', 'HEIF'):
        return 'HEIC'
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
