# -*- coding: utf-8 -*-
"""Pydantic models for the ImgBatch HTTP API.

JSON field names here **must not** be renamed — the React frontend
will mirror these names exactly.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── File info (matches core.common.scan_folder return) ──────────────────

class FileInfo(BaseModel):
    name: str = Field(..., description="Relative path, e.g. colorful/promo/a.png")
    path: str = Field(..., description="Absolute path")
    size: int
    size_str: str
    dimensions: str = Field(..., description='"1920x1080" or "?"')
    format: str


# ── Scan ─────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    folder: str
    recursive: bool = False


class ScanResponse(BaseModel):
    files: List[FileInfo]


# ── Filter ───────────────────────────────────────────────────────────────

class FilterRequest(BaseModel):
    files: List[FileInfo]
    name_query: str = ""
    format: str = "ALL"           # ALL | PNG | JPEG | ...
    size_preset: str = "all"     # corresponds to SIZE_PRESETS key
    size_min_kb: str = ""
    size_max_kb: str = ""
    min_width: str = ""
    min_height: str = ""


class FilterResponse(BaseModel):
    files: List[FileInfo]


# ── Compress estimate ─────────────────────────────────────────────────────

class CompressEstimateRequest(BaseModel):
    files: List[FileInfo]
    quality: int = 75
    resize_pct: int = 100


class CompressEstimateResponse(BaseModel):
    total_before: int
    total_after: int


# ── Rename preview ───────────────────────────────────────────────────────

class RenamePreviewRequest(BaseModel):
    files: List[FileInfo]
    mode: str = "prefix"
    prefix: str = ""
    suffix: str = ""
    find: str = ""
    replace: str = ""
    seq_template: str = "photo_{num}"
    seq_start: int = 1
    seq_digits: int = 3
    lowercase: bool = False
    uppercase: bool = False


class RenamePreviewResponse(BaseModel):
    mapping: Dict[str, str]


# ── Task creation ─────────────────────────────────────────────────────────

TaskType = Literal[
    "compress", "convert", "rename", "watermark",
    "ai_rename", "ai_apply", "trim", "inspect",
    "normalize", "spritesheet",
]


class TaskCreateRequest(BaseModel):
    type: TaskType
    folder: str
    file_list: List[str] = Field(default_factory=list, description="Relative path names")
    params: Dict[str, Any] = {}


class TaskCreateResponse(BaseModel):
    task_id: str


# ── SSE events ───────────────────────────────────────────────────────────

class TaskProgressEvent(BaseModel):
    pct: float
    message: str


class TaskDoneEvent(BaseModel):
    status: Literal["done", "error", "cancelled"]
    result: Dict[str, Any]


# ── Config ────────────────────────────────────────────────────────────────

class ConfigUpdate(BaseModel):
    config: Dict[str, Any]


# ── Preview ──────────────────────────────────────────────────────────────

class PreviewRequest(BaseModel):
    path: str
    max_size: int = 300  # max dimension in pixels


class PreviewResponse(BaseModel):
    data_url: str = Field(..., description='data:image/png;base64,...')


# ── Backups ───────────────────────────────────────────────────────────────

class BackupRestoreRequest(BaseModel):
    backup_dir: str
    folder: str


class BackupClearRequest(BaseModel):
    backups: List[str]


# ── Undo ──────────────────────────────────────────────────────────────────

class UndoResponse(BaseModel):
    success: bool
    message: str
