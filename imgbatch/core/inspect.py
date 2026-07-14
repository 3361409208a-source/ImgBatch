#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inspect PNG images: canvas size, content bbox, padding metrics."""


import os
from typing import Callable, List, Optional

from PIL import Image, UnidentifiedImageError

from ..infra.logger import get_logger


def inspect_single(path: str) -> dict:
    """Inspect a single PNG file.

    Returns dict with keys:
        name, canvas, content, top_pad, bot_pad, left_pad, right_pad
        or name, canvas, content='transparent', pads='-'
    """
    name = os.path.basename(path)
    with Image.open(path) as img:
        img = img.convert('RGBA')
        w, h = img.size
        bbox = img.getbbox()
        if bbox:
            cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
            return {
                'name': name,
                'canvas': f'{w}x{h}',
                'content': f'{cw}x{ch}',
                'top_pad': str(bbox[1]),
                'bot_pad': str(h - 1 - bbox[3]),
                'left_pad': str(bbox[0]),
                'right_pad': str(w - 1 - bbox[2]),
            }
        else:
            return {
                'name': name,
                'canvas': f'{w}x{h}',
                'content': 'transparent',
                'top_pad': '-', 'bot_pad': '-',
                'left_pad': '-', 'right_pad': '-',
            }


def run_inspect_batch(
    state,
    png_list: List[dict],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_result: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Run batch inspection of PNG files.

    png_list: list of file info dicts (must have 'path' and 'name' keys)

    Returns dict with results list and errors list.
    """
    logger = get_logger()
    results: List[dict] = []
    errors: List[str] = []
    total = len(png_list)

    for i, d in enumerate(png_list):
        if state.cancelled:
            break

        path = d['path']
        try:
            info = inspect_single(path)
            results.append(info)
            if on_result:
                on_result(info)
        except (UnidentifiedImageError, OSError) as exc:
            err_entry = {
                'name': d['name'],
                'canvas': 'error',
                'content': str(exc),
                'top_pad': '', 'bot_pad': '',
                'left_pad': '', 'right_pad': '',
            }
            results.append(err_entry)
            errors.append(f'{d["name"]}: {exc}')
            if on_result:
                on_result(err_entry)

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i+1}/{total}')

    return {
        'results': results,
        'errors': errors,
        'cancelled': state.cancelled,
    }
