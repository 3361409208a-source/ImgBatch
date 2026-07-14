#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Optional, Tuple
"""Shared constants and helpers for image processing."""


import os
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico'}
QUALITY_FORMATS = {'.jpg', '.jpeg', '.webp'}
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


def scan_folder(folder: str, recursive: bool = False) -> List[dict]:
    """Scan a folder for supported images. Returns list of file info dicts.

    Each dict: {name, path, size, size_str, dimensions, format}
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
            'name': f.name,
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


def convert_to_rgb_if_needed(img: Image.Image, target_ext: str) -> Image.Image:
    """Convert RGBA/P/LA to RGB for JPEG/WebP targets.

    Shared by compress, convert, and preview logic.
    """
    ext = target_ext.lower()
    om = img.mode
    if om in ('RGBA', 'P', 'LA') and ext in ('.jpg', '.jpeg'):
        rgb = Image.new('RGB', img.size, (255, 255, 255))
        if om == 'P':
            img = img.convert('RGBA')
        rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        return rgb
    if om not in ('RGB', 'L'):
        return img.convert('RGB')
    return img


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
