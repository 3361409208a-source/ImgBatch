# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Tauri sidecar (imgbatch-api.exe)."""

from pathlib import Path

ROOT = Path(SPECPATH)

hiddenimports = [
    'PIL', 'PIL.Image', 'PIL.ExifTags',
    'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'fastapi', 'starlette', 'pydantic', 'multipart', 'sse_starlette', 'sse_starlette.sse',
    'imgbatch.__init__',
    'imgbatch.api.deps', 'imgbatch.api.main', 'imgbatch.api.schemas', 'imgbatch.api.tasks',
    'imgbatch.api.__init__',
    'imgbatch.api.routes.backups', 'imgbatch.api.routes.config', 'imgbatch.api.routes.convert',
    'imgbatch.api.routes.doc', 'imgbatch.api.routes.extensions', 'imgbatch.api.routes.gif',
    'imgbatch.api.routes.health', 'imgbatch.api.routes.preview', 'imgbatch.api.routes.scan',
    'imgbatch.api.routes.tasks', 'imgbatch.api.routes.undo', 'imgbatch.api.routes.__init__',
    'imgbatch.core.ai_rename', 'imgbatch.core.balanced_compress', 'imgbatch.core.common',
    'imgbatch.core.compress', 'imgbatch.core.convert', 'imgbatch.core.doc_convert',
    'imgbatch.core.doc_preview', 'imgbatch.core.extensions', 'imgbatch.core.gif',
    'imgbatch.core.inspect', 'imgbatch.core.matting', 'imgbatch.core.normalize',
    'imgbatch.core.rename', 'imgbatch.core.spritesheet', 'imgbatch.core.trim',
    'imgbatch.core.video_anim', 'imgbatch.core.watermark', 'imgbatch.core.webm_compress',
    'imgbatch.core.__init__',
    'imgbatch.infra.backup', 'imgbatch.infra.i18n', 'imgbatch.infra.logger',
    'imgbatch.infra.settings', 'imgbatch.infra.threading', 'imgbatch.infra.__init__',
]

a = Analysis(
    [str(ROOT / 'imgbatch' / 'api' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / 'imgbatch'), 'imgbatch')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        'pytest', 'scipy', 'numba', 'skimage', 'tensorflow', 'rembg', 'onnxruntime',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='imgbatch-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
