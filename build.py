#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch — Build EXE script (v2.0, modular package support)."""

import os
import sys
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SCRIPT_DIR, 'image_compressor.pyw')
DIST = os.path.join(SCRIPT_DIR, 'dist')
BUILD = os.path.join(SCRIPT_DIR, 'build')
PKG_DIR = os.path.join(SCRIPT_DIR, 'imgbatch')

print('\n' + '=' * 50)
print('  ImgBatch v2.0 — Build EXE')
print('=' * 50 + '\n')

# Step 1: Check PyInstaller
print('[1/5] Checking PyInstaller...')
try:
    subprocess.check_call([sys.executable, '-m', 'PyInstaller', '--version'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('  OK - PyInstaller found')
except (subprocess.CalledProcessError, FileNotFoundError):
    print('  Installing PyInstaller...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    print('  OK - Installed')

# Step 2: Clean old build (handle locked files)
print('[2/5] Cleaning old builds...')

def safe_rmtree(path):
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                os.chmod(fp, 0o777)
                os.unlink(fp)
            except (PermissionError, OSError):
                try:
                    tmp = fp + '.old'
                    if os.path.exists(tmp):
                        os.unlink(tmp)
                    os.rename(fp, tmp)
                except Exception:
                    pass
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
    try:
        os.rmdir(path)
    except OSError:
        pass

for p in [BUILD, DIST]:
    if os.path.exists(p):
        print(f'  Removing {os.path.basename(p)}...')
        safe_rmtree(p)

for f in os.listdir(SCRIPT_DIR):
    if f.endswith('.spec'):
        try:
            os.remove(os.path.join(SCRIPT_DIR, f))
        except Exception:
            pass
print('  OK - Cleaned')

# Step 3: Build
print('[3/5] Building EXE (1-2 minutes)...')

# Collect all Python files in the imgbatch package as hidden imports
hidden_imports = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageTk',
    'PIL.ExifTags', 'pkg_resources', 'pkg_resources.py2_warn',
    'json', 'urllib.request', 'urllib.error', 'ctypes', 'argparse',
    'concurrent.futures',
]

# Add all imgbatch submodules
for root, dirs, files in os.walk(PKG_DIR):
    for f in files:
        if f.endswith('.py') and f != '__pycache__':
            rel = os.path.relpath(os.path.join(root, f), SCRIPT_DIR)
            mod = rel.replace(os.sep, '.').replace('.py', '')
            hidden_imports.append(mod)

# Deduplicate
hidden_imports = list(dict.fromkeys(hidden_imports))

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile', '--windowed',
    '--name', 'ImgBatch',
    '--clean',
    '--noconfirm',
    '--noupx',
]

for imp in hidden_imports:
    cmd.extend(['--hidden-import', imp])

# Add the package directory as a data file so PyInstaller can find it
cmd.extend([
    '--add-data', f'{PKG_DIR}{os.pathsep}imgbatch',
    '--exclude-module', 'matplotlib',
    '--exclude-module', 'numpy',
    '--exclude-module', 'scipy',
    '--exclude-module', 'pandas',
    SRC,
])

subprocess.check_call(cmd, cwd=SCRIPT_DIR)

# Step 4: Copy extras
print('[4/5] Copying extra files...')
readme = os.path.join(SCRIPT_DIR, '\u8BF4\u660E.txt')
if os.path.exists(readme):
    shutil.copy(readme, DIST)
    print('  OK - docs copied')

# Step 5: Done
print('[5/5] Done.')
exe_path = os.path.join(DIST, 'ImgBatch.exe')
print('\n' + '=' * 50)
print(f'  Build complete!')
print(f'  {exe_path}')
print('=' * 50 + '\n')

if os.path.exists(exe_path):
    os.startfile(DIST)
else:
    print('WARNING: EXE not found. Check PyInstaller output above.')
    input('Press Enter to exit...')
