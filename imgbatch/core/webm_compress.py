#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WebM alpha video compression via ffmpeg (VP9 yuva420p)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from .common import ensure_parent_dir
from ..infra.logger import get_logger
from ..infra.settings import CONFIG_DIR

WEBM_EXT = {'.webm'}
FFMPEG_EXT_DIR = CONFIG_DIR / 'extensions' / 'ffmpeg'


def _find_ffmpeg_under(root: Path) -> Optional[str]:
    if not root.is_dir():
        return None
    for name in ('ffmpeg.exe', 'ffmpeg'):
        for candidate in (root / 'bin' / name, root / name):
            if candidate.is_file():
                return str(candidate)
    for path in root.rglob('ffmpeg.exe'):
        if path.is_file():
            return str(path)
    for path in root.rglob('ffmpeg'):
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def find_ffmpeg() -> Optional[str]:
    """Locate ffmpeg: config → managed extension → PATH → common installs."""
    try:
        from ..infra.settings import load_config
        custom = (load_config().get('ffmpeg_path') or '').strip().strip('"')
        if custom and os.path.isfile(custom):
            return custom
    except Exception:
        pass

    managed = _find_ffmpeg_under(FFMPEG_EXT_DIR)
    if managed:
        return managed

    path = shutil.which('ffmpeg')
    if path:
        return path
    candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\ProgramData\chocolatey\bin\ffmpeg.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe'),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def build_ffmpeg_cmd(
    ffmpeg: str,
    src: str,
    dst: str,
    *,
    max_edge: int = 256,
    crf: int = 40,
    fps: int = 24,
    keep_alpha: bool = True,
) -> List[str]:
    """Build ffmpeg command for VP9 WebM compression."""
    vf = (
        f"scale='if(gt(iw,ih),{max_edge},-2)'"
        f":'if(gt(ih,iw),{max_edge},-2)':flags=lanczos"
    )
    cmd = [
        ffmpeg,
        '-y',
        '-c:v', 'libvpx-vp9',
        '-i', src,
        '-an',
        '-vf', vf,
        '-r', str(fps),
        '-c:v', 'libvpx-vp9',
        '-b:v', '0',
        '-crf', str(crf),
        '-row-mt', '1',
        '-cpu-used', '2',
        '-deadline', 'good',
    ]
    if keep_alpha:
        cmd += ['-pix_fmt', 'yuva420p', '-auto-alt-ref', '0']
    else:
        cmd += ['-pix_fmt', 'yuv420p']
    cmd.append(dst)
    return cmd


def compress_webm(
    src: str,
    dst: str,
    *,
    max_edge: int = 256,
    crf: int = 40,
    fps: int = 24,
    keep_alpha: bool = True,
    ffmpeg: Optional[str] = None,
) -> int:
    """Compress a WebM file. Returns output size in bytes."""
    ffmpeg_bin = ffmpeg or find_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError('ffmpeg not found — install ffmpeg and add it to PATH')

    ensure_parent_dir(dst)
    cmd = build_ffmpeg_cmd(
        ffmpeg_bin, src, dst,
        max_edge=max_edge, crf=crf, fps=fps, keep_alpha=keep_alpha,
    )
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

    return os.path.getsize(dst)


def _is_webm(filename: str) -> bool:
    return Path(filename).suffix.lower() in WEBM_EXT


def run_webm_compress_batch(
    state,
    folder: str,
    file_list: List[str],
    max_edge: int,
    crf: int,
    fps: int,
    keep_alpha: bool,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    """Batch compress WebM files with VP9 alpha."""
    logger = get_logger()
    errors: List[str] = []
    skipped: List[str] = []
    results: List[dict] = []
    total_before = 0
    total_after = 0

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

    webm_list = [f for f in file_list if _is_webm(f)]
    for f in file_list:
        if f not in webm_list:
            skipped.append(f)

    total = len(webm_list)
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
            logger.error("Backup failed: %s", exc)
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

    for i, fname in enumerate(webm_list):
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
            sa = compress_webm(
                src, dst,
                max_edge=max_edge,
                crf=crf,
                fps=fps,
                keep_alpha=keep_alpha,
                ffmpeg=ffmpeg_bin,
            )
            total_after += sa
            results.append({
                'name': fname,
                'size': sa,
                'max_edge': max_edge,
                'crf': crf,
                'fps': fps,
                'keep_alpha': keep_alpha,
            })
            if on_file_done:
                on_file_done(fname, sa)
        except (OSError, RuntimeError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            pct = (i + 1) / total * 100
            on_progress(pct, f'{i + 1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'skipped': skipped,
        'results': results,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
