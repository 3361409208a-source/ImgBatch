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


def start_install_extension(ext_id: str) -> dict:
    if ext_id != 'libreoffice':
        raise ValueError(f'Unknown extension: {ext_id}')
    with _install_lock:
        if _install_state.get('running'):
            raise RuntimeError('扩展包正在安装中，请稍候')
    if is_libreoffice_installed():
        return {
            'started': False,
            'already_installed': True,
            'install_path': find_libreoffice(),
        }

    thread = threading.Thread(target=_install_libreoffice_worker, daemon=True)
    thread.start()
    return {'started': True, 'already_installed': False}


def _detect_extension(ext_id: str) -> tuple[bool, Optional[str]]:
    if ext_id == 'libreoffice':
        path = find_libreoffice()
        return (path is not None, path)
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
    if ext_id != 'libreoffice':
        raise ValueError(f'Unknown extension: {ext_id}')
    if path and not os.path.isfile(path):
        raise ValueError(f'Path not found: {path}')

    from ..infra.settings import save_config

    cfg = load_config()
    cfg['libreoffice_path'] = path
    save_config(cfg)
    installed, install_path = _detect_extension(ext_id)
    return {
        'ok': True,
        'installed': installed,
        'install_path': install_path,
    }
