#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Settings persistence for ImgBatch.

User preferences are stored as JSON at ``~/.imgbatch/config.json``.
API keys are NOT stored here — they use :mod:`keyring` when available.
"""

import json
from pathlib import Path
from typing import Any, Dict

from .logger import get_logger

CONFIG_DIR = Path.home() / ".imgbatch"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    # General
    "language": "zh",
    "last_folder": "",
    # Compress
    "compress_ratio": 75,
    "compress_replace": True,
    "compress_backup": True,
    "compress_output_folder": "",
    # Convert
    "convert_target_format": ".png",
    "convert_replace": True,
    "convert_backup": True,
    "convert_output_folder": "",
    # Rename
    "rename_mode": "prefix",
    "rename_prefix": "img_",
    "rename_suffix": "",
    "rename_find": "",
    "rename_replace": "",
    "rename_seq_start": 1,
    "rename_seq_digits": 3,
    "rename_seq_template": "photo_{num}",
    "rename_lowercase": False,
    "rename_uppercase": False,
    # Watermark
    "watermark_type": "text",
    "watermark_text": "\u6c34\u5370",
    "watermark_font_size": 36,
    "watermark_opacity": 50,
    "watermark_position": "bottom-right",
    "watermark_color": "#ffffff",
    "watermark_image_path": "",
    "watermark_image_scale": 20,
    "watermark_replace": True,
    "watermark_backup": True,
    "watermark_output_folder": "",
    "watermark_presets": [],
    # AI Rename
    "ai_prompt": (
        "\u8bf7\u5206\u6790\u4ee5\u4e0b\u56fe\u7247\u6587\u4ef6\u540d\u5217\u8868\uff0c"
        "\u4e3a\u6bcf\u4e2a\u6587\u4ef6\u751f\u6210\u4e00\u4e2a\u7b80\u6d01\u89c4\u8303"
        "\u7684\u82f1\u6587\u6587\u4ef6\u540d\uff08\u542b\u6269\u5c55\u540d\uff09\uff0c"
        "\u683c\u5f0f\u5982\uff1aplayer_name-position-country.jpg\u3002"
        "\u53ea\u8fd4\u56deJSON\u6570\u7ec4\uff0c\u4e0d\u8981\u5176\u4ed6\u5185\u5bb9\u3002"
    ),
    # Trim
    "trim_padding": 4,
    "trim_replace": True,
    "trim_backup": True,
    "trim_output_folder": "",
    # Normalize
    "normalize_alpha_threshold": 28,
    "normalize_target_height": 280,
    "normalize_padding": 6,
    "normalize_replace": True,
    "normalize_backup": True,
    "normalize_output_folder": "",
    # EXIF
    "exif_mode": "keep",  # keep | strip | orientation_only
    # Recursive scan
    "recursive_scan": False,
}


def load_config() -> Dict[str, Any]:
    """Load config from disk, merging with defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config.update(data)
        except (json.JSONDecodeError, OSError) as exc:
            get_logger().warning("Failed to load config: %s", exc)
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Persist config to disk."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Filter out non-serializable values
        clean = {k: v for k, v in config.items() if _is_json_serializable(v)}
        CONFIG_FILE.write_text(
            json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        get_logger().error("Failed to save config: %s", exc)


def _is_json_serializable(value: Any) -> bool:
    if isinstance(value, (str, int, float, bool, type(None))):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_json_serializable(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_json_serializable(v) for k, v in value.items())
    return False
