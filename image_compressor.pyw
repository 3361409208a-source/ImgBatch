#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch — 图片批量处理工具 (压缩/格式转换/重命名/水印/AI重命名)"""

import os
import json
import shutil
import threading
import time
import re
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

BG = '#1e1e2e'
BG2 = '#2a2a3d'
BG3 = '#181825'
FG = '#cdd6f4'
ACCENT = '#89b4fa'
ACCENT2 = '#a6e3a1'
WARN = '#fab387'
ERR = '#f38ba8'
BORDER = '#45475a'
ENTRY_BG = '#313244'


class ImgBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title('ImgBatch — 图片批量处理工具')
        self.root.geometry('900x720')
        self.root.minsize(820, 600)
        self.root.configure(bg=BG)

        self.folder = tk.StringVar()
        self.file_data = []
        self.is_running = False
        self.tree_items = {}

        # ── 压缩 Compress ──
        self.c_quality = tk.IntVar(value=75)
        self.c_resize = tk.IntVar(value=100)
        self.c_replace = tk.BooleanVar(value=True)
        self.c_outfolder = tk.StringVar()
        self.c_backup = tk.BooleanVar(value=True)

        # ── 格式转换 Convert ──
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

        # ── 水印 Watermark ──
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
        self.ai_prompt = tk.StringVar(value='请分析以下图片文件名列表，为每个文件生成一个简洁规范的英文文件名（含扩展名），格式如：player_name-position-country.jpg。只返回JSON数组，不要其他内容。')
        self.ai_result = {}

        self._build_ui()
        self._apply_dark_theme()

    # ═══════════════════════ UI 构建 ═══════════════════════

    def _build_ui(self):
        # ── 顶部：文件夹选择 ──
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=(10, 0))
        ttk.Label(top, text='目标文件夹:', font=('', 10, 'bold')).pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(top, textvariable=self.folder, width=55, font=('', 10))
        self.folder_entry.pack(side=tk.LEFT, padx=(6, 6), fill=tk.X, expand=True)
        ttk.Button(top, text='浏览...', command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top, text='刷新', command=self._refresh).pack(side=tk.LEFT, padx=(6, 0))
        self._drop_target(top)

        # ── 文件列表 ──
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=6)
        list_hdr = ttk.Frame(self.root)
        list_hdr.pack(fill=tk.X, padx=12)
        ttk.Label(list_hdr, text='文件列表（双击预览）', font=('', 9, 'bold')).pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(list_hdr, text='')
        self.lbl_count.pack(side=tk.RIGHT)

        tree_fr = ttk.Frame(self.root)
        tree_fr.pack(fill=tk.BOTH, expand=True, padx=12)
        cols = ('filename', 'size', 'dimensions', 'format')
        self.tree = ttk.Treeview(tree_fr, columns=cols, show='headings', height=8, selectmode='extended')
        for c, w, txt in zip(cols, [340, 80, 110, 70], ['文件名', '大小', '尺寸', '格式']):
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

        # ── 状态栏 ──
        st = ttk.Frame(self.root)
        st.pack(fill=tk.X, padx=12, pady=(4, 8))
        self.progress = ttk.Progressbar(st, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 2))
        sf = ttk.Frame(st)
        sf.pack(fill=tk.X)
        self.lbl_status = ttk.Label(sf, text='就绪')
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_stats = ttk.Label(sf, text='')
        self.lbl_stats.pack(side=tk.RIGHT)

    def _drop_target(self, widget):
        """简陋的拖拽支持 — 监听剪贴板也可"""
        pass

    # ═══════════════════════ Tab: 压缩 ═══════════════════════

    def _tab_compress(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' 压缩 Compress ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 质量
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='质量:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r1, from_=1, to=100, variable=self.c_quality,
                  command=lambda v: self._slider_label(v, self.ql)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ql = ttk.Label(r1, text='75%', width=5); self.ql.pack(side=tk.LEFT, padx=4)

        # 缩放
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text='缩放:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.c_resize,
                  command=lambda v: self._slider_label(v, self.rl)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.rl = ttk.Label(r2, text='100%', width=5); self.rl.pack(side=tk.LEFT, padx=4)

        # 输出
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r3, text='替换原文件', variable=self.c_replace, value=True,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r3, text='输出到:', variable=self.c_replace, value=False,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT, padx=10)
        self.c_outrow = ttk.Frame(r3)
        ttk.Entry(self.c_outrow, textvariable=self.c_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.c_outrow, text='浏览', command=lambda: self._browse_out(self.c_outfolder)).pack(side=tk.LEFT)

        # 备份 + 按钮
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r4, text='启用备份', variable=self.c_backup).pack(side=tk.LEFT)
        ttk.Button(r4, text='开始压缩', command=self._run_compress).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r4, text='备份管理 ▾', command=self._backup_mgr).pack(side=tk.RIGHT, padx=8)

    # ═══════════════════════ Tab: 格式转换 ═══════════════════════

    def _tab_convert(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' 格式转换 Format ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text='转为格式:', width=10).pack(side=tk.LEFT)
        self._fmt_btns(r1)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r2, text='替换原文件', variable=self.v_conv_replace, value=True,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r2, text='输出到:', variable=self.v_conv_replace, value=False,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT, padx=10)
        self.conv_outrow = ttk.Frame(r2)
        ttk.Entry(self.conv_outrow, textvariable=self.v_conv_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.conv_outrow, text='浏览', command=lambda: self._browse_out(self.v_conv_outfolder)).pack(side=tk.LEFT)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r3, text='启用备份', variable=self.v_conv_backup).pack(side=tk.LEFT)
        ttk.Button(r3, text='开始转换', command=self._run_convert).pack(side=tk.RIGHT, ipadx=8)

    def _fmt_btns(self, parent):
        for fmt in CONVERT_TARGETS:
            ttk.Radiobutton(parent, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=3)

    # ═══════════════════════ Tab: 重命名 ═══════════════════════

    def _tab_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' 批量重命名 Rename ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 模式选择
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text='模式:', width=8).pack(side=tk.LEFT)
        modes = [('添加前缀', 'prefix'), ('添加后缀', 'suffix'), ('查找替换', 'replace'),
                 ('序号模板', 'seq'), ('大小写转换', 'case')]
        for txt, val in modes:
            ttk.Radiobutton(r0, text=txt, variable=self.r_mode, value=val,
                            command=self._toggle_rename_ui).pack(side=tk.LEFT, padx=3)

        # 动态参数区
        self.r_frame = ttk.Frame(f)
        self.r_frame.pack(fill=tk.X, pady=4)

        # 前后缀
        self.r_prefix_row = ttk.Frame(f)
        ttk.Label(self.r_prefix_row, text='前缀:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_prefix_row, textvariable=self.r_prefix, width=20).pack(side=tk.LEFT, padx=4)

        self.r_suffix_row = ttk.Frame(f)
        ttk.Label(self.r_suffix_row, text='后缀:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_suffix_row, textvariable=self.r_suffix, width=20).pack(side=tk.LEFT, padx=4)

        # 查找替换
        self.r_replace_row = ttk.Frame(f)
        ttk.Label(self.r_replace_row, text='查找:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_src, width=18).pack(side=tk.LEFT)
        ttk.Label(self.r_replace_row, text='替换为:').pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_dst, width=18).pack(side=tk.LEFT)

        # 序号模板
        self.r_seq_row = ttk.Frame(f)
        ttk.Label(self.r_seq_row, text='模板:', width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_seq_row, textvariable=self.r_seq_template, width=20).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.r_seq_row, text='起始:').pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=99999, textvariable=self.r_seq_start, width=5, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text='位数:').pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=10, textvariable=self.r_seq_digits, width=3, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text='{num}=序号', foreground='#6c7086').pack(side=tk.LEFT, padx=4)

        # 大小写
        self.r_case_row = ttk.Frame(f)
        ttk.Checkbutton(self.r_case_row, text='全小写', variable=self.r_lowercase).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(self.r_case_row, text='全大写', variable=self.r_uppercase).pack(side=tk.LEFT, padx=4)

        # 预览 + 按钮
        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Button(r5, text='预览重命名', command=self._preview_rename).pack(side=tk.LEFT)
        ttk.Button(r5, text='执行重命名', command=self._run_rename).pack(side=tk.RIGHT, ipadx=8)

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

    # ═══════════════════════ Tab: 水印 ═══════════════════════

    def _tab_watermark(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' 水印 Watermark ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 类型
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text='水印类型:', width=10).pack(side=tk.LEFT)
        ttk.Radiobutton(r0, text='文字', variable=self.w_type, value='text',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(r0, text='图片', variable=self.w_type, value='image',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)

        # ── 文字水印参数 ──
        self.w_text_frame = ttk.Frame(f)
        self.w_text_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_text_frame, text='内容:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_text_frame, textvariable=self.w_text, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.w_text_frame, text='字号:').pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_text_frame, from_=8, to=200, textvariable=self.w_fontsize, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='颜色:').pack(side=tk.LEFT, padx=(8, 2))
        ttk.Entry(self.w_text_frame, textvariable=self.w_color, width=8).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='(#HEX)', foreground='#6c7086').pack(side=tk.LEFT, padx=2)

        # ── 图片水印参数 ──
        self.w_img_frame = ttk.Frame(f)
        self.w_img_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_img_frame, text='图片:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_img_frame, textvariable=self.w_image_path, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.w_img_frame, text='浏览',
                   command=lambda: self._browse_img(self.w_image_path)).pack(side=tk.LEFT)
        ttk.Label(self.w_img_frame, text='缩放%:').pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_img_frame, from_=5, to=100, textvariable=self.w_img_scale, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        # 通用参数
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text='透明度:', width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.w_opacity).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.w_op_lbl = ttk.Label(r2, text='50%', width=4); self.w_op_lbl.pack(side=tk.LEFT, padx=4)
        self.w_opacity.trace_add('write', lambda *a: self.w_op_lbl.config(
            text=f'{self.w_opacity.get()}%'))

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text='位置:', width=10).pack(side=tk.LEFT)
        positions = [('左上', 'top-left'), ('右上', 'top-right'), ('居中', 'center'),
                     ('左下', 'bottom-left'), ('右下', 'bottom-right')]
        for txt, val in positions:
            ttk.Radiobutton(r3, text=txt, variable=self.w_position,
                            value=val).pack(side=tk.LEFT, padx=3)

        # 输出
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r4, text='替换原文件', variable=self.w_replace, value=True,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text='输出到:', variable=self.w_replace, value=False,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT, padx=10)
        self.wm_outrow = ttk.Frame(r4)
        ttk.Entry(self.wm_outrow, textvariable=self.w_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.wm_outrow, text='浏览', command=lambda: self._browse_out(self.w_outfolder)).pack(side=tk.LEFT)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r5, text='启用备份', variable=self.w_backup).pack(side=tk.LEFT)
        ttk.Button(r5, text='批量加水印', command=self._run_watermark).pack(side=tk.RIGHT, ipadx=8)

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
        self.notebook.add(tab, text=' AI重命名 AI Rename ')

        f = ttk.Frame(tab)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # API Key
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='DeepSeek API Key:', width=14).pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.ai_api_key, width=50, show='*').pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(r1, text='显示/隐藏', command=lambda: self._toggle_key_show(r1)).pack(side=tk.LEFT)

        # Prompt
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text='提示词 Prompt:').pack(anchor=tk.W)
        self.ai_prompt_text = tk.Text(f, height=4, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                                       font=('Consolas', 9), borderwidth=1, relief=tk.SOLID)
        self.ai_prompt_text.pack(fill=tk.X, padx=0, pady=2)
        self.ai_prompt_text.insert('1.0', self.ai_prompt.get())

        # 按钮
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Button(r3, text='AI 分析文件名', command=self._ai_analyze).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(r3, text='应用 AI 重命名', command=self._ai_apply).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r3, text='清除结果', command=self._ai_clear).pack(side=tk.RIGHT, padx=8)

        # 结果预览
        ttk.Label(f, text='AI 建议预览:').pack(anchor=tk.W, pady=(6, 2))
        tree_fr = ttk.Frame(f)
        tree_fr.pack(fill=tk.BOTH, expand=True)
        self.ai_tree = ttk.Treeview(tree_fr, columns=('original', 'suggested'),
                                     show='headings', height=6)
        self.ai_tree.heading('original', text='原文件名')
        self.ai_tree.heading('suggested', text='AI 建议名')
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
        path = filedialog.askdirectory(title='选择图片文件夹')
        if path:
            self.folder.set(os.path.normpath(path))
            self._refresh()

    def _browse_out(self, var):
        path = filedialog.askdirectory(title='选择输出文件夹')
        if path:
            var.set(os.path.normpath(path))

    def _browse_img(self, var):
        path = filedialog.askopenfilename(title='选择水印图片',
                                          filetypes=[('图片', '*.png *.jpg *.jpeg *.webp *.bmp')])
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
        self.lbl_count.config(text=f'{len(self.file_data)} 个文件 · {self._fmt_size(total)}')

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
                messagebox.showerror('预览失败', str(e))

    def _backup_mgr(self):
        folder = self.folder.get()
        if not folder:
            return
        backups = self._find_backups(folder)
        if not backups:
            messagebox.showinfo('备份管理', '暂无备份记录')
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
        if not messagebox.askyesno('确认恢复', f'将用备份覆盖当前文件夹:\n{os.path.basename(backup_dir)}\n\n确认？'):
            return
        for f in os.listdir(backup_dir):
            src = os.path.join(backup_dir, f)
            dst = os.path.join(folder, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        self._refresh()
        messagebox.showinfo('恢复完成', '备份已恢复')

    def _do_clear_backups(self, backups):
        if not messagebox.askyesno('确认', f'将删除 {len(backups)} 个备份，不可撤销。确认？'):
            return
        for d in backups:
            shutil.rmtree(d)
        messagebox.showinfo('完成', f'已清除 {len(backups)} 个备份')

    # ═══════════════════════ 压缩执行 ═══════════════════════

    def _run_compress(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('提示', '请先选择文件夹并刷新')
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
        self._set_status('正在压缩...')
        self._set_progress(0)
        if do_backup:
            self._set_status('正在备份...')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'备份失败: {e}')
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)
        for i, fname in enumerate(file_list):
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
            self._set_status(f'压缩中 {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, '压缩')

    # ═══════════════════════ 格式转换执行 ═══════════════════════

    def _run_convert(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('提示', '请先选择文件夹并刷新')
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
        self._set_status('正在转换格式...')
        self._set_progress(0)
        if do_backup:
            self._set_status('正在备份...')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'备份失败: {e}')
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)
        for i, fname in enumerate(file_list):
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
                # Remove old file if format changed and replacing
                if replace and target_fmt != os.path.splitext(fname)[1].lower() and os.path.exists(src):
                    try:
                        os.remove(src)
                    except Exception:
                        pass
                self.root.after(0, lambda n=new_name, s=sa: self._update_row_rename(fname, n, s))
            except Exception as e:
                errors.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._set_status(f'转换中 {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, '转换', post_refresh=True)

    # ═══════════════════════ 重命名执行 ═══════════════════════

    def _preview_rename(self):
        mapping = self._gen_rename_map()
        if not mapping:
            messagebox.showwarning('提示', '无匹配文件')
            return
        msgs = []
        for old, new in list(mapping.items())[:20]:
            msgs.append(f'{old}\n  → {new}')
        if len(mapping) > 20:
            msgs.append(f'... 共 {len(mapping)} 个文件')
        messagebox.showinfo('重命名预览', '\n'.join(msgs))

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
            messagebox.showwarning('提示', '没有需要重命名的文件')
            return
        if not messagebox.askyesno('确认重命名', f'将重命名 {len(mapping)} 个文件，确认？'):
            return
        self.is_running = True
        threading.Thread(target=self._rename_thread, args=(folder, mapping), daemon=True).start()

    def _rename_thread(self, folder, mapping):
        self._set_status('正在重命名...')
        self._set_progress(0)
        total = len(mapping)
        errors = []
        for i, (old, new) in enumerate(mapping.items()):
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                errors.append(f'{old} → {new}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._set_status(f'重命名中 {i+1}/{total}')
        self._set_progress(100)
        if errors:
            self._set_status(f'完成，{len(errors)} 个错误')
            self.root.after(100, lambda: messagebox.showerror('错误', '\n'.join(errors[:10])))
        else:
            self._set_status('重命名完成')
            self.root.after(100, lambda: messagebox.showinfo('完成', f'{total} 个文件已重命名'))
        self.root.after(50, self._refresh)
        self.is_running = False

    # ═══════════════════════ 水印执行 ═══════════════════════

    def _run_watermark(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning('提示', '请先选择文件夹并刷新')
            return
        wtype = self.w_type.get()
        if wtype == 'image' and not self.w_image_path.get():
            messagebox.showwarning('提示', '请先选择水印图片')
            return
        if wtype == 'image' and not os.path.exists(self.w_image_path.get()):
            messagebox.showwarning('提示', '水印图片不存在')
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
        self._set_status('正在加水印...')
        self._set_progress(0)
        if do_backup:
            self._set_status('正在备份...')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'备份失败: {e}')
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        errors = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)

        # 预加载图片水印
        wm_img = None
        if params['type'] == 'image':
            wm_img = Image.open(params['image_path']).convert('RGBA')

        for i, fname in enumerate(file_list):
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
                # Convert back if original was not RGBA
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
            self._set_status(f'水印中 {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, errors, '水印')

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
            messagebox.showwarning('提示', '请先选择文件夹并刷新')
            return
        api_key = self.ai_api_key.get().strip()
        if not api_key:
            messagebox.showwarning('提示', '请输入 DeepSeek API Key')
            return
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        file_names = [d['name'] for d in self.file_data]
        prompt = self.ai_prompt_text.get('1.0', tk.END).strip()
        self._set_status('AI 分析中...')
        threading.Thread(target=self._ai_thread, args=(api_key, file_names, prompt), daemon=True).start()

    def _ai_thread(self, api_key, file_names, prompt):
        try:
            import urllib.request
            import urllib.error
            import ast
            req_body = json.dumps({
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': '你是一个文件命名助手，严格返回 JSON 数组（标准 JSON，使用双引号）。每个元素为 {"original": "原文件名", "new": "新文件名"}。'},
                    {'role': 'user', 'content': f'{prompt}\n\n文件名列表:\n' + '\n'.join(file_names)}
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

            # Robust parsing: try standard JSON, then Python literal, then fallback
            result_list = None
            # 1. Try standard JSON (double quotes)
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    result_list = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    pass
            # 2. Fallback: try Python literal eval (handles single quotes)
            if result_list is None:
                try:
                    result_list = ast.literal_eval(json_match.group() if json_match else content)
                except (ValueError, SyntaxError):
                    pass
            # 3. Ultimate fallback: split by lines
            if result_list is None:
                result_list = [line.strip() for line in content.splitlines() if line.strip()]
                if not result_list:
                    result_list = [content]

            # Ensure it's a list
            if not isinstance(result_list, list):
                result_list = [result_list]

            # Map results
            for item in result_list:
                if isinstance(item, dict):
                    orig = item.get('original', '')
                    new_name = item.get('new', item.get('new_name', item.get('suggested', '')))
                    if orig and orig in file_names:
                        self.ai_result[orig] = self._sanitize_filename(new_name) or orig
                elif isinstance(item, str) and len(self.ai_result) < len(file_names):
                    self.ai_result[file_names[len(self.ai_result)]] = self._sanitize_filename(item) or file_names[len(self.ai_result)]

            # Fill missing with original
            for fn in file_names:
                if fn not in self.ai_result:
                    self.ai_result[fn] = fn

            self.root.after(0, self._ai_populate)
            self._set_status(f'AI 分析完成，{len(self.ai_result)} 条建议')
        except Exception as e:
            self._set_status(f'AI 错误: {e}')
            self.root.after(0, lambda: messagebox.showerror('AI 错误', str(e)))

    def _sanitize_filename(self, name):
        """清理文件名中的非法字符"""
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
            messagebox.showwarning('提示', '请先运行 AI 分析')
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
            messagebox.showinfo('提示', '没有需要重命名的文件')
            return
        if not messagebox.askyesno('确认', f'将 AI 重命名 {len(mapping)} 个文件，确认？'):
            return
        errors = []
        for old, new in mapping.items():
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                errors.append(f'{old} → {new}: {e}')
        self._refresh()
        if errors:
            messagebox.showerror('错误', '\n'.join(errors[:10]))
        else:
            messagebox.showinfo('完成', f'{len(mapping)} 个文件已重命名')

    def _ai_clear(self):
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        self._set_status('已清除 AI 结果')

    # ═══════════════════════ 线程工具 ═══════════════════════

    def _set_status(self, msg):
        self.root.after(0, lambda: self.lbl_status.config(text=msg))

    def _set_progress(self, val):
        self.root.after(0, lambda: self.progress.config(value=val))

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
        self._set_status(f'{op_name}完成 — {msg}')
        self.is_running = False
        if post_refresh:
            self.root.after(100, self._refresh)
        if errors:
            self.root.after(200, lambda: messagebox.showwarning(
                f'{op_name}完成', f'{msg}\n\n{len(errors)} 个错误:\n' + '\n'.join(errors[:5])))

    # ═══════════════════════ 深色主题 ═══════════════════════

    def _apply_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=BG, foreground=FG, fieldbackground=ENTRY_BG)
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=FG)
        style.configure('TButton', background=BG2, foreground=FG, borderwidth=1, padding=5)
        style.map('TButton', background=[('active', '#45475a')])
        style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=FG)
        style.configure('TScale', background=BG, troughcolor=BG2)
        style.configure('TCheckbutton', background=BG, foreground=FG)
        style.configure('TRadiobutton', background=BG, foreground=FG)
        style.configure('TSeparator', background=BORDER)
        style.configure('TProgressbar', troughcolor=BG2, background=ACCENT, borderwidth=0)
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', background=BG2, foreground=FG, padding=(12, 4))
        style.map('TNotebook.Tab', background=[('selected', BG)], foreground=[('selected', ACCENT)])
        style.configure('Treeview', background=ENTRY_BG, foreground=FG, fieldbackground=ENTRY_BG)
        style.configure('Treeview.Heading', background=BG2, foreground=FG)
        style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', '#1e1e2e')])
        style.map('Treeview.Heading', background=[('active', '#45475a')])



class BackupDialog:
    def __init__(self, parent, backups, folder):
        self.result = None
        self.chosen = None
        self.top = tk.Toplevel(parent)
        self.top.title('备份管理')
        self.top.geometry('550x320')
        self.top.configure(bg=BG)
        self.top.transient(parent)
        self.top.grab_set()

        ttk.Label(self.top, text='备份记录:', font=('', 10, 'bold')).pack(pady=(10, 4))

        frame = ttk.Frame(self.top)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        self.lb = tk.Listbox(frame, bg=ENTRY_BG, fg=FG, selectbackground=ACCENT,
                             selectforeground='#1e1e2e', font=('Consolas', 10),
                             activestyle='none', borderwidth=0, highlightthickness=0)
        self.lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lb.configure(yscrollcommand=sb.set)
        for b in backups:
            self.lb.insert(tk.END, os.path.basename(b))
        self.lb.selection_set(0)

        btn = ttk.Frame(self.top)
        btn.pack(pady=(6, 10))
        ttk.Button(btn, text='恢复', command=lambda: self._done('restore')).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(btn, text='清除所有备份', command=lambda: self._done('clear')).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn, text='取消', command=self.top.destroy).pack(side=tk.LEFT, padx=8)

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
