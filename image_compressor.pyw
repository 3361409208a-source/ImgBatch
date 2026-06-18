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
import io
from datetime import datetime
from pathlib import Path

import ctypes
from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askdirectory
    import tkMessageBox as messagebox
    filedialog = type('obj', (object,), {'askdirectory': askdirectory})()

from PIL import Image, ImageDraw, ImageFont, ImageTk

SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico'}
QUALITY_FORMATS = {'.jpg', '.jpeg', '.webp'}
CONVERT_TARGETS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico']

# ── Windows Drag & Drop (WM_DROPFILES) ──
if os.name == 'nt':
    WM_DROPFILES = 0x0233
    GWL_WNDPROC = -4

    # LONG_PTR is missing on some Python/ctypes versions (e.g. 3.6)
    _LONG_PTR = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

    _DragAcceptFiles = ctypes.windll.shell32.DragAcceptFiles
    _DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    _DragAcceptFiles.restype = None

    _DragQueryFileW = ctypes.windll.shell32.DragQueryFileW
    _DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    _DragQueryFileW.restype = wintypes.UINT

    _DragFinish = ctypes.windll.shell32.DragFinish
    _DragFinish.argtypes = [wintypes.HANDLE]
    _DragFinish.restype = None

    _WNDPROC = ctypes.WINFUNCTYPE(
        wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )

    try:
        _SetWindowLongPtr = ctypes.windll.user32.SetWindowLongPtrW
    except AttributeError:
        _SetWindowLongPtr = ctypes.windll.user32.SetWindowLongW
    _SetWindowLongPtr.argtypes = [wintypes.HWND, wintypes.INT, ctypes.c_void_p]
    _SetWindowLongPtr.restype = ctypes.c_void_p

    _CallWindowProc = ctypes.windll.user32.CallWindowProcW
    _CallWindowProc.argtypes = [
        ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    ]
    _CallWindowProc.restype = wintypes.LPARAM

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

    TRANSLATIONS = {'zh': {'tab_compress': '压缩', 'tab_format': '格式转换', 'tab_rename': '重命名', 'tab_watermark': '水印', 'tab_airename': 'AI重命名', 'app_title': 'ImgBatch -- 图片批量处理工具', 'target_folder': '目标文件夹:', 'browse': '浏览...', 'refresh': '刷新', 'open_image': '打开图片', 'file_list': '文件列表（双击预览）', 'col_name': '文件名', 'col_size': '大小', 'col_dim': '尺寸', 'col_fmt': '格式', 'quality': '质量:', 'resize': '缩放:', 'replace_orig': '替换原文件', 'output_to': '输出到:', 'enable_backup': '启用备份', 'start_compress': '开始压缩', 'backup_mgr': '备份管理', 'to_format': '转为格式:', 'start_convert': '开始转换', 'mode': '模式:', 'prefix_mode': '添加前缀', 'suffix_mode': '添加后缀', 'replace_mode': '查找替换', 'seq_mode': '序号模板', 'case_mode': '大小写转换', 'prefix': '前缀:', 'suffix': '后缀:', 'find': '查找:', 'replace_to': '替换为:', 'template': '模板:', 'start': '起始:', 'digits': '位数:', 'num_seq': '{num}=序号', 'lowercase': '全小写', 'uppercase': '全大写', 'preview_rename': '预览重命名', 'run_rename': '执行重命名', 'wm_type': '水印类型:', 'text_type': '文字', 'image_type': '图片', 'content': '内容:', 'font_size': '字号:', 'color': '颜色:', 'scale_pct': '缩放%:', 'opacity': '透明度:', 'position': '位置:', 'top_left': '左上', 'top_right': '右上', 'center': '居中', 'bottom_left': '左下', 'bottom_right': '右下', 'batch_wm': '批量加水印', 'show_hide': '显示/隐藏', 'prompt': '提示词 Prompt:', 'ai_analyze': 'AI 分析文件名', 'apply_ai': '应用 AI 重命名', 'clear_results': '清除结果', 'ai_preview': 'AI 建议预览:', 'orig_name': '原文件名', 'ai_suggested': 'AI 建议名', 'ready': '就绪', 'error': '错误', 'notice': '提示', 'confirm': '确认', 'done': '完成', 'preview_failed': '预览失败', 'confirm_restore': '确认恢复', 'restore_done': '恢复完成', 'sel_img_folder': '选择图片文件夹', 'sel_out_folder': '选择输出文件夹', 'sel_wm_img': '选择水印图片', 'open_image_fd': 'Open Image', 'save_as': 'Save As', 'hidden_default': '默认隐藏', 'ai_loading_anim': '动画更新 AI 树中的加载提示', 'cleared_ai': '已清除 AI 结果', 'illegal_chars': '文件名中的非法字符', 'total': '共: ', 'save': '保存', 'saved': '节省', 'compress_preview': '预计大小', 'compress_preview_none': '预计大小: —', 'compress_ratio': '压缩比例', 'preview': '预览', 'no_preview': '选择图片预览', 'also_convert': '同时转换格式', 'also_rename': '同时重命名', 'also_watermark': '同时加水印', 'save_as_btn': '另存为...', 'all_files': '所有文件', 'drop_invalid': '拖入的文件不是支持的图片格式', 'mode_folder': '文件夹模式', 'mode_single': '单张模式', 'clear_single': '清除单张', 'target_image': '目标图片:'}, 'en': {'tab_compress': 'Compress', 'tab_format': 'Format', 'tab_rename': 'Rename', 'tab_watermark': 'Watermark', 'tab_airename': 'AI Rename', 'app_title': 'ImgBatch -- Batch Image Processor', 'target_folder': 'Target Folder:', 'browse': 'Browse...', 'refresh': 'Refresh', 'open_image': 'Open Image', 'file_list': 'File List (dbl-click preview)', 'col_name': 'Name', 'col_size': 'Size', 'col_dim': 'Dimensions', 'col_fmt': 'Format', 'quality': 'Quality:', 'resize': 'Resize:', 'replace_orig': 'Replace Original', 'output_to': 'Output to:', 'enable_backup': 'Enable Backup', 'start_compress': 'Start Compress', 'backup_mgr': 'Backup Manager', 'to_format': 'To Format:', 'start_convert': 'Start Convert', 'mode': 'Mode:', 'prefix_mode': 'Prefix', 'suffix_mode': 'Suffix', 'replace_mode': 'Replace', 'seq_mode': 'Sequence', 'case_mode': 'Case', 'prefix': 'Prefix:', 'suffix': 'Suffix:', 'find': 'Find:', 'replace_to': 'Replace:', 'template': 'Template:', 'start': 'Start:', 'digits': 'Digits:', 'num_seq': '{num}=number', 'lowercase': 'lowercase', 'uppercase': 'UPPERCASE', 'preview_rename': 'Preview Rename', 'run_rename': 'Run Rename', 'wm_type': 'Watermark Type:', 'text_type': 'Text', 'image_type': 'Image', 'content': 'Content:', 'font_size': 'Font Size:', 'color': 'Color:', 'scale_pct': 'Scale %:', 'opacity': 'Opacity:', 'position': 'Position:', 'top_left': 'Top L', 'top_right': 'Top R', 'center': 'Center', 'bottom_left': 'Bot L', 'bottom_right': 'Bot R', 'batch_wm': 'Batch Watermark', 'show_hide': 'Show/Hide', 'prompt': 'Prompt:', 'ai_analyze': 'AI Analyze', 'apply_ai': 'Apply AI Names', 'clear_results': 'Clear Results', 'ai_preview': 'AI Preview:', 'orig_name': 'Original', 'ai_suggested': 'AI Suggested', 'ready': 'Ready', 'error': 'Error', 'notice': 'Notice', 'confirm': 'Confirm', 'done': 'Done', 'preview_failed': 'Preview Failed', 'confirm_restore': 'Confirm Restore', 'restore_done': 'Restore Done', 'sel_img_folder': 'Select Image Folder', 'sel_out_folder': 'Select Output Folder', 'sel_wm_img': 'Select Watermark Image', 'open_image_fd': 'Open Image', 'save_as': 'Save As', 'hidden_default': 'Hidden by default', 'ai_loading_anim': 'AI loading animation', 'cleared_ai': 'Cleared AI results', 'illegal_chars': 'Illegal chars in filename', 'total': 'Total: ', 'save': 'Save', 'saved': 'saved', 'compress_preview': 'Estimated', 'compress_preview_none': 'Estimated: —', 'compress_ratio': 'Compress Ratio', 'preview': 'Preview', 'no_preview': 'Select image to preview', 'also_convert': 'Also Convert', 'also_rename': 'Also Rename', 'also_watermark': 'Also Watermark', 'save_as_btn': 'Save As...', 'all_files': 'All Files', 'drop_invalid': 'Dropped file is not a supported image', 'mode_folder': 'Folder Mode', 'mode_single': 'Single Mode', 'clear_single': 'Clear Single', 'target_image': 'Target Image:'}}

    def _t(self, key):
        return self.TRANSLATIONS.get(self.current_lang, {}).get(key, key)

    def _switch_lang(self, lang):
        self.current_lang = lang
        self.root.title(self._t('app_title'))
        # Update top labels
        self.folder_label.config(text=self._t('target_folder'))
        self.list_label.config(text=self._t('file_list'))
        self.lbl_status.config(text=self._t('ready'))
        # Destroy and rebuild notebook tabs
        tabs = list(self.notebook.tabs())
        for tab_id in tabs:
            self.notebook.forget(tab_id)
            tab_widget = self.notebook.nametowidget(tab_id)
            tab_widget.destroy()
        self._tab_compress()
        self._tab_convert()
        self._tab_rename()
        self._tab_watermark()
        self._tab_ai_rename()
        self.notebook.select(0)
        self._update_mode_ui()
        self._schedule_compress_preview()

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
        self.current_lang = 'zh'

        # ── 目标模式：folder / single ──
        self.target_mode = tk.StringVar(value='folder')
        self.single_path = tk.StringVar()

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
        self._preview_after_id = None

        # ── Compress / 统一处理 ──
        self.c_compress_ratio = tk.IntVar(value=75)  # 单一压缩比例
        self.c_quality = tk.IntVar(value=75)         # 自动映射：质量
        self.c_resize = tk.IntVar(value=75)          # 自动映射：缩放
        self._set_compress_from_ratio(75)
        self.c_replace = tk.BooleanVar(value=True)
        self.c_outfolder = tk.StringVar()
        self.c_backup = tk.BooleanVar(value=True)
        # 统一处理附加选项
        self.u_convert = tk.BooleanVar(value=False)
        self.u_watermark = tk.BooleanVar(value=False)
        self.u_rename = tk.BooleanVar(value=False)
        self.u_wm_text = tk.StringVar(value='')
        self.u_wm_opacity = tk.IntVar(value=50)
        self.u_prefix = tk.StringVar(value='')
        self.u_suffix = tk.StringVar(value='')

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
        self.w_text = tk.StringVar(value='水印')
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
        # ── 顶部：目标选择（文件夹 / 单张图） ──
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=(10, 0))
        self.folder_label = ttk.Label(top, text=self._t('target_folder'), font=('Tahoma', 10, 'bold'))
        self.folder_label.pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(top, textvariable=self.folder, width=55, font=('Tahoma', 10))
        self.folder_entry.pack(side=tk.LEFT, padx=(6, 6), fill=tk.X, expand=True)
        ttk.Button(top, text=self._t('browse'), command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top, text=self._t('refresh'), command=self._refresh).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(top, text=self._t('open_image'), command=self._open_single).pack(side=tk.LEFT, padx=(6, 0))
        # 模式指示 + 清除单张
        self.lbl_mode = ttk.Label(top, text=self._t('mode_folder'), font=('Tahoma', 9, 'bold'), foreground=ACCENT)
        self.lbl_mode.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_clear_single = ttk.Button(top, text=self._t('clear_single'), command=self._clear_single_mode)
        self.btn_clear_single.pack(side=tk.LEFT, padx=(4, 0))
        self.btn_clear_single.pack_forget()
        # Language switcher
        lang_fr = ttk.Frame(top)
        lang_fr.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(lang_fr, text='中文', width=4, command=lambda: self._switch_lang('zh')).pack(side=tk.LEFT)
        ttk.Button(lang_fr, text='EN', width=3, command=lambda: self._switch_lang('en')).pack(side=tk.LEFT, padx=(2, 0))
        self._drop_target(top)

        # ── 文件列表 ──
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=6)
        list_hdr = ttk.Frame(self.root)
        list_hdr.pack(fill=tk.X, padx=12)
        self.list_label = ttk.Label(list_hdr, text=self._t('file_list'), font=('Tahoma', 9, 'bold'))
        self.list_label.pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(list_hdr, text='')
        self.lbl_count.pack(side=tk.RIGHT)

        # ── 中间：文件列表 + 右侧预览 ──
        middle = ttk.Frame(self.root)
        middle.pack(fill=tk.BOTH, expand=True, padx=12)

        # 左侧文件列表
        tree_fr = ttk.Frame(middle)
        tree_fr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
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
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        # 右侧预览
        preview_fr = ttk.Frame(middle, width=240)
        preview_fr.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        preview_fr.pack_propagate(False)
        ttk.Label(preview_fr, text=self._t('preview'), font=('Tahoma', 9, 'bold')).pack(anchor=tk.W)
        self.preview_canvas = tk.Canvas(preview_fr, bg='#FFFFFF', relief=tk.SUNKEN,
                                         borderwidth=2, highlightthickness=0, width=220, height=220)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=4)
        self.preview_canvas.create_text(110, 110, text=self._t('no_preview'),
                                         fill='#888888', font=('Tahoma', 9), tags='placeholder')
        self.preview_info = ttk.Label(preview_fr, text='')
        self.preview_info.pack(anchor=tk.W)

        # ── 底部 Notebook（多标签） ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, padx=12, pady=(4, 0))

        self._tab_compress()
        self._tab_convert()
        self._tab_rename()
        self._tab_watermark()
        self._tab_ai_rename()
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

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

        self.lbl_status = ttk.Label(sf, text=self._t('ready'))
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_stats = ttk.Label(sf, text='')
        self.lbl_stats.pack(side=tk.RIGHT)

    def _drop_target(self, widget=None):
        """启用 Windows 原生文件拖入支持（主窗口全域接收单张/多张图片）"""
        if os.name != 'nt':
            return
        try:
            hwnd = self.root.winfo_id()
            self._wndproc_ref = _WNDPROC(self._wndproc)
            self._orig_wndproc = _SetWindowLongPtr(
                hwnd, GWL_WNDPROC, ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
            )
            _DragAcceptFiles(hwnd, True)
            self.root.bind('<Destroy>', self._restore_wndproc)
        except Exception as e:
            print('DragAcceptFiles init failed:', e)

    def _restore_wndproc(self, event=None):
        if os.name != 'nt' or not getattr(self, '_orig_wndproc', None):
            return
        try:
            hwnd = self.root.winfo_id()
            _SetWindowLongPtr(hwnd, GWL_WNDPROC, self._orig_wndproc)
            self._orig_wndproc = None
        except Exception:
            pass

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_DROPFILES:
            try:
                count = _DragQueryFileW(wparam, 0xFFFFFFFF, None, 0)
                files = []
                for i in range(count):
                    buf = ctypes.create_unicode_buffer(260)
                    _DragQueryFileW(wparam, i, buf, 260)
                    files.append(buf.value)
                _DragFinish(wparam)
                if files:
                    self.root.after(0, lambda f=files: self._handle_drop(f))
            except Exception as e:
                print('Drop processing error:', e)
            return 0
        return _CallWindowProc(self._orig_wndproc, hwnd, msg, wparam, lparam)

    def _handle_drop(self, files):
        """拖入文件后的统一处理：进入单张模式并加载第一张图片"""
        images = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXT]
        if not images:
            messagebox.showwarning(self._t('notice'), self._t('drop_invalid'))
            return
        self._enter_single_mode(images[0])

    def _enter_single_mode(self, path):
        """切换到单张目标模式"""
        path = os.path.normpath(path)
        self.single_path.set(path)
        self.target_mode.set('single')
        folder = os.path.dirname(path)
        if folder:
            self.folder.set(folder)
        self._update_mode_ui()
        self._refresh()
        # 可选：高亮文件列表中的唯一项
        if self.tree.get_children():
            self.tree.selection_set(self.tree.get_children()[0])

    def _clear_single_mode(self):
        """退出单张模式，回到文件夹模式"""
        self.target_mode.set('folder')
        self.single_path.set('')
        self._update_mode_ui()
        self._refresh()

    def _update_mode_ui(self):
        """根据当前目标模式更新顶部标签和按钮"""
        if self.target_mode.get() == 'single':
            self.lbl_mode.config(text=self._t('mode_single'))
            self.btn_clear_single.pack(side=tk.LEFT, padx=(4, 0))
        else:
            self.lbl_mode.config(text=self._t('mode_folder'))
            self.btn_clear_single.pack_forget()

    def _on_tab_changed(self, event=None):
        """切换标签页时，若回到压缩页则刷新实时预览"""
        if not self.notebook.tabs():
            return
        current_text = self.notebook.tab(self.notebook.select(), 'text')
        if current_text == ' ' + self._t('tab_compress') + ' ':
            self._schedule_compress_preview()

    def _toggle_u_convert(self):
        if self.u_convert.get():
            self.u_fmt_frame.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)
        else:
            self.u_fmt_frame.pack_forget()

    def _toggle_u_rename(self):
        if self.u_rename.get():
            self.u_rename_frame.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)
        else:
            self.u_rename_frame.pack_forget()

    def _toggle_u_watermark(self):
        if self.u_watermark.get():
            self.u_wm_frame.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)
        else:
            self.u_wm_frame.pack_forget()

    def _save_as_selected(self):
        """将当前选中的图片另存为"""
        sel = self.tree.selection()
        if not sel and self.file_data:
            # 默认选中第一个
            sel = (self.tree.get_children()[0],)
        if not sel:
            messagebox.showwarning(self._t('notice'), '请先选择文件')
            return
        fname = self.tree.item(sel[0], 'values')[0]
        src = os.path.join(self.folder.get(), fname)
        if not os.path.exists(src):
            return
        ext = os.path.splitext(fname)[1]
        path = filedialog.asksaveasfilename(
            title=self._t('save_as'),
            defaultextension=ext,
            filetypes=[(self._t('all_files'), '*.*'), ('PNG', '*.png'), ('JPEG', '*.jpg'), ('WebP', '*.webp'),
                       ('BMP', '*.bmp'), ('TIFF', '*.tiff')])
        if not path:
            return
        try:
            shutil.copy2(src, path)
            messagebox.showinfo(self._t('done'), f'{self._t("saved")}:\n{path}')
        except Exception as e:
            messagebox.showerror(self._t('error'), str(e))

    def _on_compress_ratio_change(self, val):
        """压缩比例滑块变化时，自动映射为质量与缩放，并刷新预览"""
        ratio = int(float(val))
        self.crl.config(text=f'{ratio}%')
        self._set_compress_from_ratio(ratio)
        self._schedule_compress_preview()

    def _set_compress_from_ratio(self, ratio):
        """将单一压缩比例映射为内部质量与缩放参数"""
        ratio = max(1, min(100, int(ratio)))
        self.c_quality.set(ratio)
        # 缩放随比例线性变化，最低 10%
        self.c_resize.set(max(10, int(10 + (ratio - 1) * 90 / 99)))

    def _schedule_compress_preview(self, event=None):
        """延迟更新压缩预览，避免滑块拖动时频繁计算"""
        if self._preview_after_id:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(150, self._update_compress_preview)

    def _update_compress_preview(self):
        """根据当前质量和缩放参数，实时估算压缩后总大小"""
        if not getattr(self, 'c_preview_lbl', None):
            return
        if not self.file_data:
            self.c_preview_lbl.config(text=self._t('compress_preview_none'))
            return
        quality = int(float(self.c_quality.get()))
        resize_pct = int(float(self.c_resize.get()))
        total_before = sum(d['size'] for d in self.file_data)
        sample = self.file_data[0]
        ext = os.path.splitext(sample['path'])[1].lower()
        try:
            with Image.open(sample['path']) as img:
                om = img.mode
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
                buf = io.BytesIO()
                kw = {'optimize': True}
                if ext in QUALITY_FORMATS:
                    kw['quality'] = quality
                # 对于不支持质量的格式，用原格式保存；否则按扩展名保存
                save_fmt = None
                if ext in ('.jpg', '.jpeg'):
                    save_fmt = 'JPEG'
                elif ext == '.png':
                    save_fmt = 'PNG'
                elif ext == '.webp':
                    save_fmt = 'WEBP'
                elif ext == '.bmp':
                    save_fmt = 'BMP'
                elif ext in ('.tiff', '.tif'):
                    save_fmt = 'TIFF'
                elif ext == '.gif':
                    save_fmt = 'GIF'
                elif ext == '.ico':
                    save_fmt = 'ICO'
                if save_fmt:
                    img.save(buf, format=save_fmt, **kw)
                else:
                    img.save(buf, **kw)
                sample_after = buf.tell()
                ratio = sample_after / sample['size'] if sample['size'] else 0
                total_after = max(int(total_before * ratio), 0)
        except Exception as e:
            self.c_preview_lbl.config(text=self._t('compress_preview_none'))
            return
        saved = total_before - total_after
        ratio_pct = (saved / total_before * 100) if total_before else 0
        self.c_preview_lbl.config(
            text=(f'{self._t("compress_preview")}: {self._fmt_size(total_before)} → {self._fmt_size(total_after)} '
                  f'({self._t("saved")} {self._fmt_size(saved)}, {ratio_pct:.1f}%)')
        )

    # ═══════════════════════ Tab: Compress ═══════════════════════

    def _tab_compress(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + self._t('tab_compress') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 压缩比例（单一滑块，自动映射为质量+缩放）
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text=self._t('compress_ratio'), width=10).pack(side=tk.LEFT)
        self.scale_compress = ttk.Scale(r1, from_=1, to=100, variable=self.c_compress_ratio,
                  command=lambda v: self._on_compress_ratio_change(v))
        self.scale_compress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.crl = ttk.Label(r1, text='75%', width=5); self.crl.pack(side=tk.LEFT, padx=4)

        # 实时大小对比预览
        r_preview = ttk.Frame(f); r_preview.pack(fill=tk.X, pady=4)
        self.c_preview_lbl = ttk.Label(r_preview, text=self._t('compress_preview_none'),
                                       font=('Tahoma', 9, 'bold'), foreground=ACCENT2)
        self.c_preview_lbl.pack(side=tk.LEFT)

        # ── 同步格式转换 ──
        r_fmt = ttk.Frame(f); r_fmt.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_fmt, text=self._t('also_convert'), variable=self.u_convert,
                        command=self._toggle_u_convert).pack(side=tk.LEFT)
        self.u_fmt_frame = ttk.Frame(r_fmt)
        for fmt in ['.jpg', '.png', '.webp', '.bmp', '.tiff']:
            ttk.Radiobutton(self.u_fmt_frame, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=2)

        # ── 同步重命名 ──
        r_rename = ttk.Frame(f); r_rename.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_rename, text=self._t('also_rename'), variable=self.u_rename,
                        command=self._toggle_u_rename).pack(side=tk.LEFT)
        self.u_rename_frame = ttk.Frame(r_rename)
        ttk.Label(self.u_rename_frame, text=self._t('prefix')).pack(side=tk.LEFT)
        ttk.Entry(self.u_rename_frame, textvariable=self.u_prefix, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.u_rename_frame, text=self._t('suffix')).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Entry(self.u_rename_frame, textvariable=self.u_suffix, width=12).pack(side=tk.LEFT, padx=2)

        # ── 同步水印 ──
        r_wm = ttk.Frame(f); r_wm.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_wm, text=self._t('also_watermark'), variable=self.u_watermark,
                        command=self._toggle_u_watermark).pack(side=tk.LEFT)
        self.u_wm_frame = ttk.Frame(r_wm)
        ttk.Label(self.u_wm_frame, text=self._t('content')).pack(side=tk.LEFT)
        ttk.Entry(self.u_wm_frame, textvariable=self.u_wm_text, width=18).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.u_wm_frame, text=self._t('opacity')).pack(side=tk.LEFT, padx=(6, 0))
        tk.Spinbox(self.u_wm_frame, from_=10, to=100, textvariable=self.u_wm_opacity,
                   width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        # Output mode
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r3, text=self._t('replace_orig'), variable=self.c_replace, value=True,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r3, text=self._t('output_to'), variable=self.c_replace, value=False,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT, padx=10)
        self.c_outrow = ttk.Frame(r3)
        ttk.Entry(self.c_outrow, textvariable=self.c_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.c_outrow, text='Browse', command=lambda: self._browse_out(self.c_outfolder)).pack(side=tk.LEFT)

        # Backup
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(r4, text=self._t('enable_backup'), variable=self.c_backup).pack(side=tk.LEFT)
        ttk.Button(r4, text=self._t('backup_mgr'), command=self._backup_mgr).pack(side=tk.RIGHT, padx=8)

        # Action Buttons
        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=4)
        ttk.Button(r5, text=self._t('start_compress'), command=self._run_compress).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r5, text=self._t('save_as_btn'), command=self._save_as_selected).pack(side=tk.RIGHT, ipadx=8, padx=8)

        # 初始状态
        self._toggle_u_convert()
        self._toggle_u_rename()
        self._toggle_u_watermark()

    # ═══════════════════════ Tab: FormatConvert ═══════════════════════

    def _tab_convert(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + self._t('tab_format') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text=self._t('to_format'), width=10).pack(side=tk.LEFT)
        self._fmt_btns(r1)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r2, text=self._t('replace_orig'), variable=self.v_conv_replace, value=True,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r2, text=self._t('output_to'), variable=self.v_conv_replace, value=False,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT, padx=10)
        self.conv_outrow = ttk.Frame(r2)
        ttk.Entry(self.conv_outrow, textvariable=self.v_conv_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.conv_outrow, text='Browse', command=lambda: self._browse_out(self.v_conv_outfolder)).pack(side=tk.LEFT)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r3, text=self._t('enable_backup'), variable=self.v_conv_backup).pack(side=tk.LEFT)
        ttk.Button(r3, text=self._t('start_convert'), command=self._run_convert).pack(side=tk.RIGHT, ipadx=8)

    def _fmt_btns(self, parent):
        for fmt in CONVERT_TARGETS:
            ttk.Radiobutton(parent, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=3)

    # ═══════════════════════ Tab: 重命名 ═══════════════════════

    def _tab_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + self._t('tab_rename') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 模式选择
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text=self._t('mode'), width=8).pack(side=tk.LEFT)
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
        ttk.Label(self.r_prefix_row, text=self._t('prefix'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_prefix_row, textvariable=self.r_prefix, width=20).pack(side=tk.LEFT, padx=4)

        self.r_suffix_row = ttk.Frame(f)
        ttk.Label(self.r_suffix_row, text=self._t('suffix'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_suffix_row, textvariable=self.r_suffix, width=20).pack(side=tk.LEFT, padx=4)

        # Replace
        self.r_replace_row = ttk.Frame(f)
        ttk.Label(self.r_replace_row, text=self._t('find'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_src, width=18).pack(side=tk.LEFT)
        ttk.Label(self.r_replace_row, text=self._t('replace_to')).pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_dst, width=18).pack(side=tk.LEFT)

        # Sequence
        self.r_seq_row = ttk.Frame(f)
        ttk.Label(self.r_seq_row, text=self._t('template'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_seq_row, textvariable=self.r_seq_template, width=20).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.r_seq_row, text=self._t('start')).pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=99999, textvariable=self.r_seq_start, width=5, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text=self._t('digits')).pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=10, textvariable=self.r_seq_digits, width=3, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text=self._t('num_seq'), foreground='#6c7086').pack(side=tk.LEFT, padx=4)

        # Size写
        self.r_case_row = ttk.Frame(f)
        ttk.Checkbutton(self.r_case_row, text=self._t('lowercase'), variable=self.r_lowercase).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(self.r_case_row, text=self._t('uppercase'), variable=self.r_uppercase).pack(side=tk.LEFT, padx=4)

        # 预览 + 按钮
        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Button(r5, text=self._t('preview_rename'), command=self._preview_rename).pack(side=tk.LEFT)
        ttk.Button(r5, text=self._t('run_rename'), command=self._run_rename).pack(side=tk.RIGHT, ipadx=8)

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
        self.notebook.add(tab, text=' ' + self._t('tab_watermark') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        # 类型
        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text=self._t('wm_type'), width=10).pack(side=tk.LEFT)
        ttk.Radiobutton(r0, text=self._t('text_type'), variable=self.w_type, value='text',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(r0, text=self._t('image_type'), variable=self.w_type, value='image',
                        command=lambda: self._toggle_wm_ui()).pack(side=tk.LEFT, padx=4)

        # ── TextWatermark参数 ──
        self.w_text_frame = ttk.Frame(f)
        self.w_text_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_text_frame, text=self._t('content'), width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_text_frame, textvariable=self.w_text, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.w_text_frame, text=self._t('font_size')).pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_text_frame, from_=8, to=200, textvariable=self.w_fontsize, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text=self._t('color')).pack(side=tk.LEFT, padx=(8, 2))
        ttk.Entry(self.w_text_frame, textvariable=self.w_color, width=8).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='(#HEX)', foreground='#6c7086').pack(side=tk.LEFT, padx=2)

        # ── ImageWatermark参数 ──
        self.w_img_frame = ttk.Frame(f)
        self.w_img_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_img_frame, text='Image:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_img_frame, textvariable=self.w_image_path, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.w_img_frame, text='Browse',
                   command=lambda: self._browse_img(self.w_image_path)).pack(side=tk.LEFT)
        ttk.Label(self.w_img_frame, text=self._t('scale_pct')).pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_img_frame, from_=5, to=100, textvariable=self.w_img_scale, width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        # 通用参数
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text=self._t('opacity'), width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.w_opacity).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.w_op_lbl = ttk.Label(r2, text='50%', width=4); self.w_op_lbl.pack(side=tk.LEFT, padx=4)
        self.w_opacity.trace_add('write', lambda *a: self.w_op_lbl.config(
            text=f'{self.w_opacity.get()}%'))

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text=self._t('position'), width=10).pack(side=tk.LEFT)
        positions = [('左上', 'top-left'), ('右上', 'top-right'), ('居中', 'center'),
                     ('左下', 'bottom-left'), ('右下', 'bottom-right')]
        for txt, val in positions:
            ttk.Radiobutton(r3, text=txt, variable=self.w_position,
                            value=val).pack(side=tk.LEFT, padx=3)

        # 输出
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r4, text=self._t('replace_orig'), variable=self.w_replace, value=True,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text=self._t('output_to'), variable=self.w_replace, value=False,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT, padx=10)
        self.wm_outrow = ttk.Frame(r4)
        ttk.Entry(self.wm_outrow, textvariable=self.w_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.wm_outrow, text='Browse', command=lambda: self._browse_out(self.w_outfolder)).pack(side=tk.LEFT)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r5, text=self._t('enable_backup'), variable=self.w_backup).pack(side=tk.LEFT)
        ttk.Button(r5, text='水印', command=self._run_watermark).pack(side=tk.RIGHT, ipadx=8)

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
        self.notebook.add(tab, text=' ' + self._t('tab_airename') + ' ')

        f = ttk.Frame(tab)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # API Key
        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='DeepSeek API Key:', width=14).pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.ai_api_key, width=50, show='*').pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(r1, text=self._t('show_hide'), command=lambda: self._toggle_key_show(r1)).pack(side=tk.LEFT)

        # Prompt
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text='Prompt Prompt:').pack(anchor=tk.W)
        self.ai_prompt_text = tk.Text(f, height=4, bg='#FFFFFF', fg=FG, insertbackground=FG,
                                       font=('Lucida Console', 9), relief=tk.SUNKEN, borderwidth=2)
        self.ai_prompt_text.pack(fill=tk.X, padx=0, pady=2)
        self.ai_prompt_text.insert('1.0', self.ai_prompt.get())

        # 按钮
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Button(r3, text=self._t('ai_analyze'), command=self._ai_analyze).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(r3, text=self._t('apply_ai'), command=self._ai_apply).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r3, text=self._t('clear_results'), command=self._ai_clear).pack(side=tk.RIGHT, padx=8)

        # 结果预览
        ttk.Label(f, text=self._t('ai_preview')).pack(anchor=tk.W, pady=(6, 2))
        tree_fr = ttk.Frame(f)
        tree_fr.pack(fill=tk.BOTH, expand=True)
        self.ai_tree = ttk.Treeview(tree_fr, columns=('original', 'suggested'),
                                     show='headings', height=6)
        self.ai_tree.heading('original', text=self._t('orig_name'))
        self.ai_tree.heading('suggested', text=self._t('ai_suggested'))
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

    def _open_single(self):
        path = filedialog.askopenfilename(
            title=self._t('open_image_fd'),
            filetypes=[('Images', '*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.gif *.ico')])
        if not path:
            return
        self._enter_single_mode(path)


    # ═══════════════════════ 通用工具方法 ═══════════════════════

    def _browse(self):
        path = filedialog.askdirectory(title=self._t('sel_img_folder'))
        if path:
            self.target_mode.set('folder')
            self.single_path.set('')
            self.folder.set(os.path.normpath(path))
            self._update_mode_ui()
            self._refresh()

    def _browse_out(self, var):
        path = filedialog.askdirectory(title=self._t('sel_out_folder'))
        if path:
            var.set(os.path.normpath(path))

    def _browse_img(self, var):
        path = filedialog.askopenfilename(title=self._t('sel_wm_img'),
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
        # 单张模式：只加载当前单张图
        if self.target_mode.get() == 'single':
            path = self.single_path.get()
            if not path or not os.path.isfile(path):
                self.lbl_count.config(text='')
                return
            f = os.path.basename(path)
            ext = os.path.splitext(f)[1].lower()
            if ext not in SUPPORTED_EXT:
                self.lbl_count.config(text='')
                return
            try:
                sz = os.path.getsize(path)
            except OSError:
                self.lbl_count.config(text='')
                return
            try:
                with Image.open(path) as img:
                    dims = f'{img.width}x{img.height}'
                    fmt = img.format or ext
            except Exception:
                dims = '?'
                fmt = ext
            d = {'name': f, 'path': path, 'size': sz, 'size_str': self._fmt_size(sz),
                 'dimensions': dims, 'format': fmt}
            self.file_data.append(d)
            item = self.tree.insert('', tk.END, values=(f, self._fmt_size(sz), dims, fmt))
            self.tree_items[f] = item
            self.lbl_count.config(text=f'1 file | {self._fmt_size(sz)}')
            self._schedule_compress_preview()
            return
        # 文件夹模式：扫描整个目录
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
        self._schedule_compress_preview()

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
                messagebox.showerror(self._t('preview_failed'), str(e))

    def _on_tree_select(self, event=None):
        """文件列表选中变化时，更新右侧预览"""
        sel = self.tree.selection()
        if not sel:
            self._clear_preview()
            return
        fname = self.tree.item(sel[0], 'values')[0]
        path = os.path.join(self.folder.get(), fname)
        self._update_preview_panel(path)

    def _update_preview_panel(self, path):
        """在右侧预览面板显示指定图片"""
        if not path or not os.path.exists(path):
            self._clear_preview()
            return
        try:
            img = Image.open(path)
            # 生成适合预览区的缩略图（窗口未显示时使用请求尺寸）
            cw = self.preview_canvas.winfo_width()
            ch = self.preview_canvas.winfo_height()
            if cw <= 1:
                cw = self.preview_canvas.winfo_reqwidth() or 220
            if ch <= 1:
                ch = self.preview_canvas.winfo_reqheight() or 220
            scale = min(cw / img.width, ch / img.height, 1.0)
            nw, nh = int(img.width * scale), int(img.height * scale)
            if nw < 1 or nh < 1:
                self._clear_preview()
                return
            thumb = img.copy()
            thumb.thumbnail((nw, nh), Image.LANCZOS)
            self.preview_tk_img = ImageTk.PhotoImage(thumb)
            self.preview_canvas.delete('all')
            x = max((cw - self.preview_tk_img.width()) // 2, 0)
            y = max((ch - self.preview_tk_img.height()) // 2, 0)
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_tk_img)
            info = f'{img.width}x{img.height} | {img.format or "?"}'
            self.preview_info.config(text=info)
        except Exception:
            self._clear_preview()

    def _clear_preview(self):
        """清空右侧预览"""
        self.preview_canvas.delete('all')
        self.preview_canvas.create_text(110, 110, text=self._t('no_preview'),
                                         fill='#888888', font=('Tahoma', 9), tags='placeholder')
        self.preview_info.config(text='')

    def _backup_mgr(self):
        folder = self.folder.get()
        if not folder:
            return
        backups = self._find_backups(folder)
        if not backups:
            messagebox.showinfo(self._t('backup_mgr'), '暂无备份记录')
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
        if not messagebox.askyesno(self._t('confirm_restore'), f'This will overwrite current folder from backup:\n{os.path.basename(backup_dir)}\n\nConfirm？'):
            return
        for f in os.listdir(backup_dir):
            src = os.path.join(backup_dir, f)
            dst = os.path.join(folder, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        self._refresh()
        messagebox.showinfo(self._t('restore_done'), '备份已恢复')

    def _do_clear_backups(self, backups):
        if not messagebox.askyesno(self._t('confirm'), f'将删除 {len(backups)}  个备份，不可撤销。Confirm？'):
            return
        for d in backups:
            shutil.rmtree(d)
        messagebox.showinfo(self._t('done'), f'Cleared {len(backups)}  个备份')

    # ═══════════════════════ Compress执行 ═══════════════════════

    def _run_compress(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(self._t('notice'), '请先选择文件夹并刷新')
            return
        self.is_running = True
        file_list = [d['name'] for d in self.file_data]
        quality = int(float(self.c_quality.get()))
        resize_pct = int(float(self.c_resize.get()))
        do_backup = self.c_backup.get()
        replace = self.c_replace.get()
        out = self.c_outfolder.get() if not replace else None
        options = {
            'convert': self.u_convert.get(),
            'target_fmt': self.v_target_fmt.get(),
            'rename': self.u_rename.get(),
            'prefix': self.u_prefix.get(),
            'suffix': self.u_suffix.get(),
            'watermark': self.u_watermark.get(),
            'wm_text': self.u_wm_text.get(),
            'wm_opacity': self.u_wm_opacity.get() / 100,
        }
        threading.Thread(target=self._unified_thread,
                         args=(folder, file_list, quality, resize_pct, do_backup, replace, out, options),
                         daemon=True).start()

    def _compress_thread(self, folder, file_list, quality, resize_pct, do_backup, replace, out):
        self._animate_status('正在压缩')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('正在备份')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        个错误 = []
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
                个错误.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Compressing {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, 个错误, '压缩')

    def _unified_thread(self, folder, file_list, quality, resize_pct, do_backup, replace, out, options):
        """统一处理线程：压缩 + 可选格式转换/水印/重命名"""
        self._animate_status('正在处理')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('正在备份')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        个错误 = []
        total = len(file_list)
        if not replace:
            os.makedirs(out, exist_ok=True)
        rename_map = {}

        for i, fname in enumerate(file_list):
            if fname in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[fname]: self._highlight_item(t))
            src = os.path.join(folder, fname)
            sb = os.path.getsize(src)
            total_before += sb
            base, orig_ext = os.path.splitext(fname)
            orig_ext_l = orig_ext.lower()
            target_ext = options['target_fmt'] if options['convert'] else orig_ext
            target_ext_l = target_ext.lower()
            out_name = base + target_ext
            dst = os.path.join(folder if replace else out, out_name)
            try:
                with Image.open(src) as img:
                    om = img.mode
                    if om in ('RGBA', 'P', 'LA') and target_ext_l in ('.jpg', '.jpeg'):
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
                    if options['watermark'] and options['wm_text']:
                        img = self._add_text_watermark_to_img(img, options['wm_text'], options['wm_opacity'])
                    kw = {'optimize': True}
                    if target_ext_l in QUALITY_FORMATS:
                        kw['quality'] = quality
                    img.save(dst, **kw)
                if replace and target_ext_l != orig_ext_l and os.path.exists(src):
                    try:
                        os.remove(src)
                    except Exception:
                        pass
                sa = os.path.getsize(dst)
                total_after += sa
                self.root.after(0, lambda n=fname, s=sa: self._update_row_size(n, s))
                if options['rename']:
                    new_name = options['prefix'] + base + options['suffix'] + target_ext
                    if new_name != out_name:
                        rename_map[out_name] = new_name
            except Exception as e:
                个错误.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Processing {i+1}/{total}')
            time.sleep(0.005)

        # 统一应用重命名
        for old_name, new_name in rename_map.items():
            try:
                old_path = os.path.join(folder if replace else out, old_name)
                new_path = os.path.join(folder if replace else out, new_name)
                os.rename(old_path, new_path)
            except Exception as e:
                个错误.append(f'{old_name} → {new_name}: {e}')

        self._finish_op(total_before, total_after, 个错误, '处理', post_refresh=True)

    def _add_text_watermark_to_img(self, img, text, opacity):
        """给图片添加右下角文字水印，返回 RGB 图像"""
        img = img.convert('RGBA')
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        fontsize = max(12, int(min(img.size) * 0.04))
        try:
            font = ImageFont.truetype('simhei.ttf', fontsize)
        except Exception:
            try:
                font = ImageFont.truetype('arial.ttf', fontsize)
            except Exception:
                font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = max(img.width - tw - 20, 0)
        y = max(img.height - th - 20, 0)
        alpha = int(max(0, min(1, opacity)) * 255)
        draw.text((x, y), text, fill=(255, 255, 255, alpha), font=font)
        result = Image.alpha_composite(img, layer)
        return result.convert('RGB')

    # ═══════════════════════ FormatConvert执行 ═══════════════════════

    def _run_convert(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(self._t('notice'), '请先选择文件夹并刷新')
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
            self._animate_status('正在备份')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        个错误 = []
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
                个错误.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Converting {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, 个错误, '转换', post_refresh=True)

    # ═══════════════════════ 重命名执行 ═══════════════════════

    def _preview_rename(self):
        mapping = self._gen_rename_map()
        if not mapping:
            messagebox.showwarning(self._t('notice'), '无匹配文件')
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
            messagebox.showwarning(self._t('notice'), '没有需要重命名的文件')
            return
        if not messagebox.askyesno('Confirm Rename', f'Will rename {len(mapping)} 个文件，Confirm？'):
            return
        self.is_running = True
        threading.Thread(target=self._rename_thread, args=(folder, mapping), daemon=True).start()

    def _rename_thread(self, folder, mapping):
        self._animate_status('正在重命名')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        total = len(mapping)
        个错误 = []
        for i, (old, new) in enumerate(mapping.items()):
            if old in self.tree_items:
                self.root.after(0, lambda t=self.tree_items[old]: self._highlight_item(t))
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                个错误.append(f'{old} → {new}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Renaming {i+1}/{total}')
        self._set_progress(100)
        self.root.after(0, self._stop_spinner)
        self.root.after(0, self._clear_highlight)
        if 个错误:
            self._set_status(f'Done，{len(个错误)}  个错误')
            self.root.after(100, lambda errs=个错误[:]: messagebox.showerror(self._t('error'), '\n'.join(errs[:10])))
        else:
            self._set_status('Rename Done')
            self.root.after(100, lambda: messagebox.showinfo(self._t('done'), f'{total}  个文件已重命名'))
        self.root.after(50, self._refresh)
        self.is_running = False

    # ═══════════════════════ Watermark执行 ═══════════════════════

    def _run_watermark(self):
        if self.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(self._t('notice'), '请先选择文件夹并刷新')
            return
        wtype = self.w_type.get()
        if wtype == 'image' and not self.w_image_path.get():
            messagebox.showwarning(self._t('notice'), 'Please select watermark image')
            return
        if wtype == 'image' and not os.path.exists(self.w_image_path.get()):
            messagebox.showwarning(self._t('notice'), 'Watermark image not found')
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
        self._animate_status('正在加水印')
        self.root.after(0, self._start_spinner)
        self._set_progress(0)
        if do_backup:
            self._animate_status('正在备份')
            try:
                self._do_backup(folder, file_list)
            except Exception as e:
                self._set_status(f'Backup failed: {e}')
                self.root.after(0, self._stop_spinner)
                self.is_running = False
                return
        total_before = 0
        total_after = 0
        个错误 = []
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
                个错误.append(f'{fname}: {e}')
            self._set_progress((i + 1) / total * 100)
            self._animate_status(f'Watermarking {i+1}/{total}')
            time.sleep(0.005)
        self._finish_op(total_before, total_after, 个错误, '水印')

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
            messagebox.showwarning(self._t('notice'), '请先选择文件夹并刷新')
            return
        api_key = self.ai_api_key.get().strip()
        if not api_key:
            messagebox.showwarning(self._t('notice'), '请输入 DeepSeek API Key')
            return
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        # Show loading placeholder in AI tree
        self.ai_tree.insert('', tk.END, values=('Connecting to DeepSeek...', '⏳ Waiting...'))
        file_names = [d['name'] for d in self.file_data]
        prompt = self.ai_prompt_text.get('1.0', tk.END).strip()
        self._animate_status('AI 分析中')
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
            self._set_status(f'AI done: {len(self.ai_result)}  条建议')
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
            messagebox.showwarning(self._t('notice'), '请先运行 AI 分析')
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
            messagebox.showinfo(self._t('notice'), '没有需要重命名的文件')
            return
        if not messagebox.askyesno(self._t('confirm'), f'AI rename {len(mapping)} 个文件，Confirm？'):
            return
        个错误 = []
        for old, new in mapping.items():
            try:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
            except Exception as e:
                个错误.append(f'{old} → {new}: {e}')
        self._refresh()
        if 个错误:
            messagebox.showerror(self._t('error'), '\n'.join(个错误[:10]))
        else:
            messagebox.showinfo(self._t('done'), f'{len(mapping)}  个文件已重命名')

    def _ai_clear(self):
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        self._set_status('已清除 AI 结果')

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

    def _finish_op(self, total_before, total_after, 个错误, op_name, post_refresh=False):
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
        if 个错误:
            self.root.after(200, lambda errs=个错误[:]: messagebox.showwarning(
                f'{op_name}Done', f'{msg}\n\n{len(errs)}  个错误:\n' + '\n'.join(errs[:5])))

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
        self.top.title('备份管理')
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
