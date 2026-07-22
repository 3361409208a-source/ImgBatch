#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Optional extension packs — user-installed, managed under ~/.imgbatch/extensions/."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..infra.settings import CONFIG_DIR, load_config

_SOFFICE_CANDIDATES = [
    r'C:\Program Files\LibreOffice\program\soffice.exe',
    r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    '/usr/bin/libreoffice',
    '/usr/bin/soffice',
]

EXTENSIONS_ROOT = CONFIG_DIR / 'extensions'
LIBREOFFICE_EXT_DIR = EXTENSIONS_ROOT / 'libreoffice'
FFMPEG_EXT_DIR = EXTENSIONS_ROOT / 'ffmpeg'

# Direct mirror URLs (Document Foundation) — not the marketing download page.
_LIBREOFFICE_DIRECT = {
    'win64': {
        'url': (
            'https://download.documentfoundation.org/libreoffice/stable/24.8.7/win/x86_64/'
            'LibreOffice_24.8.7_Win_x86-64.msi'
        ),
        'kind': 'msi',
        'filename': 'LibreOffice_24.8.7_Win_x86-64.msi',
    },
    'win64_portable': {
        'url': (
            'https://download.documentfoundation.org/libreoffice/portable/25.8.5/'
            'LibreOfficePortablePrevious_25.8.5_MultilingualStandard.paf.exe'
        ),
        'kind': 'paf',
        'filename': 'LibreOfficePortable.paf.exe',
    },
}

# Gyan.dev essentials build (Windows) — always points at latest release zip.
_FFMPEG_DIRECT = {
    'win64': {
        'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        'filename': 'ffmpeg-release-essentials.zip',
    },
    # Fallback: known-good BtbN shared essentials release
    'win64_fallback': {
        'url': (
            'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/'
            'ffmpeg-master-latest-win64-gpl-shared.zip'
        ),
        'filename': 'ffmpeg-btbn-win64.zip',
    },
}

EXTENSION_DEFINITIONS: List[Dict[str, Any]] = [
    {
        'id': 'libreoffice',
        'name': 'Office 文档扩展包',
        'name_en': 'Office Document Pack',
        'description': '解锁 Word / Excel / PPT 与 PDF 互转、Office 格式批量转换。',
        'description_en': 'Unlock Word/Excel/PPT ↔ PDF and batch Office conversions.',
        'download_url': _LIBREOFFICE_DIRECT['win64']['url'],
        'install_dir_hint': str(LIBREOFFICE_EXT_DIR),
        'size_hint': '~200 MB 下载 · 解压至用户目录',
        'size_hint_en': '~200 MB download · extracts to user app folder',
        'config_key': 'libreoffice_path',
        'unlocks': [
            '办公文档 → PDF',
            'PDF → Word (DOCX)',
            'Word / Excel / PPT 格式互转',
            'RTF / ODF / HTML 文档转换',
        ],
        'unlocks_en': [
            'Office → PDF',
            'PDF → Word (DOCX)',
            'Word / Excel / PPT cross-convert',
            'RTF / ODF / HTML document convert',
        ],
    },
    {
        'id': 'ffmpeg',
        'name': 'FFmpeg 音视频扩展包',
        'name_en': 'FFmpeg Media Pack',
        'description': '解锁视频转 GIF/WebP、WebM 透明压缩等音视频处理能力。',
        'description_en': 'Unlock video→GIF/WebP and WebM alpha compression.',
        'download_url': _FFMPEG_DIRECT['win64']['url'],
        'install_dir_hint': str(FFMPEG_EXT_DIR),
        'size_hint': '~80 MB 下载 · 解压至用户目录',
        'size_hint_en': '~80 MB download · extracts to user folder',
        'config_key': 'ffmpeg_path',
        'unlocks': [
            '视频 → 动画 WebP / GIF',
            'WebM 透明通道压缩',
            'VP9 Alpha 正确解码',
        ],
        'unlocks_en': [
            'Video → animated WebP / GIF',
            'WebM alpha compression',
            'Correct VP9 alpha decode',
        ],
    },
    {
        'id': 'rembg',
        'name': 'AI 抠图模型扩展包',
        'name_en': 'AI Matting Pack (Rembg)',
        'description': '解锁基于 U2-Net 深度学习模型的离线高精度人像与物体抠图。',
        'description_en': 'Unlock offline high-precision AI matting via U2-Net model.',
        'download_url': 'https://pypi.org/project/rembg/',
        'install_dir_hint': 'pip install rembg[gpu]',
        'size_hint': '~170 MB 模型权重 · 离线推理',
        'size_hint_en': '~170 MB model weights · offline inference',
        'config_key': 'rembg_path',
        'unlocks': [
            '高精度 AI 自动发丝级抠图',
            '复杂背景人像分离',
            '离线本地 GPU/CPU 加速',
        ],
        'unlocks_en': [
            'High-precision AI portrait matting',
            'Complex background separation',
            'Offline local GPU/CPU acceleration',
        ],
    },
]

_install_lock = threading.Lock()
_install_state: Dict[str, Any] = {
    'running': False,
    'progress': 0.0,
    'message': '',
    'error': None,
    'install_path': None,
}


def _find_soffice_under(root: Path) -> Optional[str]:
    if not root.is_dir():
        return None
    direct = root / 'program' / 'soffice.exe'
    if direct.is_file():
        return str(direct)
    direct = root / 'App' / 'LibreOffice' / 'program' / 'soffice.exe'
    if direct.is_file():
        return str(direct)
    for path in root.rglob('soffice.exe'):
        if path.is_file():
            return str(path)
    for path in root.rglob('soffice'):
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def find_libreoffice() -> Optional[str]:
    """Return path to soffice if the Office extension pack is available."""
    cfg = load_config()
    custom = (cfg.get('libreoffice_path') or '').strip().strip('"')
    if custom and os.path.isfile(custom):
        return custom

    managed = _find_soffice_under(LIBREOFFICE_EXT_DIR)
    if managed:
        return managed

    for path in _SOFFICE_CANDIDATES:
        if os.path.isfile(path):
            return path
    return shutil.which('soffice') or shutil.which('libreoffice')


def is_libreoffice_installed() -> bool:
    return find_libreoffice() is not None


def find_ffmpeg_extension() -> Optional[str]:
    """Return ffmpeg path (managed extension / config / PATH)."""
    from .webm_compress import find_ffmpeg
    return find_ffmpeg()


def is_ffmpeg_installed() -> bool:
    return find_ffmpeg_extension() is not None


def get_install_status() -> dict:
    with _install_lock:
        return dict(_install_state)


def _set_install_state(**kwargs) -> None:
    with _install_lock:
        _install_state.update(kwargs)


def _download_file(
    url: str,
    dest: Path,
    on_progress: Optional[Callable[[float, str], None]] = None,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'ImgBatch/3.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get('Content-Length') or 0)
        read = 0
        chunk = 1024 * 256
        with open(dest, 'wb') as handle:
            while True:
                block = resp.read(chunk)
                if not block:
                    break
                handle.write(block)
                read += len(block)
                if on_progress:
                    pct = (read / total * 100) if total else min(99.0, read / (200 * 1024 * 1024) * 100)
                    mb = read / (1024 * 1024)
                    on_progress(pct, f'下载中 {mb:.1f} MB')


def _extract_msi(msi_path: Path, target_dir: Path) -> None:
    if sys.platform != 'win32':
        raise RuntimeError('MSI install is only supported on Windows')
    target_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            'msiexec', '/a', str(msi_path),
            f'TARGETDIR={target_dir}',
            '/qn', '/norestart',
        ],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or '').strip()
        raise RuntimeError(detail or f'msiexec failed ({proc.returncode})')


def _extract_paf(paf_path: Path, target_dir: Path) -> None:
    if sys.platform != 'win32':
        raise RuntimeError('Portable .paf install is only supported on Windows')
    target_dir.mkdir(parents=True, exist_ok=True)
    # PortableApps / NSIS: /D= must be the last argument.
    proc = subprocess.run(
        [str(paf_path), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', f'/D={target_dir}'],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or '').strip()
        raise RuntimeError(detail or f'paf extract failed ({proc.returncode})')


def _pick_libreoffice_package() -> dict:
    if sys.platform != 'win32':
        raise RuntimeError('一键安装扩展包目前仅支持 Windows；请手动安装 LibreOffice 后点「重新检测」')
    # Prefer portable Standard (~194 MB); MSI is larger but used as fallback.
    return _LIBREOFFICE_DIRECT['win64_portable']


def _install_libreoffice_worker() -> None:
    try:
        pkg = _pick_libreoffice_package()
        _set_install_state(running=True, progress=0, message='准备下载…', error=None, install_path=None)

        LIBREOFFICE_EXT_DIR.mkdir(parents=True, exist_ok=True)
        archive = LIBREOFFICE_EXT_DIR / pkg['filename']

        def on_dl(pct: float, msg: str) -> None:
            _set_install_state(progress=min(70.0, pct * 0.7), message=msg)

        _download_file(pkg['url'], archive, on_progress=on_dl)
        _set_install_state(progress=75, message='正在解压到扩展目录…')

        extract_root = LIBREOFFICE_EXT_DIR / 'app'
        if extract_root.exists():
            shutil.rmtree(extract_root, ignore_errors=True)
        extract_root.mkdir(parents=True, exist_ok=True)

        if pkg['kind'] == 'msi':
            _extract_msi(archive, extract_root)
        else:
            try:
                _extract_paf(archive, extract_root)
            except RuntimeError:
                # Fallback: full MSI administrative image (~350 MB download)
                _set_install_state(message='便携版解压失败，尝试 MSI 包…', progress=72)
                msi_pkg = _LIBREOFFICE_DIRECT['win64']
                msi_archive = LIBREOFFICE_EXT_DIR / msi_pkg['filename']
                _download_file(msi_pkg['url'], msi_archive, on_progress=on_dl)
                _extract_msi(msi_archive, extract_root)

        _set_install_state(progress=90, message='正在配置…')
        soffice = _find_soffice_under(extract_root)
        if not soffice:
            raise RuntimeError('解压完成但未找到 soffice.exe')

        set_extension_path('libreoffice', soffice)
        _set_install_state(
            running=False,
            progress=100,
            message='扩展包安装完成',
            error=None,
            install_path=soffice,
        )
    except Exception as exc:
        _set_install_state(running=False, progress=0, message='', error=str(exc), install_path=None)


def _extract_zip(archive: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'r') as zf:
        zf.extractall(target_dir)


def _find_ffmpeg_under(root: Path) -> Optional[str]:
    from .webm_compress import _find_ffmpeg_under as _find
    return _find(root)


def _install_ffmpeg_worker() -> None:
    """Download portable FFmpeg zip into ~/.imgbatch/extensions/ffmpeg."""
    try:
        if sys.platform != 'win32':
            raise RuntimeError(
                '一键安装 FFmpeg 目前仅支持 Windows；'
                '请用包管理器安装 ffmpeg 后点「重新检测」'
            )

        _set_install_state(
            running=True, progress=0, message='准备下载 FFmpeg…',
            error=None, install_path=None,
        )
        FFMPEG_EXT_DIR.mkdir(parents=True, exist_ok=True)

        def on_dl(pct: float, msg: str) -> None:
            _set_install_state(progress=min(75.0, pct * 0.75), message=msg)

        packages = [_FFMPEG_DIRECT['win64'], _FFMPEG_DIRECT['win64_fallback']]
        archive = None
        last_err: Optional[Exception] = None
        for pkg in packages:
            candidate = FFMPEG_EXT_DIR / pkg['filename']
            try:
                _set_install_state(message=f'正在下载 {pkg["filename"]}…')
                _download_file(pkg['url'], candidate, on_progress=on_dl)
                archive = candidate
                break
            except Exception as exc:
                last_err = exc
                continue
        if archive is None:
            raise RuntimeError(f'下载 FFmpeg 失败: {last_err}')

        _set_install_state(progress=80, message='正在解压 FFmpeg…')
        extract_root = FFMPEG_EXT_DIR / 'app'
        if extract_root.exists():
            shutil.rmtree(extract_root, ignore_errors=True)
        extract_root.mkdir(parents=True, exist_ok=True)
        _extract_zip(archive, extract_root)

        _set_install_state(progress=92, message='正在配置…')
        ffmpeg_bin = _find_ffmpeg_under(extract_root) or _find_ffmpeg_under(FFMPEG_EXT_DIR)
        if not ffmpeg_bin:
            raise RuntimeError('解压完成但未找到 ffmpeg.exe')

        set_extension_path('ffmpeg', ffmpeg_bin)
        _set_install_state(
            running=False,
            progress=100,
            message='FFmpeg 安装完成，已自动启用',
            error=None,
            install_path=ffmpeg_bin,
        )
    except Exception as exc:
        _set_install_state(running=False, progress=0, message='', error=str(exc), install_path=None)


def is_rembg_installed() -> bool:
    """Check if rembg package or u2net model is available."""
    try:
        import importlib.util
        if importlib.util.find_spec('rembg') is not None:
            return True
    except Exception:
        pass
    # Check if u2net model exists in home directory or extensions folder
    u2net_path = Path.home() / '.u2net' / 'u2net.onnx'
    if u2net_path.is_file():
        return True
    managed_model = EXTENSIONS_ROOT / 'rembg' / 'u2net.onnx'
    return managed_model.is_file()


def _find_python_executable() -> Optional[str]:
    """Find a valid system python.exe (not the frozen PyInstaller binary)."""
    if not getattr(sys, 'frozen', False):
        return sys.executable
    for candidate in ['python.exe', 'python3.exe', 'python']:
        found = shutil.which(candidate)
        if found:
            return found
    py_launcher = r'C:\Windows\py.exe'
    if os.path.isfile(py_launcher):
        return py_launcher
    return None


def _install_rembg_worker() -> None:
    """Worker to install rembg package and download U2-Net model weights."""
    try:
        _set_install_state(running=True, progress=5, message='准备开始下载 AI 抠图模型权重…', error=None, install_path=None)

        # 1. Direct download U2-Net ONNX model (~175 MB) to ~/.u2net/u2net.onnx
        u2net_dir = Path.home() / '.u2net'
        u2net_dir.mkdir(parents=True, exist_ok=True)
        u2net_file = u2net_dir / 'u2net.onnx'

        model_url = 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx'

        def on_dl(pct: float, msg: str) -> None:
            _set_install_state(running=True, progress=max(5.0, min(85.0, pct * 0.85)), message=f'正在下载 AI 模型: {msg}')

        _set_install_state(progress=10, message='正在连接模型服务器下载 U2-Net 权重 (~170MB)…')
        
        dl_success = False
        try:
            _download_file(model_url, u2net_file, on_progress=on_dl)
            dl_success = True
        except Exception as dl_err:
            # Fallback mirror if github is blocked
            mirror_url = 'https://huggingface.co/danielgatis/rembg/resolve/main/u2net.onnx'
            try:
                _download_file(mirror_url, u2net_file, on_progress=on_dl)
                dl_success = True
            except Exception:
                if not u2net_file.exists():
                    raise RuntimeError(f'下载模型失败: {dl_err}')

        # 2. Try optional pip install if python is available
        py_exe = _find_python_executable()
        if py_exe:
            _set_install_state(progress=88, message='正在配置 Python 依赖环境…')
            subprocess.run([py_exe, '-m', 'pip', 'install', 'rembg', 'onnxruntime'], capture_output=True, check=False)

        _set_install_state(
            running=False,
            progress=100,
            message='AI 抠图模型扩展包安装完成！',
            error=None,
            install_path=str(u2net_file if u2net_file.exists() else u2net_dir),
        )
    except Exception as exc:
        _set_install_state(running=False, progress=0, message='', error=str(exc), install_path=None)


def start_install_extension(ext_id: str) -> dict:
    if ext_id not in ('libreoffice', 'rembg', 'ffmpeg'):
        raise ValueError(f'Unknown extension: {ext_id}')

    with _install_lock:
        if _install_state.get('running'):
            raise RuntimeError('扩展包正在安装中，请稍候')

    if ext_id == 'libreoffice':
        if is_libreoffice_installed():
            return {
                'started': False,
                'already_installed': True,
                'install_path': find_libreoffice(),
            }
        thread = threading.Thread(target=_install_libreoffice_worker, daemon=True)
        thread.start()
        return {'started': True, 'already_installed': False}

    if ext_id == 'ffmpeg':
        if is_ffmpeg_installed():
            return {
                'started': False,
                'already_installed': True,
                'install_path': find_ffmpeg_extension(),
            }
        thread = threading.Thread(target=_install_ffmpeg_worker, daemon=True)
        thread.start()
        return {'started': True, 'already_installed': False}

    # rembg
    if is_rembg_installed():
        return {
            'started': False,
            'already_installed': True,
            'install_path': str(Path.home() / '.u2net'),
        }

    thread = threading.Thread(target=_install_rembg_worker, daemon=True)
    thread.start()
    return {'started': True, 'already_installed': False}


def _detect_extension(ext_id: str) -> tuple[bool, Optional[str]]:
    if ext_id == 'libreoffice':
        path = find_libreoffice()
        return (path is not None, path)
    if ext_id == 'ffmpeg':
        path = find_ffmpeg_extension()
        return (path is not None, path)
    if ext_id == 'rembg':
        installed = is_rembg_installed()
        u2path = Path.home() / '.u2net' / 'u2net.onnx'
        return (installed, str(u2path) if u2path.exists() else ('已安装 Python 库' if installed else None))
    return (False, None)


def get_extensions_catalog() -> dict:
    items = []
    locked = 0
    for definition in EXTENSION_DEFINITIONS:
        installed, install_path = _detect_extension(definition['id'])
        if not installed:
            locked += 1
        items.append({
            'id': definition['id'],
            'name': definition['name'],
            'name_en': definition['name_en'],
            'description': definition['description'],
            'description_en': definition['description_en'],
            'download_url': definition['download_url'],
            'install_dir': definition.get('install_dir_hint', ''),
            'size_hint': definition['size_hint'],
            'size_hint_en': definition['size_hint_en'],
            'installed': installed,
            'install_path': install_path,
            'unlocks': definition['unlocks'],
            'unlocks_en': definition['unlocks_en'],
        })

    return {
        'extensions': items,
        'locked_count': locked,
        'unlocked_count': len(items) - locked,
        'total_count': len(items),
        'install': get_install_status(),
    }


def set_extension_path(ext_id: str, path: str) -> dict:
    path = (path or '').strip().strip('"')
    if ext_id not in ('libreoffice', 'rembg', 'ffmpeg'):
        raise ValueError(f'Unknown extension: {ext_id}')
    if path and not os.path.isfile(path) and not os.path.isdir(path):
        raise ValueError(f'Path not found: {path}')

    from ..infra.settings import save_config

    cfg = load_config()
    cfg[f'{ext_id}_path'] = path
    save_config(cfg)
    installed, install_path = _detect_extension(ext_id)
    return {
        'ok': True,
        'installed': installed,
        'install_path': install_path,
    }
