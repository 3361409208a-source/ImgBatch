#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert video files (WebM/MP4/…) to animated WebP or GIF.

Preserves VP9 alpha when decoding with libvpx-vp9, optionally cleans dark
matte fringe, and patches animated WebP ANMF flags (disposal=1, blend=0)
to avoid ghosting on semi-transparent frames.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional

from PIL import Image

from .common import ensure_parent_dir
from .webm_compress import find_ffmpeg
from ..infra.logger import get_logger

VIDEO_EXT = {'.webm', '.mp4', '.mov', '.avi', '.mkv', '.m4v'}
TARGET_EXT = {'.webp', '.gif'}


def is_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in VIDEO_EXT


def _norm_target(target: str) -> str:
    t = (target or '.webp').lower().strip()
    if not t.startswith('.'):
        t = '.' + t
    if t not in TARGET_EXT:
        raise ValueError(f'unsupported target format: {target}')
    return t


def _scale_vf(max_edge: int) -> str:
    if max_edge and max_edge > 0:
        return (
            f"scale='if(gt(iw,ih),{max_edge},-2)'"
            f":'if(gt(ih,iw),{max_edge},-2)':flags=lanczos"
        )
    return 'scale=iw:ih'


def _white_key_filter(similarity: float = 0.12, blend: float = 0.04) -> str:
    """ffmpeg colorkey filter for solid white backgrounds."""
    sim = max(0.01, min(1.0, float(similarity)))
    bl = max(0.0, min(1.0, float(blend)))
    return f'colorkey=0xFFFFFF:{sim:.3f}:{bl:.3f},format=rgba'


def _vf_prefix(
    *,
    white_key: bool,
    white_key_similarity: float,
    white_key_blend: float,
) -> str:
    if not white_key:
        return ''
    return _white_key_filter(white_key_similarity, white_key_blend) + ','


def _input_args(src: str, keep_alpha: bool) -> List[str]:
    """Prefer libvpx-vp9 for WebM so VP9 alpha is not dropped."""
    if keep_alpha and Path(src).suffix.lower() == '.webm':
        return ['-c:v', 'libvpx-vp9', '-i', src]
    return ['-i', src]


def clean_fringe_frame(im: Image.Image) -> Image.Image:
    """Remove muddy dark fringe left by bad chroma-key / matting."""
    im = im.convert('RGBA')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                px[x, y] = (0, 0, 0, 0)
                continue

            lum = (r + g + b) / 3.0

            if a < 200 and lum < 45:
                px[x, y] = (0, 0, 0, 0)
                continue
            if a < 90 and lum < 90:
                px[x, y] = (0, 0, 0, 0)
                continue

            if a < 180 and lum < 110:
                a = max(0, int(a * (lum / 140)))
                if a < 24:
                    px[x, y] = (0, 0, 0, 0)
                    continue

            r = min(255, int(r * 1.08 + 6))
            g = min(255, int(g * 1.06 + 4))
            b = min(255, int(b * 1.08 + 8))
            px[x, y] = (r, g, b, a)
    return im


def patch_webp_anmf_disposal(path: str) -> int:
    """Set every ANMF frame to dispose-to-background + no blend.

    Returns number of frames patched.
    """
    data = bytearray(Path(path).read_bytes())
    i = 12
    n = 0
    while i + 8 <= len(data):
        tag = data[i : i + 4]
        size = int.from_bytes(data[i + 4 : i + 8], 'little')
        if tag == b'ANMF' and size >= 16:
            flag_off = i + 8 + 15
            if flag_off < len(data):
                data[flag_off] = (data[flag_off] & ~0x02) | 0x01
                n += 1
        i += 8 + size + (size & 1)
    Path(path).write_bytes(data)
    return n


def _run_ffmpeg(cmd: List[str]) -> None:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or 'ffmpeg failed')[-1500:]
        raise RuntimeError(tail.strip())


def _extract_frames(
    ffmpeg: str,
    src: str,
    frame_dir: str,
    *,
    max_edge: int,
    fps: int,
    keep_alpha: bool,
    white_key: bool = False,
    white_key_similarity: float = 0.12,
    white_key_blend: float = 0.04,
) -> List[str]:
    pattern = os.path.join(frame_dir, 'f_%05d.png')
    prefix = _vf_prefix(
        white_key=white_key,
        white_key_similarity=white_key_similarity,
        white_key_blend=white_key_blend,
    )
    vf = f'{prefix}{_scale_vf(max_edge)},format=rgba'
    cmd = [ffmpeg, '-y', *_input_args(src, keep_alpha)]
    if fps and fps > 0:
        cmd += ['-r', str(fps)]
    cmd += ['-vf', vf, '-start_number', '0', pattern]
    _run_ffmpeg(cmd)
    frames = sorted(Path(frame_dir).glob('f_*.png'))
    if not frames:
        raise RuntimeError('no frames extracted from video')
    return [str(p) for p in frames]


def _save_webp_from_frames(
    frame_paths: List[str],
    dst: str,
    *,
    fps: int,
    quality: int,
    clean_fringe: bool,
) -> None:
    duration = max(10, int(round(1000 / max(1, fps))))
    frames: List[Image.Image] = []
    for path in frame_paths:
        im = Image.open(path)
        if clean_fringe:
            im = clean_fringe_frame(im)
        else:
            im = im.convert('RGBA')
        frames.append(im)

    ensure_parent_dir(dst)
    frames[0].save(
        dst,
        format='WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        lossless=False,
        quality=max(1, min(100, quality)),
        method=6,
    )
    for im in frames:
        im.close()
    patch_webp_anmf_disposal(dst)


def _save_gif_from_frames(
    frame_paths: List[str],
    dst: str,
    *,
    fps: int,
    colors: int,
    clean_fringe: bool,
) -> None:
    duration = max(20, int(round(1000 / max(1, fps))))
    frames: List[Image.Image] = []
    for path in frame_paths:
        im = Image.open(path)
        if clean_fringe:
            im = clean_fringe_frame(im)
        else:
            im = im.convert('RGBA')
        # Quantize with transparency
        alpha = im.split()[-1]
        mask = Image.eval(alpha, lambda a: 255 if a < 16 else 0)
        rgb = im.convert('RGB').convert(
            'P', palette=Image.ADAPTIVE, colors=max(2, min(256, colors) - 1),
        )
        rgb.paste(255, mask=mask)
        rgb.info['transparency'] = 255
        frames.append(rgb)

    ensure_parent_dir(dst)
    frames[0].save(
        dst,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=True,
    )
    for im in frames:
        im.close()


def _ffmpeg_direct_webp(
    ffmpeg: str,
    src: str,
    dst: str,
    *,
    max_edge: int,
    fps: int,
    quality: int,
    keep_alpha: bool,
    white_key: bool = False,
    white_key_similarity: float = 0.12,
    white_key_blend: float = 0.04,
) -> None:
    use_alpha = keep_alpha or white_key
    prefix = _vf_prefix(
        white_key=white_key,
        white_key_similarity=white_key_similarity,
        white_key_blend=white_key_blend,
    )
    vf = f'{prefix}{_scale_vf(max_edge)},format=rgba' if use_alpha else _scale_vf(max_edge)
    cmd = [
        ffmpeg, '-y',
        *_input_args(src, keep_alpha),
        '-an',
        '-vf', vf,
        '-r', str(max(1, fps)),
        '-c:v', 'libwebp',
        '-lossless', '0',
        '-compression_level', '6',
        '-q:v', str(max(0, min(100, quality))),
        '-loop', '0',
        dst,
    ]
    ensure_parent_dir(dst)
    _run_ffmpeg(cmd)
    if use_alpha:
        patch_webp_anmf_disposal(dst)


def _ffmpeg_direct_gif(
    ffmpeg: str,
    src: str,
    dst: str,
    *,
    max_edge: int,
    fps: int,
    colors: int,
    keep_alpha: bool,
    white_key: bool = False,
    white_key_similarity: float = 0.12,
    white_key_blend: float = 0.04,
) -> None:
    use_alpha = keep_alpha or white_key
    prefix = _vf_prefix(
        white_key=white_key,
        white_key_similarity=white_key_similarity,
        white_key_blend=white_key_blend,
    )
    scale = _scale_vf(max_edge)
    # Two-pass palette with optional transparency
    if use_alpha:
        vf = (
            f'{prefix}{scale},fps={max(1, fps)},split[s0][s1];'
            f'[s0]palettegen=max_colors={max(2, min(256, colors))}:reserve_transparent=1[p];'
            f'[s1][p]paletteuse=alpha_threshold=128'
        )
    else:
        vf = (
            f'{prefix}{scale},fps={max(1, fps)},split[s0][s1];'
            f'[s0]palettegen=max_colors={max(2, min(256, colors))}[p];'
            f'[s1][p]paletteuse'
        )
    cmd = [
        ffmpeg, '-y',
        *_input_args(src, keep_alpha),
        '-an',
        '-vf', vf,
        dst,
    ]
    ensure_parent_dir(dst)
    _run_ffmpeg(cmd)


def convert_video_to_anim(
    src: str,
    dst: str,
    *,
    target: str = '.webp',
    max_edge: int = 0,
    fps: int = 24,
    quality: int = 80,
    colors: int = 256,
    keep_alpha: bool = True,
    clean_fringe: bool = False,
    white_key: bool = False,
    white_key_similarity: float = 0.12,
    white_key_blend: float = 0.04,
    ffmpeg: Optional[str] = None,
) -> int:
    """Convert one video to animated WebP or GIF. Returns output size."""
    target_ext = _norm_target(target)
    ffmpeg_bin = ffmpeg or find_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError('ffmpeg not found — install ffmpeg and add it to PATH')

    effective_keep_alpha = keep_alpha or white_key
    key_kwargs = {
        'white_key': white_key,
        'white_key_similarity': white_key_similarity,
        'white_key_blend': white_key_blend,
    }

    if clean_fringe:
        with tempfile.TemporaryDirectory(prefix='imgbatch_va_') as tmp:
            frames = _extract_frames(
                ffmpeg_bin, src, tmp,
                max_edge=max_edge, fps=fps, keep_alpha=effective_keep_alpha,
                **key_kwargs,
            )
            if target_ext == '.webp':
                _save_webp_from_frames(
                    frames, dst, fps=fps, quality=quality, clean_fringe=True,
                )
            else:
                _save_gif_from_frames(
                    frames, dst, fps=fps, colors=colors, clean_fringe=True,
                )
    elif target_ext == '.webp':
        _ffmpeg_direct_webp(
            ffmpeg_bin, src, dst,
            max_edge=max_edge, fps=fps, quality=quality, keep_alpha=effective_keep_alpha,
            **key_kwargs,
        )
    else:
        _ffmpeg_direct_gif(
            ffmpeg_bin, src, dst,
            max_edge=max_edge, fps=fps, colors=colors, keep_alpha=effective_keep_alpha,
            **key_kwargs,
        )

    return os.path.getsize(dst)


def run_video_anim_batch(
    state,
    folder: str,
    file_list: List[str],
    *,
    target: str = '.webp',
    max_edge: int = 0,
    fps: int = 24,
    quality: int = 80,
    colors: int = 256,
    keep_alpha: bool = True,
    clean_fringe: bool = False,
    white_key: bool = False,
    white_key_similarity: float = 0.12,
    white_key_blend: float = 0.04,
    do_backup: bool = False,
    replace: bool = True,
    out: Optional[str] = None,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Batch convert videos to animated WebP/GIF."""
    logger = get_logger()
    errors: List[str] = []
    skipped: List[str] = []
    results: List[dict] = []
    total_before = 0
    total_after = 0

    try:
        target_ext = _norm_target(target)
    except ValueError as exc:
        return {
            'total_before': 0,
            'total_after': 0,
            'errors': [str(exc)],
            'skipped': [],
            'results': [],
            'cancelled': False,
        }

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        return {
            'total_before': 0,
            'total_after': 0,
            'errors': ['ffmpeg not found — install ffmpeg and add it to PATH'],
            'skipped': [],
            'results': [],
            'cancelled': False,
        }

    video_list = [f for f in file_list if is_video(f)]
    for f in file_list:
        if f not in video_list:
            skipped.append(f)

    total = len(video_list)
    if total == 0:
        return {
            'total_before': 0,
            'total_after': 0,
            'errors': errors,
            'skipped': skipped,
            'results': results,
            'cancelled': False,
        }

    backup_dir = None
    if do_backup and backup_fn:
        try:
            backup_dir = backup_fn(folder, file_list)
        except OSError as exc:
            logger.error('Backup failed: %s', exc)
            return {
                'total_before': 0,
                'total_after': 0,
                'errors': [f'Backup failed: {exc}'],
                'skipped': skipped,
                'results': [],
                'cancelled': False,
                'backup_dir': None,
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    for i, fname in enumerate(video_list):
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
        base = os.path.splitext(fname)[0]
        new_name = base + target_ext
        current_ext = Path(fname).suffix.lower()
        if replace and current_ext == target_ext:
            dst = src
        elif replace:
            dst = os.path.join(folder, new_name)
        else:
            dst = os.path.join(out or folder, new_name)

        if not replace or dst != src:
            ensure_parent_dir(dst)

        try:
            sa = convert_video_to_anim(
                src, dst,
                target=target_ext,
                max_edge=max_edge,
                fps=fps,
                quality=quality,
                colors=colors,
                keep_alpha=keep_alpha,
                clean_fringe=clean_fringe,
                white_key=white_key,
                white_key_similarity=white_key_similarity,
                white_key_blend=white_key_blend,
                ffmpeg=ffmpeg_bin,
            )
            if replace and dst != src and os.path.exists(src):
                try:
                    os.remove(src)
                except OSError as exc:
                    logger.warning('Could not remove original %s: %s', src, exc)
            total_after += sa
            results.append({
                'name': new_name,
                'source': fname,
                'size': sa,
                'target': target_ext,
                'max_edge': max_edge,
                'fps': fps,
                'keep_alpha': keep_alpha or white_key,
                'clean_fringe': clean_fringe,
                'white_key': white_key,
                'white_key_similarity': white_key_similarity,
                'white_key_blend': white_key_blend,
            })
            if on_file_done:
                on_file_done(new_name, sa)
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f'{fname}: {exc}')
            if dst != src and os.path.exists(dst):
                try:
                    os.remove(dst)
                except OSError:
                    pass

        if on_progress:
            on_progress((i + 1) / total * 100, f'{i + 1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'skipped': skipped,
        'results': results,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
