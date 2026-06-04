#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch — Image批量处理工具 (Compress/FormatConvert/重命名/Watermark/AI重命名)"""

import os
import json
import shutil
import threading
import time
import re
import math
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askdirectory
    import tkMessageBox as messagebox
    filedialog = type('obj', (object,), {'askdirectory': askdirectory})()

from PIL import Image, ImageDraw, ImageFont

SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico'}
QUALITY_FORMATS = {'.jpg', '.jpeg', '.webp'}
CONVERT_TARGETS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico']

# ── XP Classic Style Colors ──
BG   = '#ECE9D8'  # 3D Face
BG2  = '#D4D0C8'  # 3D Shadow
BG3  = '#FFFFFF'  # Window
FG   = '#000000'  # Button Text
ACCENT  = '#316AC5'  # Selection Blue
ACCENT2 = '#008000'  # Green
WARN    = '#FF0000'  # Red
ERR     = '#CC0000'
BORDER  = '#ACA899'  # 3D Dark Shadow
ENTRY_BG = '#FFFFFF'


class ImgBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title('ImgBatch — Batch Image Processor')
        self.root.geometry('900x720')
        self.root.minsize(820, 600)
        self.root.configure(bg=BG)

        self.folder = tk.StringVar()
        self.file_data = []
        self.is_running = False
        self.tree_items = {}

        # ── 动画 Animation ──
        self._anim_spinner_angle = 0
        self._anim_spinner_id = None
        self._anim_highlight_id = None
        self._anim_highlight_item = None
        self._anim_highlight_on = False
        self._progress_target = 0
        self._progress_current = 0
        self._progress_anim_id = None
        self._status_dots = 0
        self._status_anim_id = None

        # ── Compress Compress ──
        self.c_quality = tk.IntVar(value=75)
        self.c_resize = tk.IntVar(value=100)
        self.c_replace = tk.BooleanVar(value=True)
        self.c_outfolder = tk.StringVar()
        self.c_backup = tk.BooleanVar(value=True)

        # ── FormatConvert Convert ──
        self.v_target_fmt = tk.StringVar(value='.png')
        self.v_conv_replace = tk.BooleanVar(value=True)
        self.v_conv_outfolder = tk.StringVar()
        self.v_conv_backup = tk.BooleanVar(value=True)

        # ── 重命名 Rename ──
        self.r_mode = tk.StringVar(value='prefix')
        self.r_prefix = tk.StringVar(value='img_')
        self.r_suffix = tk.StringVar(value='')
        self.r_replace_src = tk.StringVar(value='')
        self.r_replace_dst = tk.StringVar(value='')
        self.r_seq_start = tk.IntVar(value=1)
        self.r_seq_digits = tk.IntVar(value=3)
        self.r_seq_template = tk.StringVar(value='photo_{num}')
        self.r_lowercase = tk.BooleanVar(value=False)
        self.r_uppercase = tk.BooleanVar(value=False)

        # ── Watermark Watermark ──
        self.w_type = tk.StringVar(value='text')
        self.w_text = tk.StringVar(value='Watermark')
        self.w_fontsize = tk.IntVar(value=36)
        self.w_opacity = tk.IntVar(value=50)
        self.w_position = tk.StringVar(value='bottom-right')
        self.w_color = tk.StringVar(value='#ffffff')
        self.w_image_path = tk.StringVar()
        self.w_img_scale = tk.IntVar(value=20)
        self.w_replace = tk.BooleanVar(value=True)
        self.w_outfolder = tk.StringVar()
        self.w_backup = tk.BooleanVar(value=True)

        # ── AI 重命名 ──
        self.ai_api_key = tk.StringVar()
        self.ai_prompt = tk.StringVar(value='Analyze the filenames below. Generate clean English names with extensions. Format: player_name-position-country.jpg. Return ONLY a JSON array, nothing else.')
        self.ai_result = {}

        self._build_ui()
        self._apply_dark_theme()

    # ═══════════════════════ UI 构建 ═══════════════════════

    def _build_ui(self):
        # ── 顶部：文件夹选择 ──
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=(10, 0))
        ttk.Label(top, text='Target Folder:', font=('Tahoma', 10, 'bold')).pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(top, textvariable=self.folder, width=55, font=('Tahoma', 10))
        self.folder_entry.pack(side=tk.LEFT, padx=(6, 6), fill=tk.X, expand=True)
        ttk.Button(top, text='Browse...', command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top, text='Refresh', command=self._refresh).pack(side=tk.LEFT, padx=(6, 0))
        self._drop_target(top)

        # ── 文件列表 ──
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=6)
        list_hdr = ttk.Frame(self.root)
        list_hdr.pack(fill=tk.X, padx=12)
        ttk.Label(list_hdr, text='File List (double-click to preview)', font=('Tahoma', 9, 'bold')).pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(list_hdr, text='')
        self.lbl_count.pack(side=tk.RIGHT)

        tree_fr = ttk.Frame(self.root)
        tree_fr.pack(fill=tk.BOTH, expand=True, padx=12)
        cols = ('filename', 'size', 'dimensions', 'format')
        self.tree = ttk.Treeview(tree_fr, columns=cols, show='headings', height=8, selectmode='extended')
        for c, w, txt in zip(cols, [340, 80, 110, 70], ['Name', 'Size', 'Dimensions', 'Format']):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, minwidth=60, anchor=tk.CENTER if c != 'filename' else tk.W)
        vsb = ttk.Scrollbar(tree_fr, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<Double-1>', self._preview)

        # ── 底部 Notebook（多标签） ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, padx=12, pady=(4, 0))

        self._tab_compress()
        self._tab_convert()
        self._tab_rename()
        self._tab_watermark()
        self._tab_ai_rename()

        # ── 状态栏 + 动画 ──
        st = ttk.Frame(self.root)
        st.pack(fill=tk.X, padx=12, pady=(4, 8))
        self.progress = ttk.Progressbar(st, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 2))

        # 动画区域：spinner + 状态 + 统计
        sf = ttk.Frame(st)
        sf.pack(fill=tk.X, pady=(2, 0))

        # 旋转加载器 Spinner
        self.spinner = tk.Canvas(sf, width=20, height=20, bg=BG, highlightthickness=0)
        self.spinner.pack(side=tk.LEFT, padx=(0, 6))
        self.spinner.create_oval(4, 4, 16, 16, outline=BG2, width=2, tags='bg')
        self.spinner_arc = self.spinner.create_arc(4, 4, 16, 16, start=0, extent=60,
                                                    outline=ACCENT, width=2, style='arc', tags='arc')
        self.spinner.pack_forget()  # 默认隐藏

        self.lbl_status = ttk.Label(sf, text='Ready')
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_stats = ttk.Label(sf, text='')
        self.lbl_stats.pack(side=tk.RIGHT)

    def _drop_target(self, widget):
        """简陋的拖拽支持 — 监听剪贴板也可"""
        pass

    # ═══════════════════════ Tab: Compress ═══════════════════════

    def _tab_compress(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' Compress ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 质量
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='Quality:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r1, from_=1, to=100, variable=self.c_quality,
                  command=lambda v: self._slider_label(v, self.ql)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ql = ttk.Label(r1, text='75%', width=5); self.ql.pack(side=tk.LEFT, padx=4)

        # Resize
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text='Resize:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.c_resize,
                  command=lambda v: self._slider_label(v, self.rl)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.rl = ttk.Label(r2, text='100%', width=5); self.rl.pack(side=tk.LEFT, padx=4)

        # Output mode
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r3, text='Replace Original', variable=self.c_replace, value=True,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r3, text='Output to:', variable=self.c_replace, value=False,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT, padx=10)
        self.c_outrow = ttk.Frame(r3)
        ttk.Entry(self.c_outrow, textvariable=self.c_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.c_outrow, text='Browse', command=lambda: self._browse_out(self.c_outfolder)).pack(side=tk.LEFT)

        # Backup + Button
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r4, text='Backup', variable=self.c_backup).pack(side=tk.LEFT)
        ttk.Button(r4, text='Start Compress', command=self._run_compress).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r4, text='Backups', command=self._backup_mgr).pack(side=tk.RIGHT, padx=8)

    # ═══════════════════════ Tab: FormatConvert ═══════════════════════

    def _tab_convert(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' Format ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text='To Format:', width=10).pack(side=tk.LEFT)
        self._fmt_btns(r1)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r2, text='Replace Original', variable=self.v_conv_replace, value=True,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r2, text='Output to:', variable=self.v_conv_replace, value=False,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT, padx=10)
        self.conv_outrow = ttk.Frame(r2)
        ttk.Entry(self.conv_outrow, textvariable=self.v_conv_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.conv_outrow, text='Browse', command=lambda: self._browse_out(self.v_conv_outfolder)).pack(side=tk.LEFT)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r3, text='Backup', variable=self.v_conv_backup).pack(side=tk.LEFT)
        ttk.Button(r3, text='Start Convert', command=self._run_convert).pack(side=tk.RIGHT, ipadx=8)

    def _fmt_btns(self, parent):
        for fmt in CONVERT_TARGETS:
            ttk.Radiobutton(parent, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=3)

    # ═══════════════════════ Tab: 重命名 ═══════════════════════

    def _tab_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' Rename ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 模式选择
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text='Mode:', width=8).pack(side=tk.LEFT)
        modes = [('Prefix', 'prefix'), ('Suffix', 'suffix'), ('Replace', 'replace'),
                 ('Sequence', 'seq'), ('Case', 'case')]
        for txt, val in modes:
            ttk.Radiobutton(r0, text=txt, variable=self.r_mode, value=val,
                            command=self._toggle_rename_ui).pack(side=tk.LEFT, padx=3)

        # 动态参数区
        self.r_frame = ttk.Frame(f)
        self.r_frame.pack(fill=tk.X, pady=4)

        # 前后缀
        self.r_prefix_row = ttk.Frame(f)
        ttk.Label(self.r_prefix_row, text='Prefix:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_prefix_row, textvariable=self.r_prefix, width=20).pack(side=tk.LEFT, padx=4)

        self.r_suffix_row = ttk.Frame(f)
        ttk.Label(self.r_suffix_row, text='Suffix:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_suffix_row, textvariable=self.r_suffix, width=20).pack(side=tk.LEFT, padx=4)

        # Replace
        self.r_replace_row = ttk.Frame(f)
        ttk.Label(self.r_replace_row, text='Find:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_src, width=18).pack(side=tk.LEFT)
        ttk.Label(self.r_replace_row, text='Replace:').pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_dst, width=18).pack(side=tk.LEFT)

        # Sequence
        self.r_seq_row = ttk.Frame(f)
        ttk.Label(self.r_seq_row, text='Template:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_seq_row, textvariable=self.r_seq_template, width=20).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.r_seq_row, text='Start:').pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=99999, textvariable=self.r_seq_start, width=5, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text='Digits:').pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=10, textvariable=self.r_seq_digits, width=3, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text='{num}=number', foreground='#6c7086').pack(side=tk.LEFT, padx=4)

        # Size写
        self.r_case_row = ttk.Frame(f)
        ttk.Checkbutton(self.r_case_row, text='lowercase', variable=self.r_lowercase).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(self.r_case_row, text='UPPERCASE', variable=self.r_uppercase).pack(side=tk.LEFT, padx=4)

        # 预览 + 按钮
        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Button(r5, text='Preview', command=self._preview_rename).pack(side=tk.LEFT)
        ttk.Button(r5, text='Rename', command=self._run_rename).pack(side=tk.RIGHT, ipadx=8)

        self._toggle_rename_ui()

    def _toggle_rename_ui(self):
        for w in [self.r_prefix_row, self.r_suffix_row, self.r_replace_row,
                   self.r_seq_row, self.r_case_row]:
            w.pack_forget()
        mode = self.r_mode.get()
        if mode in ('prefix', 'suffix'):
            self.r_prefix_row.pack(fill=tk.X, pady=2)
            self.r_suffix_row.pack(fill=tk.X, pady=2)
        elif mode == 'replace':
            self.r_replace_row.pack(fill=tk.X, pady=2)
        elif mode == 'seq':
            self.r_seq_row.pack(fill=tk.X, pady=2)
        elif mode == 'case':
            self.r_case_row.pack(fill=tk.X, pady=2)

    # ═══════════════════════ Tab: Watermark ═══════════════════════

    def _tab_watermark(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' Watermark ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 类型
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text='Type:', width=10).pack(side=tk.LEFT)
        ttk.Radiobutton(r0, text='Text', variable=self.w_type, value='text',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(r0, text='Image', variable=self.w_type, value='image',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)

        # ── TextWatermark参数 ──
        self.w_text_frame = ttk.Frame(f)
        self.w_text_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_text_frame, text='Content:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_text_frame, textvariable=self.w_text, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.w_text_frame, text='Size:').pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_text_frame, from_=8, to=200, textvariable=self.w_fontsize, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='Color:').pack(side=tk.LEFT, padx=(8, 2))
        ttk.Entry(self.w_text_frame, textvariable=self.w_color, width=8).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='(#HEX)', foreground='#6c7086').pack(side=tk.LEFT, padx=2)

        # ── ImageWatermark参数 ──
        self.w_img_frame = ttk.Frame(f)
        self.w_img_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_img_frame, text='Image:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_img_frame, textvariable=self.w_image_path, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.w_img_frame, text='Browse',
                   command=lambda: self._browse_img(self.w_image_path)).pack(side=tk.LEFT)
        ttk.Label(self.w_img_frame, text='Scale%:').pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_img_frame, from_=5, to=100, textvariable=self.w_img_scale, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        # 通用参数
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text='Opacity:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.w_opacity).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.w_op_lbl = ttk.Label(r2, text='50%', width=4); self.w_op_lbl.pack(side=tk.LEFT, padx=4)
        self.w_opacity.trace_add('write', lambda *a: self.w_op_lbl.config(
            text=f'{self.w_opacity.get()}%'))

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text='Position:', width=10).pack(side=tk.LEFT)
        positions = [('Top L', 'top-left'), ('Top R', 'top-right'), ('Center', 'center'),
                     ('Bot L', 'bottom-left'), ('Bot R', 'bottom-right')]
        for txt, val in positions:
            ttk.Radiobutton(r3, text=txt, variable=self.w_position,
                            value=val).pack(side=tk.LEFT, padx=3)

        # 输出
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r4, text='Replace Original', variable=self.w_replace, value=True,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text='Output to:', variable=self.w_replace, value=False,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT, padx=10)
        self.wm_outrow = ttk.Frame(r4)
        ttk.Entry(self.wm_outrow, textvariable=self.w_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.wm_outrow, text='Browse', command=lambda: self._browse_out(self.w_outfolder)).pack(side=tk.LEFT)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r5, text='Backup', variable=self.w_backup).pack(side=tk.LEFT)
        ttk.Button(r5, text='Watermark', command=self._run_watermark).pack(side=tk.RIGHT, ipadx=8)

        self.w_img_frame.pack_forget()

    def _toggle_wm_ui(self):
        if self.w_type.get() == 'text':
            self.w_img_frame.pack_forget()
            self.w_text_frame.pack(fill=tk.X, pady=2)
        else:
            self.w_text_frame.pack_forget()
            self.w_img_frame.pack(fill=tk.X, pady=2)

    # ═══════════════════════ Tab: AI 重命名 ═══════════════════════

    def _tab_ai_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' AI Rename ')

        f = ttk.Frame(tab)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # API Key
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='DeepSeek API Key:', width=14).pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.ai_api_key, width=50, show='*').pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(r1, text='Show/Hide', command=lambda: self._toggle_key_show(r1)).pack(side=tk.LEFT)

        # Prompt
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text='Prompt Prompt:').pack(anchor=tk.W)
        self.ai_prompt_text = tk.Text(f, height=4, bg='#FFFFFF', fg=FG, insertbackground=FG,
                                       font=('Lucida Console', 9), relief=tk.SUNKEN, borderwidth=2)
        self.ai_prompt_text.pack(fill=tk.X, padx=0, pady=2)
        self.ai_prompt_text.insert('1.0', self.ai_prompt.get())

        # 按钮
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Button(r3, text='AI Analyze', command=self._ai_analyze).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(r3, text='Apply AI', command=self._ai_apply).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r3, text='Clear', command=self._ai_clear).pack(side=tk.RIGHT, padx=8)

        # 结果预览
        ttk.Label(f, text='AI Suggestions:').pack(anchor=tk.W, pady=(6, 2))
        tree_fr = ttk.Frame(f)
        tree_fr.pack(fill=tk.BOTH, expand=True)
        self.ai_tree = ttk.Treeview(tree_fr, columns=('original', 'suggested'),
                                     show='headings', height=6)
        self.ai_tree.heading('original', text='Original')
        self.ai_tree.heading('suggested', text='Suggested')
        self.ai_tree.column('original', width=320, minwidth=150)
        self.ai_tree.column('suggested', width=320, minwidth=150)
        ai_vsb = ttk.Scrollbar(tree_fr, orient=tk.VERTICAL, command=self.ai_tree.yview)
        self.ai_tree.configure(yscrollcommand=ai_vsb.set)
        self.ai_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ai_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _toggle_key_show(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.config(show='' if child.cget('show') == '*' else '*')

    # ═══════════════════════ 通用工具方法 ═══════════════════════

    def _browse(self):
        path = filedialog.askdirectory(title='Select Image Folder')
        if path:
            self.folder.set(os.path.normpath(path))
            self._refresh()

    def _browse_out(self, var):
        path = filedialog.askdirectory(title='Select Output Folder')
        if path:
            var.set(os.path.normpath(path))

    def _browse_img(self, var):
        path = filedialog.askopenfilename(title='Select Watermark Image',
                                          filetypes=[('Image', '*.png *.jpg *.jpeg *.webp *.bmp')])
        if path:
            var.set(os.path.normpath(path))

    def _toggle_out(self, replace_var, row, folder_var):
        if replace_var.get():
            row.pack_forget()
        else:
            row.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
            if not folder_var.get():
                default = os.path.join(self.folder.get() or '', 'output')
                folder_var.set(default)

    def _slider_label(self, val, lbl):
        lbl.config(text=f'{int(float(val))}%')

    def _fmt_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'

    def _refresh(self):
        folder = self.folder.get()
        self.file_data.clear()
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()
        if not folder or not os.path.isdir(folder):
            self.lbl_count.config(text='')
            return
        for f in sorted(os.listdir(folder)):
            ext = os.path.splitext(f)[1].lower()
            if ext not in SUPPORTED_EXT:
                continue
            full = os.path.join(folder, f)
            try:
                sz = os.path.getsize(full)
            except OSError:
                continue
            try:
                with Image.open(full) as img:
                    dims = f'{img.width}x{img.height}'
                    fmt = img.format or ext
            except Exception:
                dims = '?'
                fmt = ext
            d = {'name': f, 'path': full, 'size': sz, 'size_str': self._fmt_size(sz),
                 'dimensions': dims, 'format': fmt}
            self.file_data.append(d)
            item = self.tree.insert('', tk.END, values=(f, self._fmt_size(sz), dims, fmt))
            self.tree_items[f] = item
        total = sum(d['size'] for d in self.file_data)
        self.lbl_count.config(text=f'{len(self.file_data)}  files | {self._fmt_size(total)}')

    def _preview(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        fname = self.tree.item(sel[0], 'values')[0]
        path = os.path.join(self.folder.get(), fname)
        if os.path.exists(path):
            try:
                Image.open(path).show()
            except Exception as e:
                messagebox.showerror('Preview Failed', str(e))

    def _backup_mgr(self):
        folder = self.folder.get()
        if not folder:
            return
        backups = self._find_backups(folder)
        if not backups:
            messagebox.showinfo('Backup Manager', 'No backups found')
            return
        dialog = BackupDialog(self.root, backups, folder)
        self.root.wait_window(dialog.top)
        if dialog.result == 'restore':
            self._do_restore(dialog.chosen, folder)
        elif dialog.result == 'clear':
            self._do_clear_backups(backups)

    def _find_backups(self, folder):
        folder_name = os.path.basename(folder.rstrip(os.sep))
        backup_root = os.path.join(os.path.dirname(folder), 'backup')
        if not os.path.isdir(backup_root):
            return []
        backups = []
        for name in sorted(os.listdir(backup_root), reverse=True):
            if name.startswith(folder_name + '_'):
                backups.append(os.path.join(backup_root, name))
        return backups

    def _do_backup(self, folder, file_names):
        folder_name = os.path.basename(folder.rstrip(os.sep))
        backup_root = os.path.join(os.path.dirname(folder), 'backup')
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(backup_root, f'{folder_name}_{ts}')
        os.makedirs(backup_dir, exist_ok=True)
        for f in file_names:
            shutil.copy2(os.path.join(folder, f), os.path.join(backup_dir, f))
        return backup_dir

    def _do_restore(self, backup_dir, folder):
        if not messagebox.askyesno('Confirm Restore', f'This will overwrite current folder from backup:\n{os.path.basename(backup_dir)}\n\nConfirm？'):
            return
        for f in os.listdir(backup_dir):
            src = os.path.join(backup_dir, f)
            dst = os.path.join(folder, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        self._refresh()
        messagebox.showinfo('Restore Done', 'Backup restored')

    def _do_clear_backups(self, backups):
        if not messagebox.askyesno('Confirm', f'将删除 {len(backups)}  backup(s)，不可撤销。Confirm？'):
            return
        for d in backups:
            shutil.rmtree(d)
        messagebox.showinfo('Done', f'Cleared {len(backups)}  backup(s)')

    # ═══════════════════════ Compress执行 ═══════════════════════

    def _run_compress(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('Notice', 'Please select a folder and refresh')
            return
        self.is_running = True
        file_list = [d['name'] for d in self.file_data]
        quality = int(float(self.c_quality.get()))
        resize_pct = int(float(self.c_resize.get()))
        do_backup = self.c_backup.get()
        replace = self.c_replace.get()
        out = self.c_outfolder.get() if not replace else None
        threading.Thread(target=self._compress_thread,
                         args=(folder, file_list, quality, resize_pct, do_backup, replace, out),
                         daemon=True).start()

    def _compress_thread(self, folder, file_list, quality, resize_pct, do_backup, replace, out):
        self._animate_status('Compressing')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('Backing up')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)
        for i, fname in enumerate(file_list):
            if fname in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[fname]: self._highlight_item(t))
            src = os.path.join(folder, fname)
            sb = os.path.getsize(src)
            total_before += sb
            dst = src if replace else os.path.join(out, fname)
            try:
                img = Image.open(src)
                om = img.mode
                ext = os.path.splitext(dst)[1].lower()
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
                    img = img.resize((int(w * resize_pct / 100), int(h * resize_pct / 100)), Image.LANCZOS)
                kw = {'optimize': True}
                if ext in QUALITY_FORMATS:
                    kw['quality'] = quality
                img.save(dst, **kw)
                img.close()
                sa = os.path.getsize(dst)
                total_after += sa
                self.root.after(0, lambda n=fname, s=sa: self._update_row_size(n, s))
            except Exception as e:
                errors.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Compressing {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, 'Compress')

    # ═══════════════════════ FormatConvert执行 ═══════════════════════

    def _run_convert(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('Notice', 'Please select a folder and refresh')
            return
        self.is_running = True
        file_list = [d['name'] for d in self.file_data]
        target_fmt = self.v_target_fmt.get()
        do_backup = self.v_conv_backup.get()
        replace = self.v_conv_replace.get()
        out = self.v_conv_outfolder.get() if not replace else None
        threading.Thread(target=self._convert_thread,
                         args=(folder, file_list, target_fmt, do_backup, replace, out),
                         daemon=True).start()

    def _convert_thread(self, folder, file_list, target_fmt, do_backup, replace, out):
        self._animate_status('Converting Format')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('Backing up')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)
        for i, fname in enumerate(file_list):
            if fname in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[fname]: self._highlight_item(t))
            src = os.path.join(folder, fname)
            sb = os.path.getsize(src)
            total_before += sb
            base = os.path.splitext(fname)[0]
            new_name = base + target_fmt
            dst = src if (replace and target_fmt == os.path.splitext(fname)[1].lower()) else (
                os.path.join(folder, new_name) if replace else os.path.join(out, new_name))
            try:
                img = Image.open(src)
                om = img.mode
                if om in ('RGBA', 'P', 'LA') and target_fmt.lower() in ('.jpg', '.jpeg'):
                    rgb = Image.new('RGB', img.size, (255, 255, 255))
                    if om == 'P':
                        img = img.convert('RGBA')
                    rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb
                elif om not in ('RGB', 'L'):
                    img = img.convert('RGB')
                img.save(dst, optimize=True)
                img.close()
                sa = os.path.getsize(dst)
                total_after += sa
                if replace and target_fmt != os.path.splitext(fname)[1].lower() and os.path.exists(src):
                    try:
                        os.remove(src)
                    except Exception:
                        pass
                self.root.after(0, lambda n=new_name, s=sa: self._update_row_rename(fname, n, s))
            except Exception as e:
                errors.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Converting {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, 'Convert', post_refresh=True)

    # ═══════════════════════ 重命名执行 ═══════════════════════

    def _preview_rename(self):
        mapping = self._gen_rename_map()
        if not mapping:
            messagebox.showwarning('Notice', 'No matching files')
            return
        msgs = []
        for old, new in list(mapping.items())[:20]:
            msgs.append(f'{old}\n  → {new}')
        if len(mapping) > 20:
            msgs.append(f'... 共 {len(mapping)} 个文件')
        messagebox.showinfo('Rename Preview', '\n'.join(msgs))

    def _gen_rename_map(self):
        folder = self.folder.get()
        if not folder or not self.file_data:
            return {}
        mode = self.r_mode.get()
        mapping = {}
        seq = self.r_seq_start.get()
        digits = self.r_seq_digits.get()
        for d in self.file_data:
            name = d['name']
            base, ext = os.path.splitext(name)
            if mode == 'prefix':
                new = self.r_prefix.get() + base + self.r_suffix.get() + ext
            elif mode == 'suffix':
                new = base + self.r_prefix.get() + self.r_suffix.get() + ext
            elif mode == 'replace':
                src = self.r_replace_src.get()
                if src and src in base:
                    new = base.replace(src, self.r_replace_dst.get()) + ext
                else:
                    continue
            elif mode == 'seq':
                template = self.r_seq_template.get()
                new = template.replace('{num}', str(seq).zfill(digits)) + ext
                seq += 1
            elif mode == 'case':
                if self.r_lowercase.get():
                    base = base.lower()
                if self.r_uppercase.get():
                    base = base.upper()
                new = base + ext
            else:
                continue
            if new != name:
                mapping[name] = new
        return mapping

    def _run_rename(self):
        if self.is_running:
            return
        folder = self.folder.get()
        mapping = self._gen_rename_map()
        if not mapping:
            messagebox.showwarning('Notice', 'No files to rename')
            return
        if not messagebox.askyesno('Confirm Rename', f'Will rename {len(mapping)} 个文件，Confirm？'):
            return
        self.is_running = True
        threading.Thread(target=self._rename_thread, args=(folder, mapping), daemon=True).start()

    def _rename_thread(self, folder, mapping):
        self._animate_status('Renaming')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        total = len(mapping)
        errors = []
        for i, (old, new) in enumerate(mapping.items()):
            if old in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[old]: self._highlight_item(t))
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                errors.append(f'{old} → {new}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Renaming {i+1}/{total}')
        self._set_progress(100)
        self.root.after(0, self._stop_spinner)
        self.root.after(0, self._clear_highlight)
        if errors:
            self._set_status(f'Done，{len(errors)}  errors')
            self.root.after(100, lambda: messagebox.showerror('Error', '\n'.join(errors[:10])))
        else:
            self._set_status('Rename Done')
            self.root.after(100, lambda: messagebox.showinfo('Done', f'{total}  file(s) renamed'))
        self.root.after(50, self._refresh)
        self.is_running = False

    # ═══════════════════════ Watermark执行 ═══════════════════════

    def _run_watermark(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('Notice', 'Please select a folder and refresh')
            return
        wtype = self.w_type.get()
        if wtype == 'image' and not self.w_image_path.get():
            messagebox.showwarning('Notice', 'Please select watermark image')
            return
        if wtype == 'image' and not os.path.exists(self.w_image_path.get()):
            messagebox.showwarning('Notice', 'Watermark image not found')
            return
        self.is_running = True
        file_list = [d['name'] for d in self.file_data]
        do_backup = self.w_backup.get()
        replace = self.w_replace.get()
        out = self.w_outfolder.get() if not replace else None
        params = {
            'type': wtype,
            'text': self.w_text.get(),
            'fontsize': self.w_fontsize.get(),
            'opacity': self.w_opacity.get() / 100,
            'position': self.w_position.get(),
            'color': self.w_color.get(),
            'image_path': self.w_image_path.get(),
            'img_scale': self.w_img_scale.get() / 100,
        }
        threading.Thread(target=self._watermark_thread,
                         args=(folder, file_list, params, do_backup, replace, out),
                         daemon=True).start()

    def _watermark_thread(self, folder, file_list, params, do_backup, replace, out):
        self._animate_status('Watermarking')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('Backing up')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)

        wm_img = None
        if params['type'] == 'image':
            wm_img = Image.open(params['image_path']).convert('RGBA')

        for i, fname in enumerate(file_list):
            if fname in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[fname]: self._highlight_item(t))
            src = os.path.join(folder, fname)
            sb = os.path.getsize(src)
            total_before += sb
            dst = src if replace else os.path.join(out, fname)
            try:
                img = Image.open(src).convert('RGBA')
                layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                if params['type'] == 'text':
                    self._draw_text_wm(draw, img.size, params)
                else:
                    self._draw_image_wm(layer, img.size, wm_img, params)

                result = Image.alpha_composite(img, layer)
                if img.mode != 'RGBA':
                    result = result.convert('RGB')
                result.save(dst, optimize=True)
                img.close()
                result.close()
                sa = os.path.getsize(dst)
                total_after += sa
            except Exception as e:
                errors.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Watermarking {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, 'Watermark')

    def _draw_text_wm(self, draw, size, params):
        try:
            font = ImageFont.truetype('simhei.ttf', params['fontsize'])
        except Exception:
            try:
                font = ImageFont.truetype('arial.ttf', params['fontsize'])
            except Exception:
                font = ImageFont.load_default()
        text = params['text']
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._calc_position(size, (tw, th), params['position'], margin=20)
        color = self._hex_to_rgba(params['color'], int(params['opacity'] * 255))
        draw.text((x, y), text, fill=color, font=font)

    def _draw_image_wm(self, layer, size, wm_img, params):
        w, h = size
        wm_w = int(w * params['img_scale'] / 100)
        wm_h = int(wm_img.height * wm_w / wm_img.width)
        wm_resized = wm_img.resize((wm_w, wm_h), Image.LANCZOS)
        # Apply opacity
        if params['opacity'] < 1.0:
            alpha = wm_resized.split()[3]
            alpha = alpha.point(lambda p: int(p * params['opacity']))
            wm_resized.putalpha(alpha)
        x, y = self._calc_position(size, (wm_w, wm_h), params['position'], margin=20)
        layer.paste(wm_resized, (x, y), wm_resized)

    def _calc_position(self, img_size, elem_size, pos, margin=20):
        iw, ih = img_size
        ew, eh = elem_size
        pos_map = {
            'top-left': (margin, margin),
            'top-right': (iw - ew - margin, margin),
            'center': ((iw - ew) // 2, (ih - eh) // 2),
            'bottom-left': (margin, ih - eh - margin),
            'bottom-right': (iw - ew - margin, ih - eh - margin),
        }
        return pos_map.get(pos, pos_map['bottom-right'])

    def _hex_to_rgba(self, hex_color, alpha):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r, g, b, alpha)

    # ═══════════════════════ AI 重命名 ═══════════════════════

    def _ai_analyze(self):
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('Notice', 'Please select a folder and refresh')
            return
        api_key = self.ai_api_key.get().strip()
        if not api_key:
            messagebox.showwarning('Notice', 'Enter DeepSeek API Key')
            return
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        # Show loading placeholder in AI tree
        self.ai_tree.insert('', tk.END, values=('Connecting to DeepSeek...', '⏳ Waiting...'))
        file_names = [d['name'] for d in self.file_data]
        prompt = self.ai_prompt_text.get('1.0', tk.END).strip()
        self._animate_status('AI Analyzing')
        self.root.after(0, self._start_spinner)
        self.is_running = True
        self._anim_ai_loading_id = self.root.after(0, self._anim_ai_loading)
        threading.Thread(target=self._ai_thread, args=(api_key, file_names, prompt), daemon=True).start()

    def _anim_ai_loading(self):
        """动画更新 AI 树中的加载Notice"""
        if not self.is_running:
            return
        items = self.ai_tree.get_children()
        if items and not self.ai_result:
            dots_list = ['⏳ Waiting.', '⏳ Waiting..', '⏳ Waiting...',
                         '⏳ Analyzing.', '⏳ Analyzing..', '⏳ Analyzing...']
            idx = int(time.time() * 1.5) % len(dots_list)
            self.ai_tree.item(items[0], values=('Connecting to DeepSeek...', dots_list[idx]))
            self._anim_ai_loading_id = self.root.after(400, self._anim_ai_loading)

    def _ai_thread(self, api_key, file_names, prompt):
        try:
            import urllib.request
            import urllib.error
            import ast
            req_body = json.dumps({
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': 'You are a file naming assistant，Return a standard JSON array (double quotes). Format:。Each element: {"original": "name", "new": "newname"}.'},
                    {'role': 'user', 'content': f'{prompt}\n\nName列表:\n' + '\n'.join(file_names)}
                ],
                'temperature': 0.7,
                'max_tokens': 4096
            }).encode('utf-8')
            req = urllib.request.Request(
                'https://api.deepseek.com/v1/chat/completions',
                data=req_body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode('utf-8'))
            content = data['choices'][0]['message']['content'].strip()

            result_list = None
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    result_list = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    pass
            if result_list is None:
                try:
                    result_list = ast.literal_eval(json_match.group() if json_match else content)
                except (ValueError, SyntaxError):
                    pass
            if result_list is None:
                result_list = [line.strip() for line in content.splitlines() if line.strip()]
                if not result_list:
                    result_list = [content]

            if not isinstance(result_list, list):
                result_list = [result_list]

            for item in result_list:
                if isinstance(item, dict):
                    orig = item.get('original', '')
                    new_name = item.get('new', item.get('new_name', item.get('suggested', '')))
                    if orig and orig in file_names:
                        self.ai_result[orig] = self._sanitize_filename(new_name) or orig
                elif isinstance(item, str) and len(self.ai_result) < len(file_names):
                    self.ai_result[file_names[len(self.ai_result)]] = self._sanitize_filename(item) or file_names[len(self.ai_result)]

            for fn in file_names:
                if fn not in self.ai_result:
                    self.ai_result[fn] = fn

            self.root.after(0, self._ai_populate)
            self.root.after(0, self._stop_ai_loading)
            self.root.after(0, self._stop_spinner)
            self._set_status(f'AI done: {len(self.ai_result)}  suggestions')
            self.is_running = False
        except Exception as e:
            self.root.after(0, self._stop_ai_loading)
            self.root.after(0, self._stop_spinner)
            self._set_status(f'AI Error: {e}')
            self.root.after(0, lambda: messagebox.showerror('AI Error', str(e)))
            self.is_running = False

    def _stop_ai_loading(self):
        if hasattr(self, '_anim_ai_loading_id') and self._anim_ai_loading_id:
            self.root.after_cancel(self._anim_ai_loading_id)
            self._anim_ai_loading_id = None

    def _sanitize_filename(self, name):
        """清理Name中的非法字符"""
        if not name:
            return name
        # Remove Windows illegal chars: < > : " / \ | ? *
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Remove control chars
        name = re.sub(r'[\x00-\x1f]', '', name)
        # Remove leading/trailing dots and spaces
        name = name.strip('. ')
        # Replace curly quotes and braces
        name = name.replace('{', '').replace('}', '').replace("'", '').replace('"', '')
        return name

    def _ai_populate(self):
        self.ai_tree.delete(*self.ai_tree.get_children())
        for orig, sugg in self.ai_result.items():
            self.ai_tree.insert('', tk.END, values=(orig, sugg))

    def _ai_apply(self):
        if not self.ai_result:
            messagebox.showwarning('Notice', 'Run AI Analyze first')
            return
        folder = self.folder.get()
        mapping = {}
        for orig, sugg in self.ai_result.items():
            if not sugg or not isinstance(sugg, str):
                continue
            # Ensure sugg has extension, otherwise use original
            if '.' not in sugg:
                sugg = sugg + os.path.splitext(orig)[1]
            # Extract base name and force original extension
            orig_ext = os.path.splitext(orig)[1]
            sugg_base = os.path.splitext(sugg)[0]
            new_name = self._sanitize_filename(sugg_base) + orig_ext
            if new_name and new_name != orig:
                # Prevent duplicate names
                if new_name in mapping.values() or new_name in self.ai_result:
                    new_name = f"{os.path.splitext(new_name)[0]}_{len(mapping)}{orig_ext}"
                mapping[orig] = new_name
        if not mapping:
            messagebox.showinfo('Notice', 'No files to rename')
            return
        if not messagebox.askyesno('Confirm', f'AI rename {len(mapping)} 个文件，Confirm？'):
            return
        errors = []
        for old, new in mapping.items():
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                errors.append(f'{old} → {new}: {e}')
        self._refresh()
        if errors:
            messagebox.showerror('Error', '\n'.join(errors[:10]))
        else:
            messagebox.showinfo('Done', f'{len(mapping)}  file(s) renamed')

    def _ai_clear(self):
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        self._set_status('Cleared AI results')

    # ═══════════════════════ 动画系统 ═══════════════════════

    def _start_spinner(self):
        self.spinner.pack(side=tk.LEFT, padx=(0, 6))
        self._anim_spinner()

    def _stop_spinner(self):
        if self._anim_spinner_id:
            self.root.after_cancel(self._anim_spinner_id)
            self._anim_spinner_id = None
        self.spinner.pack_forget()

    def _anim_spinner(self):
        self._anim_spinner_angle = (self._anim_spinner_angle + 15) % 360
        self.spinner.itemconfig(self.spinner_arc, start=self._anim_spinner_angle)
        self._anim_spinner_id = self.root.after(60, self._anim_spinner)

    def _highlight_item(self, item_id):
        self._clear_highlight()
        self._anim_highlight_item = item_id
        self._anim_highlight_on = True
        self._do_highlight()

    def _do_highlight(self):
        if not self._anim_highlight_item:
            return
        tag = 'processing'
        if self._anim_highlight_on:
            self.tree.tag_configure(tag, background=ACCENT, foreground=BG3)
            self.tree.item(self._anim_highlight_item, tags=(tag,))
        else:
            self.tree.tag_configure(tag, background=BG2, foreground=FG)
            self.tree.item(self._anim_highlight_item, tags=(tag,))
        self._anim_highlight_on = not self._anim_highlight_on
        self._anim_highlight_id = self.root.after(350, self._do_highlight)

    def _clear_highlight(self):
        if self._anim_highlight_id:
            self.root.after_cancel(self._anim_highlight_id)
            self._anim_highlight_id = None
        if self._anim_highlight_item:
            self.tree.item(self._anim_highlight_item, tags=())
            self._anim_highlight_item = None

    def _animate_progress(self):
        if self._progress_anim_id:
            self.root.after_cancel(self._progress_anim_id)
        diff = self._progress_target - self._progress_current
        if abs(diff) < 0.5:
            self._progress_current = self._progress_target
            self.progress.config(value=self._progress_current)
            return
        step = diff * 0.15
        self._progress_current += step
        self.progress.config(value=self._progress_current)
        self._progress_anim_id = self.root.after(20, self._animate_progress)

    def _set_progress(self, val):
        self._progress_target = val
        self.root.after(0, self._animate_progress)

    def _animate_status(self, msg):
        if self._status_anim_id:
            self.root.after_cancel(self._status_anim_id)
        dots = ['', '.', '..', '...']
        def cycle(i=0):
            self.lbl_status.config(text=f'{msg}{dots[i % 4]}')
            self._status_anim_id = self.root.after(400, lambda: cycle(i + 1))
        cycle()

    def _stop_status_anim(self):
        if self._status_anim_id:
            self.root.after_cancel(self._status_anim_id)
            self._status_anim_id = None

    # ═══════════════════════ 线程工具 ═══════════════════════

    def _set_status(self, msg):
        self._stop_status_anim()
        self.root.after(0, lambda: self.lbl_status.config(text=msg))

    def _update_row_size(self, fname, new_size):
        if fname in self.tree_items:
            vals = list(self.tree.item(self.tree_items[fname], 'values'))
            vals[1] = self._fmt_size(new_size)
            self.tree.item(self.tree_items[fname], values=vals)

    def _update_row_rename(self, old_name, new_name, new_size):
        self._update_row_size(old_name, new_size)
        if old_name in self.tree_items:
            vals = list(self.tree.item(self.tree_items[old_name], 'values'))
            vals[0] = new_name
            self.tree.item(self.tree_items[old_name], values=vals)

    def _finish_op(self, total_before, total_after, errors, op_name, post_refresh=False):
        saved = total_before - total_after
        ratio = (total_after / total_before * 100) if total_before else 0
        msg = (f'{self._fmt_size(total_before)} → {self._fmt_size(total_after)} '
               f'(节省 {self._fmt_size(saved)}, {ratio:.1f}%)')
        self._stop_spinner()
        self._clear_highlight()
        self._set_status(f'{op_name}Done — {msg}')
        self.is_running = False
        if post_refresh:
            self.root.after(100, self._refresh)
        if errors:
            self.root.after(200, lambda: messagebox.showwarning(
                f'{op_name}Done', f'{msg}\n\n{len(errors)}  errors:\n' + '\n'.join(errors[:5])))

    # ═══════════════════════ XP Classic Theme ═══════════════════════

    def _apply_dark_theme(self):
        style = ttk.Style()
        # Use classic/winnative for native Win32 look
        try:
            style.theme_use('winnative')
        except Exception:
            try:
                style.theme_use('classic')
            except Exception:
                style.theme_use('vista')

        style.configure('.', background=BG, foreground=FG)
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=FG, font=('Tahoma', 9))
        style.configure('TLabelframe', background=BG, foreground=FG)
        style.configure('TButton', font=('Tahoma', 9), padding=4)
        style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=FG, font=('Tahoma', 9))
        style.configure('TScale', background=BG)
        style.configure('TCheckbutton', background=BG, foreground=FG, font=('Tahoma', 9))
        style.configure('TRadiobutton', background=BG, foreground=FG, font=('Tahoma', 9))
        style.configure('TSeparator', background=BORDER)
        style.configure('TProgressbar', background=ACCENT, troughcolor=BG2)
        style.configure('TNotebook', background=BG, borderwidth=1)
        style.configure('TNotebook.Tab', background=BG2, foreground=FG, font=('Tahoma', 9), padding=(14, 4))
        style.map('TNotebook.Tab', background=[('selected', BG)], foreground=[('selected', FG)])
        style.configure('Treeview', background=ENTRY_BG, foreground=FG, fieldbackground=ENTRY_BG, font=('Tahoma', 9))
        style.configure('Treeview.Heading', background=BG, foreground=FG, font=('Tahoma', 9, 'bold'))
        style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', '#FFFFFF')])
        style.map('Treeview.Heading', background=[('active', BG2)])



class BackupDialog:
    def __init__(self, parent, backups, folder):
        self.result = None
        self.chosen = None
        self.top = tk.Toplevel(parent)
        self.top.title('Backup Manager')
        self.top.geometry('550x320')
        self.top.configure(bg=BG)
        self.top.transient(parent)
        self.top.grab_set()

        ttk.Label(self.top, text='Backup Records:', font=('Tahoma', 10, 'bold')).pack(pady=(10, 4))

        frame = ttk.Frame(self.top)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        self.lb = tk.Listbox(frame, bg='#FFFFFF', fg=FG, selectbackground=ACCENT,
                             selectforeground='#FFFFFF', font=('Tahoma', 10),
                             activestyle='none', relief=tk.SUNKEN, borderwidth=2)
        self.lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lb.configure(yscrollcommand=sb.set)
        for b in backups:
            self.lb.insert(tk.END, os.path.basename(b))
        self.lb.selection_set(0)

        btn = ttk.Frame(self.top)
        btn.pack(pady=(6, 10))
        ttk.Button(btn, text='Restore', command=lambda: self._done('restore')).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(btn, text='Clear All', command=lambda: self._done('clear')).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn, text='Cancel', command=self.top.destroy).pack(side=tk.LEFT, padx=8)

        self._backups = backups

    def _done(self, action):
        self.result = action
        sel = self.lb.curselection()
        if sel:
            self.chosen = self._backups[sel[0]]
        self.top.destroy()


def main():
    root = tk.Tk()
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    ImgBatchApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
