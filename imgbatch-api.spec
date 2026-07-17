# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ImgBatch API sidecar.

Key: does NOT include tkinter.
"""
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
ROOT = os.path.abspath('.')

hidden = collect_submodules('imgbatch')
hidden += [
    'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'fastapi', 'sse_starlette', 'pydantic',
    'pillow_heif', 'pillow_heif.register_heif_opener',
    'fitz', 'openpyxl',
]
excludes = ['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy']

a = Analysis(
    ['imgbatch_api_entry.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='imgbatch-api',
    debug=False,
    console=True,
    disable_windowed_traceback=False,
)
