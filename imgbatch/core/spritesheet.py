#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smart sprite sheet builder — no GUI dependency.

Combines multiple images into a single sprite atlas with intelligent
layout, optional transparent-edge trimming, and JSON metadata export.
"""

import json
import math
import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError

from .common import ensure_parent_dir
from ..infra.logger import get_logger

LAYOUT_AUTO = 'auto'
LAYOUT_GRID = 'grid'
LAYOUT_HORIZONTAL = 'horizontal'
LAYOUT_VERTICAL = 'vertical'

LAYOUTS = (LAYOUT_AUTO, LAYOUT_GRID, LAYOUT_HORIZONTAL, LAYOUT_VERTICAL)


class SpriteFrame:
    """A single frame placed on the sprite sheet."""

    __slots__ = ('name', 'image', 'x', 'y', 'source_w', 'source_h', 'orig_w', 'orig_h')

    def __init__(
        self,
        name: str,
        image: Image.Image,
        x: int = 0,
        y: int = 0,
        source_w: int = 0,
        source_h: int = 0,
        orig_w: int = 0,
        orig_h: int = 0,
    ):
        self.name = name
        self.image = image
        self.x = x
        self.y = y
        self.source_w = source_w
        self.source_h = source_h
        self.orig_w = orig_w
        self.orig_h = orig_h


def natural_sort_key(name: str) -> list:
    """Natural sort key for animation sequences (frame_2 before frame_10)."""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', name)]


def next_power_of_2(value: int) -> int:
    """Round up to the nearest power of two (minimum 1)."""
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()


def trim_frame(
    img: Image.Image,
    padding: int = 2,
    alpha_threshold: int = 28,
) -> Image.Image:
    """Trim transparent edges and add optional padding."""
    rgba = img.convert('RGBA')
    alpha = rgba.getchannel('A')
    mask = alpha.point(lambda a: 255 if a >= alpha_threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return rgba

    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(rgba.width, bbox[2] + padding)
    bottom = min(rgba.height, bbox[3] + padding)
    return rgba.crop((left, top, right, bottom))


def _estimate_auto_width(frames: List[SpriteFrame], spacing: int) -> int:
    """Estimate a near-square canvas width for shelf packing."""
    if not frames:
        return 1
    max_w = max(f.image.width for f in frames)
    total_area = sum(
        (f.image.width + spacing) * (f.image.height + spacing)
        for f in frames
    )
    estimated = int(math.sqrt(total_area))
    return max(max_w, estimated)


def _layout_shelf(
    frames: List[SpriteFrame],
    spacing: int,
    max_width: int = 0,
) -> Tuple[int, int]:
    """Shelf packing — sort by height, fill rows left-to-right."""
    if not frames:
        return 0, 0

    if max_width <= 0:
        max_width = _estimate_auto_width(frames, spacing)

    ordered = sorted(frames, key=lambda f: f.image.height, reverse=True)
    rows: List[Tuple[List[SpriteFrame], int, int]] = []
    current: List[SpriteFrame] = []
    row_w = 0
    row_h = 0

    for frame in ordered:
        fw = frame.image.width + spacing
        fh = frame.image.height + spacing
        if current and row_w + fw - spacing > max_width:
            rows.append((current, row_w, row_h))
            current = []
            row_w = 0
            row_h = 0
        current.append(frame)
        row_w += fw
        row_h = max(row_h, fh)

    if current:
        rows.append((current, row_w, row_h))

    y = 0
    sheet_w = 0
    for row_frames, _, row_h in rows:
        x = 0
        for frame in row_frames:
            frame.x = x
            frame.y = y
            frame.source_w = frame.image.width
            frame.source_h = frame.image.height
            x += frame.image.width + spacing
        sheet_w = max(sheet_w, x - spacing if x > 0 else 0)
        y += row_h

    return sheet_w, max(0, y - spacing)


def _layout_grid(
    frames: List[SpriteFrame],
    spacing: int,
    columns: int = 0,
) -> Tuple[int, int]:
    """Uniform grid layout with auto column count."""
    if not frames:
        return 0, 0

    n = len(frames)
    cols = columns if columns > 0 else max(1, int(math.ceil(math.sqrt(n))))
    cell_w = max(f.image.width for f in frames)
    cell_h = max(f.image.height for f in frames)
    step_x = cell_w + spacing
    step_y = cell_h + spacing

    for i, frame in enumerate(frames):
        col = i % cols
        row = i // cols
        frame.x = col * step_x
        frame.y = row * step_y
        frame.source_w = frame.image.width
        frame.source_h = frame.image.height

    rows = int(math.ceil(n / cols))
    sheet_w = cols * step_x - spacing
    sheet_h = rows * step_y - spacing
    return max(sheet_w, 0), max(sheet_h, 0)


def _layout_strip(
    frames: List[SpriteFrame],
    spacing: int,
    horizontal: bool,
) -> Tuple[int, int]:
    """Single-row or single-column layout."""
    if not frames:
        return 0, 0

    x = y = 0
    max_w = max_h = 0
    for frame in frames:
        frame.x = x
        frame.y = y
        frame.source_w = frame.image.width
        frame.source_h = frame.image.height
        max_w = max(max_w, x + frame.image.width)
        max_h = max(max_h, y + frame.image.height)
        if horizontal:
            x += frame.image.width + spacing
        else:
            y += frame.image.height + spacing

    if horizontal and len(frames) > 1:
        max_w -= spacing
    elif not horizontal and len(frames) > 1:
        max_h -= spacing

    return max(max_w, 0), max(max_h, 0)


def build_metadata(
    frames: List[SpriteFrame],
    sheet_w: int,
    sheet_h: int,
    image_name: str,
) -> dict:
    """Build TexturePacker-compatible JSON metadata."""
    frame_data = {}
    for frame in frames:
        frame_data[frame.name] = {
            'frame': {
                'x': frame.x, 'y': frame.y,
                'w': frame.source_w, 'h': frame.source_h,
            },
            'rotated': False,
            'trimmed': frame.orig_w != frame.source_w or frame.orig_h != frame.source_h,
            'spriteSourceSize': {
                'x': 0, 'y': 0,
                'w': frame.source_w, 'h': frame.source_h,
            },
            'sourceSize': {
                'w': frame.orig_w, 'h': frame.orig_h,
            },
        }

    return {
        'meta': {
            'image': image_name,
            'size': {'w': sheet_w, 'h': sheet_h},
            'scale': 1,
        },
        'frames': frame_data,
    }


def build_spritesheet(
    image_paths: List[str],
    layout: str = LAYOUT_AUTO,
    spacing: int = 2,
    trim: bool = True,
    trim_padding: int = 2,
    alpha_threshold: int = 28,
    columns: int = 0,
    max_width: int = 0,
    power_of_two: bool = False,
    background: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Tuple[Image.Image, dict]:
    """Build a sprite sheet from image paths.

    Returns (canvas_image, metadata_dict).
    """
    if not image_paths:
        raise ValueError('No images provided')

    if layout not in LAYOUTS:
        raise ValueError(f'Unknown layout: {layout}')

    sorted_paths = sorted(image_paths, key=lambda p: natural_sort_key(os.path.basename(p)))
    frames: List[SpriteFrame] = []

    for path in sorted_paths:
        with Image.open(path) as img:
            orig_w, orig_h = img.size
            processed = trim_frame(img, trim_padding, alpha_threshold) if trim else img.convert('RGBA')
            name = os.path.basename(path)
            frames.append(SpriteFrame(
                name=name,
                image=processed,
                orig_w=orig_w,
                orig_h=orig_h,
            ))

    if layout == LAYOUT_AUTO:
        sheet_w, sheet_h = _layout_shelf(frames, spacing, max_width)
    elif layout == LAYOUT_GRID:
        sheet_w, sheet_h = _layout_grid(frames, spacing, columns)
    elif layout == LAYOUT_HORIZONTAL:
        sheet_w, sheet_h = _layout_strip(frames, spacing, horizontal=True)
    else:
        sheet_w, sheet_h = _layout_strip(frames, spacing, horizontal=False)

    if power_of_two:
        sheet_w = next_power_of_2(sheet_w)
        sheet_h = next_power_of_2(sheet_h)

    canvas = Image.new('RGBA', (max(sheet_w, 1), max(sheet_h, 1)), background)
    for frame in frames:
        canvas.paste(frame.image, (frame.x, frame.y), frame.image)

    image_name = 'spritesheet.png'
    metadata = build_metadata(frames, sheet_w, sheet_h, image_name)
    return canvas, metadata


def save_spritesheet(
    canvas: Image.Image,
    metadata: dict,
    output_path: str,
    export_json: bool = True,
) -> Tuple[int, Optional[str]]:
    """Save sprite sheet PNG and optional JSON metadata.

    Returns (png_file_size, json_path_or_none).
    """
    ensure_parent_dir(output_path)
    image_name = os.path.basename(output_path)
    metadata['meta']['image'] = image_name
    canvas.save(output_path, optimize=True)
    png_size = os.path.getsize(output_path)

    json_path = None
    if export_json:
        base, _ = os.path.splitext(output_path)
        json_path = base + '.json'
        with open(json_path, 'w', encoding='utf-8') as fh:
            json.dump(metadata, fh, indent=2, ensure_ascii=False)

    return png_size, json_path


def run_spritesheet_build(
    state,
    image_paths: List[str],
    output_path: str,
    layout: str = LAYOUT_AUTO,
    spacing: int = 2,
    trim: bool = True,
    trim_padding: int = 2,
    alpha_threshold: int = 28,
    columns: int = 0,
    max_width: int = 0,
    power_of_two: bool = False,
    export_json: bool = True,
    on_progress: Optional[Callable[[float, str], None]] = None,
) -> dict:
    """Build a sprite sheet from a list of image file paths."""
    logger = get_logger()
    errors: List[str] = []

    if state.cancelled:
        return _empty_result(cancelled=True)

    if len(image_paths) < 2:
        return {
            'errors': ['Need at least 2 images'],
            'cancelled': False,
            'frame_count': len(image_paths),
        }

    if on_progress:
        on_progress(10, 'loading')

    valid_paths = []
    for path in image_paths:
        if state.cancelled:
            return _empty_result(cancelled=True)
        if not os.path.isfile(path):
            errors.append(f'{os.path.basename(path)}: not found')
            continue
        valid_paths.append(path)

    if len(valid_paths) < 2:
        return {
            'errors': errors or ['Need at least 2 valid images'],
            'cancelled': False,
            'frame_count': len(valid_paths),
        }

    if on_progress:
        on_progress(30, 'packing')

    try:
        canvas, metadata = build_spritesheet(
            valid_paths,
            layout=layout,
            spacing=spacing,
            trim=trim,
            trim_padding=trim_padding,
            alpha_threshold=alpha_threshold,
            columns=columns,
            max_width=max_width,
            power_of_two=power_of_two,
        )
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.error("Sprite sheet build failed: %s", exc)
        return {
            'errors': [str(exc)],
            'cancelled': False,
            'frame_count': 0,
        }

    if state.cancelled:
        return _empty_result(cancelled=True)

    if on_progress:
        on_progress(80, 'saving')

    try:
        file_size, json_path = save_spritesheet(
            canvas, metadata, output_path, export_json=export_json,
        )
    except OSError as exc:
        logger.error("Sprite sheet save failed: %s", exc)
        return {
            'errors': [str(exc)],
            'cancelled': False,
            'frame_count': len(valid_paths),
        }

    if on_progress:
        on_progress(100, 'done')

    sheet_size = metadata['meta']['size']
    return {
        'errors': errors,
        'cancelled': False,
        'frame_count': len(valid_paths),
        'output_path': output_path,
        'json_path': json_path,
        'sheet_size': (sheet_size['w'], sheet_size['h']),
        'file_size': file_size,
    }


def _empty_result(cancelled: bool = False) -> dict:
    return {
        'errors': [],
        'cancelled': cancelled,
        'frame_count': 0,
    }
