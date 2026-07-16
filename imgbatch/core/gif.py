#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Animated GIF editing — frame-aware batch operations."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError

from .common import ensure_parent_dir
from .spritesheet import natural_sort_key, trim_frame
from .watermark import add_image_watermark, add_text_watermark
from ..infra.logger import get_logger

GIF_MODES = (
    'optimize',
    'resize',
    'speed',
    'set_fps',
    'loop',
    'reverse',
    'extract',
    'compose',
    'crop',
    'trim',
    'rotate',
    'flip',
    'frame_step',
    'merge',
    'watermark',
    'reduce_colors',
    'set_delay',
)


def n_frames(img: Image.Image) -> int:
    return int(getattr(img, 'n_frames', 1) or 1)


def is_gif_path(path: str) -> bool:
    return Path(path).suffix.lower() == '.gif'


def probe_gif(path: str) -> dict:
    """Return animation metadata for a GIF file."""
    with Image.open(path) as img:
        count = n_frames(img)
        durations: List[int] = []
        for i in range(count):
            img.seek(i)
            durations.append(int(img.info.get('duration', 100) or 100))
        loop = int(img.info.get('loop', 0) or 0)
        total_ms = sum(durations)
        fps = round(1000.0 * count / total_ms, 2) if total_ms > 0 else 0.0
        return {
            'path': path,
            'is_animated': count > 1,
            'n_frames': count,
            'width': img.width,
            'height': img.height,
            'duration_ms': total_ms,
            'avg_fps': fps,
            'loop': loop,
            'durations': durations,
        }


def load_gif(path: str) -> Tuple[List[Image.Image], List[int], int]:
    """Load all frames as RGBA plus per-frame durations and loop count."""
    frames: List[Image.Image] = []
    durations: List[int] = []
    loop = 0
    with Image.open(path) as img:
        loop = int(img.info.get('loop', 0) or 0)
        count = n_frames(img)
        for i in range(count):
            img.seek(i)
            frames.append(img.copy().convert('RGBA'))
            durations.append(int(img.info.get('duration', 100) or 100))
    return frames, durations, loop


def _rgba_to_palette(frame: Image.Image, colors: int = 256) -> Image.Image:
    rgba = frame.convert('RGBA')
    pal = rgba.convert('P', palette=Image.ADAPTIVE, colors=max(2, min(256, colors)))
    alpha = rgba.getchannel('A')
    mask = alpha.point(lambda a: 255 if a < 128 else 0)
    pal.paste(255, mask)
    return pal


def save_gif(
    frames: List[Image.Image],
    durations: List[int],
    dst: str,
    *,
    loop: int = 0,
    optimize: bool = True,
    colors: int = 256,
) -> int:
    if not frames:
        raise ValueError('No frames to save')

    durs = [max(10, int(d)) for d in durations]
    if len(durs) < len(frames):
        durs.extend([durs[-1] if durs else 100] * (len(frames) - len(durs)))

    pals = [_rgba_to_palette(f, colors) for f in frames]
    ensure_parent_dir(dst)
    pals[0].save(
        dst,
        format='GIF',
        save_all=True,
        append_images=pals[1:],
        duration=durs,
        loop=loop,
        disposal=2,
        optimize=optimize,
        transparency=255,
    )
    return os.path.getsize(dst)


def _resize_frame(frame: Image.Image, resize_pct: int) -> Image.Image:
    if resize_pct >= 100:
        return frame
    w, h = frame.size
    return frame.resize(
        (max(1, int(w * resize_pct / 100)), max(1, int(h * resize_pct / 100))),
        Image.LANCZOS,
    )


def _fit_frame(frame: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = frame.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale >= 1.0:
        return frame
    return frame.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)


def _apply_speed(durations: List[int], factor: float) -> List[int]:
    factor = max(0.05, factor)
    return [max(10, int(d / factor)) for d in durations]


def _apply_fps(durations: List[int], target_fps: float) -> List[int]:
    target_fps = max(0.1, target_fps)
    ms = max(10, int(1000 / target_fps))
    return [ms] * len(durations)


def _crop_frames(
    frames: List[Image.Image],
    box: Optional[Tuple[int, int, int, int]],
    auto_trim: bool,
    padding: int,
    alpha_threshold: int,
) -> List[Image.Image]:
    if auto_trim:
        return [
            trim_frame(f, padding=padding, alpha_threshold=alpha_threshold)
            for f in frames
        ]
    if not box:
        return frames
    return [f.crop(box) for f in frames]


def _rotate_frames(frames: List[Image.Image], angle: int) -> List[Image.Image]:
    angle = angle % 360
    if angle == 0:
        return frames
    return [f.rotate(angle, expand=True) for f in frames]


def _flip_frames(frames: List[Image.Image], direction: str) -> List[Image.Image]:
    if direction == 'horizontal':
        return [f.transpose(Image.FLIP_LEFT_RIGHT) for f in frames]
    if direction == 'vertical':
        return [f.transpose(Image.FLIP_TOP_BOTTOM) for f in frames]
    return frames


def _frame_step(frames: List[Image.Image], durations: List[int], step: int) -> Tuple[List[Image.Image], List[int]]:
    step = max(1, step)
    if step == 1:
        return frames, durations
    out_f: List[Image.Image] = []
    out_d: List[int] = []
    for i in range(0, len(frames), step):
        out_f.append(frames[i])
        out_d.append(durations[i] if i < len(durations) else 100)
    return out_f, out_d


def _watermark_frames(frames: List[Image.Image], params: dict) -> List[Image.Image]:
    wm_type = params.get('type', 'text')
    position = params.get('position', 'bottom-right')
    opacity = params.get('opacity', 0.5)
    if isinstance(opacity, (int, float)) and opacity > 1.0:
        opacity = opacity / 100.0

    out: List[Image.Image] = []
    if wm_type == 'image' and params.get('image_path'):
        with Image.open(params['image_path']) as wm_img:
            wm_copy = wm_img.convert('RGBA')
            for fr in frames:
                out.append(add_image_watermark(
                    fr, wm_copy,
                    scale_pct=params.get('img_scale', 20),
                    opacity=opacity,
                    position=position,
                ))
    else:
        text = params.get('text', 'GIF')
        for fr in frames:
            out.append(add_text_watermark(
                fr,
                text=text,
                opacity=opacity,
                fontsize=params.get('fontsize'),
                color=params.get('color', '#ffffff'),
                position=position,
            ))
    return out


def process_gif_file(
    src: str,
    dst: str,
    mode: str,
    params: dict,
) -> dict:
    """Apply one GIF edit mode to a single file. Returns result metadata."""
    mode = (mode or 'optimize').lower()
    if mode not in GIF_MODES:
        raise ValueError(f'Unknown GIF mode: {mode}')

    if mode == 'compose':
        raise ValueError('compose mode uses run_gif_compose, not single file')

    if mode == 'extract':
        out_dir = params.get('extract_dir') or os.path.splitext(dst)[0] + '_frames'
        os.makedirs(out_dir, exist_ok=True)
        frames, durations, loop = load_gif(src)
        saved: List[str] = []
        for i, frame in enumerate(frames):
            name = f'frame_{i:04d}.png'
            path = os.path.join(out_dir, name)
            frame.save(path, optimize=True)
            saved.append(path)
        return {
            'mode': mode,
            'frames_extracted': len(saved),
            'output_dir': out_dir,
            'size': sum(os.path.getsize(p) for p in saved),
            'loop': loop,
            'durations': durations,
        }

    frames, durations, loop = load_gif(src)
    colors = int(params.get('colors', 256))
    optimize = bool(params.get('optimize', True))

    if mode == 'merge':
        raise ValueError('merge mode handled in batch')

    if mode == 'reverse':
        frames = list(reversed(frames))
        durations = list(reversed(durations))

    if mode == 'speed':
        frames = frames
        durations = _apply_speed(durations, float(params.get('speed_factor', 1.0)))

    if mode == 'set_fps':
        durations = _apply_fps(durations, float(params.get('target_fps', 10)))

    if mode == 'set_delay':
        delay = max(10, int(params.get('frame_delay', 100)))
        durations = [delay] * len(frames)

    if mode == 'frame_step':
        frames, durations = _frame_step(frames, durations, int(params.get('frame_step', 2)))

    if mode in ('optimize', 'resize', 'reduce_colors'):
        resize_pct = int(params.get('resize_pct', 100))
        max_w = int(params.get('max_width', 0))
        max_h = int(params.get('max_height', 0))
        if mode == 'reduce_colors':
            colors = int(params.get('colors', 128))
        resized: List[Image.Image] = []
        for fr in frames:
            f = fr
            if max_w > 0 or max_h > 0:
                f = _fit_frame(f, max_w or 99999, max_h or 99999)
            elif resize_pct < 100:
                f = _resize_frame(f, resize_pct)
            resized.append(f)
        frames = resized

    if mode == 'crop' or (mode == 'trim'):
        box = None
        if mode == 'crop' and not params.get('auto_trim', False):
            right = int(params.get('right') or frames[0].width)
            bottom = int(params.get('bottom') or frames[0].height)
            box = (
                int(params.get('left', 0)),
                int(params.get('top', 0)),
                right,
                bottom,
            )
        frames = _crop_frames(
            frames,
            box,
            auto_trim=bool(params.get('auto_trim', mode == 'trim')),
            padding=int(params.get('padding', 4)),
            alpha_threshold=int(params.get('alpha_threshold', 28)),
        )

    if mode == 'rotate':
        frames = _rotate_frames(frames, int(params.get('angle', 90)))

    if mode == 'flip':
        frames = _flip_frames(frames, params.get('direction', 'horizontal'))

    if mode == 'watermark':
        frames = _watermark_frames(frames, params.get('watermark', params))

    if mode == 'loop':
        loop = int(params.get('loop', 0))

    size = save_gif(
        frames,
        durations,
        dst,
        loop=loop,
        optimize=optimize,
        colors=colors,
    )
    return {
        'mode': mode,
        'n_frames': len(frames),
        'size': size,
        'loop': loop,
    }


def compose_gif_from_images(
    image_paths: List[str],
    dst: str,
    *,
    frame_duration: int = 100,
    loop: int = 0,
    colors: int = 256,
    optimize: bool = True,
) -> dict:
    paths = sorted(image_paths, key=lambda p: natural_sort_key(Path(p).name))
    if not paths:
        raise ValueError('No images selected for compose')
    frames: List[Image.Image] = []
    for p in paths:
        with Image.open(p) as img:
            frames.append(img.convert('RGBA'))
    durations = [max(10, frame_duration)] * len(frames)
    size = save_gif(frames, durations, dst, loop=loop, optimize=optimize, colors=colors)
    return {'mode': 'compose', 'n_frames': len(frames), 'size': size, 'loop': loop}


def merge_gifs(paths: List[str], dst: str, *, colors: int = 256, optimize: bool = True) -> dict:
    if len(paths) < 2:
        raise ValueError('Merge requires at least 2 GIF files')
    all_frames: List[Image.Image] = []
    all_durations: List[int] = []
    loop = 0
    for p in paths:
        frames, durations, loop = load_gif(p)
        all_frames.extend(frames)
        all_durations.extend(durations)
    size = save_gif(all_frames, all_durations, dst, loop=loop, optimize=optimize, colors=colors)
    return {'mode': 'merge', 'n_frames': len(all_frames), 'size': size, 'sources': len(paths)}


def compress_gif_animated(
    src: str,
    dst: str,
    *,
    resize_pct: int = 100,
    colors: int = 256,
) -> int:
    """Preserve animation when compressing GIF → GIF."""
    frames, durations, loop = load_gif(src)
    if resize_pct < 100:
        frames = [_resize_frame(f, resize_pct) for f in frames]
    return save_gif(frames, durations, dst, loop=loop, optimize=True, colors=colors)


def convert_gif_to_gif(src: str, dst: str, *, colors: int = 256) -> int:
    return compress_gif_animated(src, dst, resize_pct=100, colors=colors)


def run_gif_batch(
    state,
    folder: str,
    file_list: List[str],
    mode: str,
    params: dict,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Batch GIF editing."""
    logger = get_logger()
    mode = (mode or 'optimize').lower()
    errors: List[str] = []
    results: List[dict] = []
    total_before = 0
    total_after = 0

    if mode == 'compose':
        image_paths = [
            os.path.join(folder, n) for n in file_list
            if Path(n).suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
        ]
        if len(image_paths) < 2:
            return {
                'errors': ['compose requires at least 2 images'],
                'cancelled': False,
                'results': [],
            }
        output = params.get('output') or os.path.join(folder, 'animation.gif')
        if not output.lower().endswith('.gif'):
            output += '.gif'
        try:
            meta = compose_gif_from_images(
                image_paths,
                output,
                frame_duration=int(params.get('frame_duration', 100)),
                loop=int(params.get('loop', 0)),
                colors=int(params.get('colors', 256)),
            )
            total_after = meta.get('size', 0)
            results.append({'output': output, **meta})
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            errors.append(str(exc))
        return {
            'total_before': total_before,
            'total_after': total_after,
            'errors': errors,
            'cancelled': state.cancelled,
            'results': results,
        }

    if mode == 'merge':
        gif_paths = sorted(
            [os.path.join(folder, n) for n in file_list if n.lower().endswith('.gif')],
            key=lambda p: natural_sort_key(Path(p).name),
        )
        if len(gif_paths) < 2:
            return {
                'errors': ['merge requires at least 2 GIF files'],
                'cancelled': False,
                'results': [],
            }
        output = params.get('output') or os.path.join(folder, 'merged.gif')
        if not output.lower().endswith('.gif'):
            output += '.gif'
        try:
            for p in gif_paths:
                total_before += os.path.getsize(p)
            meta = merge_gifs(gif_paths, output, colors=int(params.get('colors', 256)))
            total_after = meta.get('size', 0)
            results.append({'output': output, **meta})
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            errors.append(str(exc))
        return {
            'total_before': total_before,
            'total_after': total_after,
            'errors': errors,
            'cancelled': state.cancelled,
            'results': results,
        }

    gif_list = [f for f in file_list if f.lower().endswith('.gif')]
    if not gif_list:
        return {
            'errors': ['No GIF files in selection'],
            'cancelled': False,
            'results': [],
        }

    backup_dir = None
    if do_backup and backup_fn:
        try:
            backup_dir = backup_fn(folder, gif_list)
        except OSError as exc:
            return {
                'errors': [f'Backup failed: {exc}'],
                'cancelled': False,
                'results': [],
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    total = len(gif_list)
    for i, fname in enumerate(gif_list):
        if state.cancelled:
            break
        src = os.path.join(folder, fname)
        try:
            total_before += os.path.getsize(src)
        except OSError as exc:
            errors.append(f'{fname}: {exc}')
            continue

        if mode == 'extract':
            extract_root = out if (not replace and out) else os.path.join(folder, '_gif_frames')
            base = os.path.splitext(fname)[0]
            params_copy = dict(params)
            params_copy['extract_dir'] = os.path.join(extract_root, base + '_frames')
            dst = src
        else:
            base = os.path.splitext(fname)[0]
            dst = src if replace else os.path.join(out or folder, base + '.gif')
            if not replace:
                ensure_parent_dir(dst)

        try:
            meta = process_gif_file(src, dst, mode, params)
            if mode == 'extract':
                total_after += int(meta.get('size', 0))
            else:
                total_after += os.path.getsize(dst)
            results.append({'file': fname, **meta})
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            logger.debug('GIF edit failed for %s', fname, exc_info=True)
            errors.append(f'{fname}: {exc}')

        if on_progress:
            on_progress((i + 1) / total * 100, f'{i + 1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
        'results': results,
    }
