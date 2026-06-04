#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch — 一键打包 EXE 脚本"""

import os
import sys
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SCRIPT_DIR, 'image_compressor.pyw')
DIST = os.path.join(SCRIPT_DIR, 'dist')

print('\n' + '=' * 50)
print('  ImgBatch — 一键打包 EXE')
print('=' * 50 + '\n')

# Step 1: Check PyInstaller
print('[1/4] 检查 PyInstaller...')
try:
    subprocess.check_call([sys.executable, '-m', 'PyInstaller', '--version'], stdout=subprocess.DEVNULL)
    print('  OK - PyInstaller 已安装')
except (subprocess.CalledProcessError, FileNotFoundError):
    print('  PyInstaller 未安装，正在安装...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    print('  OK - PyInstaller 安装完成')

# Step 2: Clean old build
print('[2/4] 清理旧构建...')
for d in ['build', 'dist']:
    path = os.path.join(SCRIPT_DIR, d)
    if os.path.exists(path):
        shutil.rmtree(path)
for f in os.listdir(SCRIPT_DIR):
    if f.endswith('.spec'):
        os.remove(os.path.join(SCRIPT_DIR, f))
print('  OK - 清理完成')

# Step 3: Build
print('[3/4] 打包中（约 1-2 分钟）...')
cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile', '--windowed',
    '--name', 'ImgBatch',
    '--clean',
    '--hidden-import', 'tkinter',
    '--hidden-import', 'PIL',
    '--hidden-import', 'PIL.Image',
    '--hidden-import', 'PIL.ImageDraw',
    '--hidden-import', 'PIL.ImageFont',
    '--hidden-import', 'json',
    '--hidden-import', 'urllib.request',
    '--hidden-import', 'urllib.error',
    SRC,
]
subprocess.check_call(cmd, cwd=SCRIPT_DIR)

# Step 4: Copy extras
print('[4/4] 复制附加文件...')
readme = os.path.join(SCRIPT_DIR, '说明.txt')
if os.path.exists(readme):
    shutil.copy(readme, DIST)
    print('  OK - 说明.txt 已复制')

print('\n' + '=' * 50)
print(f'  打包完成！')
print(f'  {os.path.join(DIST, "ImgBatch.exe")}')
print('=' * 50 + '\n')

# Open dist folder
os.startfile(DIST)
