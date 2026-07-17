# -*- coding: utf-8 -*-
"""Task creation, SSE events, and cancellation routes."""

import asyncio
import json
import os
import queue

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from ..deps import get_task_manager
from ..schemas import TaskCreateRequest, TaskCreateResponse, TaskDoneEvent
from ..tasks import task_manager

router = APIRouter()


# ── Backup helper ────────────────────────────────────────────────────────

def _backup_fn(folder, file_list):
    """Import backup function lazily."""
    from imgbatch.infra.backup import do_backup
    return do_backup(folder, file_list)


# ── Task dispatchers ─────────────────────────────────────────────────────

def _dispatch_compress(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.compress import run_compress_batch
    options = params.get("options", {})
    do_backup = params.get("do_backup", False)
    replace = params.get("replace", True)
    out = params.get("out")
    backup_fn = _backup_fn if do_backup else None
    return run_compress_batch(
        state, folder, file_list,
        quality=params.get("quality", 75),
        resize_pct=params.get("resize_pct", 100),
        do_backup=do_backup,
        replace=replace,
        out=out,
        exif_mode=params.get("exif_mode", "keep"),
        options=options,
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_convert(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.convert import run_convert_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    return run_convert_batch(
        state, folder, file_list,
        target_fmt=params.get("target_fmt", ".png"),
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        quality=params.get("quality", 85),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_rename(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.rename import (
        generate_rename_map, run_rename_batch, ConflictResolution,
    )
    # Build file_data dicts for generate_rename_map
    file_data = [{"name": n} for n in file_list]
    mapping = generate_rename_map(
        file_data,
        mode=params.get("mode", "prefix"),
        prefix=params.get("prefix", ""),
        suffix=params.get("suffix", ""),
        find=params.get("find", ""),
        replace=params.get("replace", ""),
        seq_template=params.get("seq_template", "photo_{num}"),
        seq_start=params.get("seq_start", 1),
        seq_digits=params.get("seq_digits", 3),
        lowercase=params.get("lowercase", False),
        uppercase=params.get("uppercase", False),
    )
    if not mapping:
        return {"errors": [], "renamed": 0, "skipped": 0, "cancelled": False}
    return run_rename_batch(
        state, folder, mapping,
        conflict_resolution=ConflictResolution.AUTO_NUMBER,
        on_progress=on_progress,
    )


def _dispatch_watermark(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.watermark import run_watermark_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    wm_params = params.get("params", params)
    # Normalise opacity: percentage 0-100 → 0.0-1.0
    if "opacity" in wm_params:
        op = wm_params["opacity"]
        if isinstance(op, (int, float)) and op > 1.0:
            wm_params["opacity"] = op / 100.0
    return run_watermark_batch(
        state, folder, file_list,
        params=wm_params,
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_ai_rename(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.ai_rename import run_ai_rename
    return run_ai_rename(
        state,
        api_key=params.get("api_key", ""),
        file_names=file_list,
        prompt=params.get("prompt", ""),
        on_progress=on_progress,
    )


def _dispatch_ai_apply(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.ai_rename import apply_ai_rename
    return apply_ai_rename(
        state, folder,
        mapping=params.get("mapping", {}),
        on_progress=on_progress,
    )


def _dispatch_trim(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.trim import run_trim_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    return run_trim_batch(
        state, folder, file_list,
        padding=params.get("padding", 4),
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_inspect(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.inspect import run_inspect_batch
    # Only PNG files; pass full FileInfo dicts
    png_list = [{"name": n, "path": os.path.join(folder, n)} for n in file_list
                if n.lower().endswith(".png")]
    return run_inspect_batch(
        state, png_list,
        on_progress=on_progress,
    )


def _dispatch_normalize(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.normalize import run_normalize_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    return run_normalize_batch(
        state, folder, file_list,
        alpha_threshold=params.get("alpha_threshold", 28),
        target_height=params.get("target_height", 280),
        padding=params.get("padding", 6),
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_spritesheet(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.spritesheet import run_spritesheet_build
    image_paths = [os.path.join(folder, n) for n in file_list]
    return run_spritesheet_build(
        state,
        image_paths=image_paths,
        output_path=params.get("output", ""),
        layout=params.get("layout", "auto"),
        spacing=params.get("spacing", 2),
        trim=params.get("trim", True),
        trim_padding=params.get("trim_padding", 2),
        alpha_threshold=params.get("alpha_threshold", 28),
        columns=params.get("columns", 0),
        max_width=params.get("max_width", 0),
        power_of_two=params.get("power_of_two", False),
        export_json=params.get("export_json", True),
        on_progress=on_progress,
    )


def _dispatch_gif_edit(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.gif import run_gif_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    return run_gif_batch(
        state, folder, file_list,
        mode=params.get("mode", "optimize"),
        params=params,
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


def _dispatch_doc_convert(state, folder, file_list, params, on_progress=None):
    from imgbatch.core.doc_convert import run_doc_convert_batch
    do_backup = params.get("do_backup", False)
    backup_fn = _backup_fn if do_backup else None
    return run_doc_convert_batch(
        state, folder, file_list,
        target_fmt=params.get("target_fmt", ".pdf"),
        do_backup=do_backup,
        replace=params.get("replace", True),
        out=params.get("out"),
        dpi=params.get("dpi", 150),
        page_mode=params.get("page_mode", "all"),
        quality=params.get("quality", 85),
        on_progress=on_progress,
        backup_fn=backup_fn,
    )


DISPATCHERS = {
    "compress": _dispatch_compress,
    "convert": _dispatch_convert,
    "doc_convert": _dispatch_doc_convert,
    "rename": _dispatch_rename,
    "watermark": _dispatch_watermark,
    "ai_rename": _dispatch_ai_rename,
    "ai_apply": _dispatch_ai_apply,
    "trim": _dispatch_trim,
    "inspect": _dispatch_inspect,
    "normalize": _dispatch_normalize,
    "spritesheet": _dispatch_spritesheet,
    "gif_edit": _dispatch_gif_edit,
}


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("")
async def create_task(req: TaskCreateRequest) -> TaskCreateResponse:
    """Create a new batch task."""
    dispatcher = DISPATCHERS.get(req.type)
    if not dispatcher:
        raise HTTPException(status_code=400, detail=f"Unknown task type: {req.type}")

    params = req.params or {}
    try:
        task_id = await task_manager.start(
            dispatcher,
            req.folder,
            req.file_list,
            params,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return TaskCreateResponse(task_id=task_id)


@router.get("/{task_id}/events")
async def task_events(task_id: str):
    """SSE stream for task progress and completion."""
    async def gen():
        record = task_manager.get(task_id)
        if not record:
            yield {"event": "error", "data": json.dumps({"error": "not_found"})}
            return
        while True:
            # Poll the thread-safe queue without blocking the event loop
            try:
                msg = await asyncio.to_thread(record.queue.get, timeout=1.0)
            except Exception:
                # queue.Empty on timeout — check if task is done
                if record.done and record.queue.empty():
                    yield {"event": "done", "data": json.dumps({
                        "type": "done",
                        "status": "error" if record.error else "done",
                        "result": record.result or {"error": record.error or "unknown"},
                    })}
                    break
                continue
            yield {"event": msg["type"], "data": json.dumps(msg)}
            if msg["type"] == "done":
                break

    return EventSourceResponse(gen())


@router.get("/{task_id}")
async def get_task(task_id: str) -> dict:
    record = task_manager.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="task_not_found")
    return {
        "task_id": record.id,
        "done": record.done,
        "result": record.result,
        "error": record.error,
    }


@router.delete("/{task_id}")
async def cancel_task(task_id: str) -> dict:
    ok = task_manager.cancel(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="task_not_found_or_done")
    return {"ok": True}
