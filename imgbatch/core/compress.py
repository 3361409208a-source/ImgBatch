#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Image compression logic — no GUI dependency."""


import io
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from PIL import Image, UnidentifiedImageError

from .common import (
    convert_to_rgb_if_needed, get_save_format, QUALITY_FORMATS, SUPPORTED_EXT,
)
from ..infra.logger import get_logger


def compress_image(
    src: str,
    dst: str,
    quality: int = 75,
    resize_pct: int = 100,
    exif_mode: str = "keep",
) -> int:
    """Compress a single image.

    Args:
        src: Source file path.
        dst: Destination file path.
        quality: JPEG/WebP quality (1-100).
        resize_pct: Resize percentage (1-100).
        exif_mode: ``keep``, ``strip``, or ``orientation_only``.

    Returns:
        New file size in bytes.

    Raises:
        UnidentifiedImageError: If Pillow can't open the file.
        OSError: On disk I/O errors.
    """
    ext = os.path.splitext(dst)[1].lower()
    with Image.open(src) as img:
        original_exif = img.info.get('exif')
        img = convert_to_rgb_if_needed(img, ext)

        if resize_pct < 100:
            w, h = img.size
            img = img.resize(
                (int(w * resize_pct / 100), int(h * resize_pct / 100)),
                Image.LANCZOS,
            )

        kw: dict = {'optimize': True}
        if ext in QUALITY_FORMATS:
            kw['quality'] = max(1, min(100, quality))

        # EXIF handling
        if exif_mode == 'keep' and original_exif:
            kw['exif'] = original_exif
        elif exif_mode == 'orientation_only' and original_exif:
            try:
                from PIL.ExifTags import Base as ExifBase
                exif = Image.Exif()
                exif.load(original_exif)
                orientation = exif.get(ExifBase.Orientation, None)
                if orientation:
                    new_exif = Image.Exif()
                    new_exif[ExifBase.Orientation] = orientation
                    kw['exif'] = new_exif.tobytes()
            except Exception:
                get_logger().debug("Failed to extract orientation-only EXIF", exc_info=True)

        save_fmt = get_save_format(ext)
        if save_fmt:
            img.save(dst, format=save_fmt, **kw)
        else:
            img.save(dst, **kw)

    return os.path.getsize(dst)


def estimate_compressed_size(
    file_data: List[dict],
    quality: int = 75,
    resize_pct: int = 100,
) -> Tuple[int, int]:
    """Estimate total compressed size by sampling per-format.

    Groups files by extension, samples the first of each format,
    and extrapolates.

    Returns:
        (total_before, total_after) in bytes.
    """
    if not file_data:
        return (0, 0)

    total_before = sum(d['size'] for d in file_data)
    per_format_ratios: Dict[str, float] = {}
    per_format_sizes: Dict[str, int] = {}

    # Group by extension
    for d in file_data:
        ext = Path(d['path']).suffix.lower()
        per_format_sizes[ext] = per_format_sizes.get(ext, 0) + d['size']

    # Sample first file of each format
    seen_formats: Set[str] = set()
    for d in file_data:
        ext = Path(d['path']).suffix.lower()
        if ext in seen_formats:
            continue
        seen_formats.add(ext)
        try:
            with Image.open(d['path']) as img:
                om = img.mode
                if om in ('RGBA', 'P', 'LA') and ext in ('.jpg', '.jpeg'):
                    rgb = Image.new('RGB', img.size, (255, 255, 255))
                    if om == 'P':
                        img = img.convert('RGBA')
                    rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb
                elif om not in ('RGB', 'L'):
                    img = img.convert('RGB')

                if resize_pct < 100:
                    w, h = img.size
                    img = img.resize(
                        (int(w * resize_pct / 100), int(h * resize_pct / 100)),
                        Image.LANCZOS,
                    )

                buf = io.BytesIO()
                kw: dict = {'optimize': True}
                if ext in QUALITY_FORMATS:
                    kw['quality'] = quality
                save_fmt = get_save_format(ext)
                if save_fmt:
                    img.save(buf, format=save_fmt, **kw)
                else:
                    img.save(buf, **kw)
                sample_after = buf.tell()
                ratio = sample_after / d['size'] if d['size'] else 0
                per_format_ratios[ext] = ratio
        except (UnidentifiedImageError, OSError) as exc:
            get_logger().debug("Preview sample failed for %s: %s", d['name'], exc)
            per_format_ratios[ext] = 1.0  # assume no compression

    total_after = 0
    for ext, size_total in per_format_sizes.items():
        ratio = per_format_ratios.get(ext, 1.0)
        total_after += max(int(size_total * ratio), 0)

    return (total_before, total_after)


def run_compress_batch(
    state,
    folder: str,
    file_list: List[str],
    quality: int,
    resize_pct: int,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    exif_mode: str = 'keep',
    options: Optional[dict] = None,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Run a batch compress/convert/watermark/rename operation.

    The ``state`` param is a :class:`~imgbatch.infra.threading.TaskState`
    that provides ``.cancelled`` and is required by the TaskRunner contract.

    Returns:
        Dict with keys: total_before, total_after, errors, rename_map
    """
    logger = get_logger()
    options = options or {}
    errors: List[str] = []
    rename_map: Dict[str, str] = {}
    total_before = 0
    total_after = 0
    total = len(file_list)

    if do_backup and backup_fn:
        try:
            backup_fn(folder, file_list)
        except OSError as exc:
            logger.error("Backup failed: %s", exc)
            return {
                'total_before': 0, 'total_after': 0,
                'errors': [f'Backup failed: {exc}'], 'rename_map': {},
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
        base, orig_ext = os.path.splitext(fname)
        orig_ext_l = orig_ext.lower()

        target_ext = options.get('target_fmt', orig_ext) if options.get('convert') else orig_ext
        target_ext_l = target_ext.lower()
        out_name = base + target_ext
        dst = os.path.join(folder if replace else out, out_name)

        try:
            with Image.open(src) as img:
                original_exif = img.info.get('exif')
                img = convert_to_rgb_if_needed(img, target_ext_l)

                if resize_pct < 100:
                    w, h = img.size
                    img = img.resize(
                        (int(w * resize_pct / 100), int(h * resize_pct / 100)),
                        Image.LANCZOS,
                    )

                if options.get('watermark') and options.get('wm_text'):
                    from .watermark import add_text_watermark
                    img = add_text_watermark(img, options['wm_text'], options.get('wm_opacity', 0.5))

                kw: dict = {'optimize': True}
                if target_ext_l in QUALITY_FORMATS:
                    kw['quality'] = max(1, min(100, quality))
                if exif_mode == 'keep' and original_exif:
                    kw['exif'] = original_exif

                save_fmt = get_save_format(target_ext_l)
                if save_fmt:
                    img.save(dst, format=save_fmt, **kw)
                else:
                    img.save(dst, **kw)

            if replace and target_ext_l != orig_ext_l and os.path.exists(src):
                try:
                    os.remove(src)
                except OSError:
                    pass

            sa = os.path.getsize(dst)
            total_after += sa

            if on_file_done:
                on_file_done(fname, sa)

            if options.get('rename'):
                new_name = options.get('prefix', '') + base + options.get('suffix', '') + target_ext
                if new_name != out_name:
                    rename_map[out_name] = new_name

        except (UnidentifiedImageError, OSError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i+1}/{total}')

    # Apply renames
    for old_name, new_name in rename_map.items():
        try:
            old_path = os.path.join(folder if replace else out, old_name)
            new_path = os.path.join(folder if replace else out, new_name)
            os.rename(old_path, new_path)
        except OSError as exc:
            errors.append(f'{old_name} -> {new_name}: {exc}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'rename_map': rename_map,
        'cancelled': state.cancelled,
    }
