#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smart Background Removal / Matting core module.

Supports:
- Local Smart Matting (Color & Edge analysis with adaptive flood-fill and feathering)
- Optional rembg AI model integration (when rembg package is installed)
- Background output modes:
  - 'transparent': PNG / WebP with alpha transparency
  - 'color': Composite onto solid color (White, ID Red, ID Blue, Black, Custom Hex)
  - 'mask': Export single-channel Alpha mask
"""

import os
import re
from typing import Callable, List, Optional, Tuple
from PIL import Image, ImageChops, ImageFilter, ImageOps, UnidentifiedImageError

from .common import QUALITY_FORMATS, TRIM_SUPPORTED_EXT, ensure_parent_dir, get_save_format
from ..infra.logger import get_logger


def parse_hex_color(color_str: str) -> Tuple[int, int, int]:
    """Parse color string like '#FFFFFF' or 'white' or '#DC2626' into (R, G, B)."""
    s = color_str.strip().lstrip('#')
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except ValueError:
            pass
    elif len(s) == 3:
        try:
            return (int(s[0] * 2, 16), int(s[1] * 2, 16), int(s[2] * 2, 16))
        except ValueError:
            pass
    # Color presets fallback
    preset_map = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (220, 38, 38),     # #DC2626 ID Red
        'blue': (37, 99, 235),    # #2563EB ID Blue
    }
    return preset_map.get(s.lower(), (255, 255, 255))


def _extract_border_seeds(img: Image.Image) -> List[Tuple[int, int, int]]:
    """Sample representative background seed colors from image border edges."""
    w, h = img.size
    rgb = img.convert('RGB')
    samples = []

    # Corner samples and edge samples
    sample_points = [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
        (w // 4, 0), (3 * w // 4, 0), (w // 4, h - 1), (3 * w // 4, h - 1),
    ]

    for x, y in sample_points:
        if 0 <= x < w and 0 <= y < h:
            samples.append(rgb.getpixel((x, y)))

    return samples


def _build_smart_mask(
    img: Image.Image,
    sensitivity: int = 30,
    feather: int = 1,
) -> Image.Image:
    """Generate foreground alpha mask using color distance and edge analysis.

    Sensitivity: 1 (strictest) to 100 (most aggressive background removal).
    Feather: 0 to 10 (edge blur radius).
    Returns a grayscale Image (mode 'L') where 255 = foreground, 0 = background.
    """
    w, h = img.size
    rgba = img.convert('RGBA')

    # 1. Existing Alpha Channel check
    alpha = rgba.getchannel('A')
    a_min, a_max = alpha.getextrema()
    has_alpha = a_min < 250

    rgb = rgba.convert('RGB')
    seeds = _extract_border_seeds(rgb)

    # Convert sensitivity (1..100) to color threshold (roughly 10..180 distance)
    # Threshold in RGB distance space
    threshold = max(10, int(sensitivity * 1.8))

    # Compute minimum color distance to border background seed samples
    # We create a composite mask of background probability
    r_chan, g_chan, b_chan = rgb.split()

    bg_mask = Image.new('L', (w, h), 0)

    for sr, sg, sb in seeds:
        r_diff = ImageChops.difference(r_chan, Image.new('L', (w, h), sr))
        g_diff = ImageChops.difference(g_chan, Image.new('L', (w, h), sg))
        b_diff = ImageChops.difference(b_chan, Image.new('L', (w, h), sb))

        # Max delta across RGB
        diff = ImageChops.lighter(ImageChops.lighter(r_diff, g_diff), b_diff)

        # Distance thresholding: 0 where color is close to background seed (bg)
        seed_bg = diff.point(lambda d: 255 if d <= threshold else 0)
        bg_mask = ImageChops.lighter(bg_mask, seed_bg)

    # If image already had transparent areas, treat transparent pixels as background
    if has_alpha:
        alpha_bg = alpha.point(lambda a: 255 if a < 128 else 0)
        bg_mask = ImageChops.lighter(bg_mask, alpha_bg)

    # Invert bg_mask to get fg_mask (255 = foreground)
    fg_mask = ImageOps.invert(bg_mask)

    # Smooth & feather edges
    if feather > 0:
        fg_mask = fg_mask.filter(ImageFilter.GaussianBlur(radius=feather))

    return fg_mask


def _onnx_u2net_matting(img: Image.Image, model_path: str) -> Optional[Image.Image]:
    """Run direct ONNX Runtime U2-Net model inference on PIL Image."""
    try:
        import onnxruntime as ort
        import numpy as np

        w, h = img.size
        # Preprocess: RGB resize to 320x320, normalize to [0, 1]
        resized = img.convert('RGB').resize((320, 320), Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        # Normalize with ImageNet mean & std
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        # Transpose HWC -> CHW -> NCHW (1, 3, 320, 320)
        tensor = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]

        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        outs = session.run([output_name], {input_name: tensor})

        # Process output mask (1, 1, 320, 320) -> min-max normalize -> PIL Image
        mask_arr = outs[0][0, 0]
        ma, mi = np.max(mask_arr), np.min(mask_arr)
        if ma > mi:
            mask_arr = (mask_arr - mi) / (ma - mi) * 255.0
        else:
            mask_arr = mask_arr * 0.0

        mask_img = Image.fromarray(mask_arr.astype(np.uint8), mode='L').resize((w, h), Image.Resampling.BILINEAR)
        res_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        res_img.paste(img.convert('RGBA'), mask=mask_img)
        return res_img
    except Exception as exc:
        logger = get_logger()
        logger.info("ONNX U2-Net direct inference failed: %s", exc)
        return None


def _rembg_matting(img: Image.Image) -> Optional[Image.Image]:
    """Attempt AI Matting using rembg or direct ONNX Runtime model if available."""
    # 1. Try rembg package
    try:
        import io
        from rembg import remove  # type: ignore

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        result_bytes = remove(buf.getvalue())
        return Image.open(io.BytesIO(result_bytes)).convert('RGBA')
    except Exception:
        pass

    # 2. Try direct ONNX Runtime on downloaded model file ~/.u2net/u2net.onnx
    from pathlib import Path
    u2net_path = Path.home() / '.u2net' / 'u2net.onnx'
    if u2net_path.is_file():
        res = _onnx_u2net_matting(img, str(u2net_path))
        if res:
            return res

    logger = get_logger()
    logger.info("rembg package / ONNX model not ready for AI matting")
    return None


def matting_image(
    src: str,
    dst: str,
    engine: str = 'smart',
    bg_mode: str = 'transparent',
    bg_color: str = '#FFFFFF',
    feather: int = 1,
    sensitivity: int = 30,
) -> int:
    """Perform matting on a single image.

    Params:
    - engine: 'smart' (local analysis) or 'rembg' (AI model)
    - bg_mode: 'transparent', 'color', 'mask'
    - bg_color: Hex color string like '#FFFFFF', '#DC2626', '#2563EB'
    - feather: 0-10 edge smoothing
    - sensitivity: 1-100 background sensitivity

    Returns file size in bytes.
    """
    with Image.open(src) as img:
        img_rgba = img.convert('RGBA')
        w, h = img_rgba.size

        fg_mask: Optional[Image.Image] = None

        if engine == 'rembg':
            rembg_res = _rembg_matting(img_rgba)
            if rembg_res:
                fg_mask = rembg_res.getchannel('A')
                # If transparent output requested, we can use rembg directly
                if bg_mode == 'transparent':
                    rembg_res.save(dst, format='PNG')
                    return os.path.getsize(dst)

        if fg_mask is None:
            fg_mask = _build_smart_mask(img_rgba, sensitivity=sensitivity, feather=feather)

        # Process output based on bg_mode
        ext = os.path.splitext(dst)[1].lower()

        if bg_mode == 'mask':
            # Export grayscale alpha mask
            fg_mask.save(dst)
            return os.path.getsize(dst)

        if bg_mode == 'color':
            rgb_color = parse_hex_color(bg_color)
            canvas = Image.new('RGB', (w, h), rgb_color)
            canvas.paste(img_rgba.convert('RGB'), mask=fg_mask)

            save_fmt = get_save_format(ext) or ('JPEG' if ext in ('.jpg', '.jpeg') else 'PNG')
            if save_fmt == 'JPEG':
                canvas.save(dst, format=save_fmt, quality=92)
            else:
                canvas.save(dst, format=save_fmt)
            return os.path.getsize(dst)

        # Default: 'transparent'
        transparent_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        transparent_img.paste(img_rgba, mask=fg_mask)

        # Force PNG/WebP if output extension doesn't support alpha (like JPG)
        if ext in ('.jpg', '.jpeg'):
            dst_png = os.path.splitext(dst)[0] + '.png'
            transparent_img.save(dst_png, format='PNG')
            return os.path.getsize(dst_png)
        else:
            save_fmt = get_save_format(ext) or 'PNG'
            transparent_img.save(dst, format=save_fmt)
            return os.path.getsize(dst)


def run_matting_batch(
    state,
    folder: str,
    file_list: List[str],
    engine: str = 'smart',
    bg_mode: str = 'transparent',
    bg_color: str = '#FFFFFF',
    feather: int = 1,
    sensitivity: int = 30,
    do_backup: bool = False,
    replace: bool = False,
    out: Optional[str] = None,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run batch image background removal / matting."""
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0

    if not file_list:
        return {
            'total_before': 0, 'total_after': 0,
            'errors': [], 'cancelled': False,
        }

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

        # Target filename handling
        if replace:
            dst = src
        else:
            dst = os.path.join(out, fname)

        # If saving transparent mode to JPG, convert output target extension to .png
        ext = os.path.splitext(dst)[1].lower()
        if bg_mode == 'transparent' and ext in ('.jpg', '.jpeg'):
            dst = os.path.splitext(dst)[0] + '.png'

        ensure_parent_dir(dst)

        try:
            sa = matting_image(
                src, dst,
                engine=engine,
                bg_mode=bg_mode,
                bg_color=bg_color,
                feather=feather,
                sensitivity=sensitivity,
            )
            total_after += sa
            if on_file_done:
                on_file_done(fname, sa)
        except (UnidentifiedImageError, OSError, Exception) as exc:
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
