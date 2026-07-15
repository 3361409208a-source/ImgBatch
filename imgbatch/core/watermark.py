#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Watermark logic — no GUI dependency."""


import os
from typing import Callable, List, Optional, Union

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from .common import calc_position, ensure_parent_dir, hex_to_rgba
from ..infra.logger import get_logger


def _load_font(size: int) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    """Try common system fonts, fall back to default."""
    for font_name in ('simhei.ttf', 'msyh.ttc', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def add_text_watermark(
    img: Image.Image,
    text: str,
    opacity: float = 0.5,
    fontsize: Optional[int] = None,
    color: str = '#ffffff',
    position: str = 'bottom-right',
) -> Image.Image:
    """Add a text watermark to an image. Returns RGBA image."""
    img = img.convert('RGBA')
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if fontsize is None:
        fontsize = max(12, int(min(img.size) * 0.04))

    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = calc_position(img.size, (tw, th), position, margin=20)
    alpha = int(max(0.0, min(1.0, opacity)) * 255)
    rgba_color = hex_to_rgba(color, alpha)
    draw.text((x, y), text, fill=rgba_color, font=font)

    result = Image.alpha_composite(img, layer)
    return result


def add_image_watermark(
    img: Image.Image,
    wm_img: Image.Image,
    scale_pct: float = 20,
    opacity: float = 0.5,
    position: str = 'bottom-right',
) -> Image.Image:
    """Add an image watermark (logo) to an image. Returns RGBA image."""
    img = img.convert('RGBA')
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))

    w = img.width
    wm_w = int(w * scale_pct / 100)
    wm_h = int(wm_img.height * wm_w / max(wm_img.width, 1))
    wm_resized = wm_img.resize((wm_w, wm_h), Image.LANCZOS)

    if opacity < 1.0:
        alpha = wm_resized.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        wm_resized.putalpha(alpha)

    x, y = calc_position(img.size, (wm_w, wm_h), position, margin=20)
    layer.paste(wm_resized, (x, y), wm_resized)

    result = Image.alpha_composite(img, layer)
    return result


def run_watermark_batch(
    state,
    folder: str,
    file_list: List[str],
    params: dict,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch watermark application.

    params keys: type ('text'|'image'), text, fontsize, opacity,
                 position, color, image_path, img_scale
    """
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0
    total = len(file_list)

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

    # Pre-load watermark image if needed
    wm_img = None
    if params.get('type') == 'image':
        try:
            wm_img = Image.open(params['image_path']).convert('RGBA')
        except (UnidentifiedImageError, OSError) as exc:
            return {
                'total_before': 0, 'total_after': 0,
                'errors': [f'Watermark image load failed: {exc}'],
                'cancelled': False,
            }

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
        dst = src if replace else os.path.join(out, fname)
        if not replace:
            ensure_parent_dir(dst)

        try:
            img = Image.open(src).convert('RGBA')

            if params.get('type') == 'text':
                result = add_text_watermark(
                    img, params.get('text', ''),
                    opacity=params.get('opacity', 0.5),
                    fontsize=params.get('fontsize', 36),
                    color=params.get('color', '#ffffff'),
                    position=params.get('position', 'bottom-right'),
                )
            else:
                result = add_image_watermark(
                    img, wm_img,
                    scale_pct=params.get('img_scale', 20),
                    opacity=params.get('opacity', 0.5),
                    position=params.get('position', 'bottom-right'),
                )

            # Convert back if original wasn't RGBA
            if not src.lower().endswith('.png'):
                result = result.convert('RGB')

            save_ext = os.path.splitext(dst)[1].lower()
            if save_ext in ('.jpg', '.jpeg'):
                result = result.convert('RGB')
            result.save(dst, optimize=True)
            img.close()
            result.close()

            sa = os.path.getsize(dst)
            total_after += sa
            if on_file_done:
                on_file_done(fname, sa)

        except (UnidentifiedImageError, OSError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i+1}/{total}')

    if wm_img:
        wm_img.close()

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
