#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main ImgBatch application window.

Integrates all tabs, file list, preview panel, drag-and-drop,
threading, settings, and operation history.
"""


import ctypes
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Dict, List, Optional

from PIL import Image, ImageTk, UnidentifiedImageError

from ..core.common import (
    SUPPORTED_EXT, QUALITY_FORMATS, CONVERT_TARGETS, FILTER_FORMATS, SIZE_PRESETS,
    scan_folder, fmt_size, convert_to_rgb_if_needed, get_save_format,
    filter_files, parse_kb_to_bytes,
)
from ..core.compress import compress_image, estimate_compressed_size, run_compress_batch
from ..core.convert import run_convert_batch
from ..core.rename import (
    generate_rename_map, run_rename_batch, ConflictResolution, RenameMode, sanitize_filename,
)
from ..core.watermark import run_watermark_batch
from ..core.trim import run_trim_batch
from ..core.normalize import run_normalize_batch
from ..core.inspect import run_inspect_batch
from ..core.spritesheet import run_spritesheet_build, LAYOUTS
from ..core.ai_rename import run_ai_rename, apply_ai_rename, DEFAULT_PROMPT
from ..history import HistoryManager, OperationRecord, undo_operation
from ..infra.logger import get_logger, log_operation
from ..infra.settings import load_config, save_config
from ..infra.i18n import get_i18n, tr, TRANSLATIONS
from ..infra.threading import TaskRunner, ProgressTracker
from .theme import apply_theme, BG, BG2, BG3, FG, ACCENT, ACCENT2, BORDER, ENTRY_BG
from .widgets.backup_mgr import find_backups, do_backup as create_backup, do_restore, do_clear_backups

# Windows Drag & Drop
if os.name == 'nt':
    WM_DROPFILES = 0x0233
    GWL_WNDPROC = -4
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


class ImgBatchApp:
    """Main application controller."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.i18n = get_i18n()
        self.config = load_config()
        self.i18n.set_lang(self.config.get('language', 'zh'))
        self.logger = get_logger()

        # State
        self.folder = tk.StringVar(value=self.config.get('last_folder', ''))
        self.all_file_data: List[dict] = []  # unfiltered scan results
        self.file_data: List[dict] = []       # currently visible (filtered)
        self.tree_items: Dict[str, str] = {}
        self.target_mode = tk.StringVar(value='folder')
        self.single_path = tk.StringVar()
        self.multi_paths: List[str] = []

        # File list filters
        self.f_name = tk.StringVar(value='')
        self.f_format = tk.StringVar(value='ALL')
        self.f_size_preset = tk.StringVar(value='all')
        self.f_size_min_kb = tk.StringVar(value='')
        self.f_size_max_kb = tk.StringVar(value='')
        self.f_min_width = tk.StringVar(value='')
        self.f_min_height = tk.StringVar(value='')

        # Task runner
        self.task_runner = TaskRunner()

        # History
        self.history = HistoryManager()

        # Animation state
        self._anim_spinner_angle = 0
        self._anim_spinner_id = None
        self._anim_highlight_id = None
        self._anim_highlight_item = None
        self._anim_highlight_on = False
        self._progress_target = 0
        self._progress_current = 0
        self._progress_anim_id = None
        self._status_anim_id = None
        self._preview_after_id = None
        self._preview_gen = 0

        # Compress vars
        self.c_compress_ratio = tk.IntVar(value=self.config.get('compress_ratio', 75))
        self.c_quality = tk.IntVar(value=75)
        self.c_resize = tk.IntVar(value=75)
        self._set_compress_from_ratio(self.c_compress_ratio.get())
        self.c_replace = tk.BooleanVar(value=self.config.get('compress_replace', True))
        self.c_outfolder = tk.StringVar(value=self.config.get('compress_output_folder', ''))
        self.c_backup = tk.BooleanVar(value=self.config.get('compress_backup', True))
        self.u_convert = tk.BooleanVar(value=False)
        self.u_watermark = tk.BooleanVar(value=False)
        self.u_rename = tk.BooleanVar(value=False)
        self.u_wm_text = tk.StringVar(value='')
        self.u_wm_opacity = tk.IntVar(value=50)
        self.u_prefix = tk.StringVar(value='')
        self.u_suffix = tk.StringVar(value='')

        # Convert vars
        self.v_target_fmt = tk.StringVar(value=self.config.get('convert_target_format', '.png'))
        self.v_conv_replace = tk.BooleanVar(value=self.config.get('convert_replace', True))
        self.v_conv_outfolder = tk.StringVar(value=self.config.get('convert_output_folder', ''))
        self.v_conv_backup = tk.BooleanVar(value=self.config.get('convert_backup', True))

        # Rename vars
        self.r_mode = tk.StringVar(value=self.config.get('rename_mode', 'prefix'))
        self.r_prefix = tk.StringVar(value=self.config.get('rename_prefix', 'img_'))
        self.r_suffix = tk.StringVar(value=self.config.get('rename_suffix', ''))
        self.r_replace_src = tk.StringVar(value=self.config.get('rename_find', ''))
        self.r_replace_dst = tk.StringVar(value=self.config.get('rename_replace', ''))
        self.r_seq_start = tk.IntVar(value=self.config.get('rename_seq_start', 1))
        self.r_seq_digits = tk.IntVar(value=self.config.get('rename_seq_digits', 3))
        self.r_seq_template = tk.StringVar(value=self.config.get('rename_seq_template', 'photo_{num}'))
        self.r_lowercase = tk.BooleanVar(value=self.config.get('rename_lowercase', False))
        self.r_uppercase = tk.BooleanVar(value=self.config.get('rename_uppercase', False))

        # Watermark vars
        self.w_type = tk.StringVar(value=self.config.get('watermark_type', 'text'))
        self.w_text = tk.StringVar(value=self.config.get('watermark_text', '\u6c34\u5370'))
        self.w_fontsize = tk.IntVar(value=self.config.get('watermark_font_size', 36))
        self.w_opacity = tk.IntVar(value=self.config.get('watermark_opacity', 50))
        self.w_position = tk.StringVar(value=self.config.get('watermark_position', 'bottom-right'))
        self.w_color = tk.StringVar(value=self.config.get('watermark_color', '#ffffff'))
        self.w_image_path = tk.StringVar(value=self.config.get('watermark_image_path', ''))
        self.w_img_scale = tk.IntVar(value=self.config.get('watermark_image_scale', 20))
        self.w_replace = tk.BooleanVar(value=self.config.get('watermark_replace', True))
        self.w_outfolder = tk.StringVar(value=self.config.get('watermark_output_folder', ''))
        self.w_backup = tk.BooleanVar(value=self.config.get('watermark_backup', True))

        # AI vars
        self.ai_api_key = tk.StringVar()
        self.ai_prompt = tk.StringVar(value=self.config.get('ai_prompt', DEFAULT_PROMPT))
        self.ai_result: Dict[str, str] = {}

        # Trim vars
        self.t_padding = tk.IntVar(value=self.config.get('trim_padding', 4))
        self.t_replace = tk.BooleanVar(value=self.config.get('trim_replace', True))
        self.t_outfolder = tk.StringVar(value=self.config.get('trim_output_folder', ''))
        self.t_backup = tk.BooleanVar(value=self.config.get('trim_backup', True))

        # Normalize vars
        self.n_alpha_threshold = tk.IntVar(value=self.config.get('normalize_alpha_threshold', 28))
        self.n_target_height = tk.IntVar(value=self.config.get('normalize_target_height', 280))
        self.n_padding = tk.IntVar(value=self.config.get('normalize_padding', 6))
        self.n_replace = tk.BooleanVar(value=self.config.get('normalize_replace', True))
        self.n_outfolder = tk.StringVar(value=self.config.get('normalize_output_folder', ''))
        self.n_backup = tk.BooleanVar(value=self.config.get('normalize_backup', True))

        # Sprite sheet vars
        self.ss_layout = tk.StringVar(value=self.config.get('spritesheet_layout', 'auto'))
        self.ss_spacing = tk.IntVar(value=self.config.get('spritesheet_spacing', 2))
        self.ss_trim = tk.BooleanVar(value=self.config.get('spritesheet_trim', True))
        self.ss_trim_padding = tk.IntVar(value=self.config.get('spritesheet_trim_padding', 2))
        self.ss_alpha_threshold = tk.IntVar(value=self.config.get('spritesheet_alpha_threshold', 28))
        self.ss_columns = tk.IntVar(value=self.config.get('spritesheet_columns', 0))
        self.ss_max_width = tk.IntVar(value=self.config.get('spritesheet_max_width', 0))
        self.ss_power_of_two = tk.BooleanVar(value=self.config.get('spritesheet_power_of_two', False))
        self.ss_export_json = tk.BooleanVar(value=self.config.get('spritesheet_export_json', True))
        self.ss_output = tk.StringVar(value=self.config.get('spritesheet_output', ''))

        # EXIF + recursive
        self.exif_mode = tk.StringVar(value=self.config.get('exif_mode', 'keep'))
        self.recursive_scan = tk.BooleanVar(value=self.config.get('recursive_scan', False))

        self._build_ui()
        self._apply_theme()
        self.i18n.register_callback(self._on_lang_change)

        # Auto-refresh if last folder exists
        if self.folder.get() and os.path.isdir(self.folder.get()):
            self._refresh()

    # ═══════════════════════ UI Build ═══════════════════════

    def _build_ui(self):
        self.root.title(tr('app_title'))
        self.root.geometry('960x780')
        self.root.minsize(860, 640)
        self.root.configure(bg=BG)

        # Top bar
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=(10, 0))
        self.folder_label = ttk.Label(top, text=tr('target_folder'), font=('Tahoma', 10, 'bold'))
        self.folder_label.pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(top, textvariable=self.folder, width=50, font=('Tahoma', 10))
        self.folder_entry.pack(side=tk.LEFT, padx=(6, 6), fill=tk.X, expand=True)
        self.btn_browse = ttk.Button(top, text=tr('browse'), command=self._browse)
        self.btn_browse.pack(side=tk.LEFT)
        self.btn_refresh = ttk.Button(top, text=tr('refresh'), command=self._refresh)
        self.btn_refresh.pack(side=tk.LEFT, padx=(6, 0))
        self.btn_open_image = ttk.Button(top, text=tr('open_image'), command=self._open_images)
        self.btn_open_image.pack(side=tk.LEFT, padx=(6, 0))

        self.lbl_mode = ttk.Label(top, text=tr('mode_folder'), font=('Tahoma', 9, 'bold'), foreground=ACCENT)
        self.lbl_mode.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_clear_single = ttk.Button(top, text=tr('clear_single'), command=self._clear_single_mode)
        self.btn_clear_multi = ttk.Button(top, text=tr('clear_multi'), command=self._clear_multi_mode)

        # Undo button
        self.btn_undo = ttk.Button(top, text=tr('undo'), command=self._undo_last)
        self.btn_undo.pack(side=tk.LEFT, padx=(8, 0))

        # Language switcher
        lang_fr = ttk.Frame(top)
        lang_fr.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(lang_fr, text='中文', width=4, command=lambda: self._switch_lang('zh')).pack(side=tk.LEFT)
        ttk.Button(lang_fr, text='EN', width=3, command=lambda: self._switch_lang('en')).pack(side=tk.LEFT, padx=(2, 0))

        # Recursive scan checkbox
        ttk.Checkbutton(top, text=tr('recursive_scan'), variable=self.recursive_scan,
                        command=self._refresh).pack(side=tk.RIGHT, padx=(8, 0))

        self._drop_target(top)

        # File list
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=6)
        list_hdr = ttk.Frame(self.root)
        list_hdr.pack(fill=tk.X, padx=12)
        self.list_label = ttk.Label(list_hdr, text=tr('file_list'), font=('Tahoma', 9, 'bold'))
        self.list_label.pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(list_hdr, text='')
        self.lbl_count.pack(side=tk.RIGHT)

        # Filter bar
        self.filter_fr = ttk.Frame(self.root)
        self.filter_fr.pack(fill=tk.X, padx=12, pady=(4, 0))
        self.lbl_filter = ttk.Label(self.filter_fr, text=tr('filter'))
        self.lbl_filter.pack(side=tk.LEFT)

        self.lbl_filter_name = ttk.Label(self.filter_fr, text=tr('filter_name'))
        self.lbl_filter_name.pack(side=tk.LEFT, padx=(8, 2))
        self.entry_filter_name = ttk.Entry(self.filter_fr, textvariable=self.f_name, width=14)
        self.entry_filter_name.pack(side=tk.LEFT)
        self.entry_filter_name.bind('<KeyRelease>', lambda e: self._on_filter_change())

        self.lbl_filter_fmt = ttk.Label(self.filter_fr, text=tr('filter_format'))
        self.lbl_filter_fmt.pack(side=tk.LEFT, padx=(8, 2))
        self.cmb_filter_fmt = ttk.Combobox(
            self.filter_fr, textvariable=self.f_format, width=7, state='readonly',
            values=list(FILTER_FORMATS),
        )
        self.cmb_filter_fmt.pack(side=tk.LEFT)
        self.cmb_filter_fmt.bind('<<ComboboxSelected>>', lambda e: self._on_filter_change())

        self.lbl_filter_size = ttk.Label(self.filter_fr, text=tr('filter_size'))
        self.lbl_filter_size.pack(side=tk.LEFT, padx=(8, 2))
        self._size_preset_keys = list(SIZE_PRESETS.keys())
        self.cmb_filter_size = ttk.Combobox(
            self.filter_fr, width=12, state='readonly',
        )
        self.cmb_filter_size.pack(side=tk.LEFT)
        self.cmb_filter_size.bind('<<ComboboxSelected>>', self._on_size_preset_change)
        self._refresh_size_preset_labels()

        self.lbl_filter_size_unit = ttk.Label(self.filter_fr, text=tr('filter_size_kb'))
        self.lbl_filter_size_unit.pack(side=tk.LEFT, padx=(6, 2))
        self.entry_size_min = ttk.Entry(self.filter_fr, textvariable=self.f_size_min_kb, width=6)
        self.entry_size_min.pack(side=tk.LEFT)
        ttk.Label(self.filter_fr, text='-').pack(side=tk.LEFT, padx=2)
        self.entry_size_max = ttk.Entry(self.filter_fr, textvariable=self.f_size_max_kb, width=6)
        self.entry_size_max.pack(side=tk.LEFT)
        self.entry_size_min.bind('<KeyRelease>', lambda e: self._on_custom_size_edit())
        self.entry_size_max.bind('<KeyRelease>', lambda e: self._on_custom_size_edit())

        self.lbl_filter_dim = ttk.Label(self.filter_fr, text=tr('filter_dim'))
        self.lbl_filter_dim.pack(side=tk.LEFT, padx=(8, 2))
        self.entry_min_w = ttk.Entry(self.filter_fr, textvariable=self.f_min_width, width=5)
        self.entry_min_w.pack(side=tk.LEFT)
        ttk.Label(self.filter_fr, text='×').pack(side=tk.LEFT, padx=1)
        self.entry_min_h = ttk.Entry(self.filter_fr, textvariable=self.f_min_height, width=5)
        self.entry_min_h.pack(side=tk.LEFT)
        self.entry_min_w.bind('<KeyRelease>', lambda e: self._on_filter_change())
        self.entry_min_h.bind('<KeyRelease>', lambda e: self._on_filter_change())

        self.btn_filter_reset = ttk.Button(
            self.filter_fr, text=tr('filter_reset'), command=self._reset_filters, width=6,
        )
        self.btn_filter_reset.pack(side=tk.LEFT, padx=(8, 0))

        # Middle: file list + preview
        middle = ttk.Frame(self.root)
        middle.pack(fill=tk.BOTH, expand=True, padx=12)

        tree_fr = ttk.Frame(middle)
        tree_fr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cols = ('filename', 'size', 'dimensions', 'format')
        self.tree = ttk.Treeview(tree_fr, columns=cols, show='headings', height=8, selectmode='extended')
        col_map = {"filename": "col_name", "size": "col_size", "dimensions": "col_dim", "format": "col_fmt"}
        for c, w in zip(cols, [340, 80, 110, 70]):
            self.tree.heading(c, text=tr(col_map.get(c, c)))
        vsb = ttk.Scrollbar(tree_fr, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<Double-1>', self._preview)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        # Preview panel with before/after support
        preview_fr = ttk.Frame(middle, width=280)
        preview_fr.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        preview_fr.pack_propagate(False)
        self.preview_label = ttk.Label(preview_fr, text=tr('preview'), font=('Tahoma', 9, 'bold'))
        self.preview_label.pack(anchor=tk.W)
        self.preview_canvas = tk.Canvas(preview_fr, bg='#FFFFFF', relief=tk.SUNKEN,
                                         borderwidth=2, highlightthickness=0, width=260, height=260)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=4)
        self.preview_canvas.create_text(130, 130, text=tr('no_preview'),
                                         fill='#888888', font=('Tahoma', 9), tags='placeholder')
        self.preview_info = ttk.Label(preview_fr, text='')
        self.preview_info.pack(anchor=tk.W)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, padx=12, pady=(4, 0))

        # Build tabs
        self._tab_compress()
        self._tab_convert()
        self._tab_rename()
        self._tab_watermark()
        self._tab_ai_rename()
        self._tab_trim()
        self._tab_inspect()
        self._tab_normalize()
        self._tab_spritesheet()
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        # Status bar + animation
        st = ttk.Frame(self.root)
        st.pack(fill=tk.X, padx=12, pady=(4, 8))
        self.progress = ttk.Progressbar(st, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 2))

        sf = ttk.Frame(st)
        sf.pack(fill=tk.X, pady=(2, 0))
        self.spinner = tk.Canvas(sf, width=20, height=20, bg=BG, highlightthickness=0)
        self.spinner.create_oval(4, 4, 16, 16, outline=BG2, width=2, tags='bg')
        self.spinner_arc = self.spinner.create_arc(4, 4, 16, 16, start=0, extent=60,
                                                    outline=ACCENT, width=2, style='arc', tags='arc')
        self.lbl_status = ttk.Label(sf, text=tr('ready'))
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_eta = ttk.Label(sf, text='', foreground=ACCENT2)
        self.lbl_eta.pack(side=tk.LEFT, padx=(10, 0))
        self.lbl_stats = ttk.Label(sf, text='')
        self.lbl_stats.pack(side=tk.RIGHT)

    def _apply_theme(self):
        style = ttk.Style()
        apply_theme(style)

    # ═══════════════════════ Language ═══════════════════════

    def _switch_lang(self, lang: str):
        self.i18n.set_lang(lang)
        self.config['language'] = lang

    def _on_lang_change(self):
        """Update all labels in-place without rebuilding tabs."""
        self.root.title(tr('app_title'))
        self.folder_label.config(text=tr('target_folder'))
        self.btn_browse.config(text=tr('browse'))
        self.btn_refresh.config(text=tr('refresh'))
        self.btn_open_image.config(text=tr('open_image'))
        self.btn_undo.config(text=tr('undo'))
        self.list_label.config(text=tr('file_list'))
        self.preview_label.config(text=tr('preview'))
        self.lbl_status.config(text=tr('ready'))
        self.lbl_filter.config(text=tr('filter'))
        self.lbl_filter_name.config(text=tr('filter_name'))
        self.lbl_filter_fmt.config(text=tr('filter_format'))
        self.lbl_filter_size.config(text=tr('filter_size'))
        self.lbl_filter_size_unit.config(text=tr('filter_size_kb'))
        self.lbl_filter_dim.config(text=tr('filter_dim'))
        self.btn_filter_reset.config(text=tr('filter_reset'))
        self._refresh_size_preset_labels()
        self._update_count_label()

        # Update tab texts
        for i, tab_id in enumerate(self.notebook.tabs()):
            key = ['tab_compress', 'tab_format', 'tab_rename', 'tab_watermark',
                   'tab_airename', 'tab_trim', 'tab_inspect', 'tab_normalize',
                   'tab_spritesheet'][i]
            try:
                self.notebook.tab(tab_id, text=' ' + tr(key) + ' ')
            except Exception:
                pass

        # Update mode label
        mode = self.target_mode.get()
        if mode == 'single':
            self.lbl_mode.config(text=tr('mode_single'))
        elif mode == 'multi':
            self.lbl_mode.config(text=tr('mode_multi'))
        else:
            self.lbl_mode.config(text=tr('mode_folder'))

    # ═══════════════════════ Drag & Drop ═══════════════════════

    def _drop_target(self, widget=None):
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
        except (OSError, AttributeError) as exc:
            self.logger.error("DragAcceptFiles init failed: %s", exc)

    def _restore_wndproc(self, event=None):
        if os.name != 'nt' or not getattr(self, '_orig_wndproc', None):
            return
        try:
            hwnd = self.root.winfo_id()
            _SetWindowLongPtr(hwnd, GWL_WNDPROC, self._orig_wndproc)
            self._orig_wndproc = None
        except (OSError, AttributeError):
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
            except (OSError, ValueError) as exc:
                self.logger.error("Drop processing error: %s", exc)
            return 0
        return _CallWindowProc(self._orig_wndproc, hwnd, msg, wparam, lparam)

    def _handle_drop(self, files):
        images = [f for f in files if Path(f).suffix.lower() in SUPPORTED_EXT]
        if not images:
            messagebox.showwarning(tr('notice'), tr('drop_invalid'))
            return
        if len(images) == 1:
            self._enter_single_mode(images[0])
        else:
            self._enter_multi_mode(images)

    def _enter_single_mode(self, path):
        path = os.path.normpath(path)
        self.single_path.set(path)
        self.target_mode.set('single')
        folder = os.path.dirname(path)
        if folder:
            self.folder.set(folder)
        self._update_mode_ui()
        self._refresh()
        if self.tree.get_children():
            self.tree.selection_set(self.tree.get_children()[0])

    def _enter_multi_mode(self, paths):
        self.multi_paths = [os.path.normpath(p) for p in paths]
        self.target_mode.set('multi')
        folder = os.path.dirname(self.multi_paths[0])
        if folder:
            self.folder.set(folder)
        self._update_mode_ui()
        self._refresh()

    def _clear_single_mode(self):
        self.target_mode.set('folder')
        self.single_path.set('')
        self._update_mode_ui()
        self._refresh()

    def _clear_multi_mode(self):
        self.target_mode.set('folder')
        self.multi_paths.clear()
        self._update_mode_ui()
        self._refresh()

    def _update_mode_ui(self):
        mode = self.target_mode.get()
        self.btn_clear_single.pack_forget()
        self.btn_clear_multi.pack_forget()
        if mode == 'single':
            self.lbl_mode.config(text=tr('mode_single'))
            self.btn_clear_single.pack(side=tk.LEFT, padx=(4, 0))
        elif mode == 'multi':
            self.lbl_mode.config(text=tr('mode_multi'))
            self.btn_clear_multi.pack(side=tk.LEFT, padx=(4, 0))
        else:
            self.lbl_mode.config(text=tr('mode_folder'))

    # ═══════════════════════ File Operations ═══════════════════════

    def _browse(self):
        path = filedialog.askdirectory(title=tr('sel_img_folder'))
        if path:
            self.target_mode.set('folder')
            self.single_path.set('')
            self.multi_paths.clear()
            self.folder.set(os.path.normpath(path))
            self.config['last_folder'] = path
            self._update_mode_ui()
            self._refresh()

    def _browse_out(self, var):
        path = filedialog.askdirectory(title=tr('sel_out_folder'))
        if path:
            var.set(os.path.normpath(path))

    def _browse_img(self, var):
        path = filedialog.askopenfilename(title=tr('sel_wm_img'),
                                          filetypes=[('Image', '*.png *.jpg *.jpeg *.webp *.bmp')])
        if path:
            var.set(os.path.normpath(path))

    def _open_images(self):
        paths = filedialog.askopenfilenames(
            title=tr('open_image_fd'),
            filetypes=[('Images', '*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.gif *.ico')])
        if not paths:
            return
        if len(paths) == 1:
            self._enter_single_mode(paths[0])
        else:
            self._enter_multi_mode(list(paths))

    def _refresh(self):
        """Refresh file list. Runs in a background thread for large folders."""
        self.all_file_data.clear()
        self.file_data.clear()
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()

        if self.target_mode.get() == 'single':
            path = self.single_path.get()
            if not path or not os.path.isfile(path):
                self.lbl_count.config(text='')
                return
            self._collect_file_info(path)
            self._apply_filters()
            return

        if self.target_mode.get() == 'multi':
            for path in self.multi_paths:
                if os.path.isfile(path):
                    self._collect_file_info(path)
            self._apply_filters()
            return

        # Folder mode — scan in background
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            self.lbl_count.config(text='')
            return

        def _scan_thread():
            recursive = self.recursive_scan.get()
            data = scan_folder(folder, recursive=recursive)
            self.root.after(0, lambda: self._populate_file_list(data))

        threading.Thread(target=_scan_thread, daemon=True).start()
        self.lbl_count.config(text=tr('loading'))

    def _collect_file_info(self, path) -> Optional[dict]:
        """Build a file-info dict and append to ``all_file_data``."""
        f = os.path.basename(path)
        ext = Path(path).suffix.lower()
        if ext not in SUPPORTED_EXT:
            return None
        try:
            sz = os.path.getsize(path)
        except OSError:
            return None
        try:
            with Image.open(path) as img:
                dims = f'{img.width}x{img.height}'
                fmt = img.format or ext[1:]
        except (UnidentifiedImageError, OSError):
            dims = '?'
            fmt = ext[1:]
        d = {'name': f, 'path': path, 'size': sz, 'size_str': fmt_size(sz),
             'dimensions': dims, 'format': fmt}
        self.all_file_data.append(d)
        return d

    def _populate_file_list(self, data):
        self.all_file_data = list(data)
        self._apply_filters()

    def _parse_optional_int(self, value: str) -> Optional[int]:
        s = (value or '').strip()
        if not s:
            return None
        try:
            n = int(float(s))
        except ValueError:
            return None
        return n if n >= 0 else None

    def _current_size_bounds(self) -> tuple:
        preset = self.f_size_preset.get()
        if preset == 'custom' or preset not in SIZE_PRESETS:
            return (parse_kb_to_bytes(self.f_size_min_kb.get()),
                    parse_kb_to_bytes(self.f_size_max_kb.get()))
        return SIZE_PRESETS[preset]

    def _apply_filters(self):
        """Recompute ``file_data`` from ``all_file_data`` and rebuild the tree."""
        min_size, max_size = self._current_size_bounds()
        fmt = self.f_format.get()
        formats = None if not fmt or fmt == 'ALL' else {fmt}

        self.file_data = filter_files(
            self.all_file_data,
            name_query=self.f_name.get(),
            formats=formats,
            min_size=min_size,
            max_size=max_size,
            min_width=self._parse_optional_int(self.f_min_width.get()),
            min_height=self._parse_optional_int(self.f_min_height.get()),
        )

        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()
        for d in self.file_data:
            item = self.tree.insert(
                '', tk.END,
                values=(d['name'], d['size_str'], d['dimensions'], d['format']),
            )
            self.tree_items[d['name']] = item

        self._update_count_label()
        self._schedule_compress_preview()

    def _on_filter_change(self, event=None):
        self._apply_filters()

    def _on_custom_size_edit(self, event=None):
        # Typing custom KB values switches preset to Custom
        if self.f_size_preset.get() != 'custom':
            self.f_size_preset.set('custom')
            self._refresh_size_preset_labels()
        self._apply_filters()

    def _on_size_preset_change(self, event=None):
        label = self.cmb_filter_size.get()
        label_to_key = {tr(f'filter_size_{k}'): k for k in self._size_preset_keys}
        preset = label_to_key.get(label, 'all')
        self.f_size_preset.set(preset)

        if preset != 'custom' and preset in SIZE_PRESETS:
            lo, hi = SIZE_PRESETS[preset]
            if lo is None and hi is None:
                self.f_size_min_kb.set('')
                self.f_size_max_kb.set('')
            elif lo is None:
                self.f_size_min_kb.set('')
                self.f_size_max_kb.set(str((hi + 1) // 1024))
            elif hi is None:
                self.f_size_min_kb.set(str(lo // 1024))
                self.f_size_max_kb.set('')
            else:
                self.f_size_min_kb.set(str(lo // 1024))
                self.f_size_max_kb.set(str((hi + 1) // 1024))
        self._apply_filters()

    def _refresh_size_preset_labels(self):
        """Update size-preset combobox display values for current language."""
        labels = [tr(f'filter_size_{k}') for k in self._size_preset_keys]
        self.cmb_filter_size['values'] = labels
        cur = self.f_size_preset.get()
        if cur not in SIZE_PRESETS:
            cur = 'all'
            self.f_size_preset.set(cur)
        self.cmb_filter_size.set(tr(f'filter_size_{cur}'))

    def _reset_filters(self):
        self.f_name.set('')
        self.f_format.set('ALL')
        self.f_size_preset.set('all')
        self.f_size_min_kb.set('')
        self.f_size_max_kb.set('')
        self.f_min_width.set('')
        self.f_min_height.set('')
        self._refresh_size_preset_labels()
        self._apply_filters()

    def _update_count_label(self):
        shown = len(self.file_data)
        total = len(self.all_file_data)
        shown_size = sum(d['size'] for d in self.file_data)
        if total and shown < total:
            self.lbl_count.config(
                text=tr('filter_count', shown=shown, total=total, size=fmt_size(shown_size))
            )
        else:
            self.lbl_count.config(text=f'{shown} files | {fmt_size(shown_size)}')

    def _preview(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        fname = self.tree.item(sel[0], 'values')[0]
        path = os.path.join(self.folder.get(), fname)
        if os.path.exists(path):
            self._open_image_externally(path)

    def _open_image_externally(self, path: str) -> None:
        """Open an image with the system default viewer (non-blocking)."""
        try:
            if os.name == 'nt':
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except OSError as exc:
            messagebox.showerror(tr('preview_failed'), str(exc))

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            self._clear_preview()
            return
        fname = self.tree.item(sel[0], 'values')[0]
        path = os.path.join(self.folder.get(), fname)
        self._request_preview_panel(path)

    def _request_preview_panel(self, path: str) -> None:
        self._preview_gen += 1
        gen = self._preview_gen
        if not path or not os.path.exists(path):
            self._clear_preview()
            return
        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw <= 1:
            cw = 260
        if ch <= 1:
            ch = 260
        threading.Thread(
            target=self._load_preview_worker,
            args=(path, gen, cw, ch),
            daemon=True,
        ).start()

    def _load_preview_worker(self, path: str, gen: int, cw: int, ch: int) -> None:
        try:
            with Image.open(path) as img:
                info = f'{img.width}x{img.height} | {img.format or "?"}'
                scale = min(cw / img.width, ch / img.height, 1.0)
                nw, nh = int(img.width * scale), int(img.height * scale)
                if nw < 1 or nh < 1:
                    self._schedule_on_main(self._clear_preview_if_gen, gen)
                    return
                thumb = img.copy()
                thumb.thumbnail((nw, nh), Image.LANCZOS)
            self._schedule_on_main(self._apply_preview_panel, gen, thumb, info)
        except (UnidentifiedImageError, OSError):
            self._schedule_on_main(self._clear_preview_if_gen, gen)

    def _clear_preview_if_gen(self, gen: int) -> None:
        if gen == self._preview_gen:
            self._clear_preview()

    def _apply_preview_panel(self, gen: int, thumb: Image.Image, info: str) -> None:
        if gen != self._preview_gen:
            return
        try:
            self.preview_tk_img = ImageTk.PhotoImage(thumb)
            cw = self.preview_canvas.winfo_width()
            ch = self.preview_canvas.winfo_height()
            if cw <= 1:
                cw = 260
            if ch <= 1:
                ch = 260
            self.preview_canvas.delete('all')
            x = max((cw - self.preview_tk_img.width()) // 2, 0)
            y = max((ch - self.preview_tk_img.height()) // 2, 0)
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_tk_img)
            self.preview_info.config(text=info)
        except tk.TclError:
            self._clear_preview()

    def _update_preview_panel(self, path):
        self._request_preview_panel(path)

    def _clear_preview(self):
        self.preview_canvas.delete('all')
        self.preview_canvas.create_text(130, 130, text=tr('no_preview'),
                                         fill='#888888', font=('Tahoma', 9), tags='placeholder')
        self.preview_info.config(text='')

    def _on_tab_changed(self, event=None):
        if not self.notebook.tabs():
            return
        current_text = self.notebook.tab(self.notebook.select(), 'text')
        if 'Compress' in current_text or '\u538b\u7f29' in current_text:
            self._schedule_compress_preview()

    # ═══════════════════════ Compress Tab ═══════════════════════

    def _tab_compress(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_compress') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text=tr('compress_ratio'), width=10).pack(side=tk.LEFT)
        self.scale_compress = ttk.Scale(r1, from_=1, to=100, variable=self.c_compress_ratio,
                  command=lambda v: self._on_compress_ratio_change(v))
        self.scale_compress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.crl = ttk.Label(r1, text=f'{self.c_compress_ratio.get()}%', width=5)
        self.crl.pack(side=tk.LEFT, padx=4)

        r_preview = ttk.Frame(f); r_preview.pack(fill=tk.X, pady=4)
        self.c_preview_lbl = ttk.Label(r_preview, text=tr('compress_preview_none'),
                                       font=('Tahoma', 9, 'bold'), foreground=ACCENT2)
        self.c_preview_lbl.pack(side=tk.LEFT)

        # Also convert
        r_fmt = ttk.Frame(f); r_fmt.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_fmt, text=tr('also_convert'), variable=self.u_convert,
                        command=self._toggle_u_convert).pack(side=tk.LEFT)
        self.u_fmt_frame = ttk.Frame(r_fmt)
        for fmt in ['.jpg', '.png', '.webp', '.bmp', '.tiff']:
            ttk.Radiobutton(self.u_fmt_frame, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=2)

        # Also rename
        r_rename = ttk.Frame(f); r_rename.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_rename, text=tr('also_rename'), variable=self.u_rename,
                        command=self._toggle_u_rename).pack(side=tk.LEFT)
        self.u_rename_frame = ttk.Frame(r_rename)
        ttk.Label(self.u_rename_frame, text=tr('prefix')).pack(side=tk.LEFT)
        ttk.Entry(self.u_rename_frame, textvariable=self.u_prefix, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.u_rename_frame, text=tr('suffix')).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Entry(self.u_rename_frame, textvariable=self.u_suffix, width=12).pack(side=tk.LEFT, padx=2)

        # Also watermark
        r_wm = ttk.Frame(f); r_wm.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r_wm, text=tr('also_watermark'), variable=self.u_watermark,
                        command=self._toggle_u_watermark).pack(side=tk.LEFT)
        self.u_wm_frame = ttk.Frame(r_wm)
        ttk.Label(self.u_wm_frame, text=tr('content')).pack(side=tk.LEFT)
        ttk.Entry(self.u_wm_frame, textvariable=self.u_wm_text, width=18).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.u_wm_frame, text=tr('opacity')).pack(side=tk.LEFT, padx=(6, 0))
        tk.Spinbox(self.u_wm_frame, from_=10, to=100, textvariable=self.u_wm_opacity,
                   width=4, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        # EXIF mode
        r_exif = ttk.Frame(f); r_exif.pack(fill=tk.X, pady=2)
        ttk.Label(r_exif, text=tr('exif_mode'), width=10).pack(side=tk.LEFT)
        for val, key in [('keep', 'exif_keep'), ('strip', 'exif_strip'), ('orientation_only', 'exif_orient')]:
            ttk.Radiobutton(r_exif, text=tr(key), variable=self.exif_mode,
                            value=val).pack(side=tk.LEFT, padx=3)

        # Output mode
        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r3, text=tr('replace_orig'), variable=self.c_replace, value=True,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r3, text=tr('output_to'), variable=self.c_replace, value=False,
                        command=lambda: self._toggle_out(self.c_replace, self.c_outrow, self.c_outfolder)).pack(side=tk.LEFT, padx=10)
        self.c_outrow = ttk.Frame(r3)
        ttk.Entry(self.c_outrow, textvariable=self.c_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.c_outrow, text='Browse', command=lambda: self._browse_out(self.c_outfolder)).pack(side=tk.LEFT)

        # Backup
        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(r4, text=tr('enable_backup'), variable=self.c_backup).pack(side=tk.LEFT)
        ttk.Button(r4, text=tr('backup_mgr'), command=self._backup_mgr).pack(side=tk.RIGHT, padx=8)

        # Actions
        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=4)
        self.btn_cancel = ttk.Button(r5, text=tr('cancel'), command=self._cancel_operation)
        self.btn_cancel.pack(side=tk.RIGHT, ipadx=8, padx=4)
        self.btn_start_compress = ttk.Button(r5, text=tr('start_compress'), command=self._run_compress)
        self.btn_start_compress.pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r5, text=tr('save_as_btn'), command=self._save_as_selected).pack(side=tk.RIGHT, ipadx=8, padx=8)

        self._toggle_u_convert()
        self._toggle_u_rename()
        self._toggle_u_watermark()

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

    def _on_compress_ratio_change(self, val):
        ratio = int(float(val))
        self.crl.config(text=f'{ratio}%')
        self._set_compress_from_ratio(ratio)
        self._schedule_compress_preview()

    def _set_compress_from_ratio(self, ratio):
        ratio = max(1, min(100, int(ratio)))
        self.c_quality.set(ratio)
        self.c_resize.set(max(10, int(10 + (ratio - 1) * 90 / 99)))

    def _schedule_compress_preview(self, event=None):
        if self._preview_after_id:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(150, self._update_compress_preview)

    def _update_compress_preview(self):
        if not getattr(self, 'c_preview_lbl', None):
            return
        if not self.file_data:
            self.c_preview_lbl.config(text=tr('compress_preview_none'))
            return
        quality = int(float(self.c_quality.get()))
        resize_pct = int(float(self.c_resize.get()))
        total_before, total_after = estimate_compressed_size(self.file_data, quality, resize_pct)
        if total_before <= 0:
            self.c_preview_lbl.config(text=tr('compress_preview_none'))
            return
        saved = total_before - total_after
        ratio_pct = (saved / total_before * 100) if total_before else 0
        self.c_preview_lbl.config(
            text=(f'{tr("compress_preview")}: {fmt_size(total_before)} -> {fmt_size(total_after)} '
                  f'({tr("saved")} {fmt_size(saved)}, {ratio_pct:.1f}%)')
        )

    def _run_compress(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        file_list = [d['name'] for d in self.file_data]
        quality = int(float(self.c_quality.get()))
        resize_pct = int(float(self.c_resize.get()))
        do_backup = self.c_backup.get()
        replace = self.c_replace.get()
        out = self.c_outfolder.get().strip() if not replace else None
        if not self._require_output_folder(replace, out):
            return
        exif_mode = self.exif_mode.get()
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

        log_operation('compress', folder=folder, files=len(file_list), quality=quality,
                      resize=resize_pct, replace=replace, exif=exif_mode)

        self._set_running_ui(True)
        self.task_runner.start(
            run_compress_batch,
            folder, file_list, quality, resize_pct, do_backup, replace, out, exif_mode, options,
            backup_fn=create_backup if do_backup else None,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_op_complete('compress', r, folder, file_list, options),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ Convert Tab ═══════════════════════

    def _tab_convert(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_format') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text=tr('to_format'), width=10).pack(side=tk.LEFT)
        for fmt in CONVERT_TARGETS:
            ttk.Radiobutton(r1, text=fmt, variable=self.v_target_fmt,
                            value=fmt).pack(side=tk.LEFT, padx=3)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r2, text=tr('replace_orig'), variable=self.v_conv_replace, value=True,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r2, text=tr('output_to'), variable=self.v_conv_replace, value=False,
                        command=lambda: self._toggle_out(self.v_conv_replace, self.conv_outrow, self.v_conv_outfolder)).pack(side=tk.LEFT, padx=10)
        self.conv_outrow = ttk.Frame(r2)
        ttk.Entry(self.conv_outrow, textvariable=self.v_conv_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.conv_outrow, text='Browse', command=lambda: self._browse_out(self.v_conv_outfolder)).pack(side=tk.LEFT)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r3, text=tr('enable_backup'), variable=self.v_conv_backup).pack(side=tk.LEFT)
        ttk.Button(r3, text=tr('start_convert'), command=self._run_convert).pack(side=tk.RIGHT, ipadx=8)

    def _run_convert(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        file_list = [d['name'] for d in self.file_data]
        target_fmt = self.v_target_fmt.get()
        do_backup = self.v_conv_backup.get()
        replace = self.v_conv_replace.get()
        out = self.v_conv_outfolder.get().strip() if not replace else None
        if not self._require_output_folder(replace, out):
            return

        log_operation('convert', folder=folder, files=len(file_list), target=target_fmt)

        self._set_running_ui(True)
        self.task_runner.start(
            run_convert_batch,
            folder, file_list, target_fmt, do_backup, replace, out,
            backup_fn=create_backup if do_backup else None,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_op_complete('convert', r, folder, file_list),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ Rename Tab ═══════════════════════

    def _tab_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_rename') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text=tr('mode'), width=8).pack(side=tk.LEFT)
        for txt, val in [(tr('prefix_mode'), 'prefix'), (tr('suffix_mode'), 'suffix'),
                         (tr('replace_mode'), 'replace'), (tr('seq_mode'), 'seq'),
                         (tr('case_mode'), 'case')]:
            ttk.Radiobutton(r0, text=txt, variable=self.r_mode, value=val,
                            command=self._toggle_rename_ui).pack(side=tk.LEFT, padx=3)

        self.r_frame = ttk.Frame(f)
        self.r_frame.pack(fill=tk.X, pady=4)

        self.r_prefix_row = ttk.Frame(f)
        ttk.Label(self.r_prefix_row, text=tr('prefix'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_prefix_row, textvariable=self.r_prefix, width=20).pack(side=tk.LEFT, padx=4)

        self.r_suffix_row = ttk.Frame(f)
        ttk.Label(self.r_suffix_row, text=tr('suffix'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_suffix_row, textvariable=self.r_suffix, width=20).pack(side=tk.LEFT, padx=4)

        self.r_replace_row = ttk.Frame(f)
        ttk.Label(self.r_replace_row, text=tr('find'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_src, width=18).pack(side=tk.LEFT)
        ttk.Label(self.r_replace_row, text=tr('replace_to')).pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(self.r_replace_row, textvariable=self.r_replace_dst, width=18).pack(side=tk.LEFT)

        self.r_seq_row = ttk.Frame(f)
        ttk.Label(self.r_seq_row, text=tr('template'), width=8).pack(side=tk.LEFT)
        ttk.Entry(self.r_seq_row, textvariable=self.r_seq_template, width=20).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.r_seq_row, text=tr('start')).pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=99999, textvariable=self.r_seq_start, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text=tr('digits')).pack(side=tk.LEFT, padx=(10, 2))
        tk.Spinbox(self.r_seq_row, from_=1, to=10, textvariable=self.r_seq_digits, width=3,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.r_seq_row, text=tr('num_seq'), foreground='#6c7086').pack(side=tk.LEFT, padx=4)

        self.r_case_row = ttk.Frame(f)
        ttk.Checkbutton(self.r_case_row, text=tr('lowercase'), variable=self.r_lowercase).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(self.r_case_row, text=tr('uppercase'), variable=self.r_uppercase).pack(side=tk.LEFT, padx=4)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Button(r5, text=tr('preview_rename'), command=self._preview_rename).pack(side=tk.LEFT)
        ttk.Button(r5, text=tr('run_rename'), command=self._run_rename).pack(side=tk.RIGHT, ipadx=8)

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

    def _preview_rename(self):
        mapping = generate_rename_map(
            self.file_data, self.r_mode.get(),
            prefix=self.r_prefix.get(), suffix=self.r_suffix.get(),
            find=self.r_replace_src.get(), replace=self.r_replace_dst.get(),
            seq_template=self.r_seq_template.get(),
            seq_start=self.r_seq_start.get(), seq_digits=self.r_seq_digits.get(),
            lowercase=self.r_lowercase.get(), uppercase=self.r_uppercase.get(),
        )
        if not mapping:
            messagebox.showwarning(tr('notice'), tr('no_rename_needed'))
            return
        msgs = [f'{old}\n  -> {new}' for old, new in list(mapping.items())[:20]]
        if len(mapping) > 20:
            msgs.append(f'... {tr("total")} {len(mapping)}')
        messagebox.showinfo(tr('preview_rename'), '\n'.join(msgs))

    def _run_rename(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        mapping = generate_rename_map(
            self.file_data, self.r_mode.get(),
            prefix=self.r_prefix.get(), suffix=self.r_suffix.get(),
            find=self.r_replace_src.get(), replace=self.r_replace_dst.get(),
            seq_template=self.r_seq_template.get(),
            seq_start=self.r_seq_start.get(), seq_digits=self.r_seq_digits.get(),
            lowercase=self.r_lowercase.get(), uppercase=self.r_uppercase.get(),
        )
        if not mapping:
            messagebox.showwarning(tr('notice'), tr('no_rename_needed'))
            return
        if not messagebox.askyesno(tr('confirm'), tr('confirm_rename', n=len(mapping))):
            return

        log_operation('rename', folder=folder, files=len(mapping), mode=self.r_mode.get())

        self._set_running_ui(True)
        self.task_runner.start(
            run_rename_batch,
            folder, mapping, ConflictResolution.AUTO_NUMBER,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_rename_complete(r, folder, mapping),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ Watermark Tab ═══════════════════════

    def _tab_watermark(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_watermark') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r0 = ttk.Frame(f); r0.pack(fill=tk.X, pady=2)
        ttk.Label(r0, text=tr('wm_type'), width=10).pack(side=tk.LEFT)
        ttk.Radiobutton(r0, text=tr('text_type'), variable=self.w_type, value='text',
                        command=self._toggle_wm_ui).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(r0, text=tr('image_type'), variable=self.w_type, value='image',
                        command=self._toggle_wm_ui).pack(side=tk.LEFT, padx=4)

        self.w_text_frame = ttk.Frame(f)
        self.w_text_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.w_text_frame, text=tr('content'), width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_text_frame, textvariable=self.w_text, width=25).pack(side=tk.LEFT, padx=4)
        ttk.Label(self.w_text_frame, text=tr('font_size')).pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_text_frame, from_=8, to=200, textvariable=self.w_fontsize, width=4,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text=tr('color')).pack(side=tk.LEFT, padx=(8, 2))
        ttk.Entry(self.w_text_frame, textvariable=self.w_color, width=8).pack(side=tk.LEFT)
        ttk.Label(self.w_text_frame, text='(#HEX)', foreground='#6c7086').pack(side=tk.LEFT, padx=2)

        self.w_img_frame = ttk.Frame(f)
        ttk.Label(self.w_img_frame, text='Image:', width=10).pack(side=tk.LEFT)
        ttk.Entry(self.w_img_frame, textvariable=self.w_image_path, width=30).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.w_img_frame, text='Browse',
                   command=lambda: self._browse_img(self.w_image_path)).pack(side=tk.LEFT)
        ttk.Label(self.w_img_frame, text=tr('scale_pct')).pack(side=tk.LEFT, padx=(8, 2))
        tk.Spinbox(self.w_img_frame, from_=5, to=100, textvariable=self.w_img_scale, width=4,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text=tr('opacity'), width=10).pack(side=tk.LEFT)
        ttk.Scale(r2, from_=10, to=100, variable=self.w_opacity).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.w_op_lbl = ttk.Label(r2, text=f'{self.w_opacity.get()}%', width=4)
        self.w_op_lbl.pack(side=tk.LEFT, padx=4)
        self.w_opacity.trace_add('write', lambda *a: self.w_op_lbl.config(
            text=f'{self.w_opacity.get()}%'))

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text=tr('position'), width=10).pack(side=tk.LEFT)
        for txt, val in [(tr('top_left'), 'top-left'), (tr('top_right'), 'top-right'),
                         (tr('center'), 'center'), (tr('bottom_left'), 'bottom-left'),
                         (tr('bottom_right'), 'bottom-right')]:
            ttk.Radiobutton(r3, text=txt, variable=self.w_position,
                            value=val).pack(side=tk.LEFT, padx=3)

        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r4, text=tr('replace_orig'), variable=self.w_replace, value=True,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text=tr('output_to'), variable=self.w_replace, value=False,
                        command=lambda: self._toggle_out(self.w_replace, self.wm_outrow, self.w_outfolder)).pack(side=tk.LEFT, padx=10)
        self.wm_outrow = ttk.Frame(r4)
        ttk.Entry(self.wm_outrow, textvariable=self.w_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.wm_outrow, text='Browse', command=lambda: self._browse_out(self.w_outfolder)).pack(side=tk.LEFT)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r5, text=tr('enable_backup'), variable=self.w_backup).pack(side=tk.LEFT)
        ttk.Button(r5, text=tr('batch_wm'), command=self._run_watermark).pack(side=tk.RIGHT, ipadx=8)

        self.w_img_frame.pack_forget()

    def _toggle_wm_ui(self):
        if self.w_type.get() == 'text':
            self.w_img_frame.pack_forget()
            self.w_text_frame.pack(fill=tk.X, pady=2)
        else:
            self.w_text_frame.pack_forget()
            self.w_img_frame.pack(fill=tk.X, pady=2)

    def _run_watermark(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        wtype = self.w_type.get()
        if wtype == 'image' and not self.w_image_path.get():
            messagebox.showwarning(tr('notice'), tr('sel_wm_img'))
            return
        if wtype == 'image' and not os.path.exists(self.w_image_path.get()):
            messagebox.showwarning(tr('notice'), tr('sel_wm_img'))
            return

        file_list = [d['name'] for d in self.file_data]
        do_backup = self.w_backup.get()
        replace = self.w_replace.get()
        out = self.w_outfolder.get().strip() if not replace else None
        if not self._require_output_folder(replace, out):
            return
        params = {
            'type': wtype, 'text': self.w_text.get(),
            'fontsize': self.w_fontsize.get(),
            'opacity': self.w_opacity.get() / 100,
            'position': self.w_position.get(),
            'color': self.w_color.get(),
            'image_path': self.w_image_path.get(),
            'img_scale': self.w_img_scale.get() / 100,
        }

        log_operation('watermark', folder=folder, files=len(file_list), type=wtype)

        self._set_running_ui(True)
        self.task_runner.start(
            run_watermark_batch,
            folder, file_list, params, do_backup, replace, out,
            backup_fn=create_backup if do_backup else None,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_op_complete('watermark', r, folder, file_list),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ AI Rename Tab ═══════════════════════

    def _tab_ai_rename(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_airename') + ' ')

        f = ttk.Frame(tab)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text='DeepSeek API Key:', width=14).pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.ai_api_key, width=50, show='*').pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(r1, text=tr('show_hide'), command=lambda: self._toggle_key_show(r1)).pack(side=tk.LEFT)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text=tr('prompt')).pack(anchor=tk.W)
        self.ai_prompt_text = tk.Text(f, height=4, bg='#FFFFFF', fg=FG, insertbackground=FG,
                                       font=('Lucida Console', 9), relief=tk.SUNKEN, borderwidth=2)
        self.ai_prompt_text.pack(fill=tk.X, padx=0, pady=2)
        self.ai_prompt_text.insert('1.0', self.ai_prompt.get())

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Button(r3, text=tr('ai_analyze'), command=self._ai_analyze).pack(side=tk.LEFT, ipadx=8)
        ttk.Button(r3, text=tr('apply_ai'), command=self._ai_apply).pack(side=tk.RIGHT, ipadx=8)
        ttk.Button(r3, text=tr('clear_results'), command=self._ai_clear).pack(side=tk.RIGHT, padx=8)

        ttk.Label(f, text=tr('ai_preview')).pack(anchor=tk.W, pady=(6, 2))
        tree_fr = ttk.Frame(f)
        tree_fr.pack(fill=tk.BOTH, expand=True)
        self.ai_tree = ttk.Treeview(tree_fr, columns=('original', 'suggested'),
                                     show='headings', height=6)
        self.ai_tree.heading('original', text=tr('orig_name'))
        self.ai_tree.heading('suggested', text=tr('ai_suggested'))
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

    def _ai_analyze(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        api_key = self.ai_api_key.get().strip()
        if not api_key:
            messagebox.showwarning(tr('notice'), tr('enter_api_key'))
            return

        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        self.ai_tree.insert('', tk.END, values=('Connecting to DeepSeek...', 'Waiting...'))
        file_names = [d['name'] for d in self.file_data]
        prompt = self.ai_prompt_text.get('1.0', tk.END).strip()

        self._set_running_ui(True)
        self._animate_status(tr('ai_analyze'))
        self._start_spinner()
        self._anim_ai_loading()

        self.task_runner.start(
            run_ai_rename,
            api_key, file_names, prompt,
            on_progress=self._on_progress,
            on_complete=self._ai_on_complete,
            on_error=self._ai_on_error,
        )

    def _anim_ai_loading(self):
        if not self.task_runner.is_running:
            return
        items = self.ai_tree.get_children()
        if items and not self.ai_result:
            dots_list = ['Waiting.', 'Waiting..', 'Waiting...',
                         'Analyzing.', 'Analyzing..', 'Analyzing...']
            idx = int(time.time() * 1.5) % len(dots_list)
            self.ai_tree.item(items[0], values=('Connecting to DeepSeek...', dots_List[idx]))
            self._anim_ai_loading_id = self.root.after(400, self._anim_ai_loading)

    def _ai_on_complete(self, result):
        self._schedule_on_main(self._finish_ai_complete, result)

    def _finish_ai_complete(self, result):
        self.ai_result = result.get('results', {})
        self._stop_ai_loading()
        self._stop_spinner()
        self.ai_tree.delete(*self.ai_tree.get_children())
        for orig, sugg in self.ai_result.items():
            self.ai_tree.insert('', tk.END, values=(orig, sugg))
        tokens = result.get('total_tokens', 0)
        errors = result.get('errors', [])
        status = f'AI done: {len(self.ai_result)} suggestions, {tokens} tokens'
        if errors:
            status += f', {len(errors)} errors'
        self._set_status(status)
        self._set_running_ui(False)
        if errors:
            messagebox.showwarning(tr('notice'), '\n'.join(errors[:5]))

    def _ai_on_error(self, exc):
        self._schedule_on_main(self._finish_ai_error, exc)

    def _finish_ai_error(self, exc):
        self._stop_ai_loading()
        self._stop_spinner()
        self._set_status(f'AI Error: {exc}')
        self._set_running_ui(False)
        messagebox.showerror(tr('error'), str(exc))

    def _stop_ai_loading(self):
        if hasattr(self, '_anim_ai_loading_id') and self._anim_ai_loading_id:
            self.root.after_cancel(self._anim_ai_loading_id)
            self._anim_ai_loading_id = None

    def _ai_apply(self):
        if not self.ai_result:
            messagebox.showwarning(tr('notice'), tr('run_ai_first'))
            return
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder:
            return

        import os
        mapping = {}
        for orig, sugg in self.ai_result.items():
            if not sugg or not isinstance(sugg, str):
                continue
            if '.' not in sugg:
                sugg = sugg + os.path.splitext(orig)[1]
            orig_ext = os.path.splitext(orig)[1]
            sugg_base = os.path.splitext(sugg)[0]
            new_name = sanitize_filename(sugg_base) + orig_ext
            if new_name != orig:
                mapping[orig] = new_name

        if not mapping:
            messagebox.showinfo(tr('notice'), tr('no_rename_needed'))
            return
        if not messagebox.askyesno(tr('confirm'), tr('ai_rename_confirm', n=len(mapping))):
            return

        log_operation('ai_rename', folder=folder, files=len(mapping))

        self._set_running_ui(True)
        self.task_runner.start(
            apply_ai_rename,
            folder, mapping,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_rename_complete(r, folder, mapping),
            on_error=self._on_op_error,
        )

    def _ai_clear(self):
        self.ai_result.clear()
        self.ai_tree.delete(*self.ai_tree.get_children())
        self._set_status(tr('cleared_ai'))

    # ═══════════════════════ Trim Tab ═══════════════════════

    def _tab_trim(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_trim') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text=tr('padding'), width=10).pack(side=tk.LEFT)
        tk.Spinbox(r1, from_=0, to=50, textvariable=self.t_padding, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r2, text=tr('replace_orig'), variable=self.t_replace, value=True,
                        command=lambda: self._toggle_out(self.t_replace, self.t_outrow, self.t_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r2, text=tr('output_to'), variable=self.t_replace, value=False,
                        command=lambda: self._toggle_out(self.t_replace, self.t_outrow, self.t_outfolder)).pack(side=tk.LEFT, padx=10)
        self.t_outrow = ttk.Frame(r2)
        ttk.Entry(self.t_outrow, textvariable=self.t_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.t_outrow, text='Browse', command=lambda: self._browse_out(self.t_outfolder)).pack(side=tk.LEFT)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r3, text=tr('enable_backup'), variable=self.t_backup).pack(side=tk.LEFT)
        ttk.Button(r3, text=tr('start_trim'), command=self._run_trim).pack(side=tk.RIGHT, ipadx=8)

    def _run_trim(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return

        file_list = [d['name'] for d in self.file_data]
        padding = self.t_padding.get()
        do_backup = self.t_backup.get()
        replace = self.t_replace.get()
        out = self.t_outfolder.get().strip() if not replace else None
        if not self._require_output_folder(replace, out):
            return

        log_operation('trim', folder=folder, files=len(file_list), padding=padding)

        self._set_running_ui(True)
        self.task_runner.start(
            run_trim_batch,
            folder, file_list, padding, do_backup, replace, out,
            backup_fn=create_backup if do_backup else None,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_op_complete('trim', r, folder, file_list),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ Inspect Tab ═══════════════════════

    def _tab_inspect(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_inspect') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        btn_f = ttk.Frame(f); btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text=tr('start_inspect'), command=self._run_inspect).pack(side=tk.LEFT, ipadx=8)

        tree_fr = ttk.Frame(f)
        tree_fr.pack(fill=tk.BOTH, expand=True, pady=4)
        cols = ('filename', 'canvas', 'content', 'top_pad', 'bot_pad', 'left_pad', 'right_pad')
        self.inspect_tree = ttk.Treeview(tree_fr, columns=cols, show='headings', height=8)
        col_widths = [220, 90, 90, 70, 70, 70, 70]
        for c, w in zip(cols, col_widths):
            self.inspect_tree.heading(c, text=tr(c))
            self.inspect_tree.column(c, width=w, minwidth=50, anchor=tk.CENTER)
        vsb = ttk.Scrollbar(tree_fr, orient=tk.VERTICAL, command=self.inspect_tree.yview)
        self.inspect_tree.configure(yscrollcommand=vsb.set)
        self.inspect_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _run_inspect(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return

        png_list = [d for d in self.file_data if d['name'].lower().endswith('.png')]
        if not png_list:
            messagebox.showwarning(tr('notice'), tr('no_png_found'))
            return

        self.inspect_tree.delete(*self.inspect_tree.get_children())
        self._set_running_ui(True)
        self.task_runner.start(
            run_inspect_batch,
            png_list,
            on_progress=self._on_progress,
            on_complete=self._on_inspect_complete,
            on_error=self._on_op_error,
        )

    def _on_inspect_complete(self, result):
        self._schedule_on_main(self._finish_inspect_complete, result)

    def _finish_inspect_complete(self, result):
        self.inspect_tree.delete(*self.inspect_tree.get_children())
        for info in result.get('results', []):
            self.inspect_tree.insert('', tk.END, values=(
                info['name'], info['canvas'], info['content'],
                info['top_pad'], info['bot_pad'], info['left_pad'], info['right_pad']
            ))
        self._stop_spinner()
        self._set_status(f'Inspect done: {len(result.get("results", []))} files')
        self._set_running_ui(False)

    # ═══════════════════════ Normalize Tab ═══════════════════════

    def _tab_normalize(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_normalize') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text=tr('alpha_threshold'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r1, from_=1, to=255, textvariable=self.n_alpha_threshold, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text=tr('target_height'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r2, from_=16, to=4096, textvariable=self.n_target_height, width=6,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text=tr('norm_padding'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r3, from_=0, to=100, textvariable=self.n_padding, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG, highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)

        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(r4, text=tr('replace_orig'), variable=self.n_replace, value=True,
                        command=lambda: self._toggle_out(self.n_replace, self.n_outrow, self.n_outfolder)).pack(side=tk.LEFT)
        ttk.Radiobutton(r4, text=tr('output_to'), variable=self.n_replace, value=False,
                        command=lambda: self._toggle_out(self.n_replace, self.n_outrow, self.n_outfolder)).pack(side=tk.LEFT, padx=10)
        self.n_outrow = ttk.Frame(r4)
        ttk.Entry(self.n_outrow, textvariable=self.n_outfolder, width=40).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.n_outrow, text='Browse', command=lambda: self._browse_out(self.n_outfolder)).pack(side=tk.LEFT)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=6)
        ttk.Checkbutton(r5, text=tr('enable_backup'), variable=self.n_backup).pack(side=tk.LEFT)
        ttk.Button(r5, text=tr('start_normalize'), command=self._run_normalize).pack(side=tk.RIGHT, ipadx=8)

    def _run_normalize(self):
        if self.task_runner.is_running:
            return
        folder = self.folder.get()
        if not folder or not self.file_data:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return

        file_list = [d['name'] for d in self.file_data]
        alpha_threshold = self.n_alpha_threshold.get()
        target_height = self.n_target_height.get()
        padding = self.n_padding.get()
        do_backup = self.n_backup.get()
        replace = self.n_replace.get()
        out = self.n_outfolder.get().strip() if not replace else None
        if not self._require_output_folder(replace, out):
            return

        log_operation('normalize', folder=folder, files=len(file_list),
                      alpha=alpha_threshold, height=target_height)

        self._set_running_ui(True)
        self.task_runner.start(
            run_normalize_batch,
            folder, file_list, alpha_threshold, target_height, padding,
            do_backup, replace, out,
            backup_fn=create_backup if do_backup else None,
            on_progress=self._on_progress,
            on_complete=lambda r: self._on_op_complete('normalize', r, folder, file_list),
            on_error=self._on_op_error,
        )

    # ═══════════════════════ Sprite Sheet Tab ═══════════════════════

    def _tab_spritesheet(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=' ' + tr('tab_spritesheet') + ' ')
        f = ttk.Frame(tab)
        f.pack(fill=tk.X, padx=10, pady=8)

        r1 = ttk.Frame(f); r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text=tr('spritesheet_layout'), width=12).pack(side=tk.LEFT)
        self.ss_layout_combo = ttk.Combobox(
            r1, width=16, state='readonly',
            values=[tr('layout_auto'), tr('layout_grid'),
                    tr('layout_horizontal'), tr('layout_vertical')],
        )
        layout_idx = LAYOUTS.index(self.ss_layout.get()) if self.ss_layout.get() in LAYOUTS else 0
        self.ss_layout_combo.current(layout_idx)
        self.ss_layout_combo.pack(side=tk.LEFT, padx=4)

        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text=tr('spritesheet_spacing'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r2, from_=0, to=50, textvariable=self.ss_spacing, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(r2, text=tr('spritesheet_trim'), variable=self.ss_trim).pack(side=tk.LEFT, padx=12)

        r3 = ttk.Frame(f); r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text=tr('padding'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r3, from_=0, to=50, textvariable=self.ss_trim_padding, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)
        ttk.Label(r3, text=tr('alpha_threshold'), width=12).pack(side=tk.LEFT, padx=(8, 0))
        tk.Spinbox(r3, from_=1, to=255, textvariable=self.ss_alpha_threshold, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)

        r4 = ttk.Frame(f); r4.pack(fill=tk.X, pady=2)
        ttk.Label(r4, text=tr('spritesheet_columns'), width=12).pack(side=tk.LEFT)
        tk.Spinbox(r4, from_=0, to=64, textvariable=self.ss_columns, width=5,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)
        ttk.Label(r4, text=tr('spritesheet_columns_hint')).pack(side=tk.LEFT, padx=4)
        ttk.Label(r4, text=tr('spritesheet_max_width'), width=12).pack(side=tk.LEFT, padx=(8, 0))
        tk.Spinbox(r4, from_=0, to=8192, textvariable=self.ss_max_width, width=6,
                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                   highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=4)
        ttk.Label(r4, text=tr('spritesheet_max_width_hint')).pack(side=tk.LEFT, padx=4)

        r5 = ttk.Frame(f); r5.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(r5, text=tr('spritesheet_power_of_two'),
                        variable=self.ss_power_of_two).pack(side=tk.LEFT)
        ttk.Checkbutton(r5, text=tr('spritesheet_export_json'),
                        variable=self.ss_export_json).pack(side=tk.LEFT, padx=12)

        r6 = ttk.Frame(f); r6.pack(fill=tk.X, pady=4)
        ttk.Label(r6, text=tr('spritesheet_output'), width=12).pack(side=tk.LEFT)
        ttk.Entry(r6, textvariable=self.ss_output, width=40).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(r6, text=tr('browse'), command=self._browse_spritesheet_output).pack(side=tk.LEFT)

        r7 = ttk.Frame(f); r7.pack(fill=tk.X, pady=6)
        ttk.Button(r7, text=tr('start_spritesheet'),
                   command=self._run_spritesheet).pack(side=tk.RIGHT, ipadx=8)

    def _layout_key_from_combo(self) -> str:
        idx = self.ss_layout_combo.current()
        return LAYOUTS[idx] if 0 <= idx < len(LAYOUTS) else LAYOUTS[0]

    def _browse_spritesheet_output(self):
        folder = self.folder.get() or os.path.expanduser('~')
        path = filedialog.asksaveasfilename(
            title=tr('spritesheet_output'),
            initialdir=folder,
            initialfile='spritesheet.png',
            defaultextension='.png',
            filetypes=[('PNG', '*.png')],
        )
        if path:
            self.ss_output.set(os.path.normpath(path))

    def _collect_image_paths(self) -> List[str]:
        """Collect full paths of images to include in sprite sheet."""
        if self.target_mode.get() == 'multi':
            return [p for p in self.multi_paths if os.path.isfile(p)]
        folder = self.folder.get()
        if not folder:
            return []
        return [os.path.join(folder, d['name']) for d in self.file_data]

    def _run_spritesheet(self):
        if self.task_runner.is_running:
            return

        image_paths = self._collect_image_paths()
        if len(image_paths) < 2:
            messagebox.showwarning(tr('notice'), tr('spritesheet_need_two'))
            return

        output = self.ss_output.get().strip()
        if not output:
            folder = self.folder.get() or os.path.dirname(image_paths[0])
            output = os.path.join(folder, 'spritesheet.png')
            self.ss_output.set(output)

        layout = self._layout_key_from_combo()
        log_operation('spritesheet', files=len(image_paths), layout=layout,
                      output=output)

        self._set_running_ui(True)
        self.task_runner.start(
            run_spritesheet_build,
            image_paths, output,
            layout=layout,
            spacing=self.ss_spacing.get(),
            trim=self.ss_trim.get(),
            trim_padding=self.ss_trim_padding.get(),
            alpha_threshold=self.ss_alpha_threshold.get(),
            columns=self.ss_columns.get(),
            max_width=self.ss_max_width.get(),
            power_of_two=self.ss_power_of_two.get(),
            export_json=self.ss_export_json.get(),
            on_progress=self._on_progress,
            on_complete=self._on_spritesheet_complete,
            on_error=self._on_op_error,
        )

    def _on_spritesheet_complete(self, result: dict):
        self._schedule_on_main(self._finish_spritesheet_complete, result)

    def _finish_spritesheet_complete(self, result: dict):
        self._stop_spinner()
        self._clear_highlight()
        errors = result.get('errors', [])
        cancelled = result.get('cancelled', False)

        if cancelled:
            self._set_status(tr('operation_cancelled'))
        elif errors and not result.get('output_path'):
            self._set_status(tr('error'))
        else:
            w, h = result.get('sheet_size', (0, 0))
            n = result.get('frame_count', 0)
            self._set_status(tr('spritesheet_done', w=w, h=h, n=n))
            out = result.get('output_path', '')
            if out:
                self._preview_path(out)

        self._set_running_ui(False)

        if errors:
            self.root.after(200, lambda errs=errors: messagebox.showwarning(
                tr('done'), '\n'.join(errs[:5])))

    def _preview_path(self, path: str):
        """Show a file in the preview panel."""
        if os.path.isfile(path):
            self._request_preview_panel(path)

    # ═══════════════════════ Common UI Helpers ═══════════════════════

    def _schedule_on_main(self, fn: Callable, *args, **kwargs) -> None:
        """Run a UI callback on the Tk main thread (safe from worker threads)."""
        self.root.after(0, lambda: fn(*args, **kwargs))

    def _require_output_folder(self, replace: bool, out: Optional[str]) -> bool:
        if replace or (out and out.strip()):
            return True
        messagebox.showwarning(tr('notice'), tr('select_output_folder'))
        return False

    def _toggle_out(self, replace_var, row, folder_var):
        if replace_var.get():
            row.pack_forget()
        else:
            row.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
            if not folder_var.get():
                default = os.path.join(self.folder.get() or '', 'output')
                folder_var.set(default)

    def _save_as_selected(self):
        sel = self.tree.selection()
        if not sel and self.file_data:
            sel = (self.tree.get_children()[0],)
        if not sel:
            messagebox.showwarning(tr('notice'), tr('select_folder_first'))
            return
        fname = self.tree.item(sel[0], 'values')[0]
        src = os.path.join(self.folder.get(), fname)
        if not os.path.exists(src):
            return
        ext = os.path.splitext(fname)[1]
        path = filedialog.asksaveasfilename(
            title=tr('save_as'), defaultextension=ext,
            filetypes=[(tr('all_files'), '*.*'), ('PNG', '*.png'), ('JPEG', '*.jpg'),
                       ('WebP', '*.webp'), ('BMP', '*.bmp'), ('TIFF', '*.tiff')])
        if not path:
            return
        try:
            import shutil
            shutil.copy2(src, path)
            messagebox.showinfo(tr('done'), f'{tr("saved")}:\n{path}')
        except OSError as exc:
            messagebox.showerror(tr('error'), str(exc))

    def _backup_mgr(self):
        folder = self.folder.get()
        if not folder:
            return
        backups = find_backups(folder)
        if not backups:
            messagebox.showinfo(tr('backup_mgr'), 'No backups found')
            return
        # Simple dialog
        from tkinter import simpledialog
        msg = '\n'.join(os.path.basename(b) for b in backups)
        choice = simpledialog.askstring(tr('backup_mgr'),
            f'{msg}\n\nType "restore" or "clear":')
        if choice and choice.lower().startswith('r'):
            idx = 0
            if len(backups) > 1:
                idx_str = simpledialog.askinteger('Select', f'Enter index (0-{len(backups)-1}):')
                if idx_str is not None:
                    idx = idx_str
            if idx < len(backups):
                n = do_restore(backups[idx], folder)
                self._refresh()
                messagebox.showinfo(tr('restore_done'), f'Restored {n} files')
        elif choice and choice.lower().startswith('c'):
            n = do_clear_backups(backups)
            messagebox.showinfo(tr('done'), f'Cleared {n} backups')

    # ═══════════════════════ Task Callbacks ═══════════════════════

    def _on_progress(self, pct: float, msg: str):
        self._schedule_on_main(self._update_progress_ui, pct, msg)

    def _update_progress_ui(self, pct: float, msg: str):
        self._set_progress(pct)
        self._animate_status(msg)

    def _on_op_complete(self, op_type: str, result: dict, folder: str,
                        file_list: List[str], options: Optional[dict] = None):
        self._schedule_on_main(
            self._finish_op_complete, op_type, result, folder, file_list, options,
        )

    def _finish_op_complete(self, op_type: str, result: dict, folder: str,
                            file_list: List[str], options: Optional[dict] = None):
        self._stop_spinner()
        self._clear_highlight()
        total_before = result.get('total_before', 0)
        total_after = result.get('total_after', 0)
        errors = result.get('errors', [])
        cancelled = result.get('cancelled', False)
        backup_dir = result.get('backup_dir')

        if cancelled:
            self._set_status(tr('operation_cancelled'))
        else:
            saved = total_before - total_after
            ratio = (total_after / total_before * 100) if total_before else 0
            msg = f'{fmt_size(total_before)} -> {fmt_size(total_after)} ({tr("saved")} {fmt_size(saved)}, {ratio:.1f}%)'
            self._set_status(f'{op_type} done - {msg}')

        # Record in history
        rename_map = result.get('rename_map', {})
        self.history.push(OperationRecord(
            op_type=op_type,
            folder=folder,
            files=file_list,
            rename_map=rename_map,
            backup_dir=backup_dir,
            params=options or {},
        ))

        self._set_running_ui(False)
        self.root.after(100, self._refresh)

        if errors:
            self.root.after(200, lambda errs=errors: messagebox.showwarning(
                tr('done'), f'{len(errs)} errors:\n' + '\n'.join(errs[:5])))

    def _on_rename_complete(self, result: dict, folder: str, mapping: dict):
        self._schedule_on_main(self._finish_rename_complete, result, folder, mapping)

    def _finish_rename_complete(self, result: dict, folder: str, mapping: dict):
        self._stop_spinner()
        self._clear_highlight()
        renamed = result.get('renamed', 0)
        errors = result.get('errors', [])
        cancelled = result.get('cancelled', False)

        if cancelled:
            self._set_status(tr('operation_cancelled'))
        else:
            self._set_status(tr('rename_done', n=renamed))

        self.history.push(OperationRecord(
            op_type='rename',
            folder=folder,
            rename_map=mapping,
        ))

        self._set_running_ui(False)
        self.root.after(100, self._refresh)

        if errors:
            self.root.after(200, lambda errs=errors: messagebox.showerror(
                tr('error'), '\n'.join(errs[:10])))
        elif not cancelled:
            self.root.after(200, lambda: messagebox.showinfo(
                tr('done'), tr('rename_done', n=renamed)))

    def _on_op_error(self, exc: Exception):
        self._schedule_on_main(self._finish_op_error, exc)

    def _finish_op_error(self, exc: Exception):
        self._stop_spinner()
        self._clear_highlight()
        self._set_status(f'Error: {exc}')
        self._set_running_ui(False)
        messagebox.showerror(tr('error'), str(exc))

    def _cancel_operation(self):
        if self.task_runner.is_running:
            self.task_runner.cancel()
            self._set_status(tr('operation_cancelled'))

    def _undo_last(self):
        record = self.history.pop()
        if not record:
            messagebox.showinfo(tr('undo'), tr('no_undo'))
            return
        result = undo_operation(record)
        if result['success']:
            messagebox.showinfo(tr('undo'), tr('undo_done', op=record.op_type))
            self._refresh()
        else:
            messagebox.showwarning(tr('error'), result['message'])

    # ═══════════════════════ UI State ═══════════════════════

    def _set_running_ui(self, running: bool):
        self.btn_browse.config(state=tk.DISABLED if running else tk.NORMAL)
        self.btn_refresh.config(state=tk.DISABLED if running else tk.NORMAL)
        self.btn_start_compress.config(state=tk.DISABLED if running else tk.NORMAL)
        if running:
            self.btn_cancel.pack(side=tk.RIGHT, ipadx=8, padx=4)
            self._set_progress(0)
            self._start_spinner()
        else:
            self.btn_cancel.pack_forget()
            self._stop_spinner()

    # ═══════════════════════ Animation ═══════════════════════

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

    def _set_status(self, msg):
        if self._status_anim_id:
            self.root.after_cancel(self._status_anim_id)
            self._status_anim_id = None
        self.root.after(0, lambda: self.lbl_status.config(text=msg))

    # ═══════════════════════ Lifecycle ═══════════════════════

    def on_close(self):
        """Save config and clean up on window close."""
        self.config['last_folder'] = self.folder.get()
        self.config['compress_ratio'] = self.c_compress_ratio.get()
        self.config['compress_replace'] = self.c_replace.get()
        self.config['compress_backup'] = self.c_backup.get()
        self.config['compress_output_folder'] = self.c_outfolder.get()
        self.config['convert_target_format'] = self.v_target_fmt.get()
        self.config['convert_replace'] = self.v_conv_replace.get()
        self.config['convert_backup'] = self.v_conv_backup.get()
        self.config['convert_output_folder'] = self.v_conv_outfolder.get()
        self.config['rename_mode'] = self.r_mode.get()
        self.config['rename_prefix'] = self.r_prefix.get()
        self.config['rename_suffix'] = self.r_suffix.get()
        self.config['rename_find'] = self.r_replace_src.get()
        self.config['rename_replace'] = self.r_replace_dst.get()
        self.config['rename_seq_start'] = self.r_seq_start.get()
        self.config['rename_seq_digits'] = self.r_seq_digits.get()
        self.config['rename_seq_template'] = self.r_seq_template.get()
        self.config['rename_lowercase'] = self.r_lowercase.get()
        self.config['rename_uppercase'] = self.r_uppercase.get()
        self.config['watermark_type'] = self.w_type.get()
        self.config['watermark_text'] = self.w_text.get()
        self.config['watermark_font_size'] = self.w_fontsize.get()
        self.config['watermark_opacity'] = self.w_opacity.get()
        self.config['watermark_position'] = self.w_position.get()
        self.config['watermark_color'] = self.w_color.get()
        self.config['watermark_image_path'] = self.w_image_path.get()
        self.config['watermark_image_scale'] = self.w_img_scale.get()
        self.config['watermark_replace'] = self.w_replace.get()
        self.config['watermark_backup'] = self.w_backup.get()
        self.config['watermark_output_folder'] = self.w_outfolder.get()
        self.config['ai_prompt'] = self.ai_prompt_text.get('1.0', tk.END).strip()
        self.config['trim_padding'] = self.t_padding.get()
        self.config['trim_replace'] = self.t_replace.get()
        self.config['trim_backup'] = self.t_backup.get()
        self.config['trim_output_folder'] = self.t_outfolder.get()
        self.config['normalize_alpha_threshold'] = self.n_alpha_threshold.get()
        self.config['normalize_target_height'] = self.n_target_height.get()
        self.config['normalize_padding'] = self.n_padding.get()
        self.config['normalize_replace'] = self.n_replace.get()
        self.config['normalize_backup'] = self.n_backup.get()
        self.config['normalize_output_folder'] = self.n_outfolder.get()
        self.config['spritesheet_layout'] = self._layout_key_from_combo()
        self.config['spritesheet_spacing'] = self.ss_spacing.get()
        self.config['spritesheet_trim'] = self.ss_trim.get()
        self.config['spritesheet_trim_padding'] = self.ss_trim_padding.get()
        self.config['spritesheet_alpha_threshold'] = self.ss_alpha_threshold.get()
        self.config['spritesheet_columns'] = self.ss_columns.get()
        self.config['spritesheet_max_width'] = self.ss_max_width.get()
        self.config['spritesheet_power_of_two'] = self.ss_power_of_two.get()
        self.config['spritesheet_export_json'] = self.ss_export_json.get()
        self.config['spritesheet_output'] = self.ss_output.get()
        self.config['exif_mode'] = self.exif_mode.get()
        self.config['recursive_scan'] = self.recursive_scan.get()
        save_config(self.config)
        self.task_runner.shutdown()


def main():
    """Entry point for the GUI application."""
    root = tk.Tk()
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (OSError, AttributeError):
        pass

    app = ImgBatchApp(root)
    root.protocol('WM_DELETE_WINDOW', lambda: (app.on_close(), root.destroy()))
    root.mainloop()
