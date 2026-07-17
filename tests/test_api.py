# -*- coding: utf-8 -*-
"""Tests for the ImgBatch HTTP API layer.

Covers: health, scan, filter, compress estimate, rename preview,
task creation + completion, task cancellation.
"""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from imgbatch.api.main import app
    return TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_convert_formats(client):
    resp = client.get("/convert/formats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["targets"]
    assert data["presets"]
    assert "heic_input" in data["features"]


def test_doc_formats(client):
    resp = client.get("/doc/formats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["targets"]
    assert data["presets"]
    assert "libreoffice" in data["features"]
    assert ".pdf" in data["inputs"]


def test_scan_documents(client, tmp_path):
    (tmp_path / "readme.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n")
    resp = client.post("/scan", json={
        "folder": str(tmp_path),
        "recursive": False,
        "kind": "document",
    })
    assert resp.status_code == 200
    names = {f["name"] for f in resp.json()["files"]}
    assert names == {"readme.txt"}


def test_extensions(client):
    resp = client.get("/extensions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 1
    assert "extensions" in data
    lo = next(x for x in data["extensions"] if x["id"] == "libreoffice")
    assert lo["download_url"]
    assert lo["unlocks"]


# ── Scan ──────────────────────────────────────────────────────────────────

def test_scan_empty_folder(client, tmp_path):
    resp = client.post("/scan", json={"folder": str(tmp_path), "recursive": False})
    assert resp.status_code == 200
    assert resp.json()["files"] == []


def test_scan_with_images(client, tmp_image_dir):
    resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    assert resp.status_code == 200
    files = resp.json()["files"]
    assert len(files) == 5  # 2 jpg + 2 png + 1 webp from conftest
    names = [f["name"] for f in files]
    assert "test1.jpg" in names
    assert "test3.png" in names


def test_probe_selected_files(client, tmp_image_dir):
    p1 = str(Path(tmp_image_dir) / "test1.jpg")
    p2 = str(Path(tmp_image_dir) / "test3.png")
    resp = client.post("/probe", json={"paths": [p1, p2]})
    assert resp.status_code == 200
    files = resp.json()["files"]
    assert len(files) == 2
    names = {f["name"] for f in files}
    assert names == {"test1.jpg", "test3.png"}


# ── Filter ────────────────────────────────────────────────────────────────

def test_filter_by_format(client, tmp_image_dir):
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]

    # Filter for PNG only
    resp = client.post("/filter", json={"files": files, "format": "PNG"})
    assert resp.status_code == 200
    filtered = resp.json()["files"]
    assert all(f["format"].upper() in ("PNG",) for f in filtered)
    assert len(filtered) == 2


def test_filter_by_name(client, tmp_image_dir):
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]

    resp = client.post("/filter", json={"files": files, "name_query": "test1"})
    assert resp.status_code == 200
    filtered = resp.json()["files"]
    assert len(filtered) == 1
    assert "test1" in filtered[0]["name"]


# ── Compress estimate ─────────────────────────────────────────────────────

def test_compress_estimate(client, tmp_image_dir):
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]

    resp = client.post("/compress/estimate", json={
        "files": files,
        "quality": 50,
        "resize_pct": 50,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_before"] > 0
    assert data["total_after"] >= 0


# ── Rename preview ────────────────────────────────────────────────────────

def test_rename_preview(client, tmp_image_dir):
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]

    resp = client.post("/rename/preview", json={
        "files": files,
        "mode": "prefix",
        "prefix": "img_",
    })
    assert resp.status_code == 200
    mapping = resp.json()["mapping"]
    assert len(mapping) > 0
    # Each new name should start with "img_"
    for new_name in mapping.values():
        assert new_name.startswith("img_")


# ── Config ────────────────────────────────────────────────────────────────

def test_config_get_and_put(client):
    resp = client.get("/config")
    assert resp.status_code == 200
    cfg = resp.json()
    assert "language" in cfg

    # Save modified config
    cfg["language"] = "en"
    resp = client.put("/config", json=cfg)
    assert resp.status_code == 200

    # Read back
    resp = client.get("/config")
    assert resp.json()["language"] == "en"

    # Restore to zh
    cfg["language"] = "zh"
    client.put("/config", json=cfg)


# ── Tasks ──────────────────────────────────────────────────────────────────

def test_compress_task(client, tmp_image_dir):
    """Create a compress task and wait for it to complete."""
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]
    file_list = [f["name"] for f in files]

    resp = client.post("/tasks", json={
        "type": "compress",
        "folder": tmp_image_dir,
        "file_list": file_list,
        "params": {
            "quality": 50,
            "resize_pct": 100,
            "do_backup": False,
            "replace": True,
            "exif_mode": "keep",
        },
    })
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    # Poll for completion
    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/tasks/{task_id}")
        data = status.json()
        if data["done"]:
            assert data["error"] is None
            assert data["result"] is not None
            assert "total_before" in data["result"]
            break
    else:
        pytest.fail("Task did not complete within 15 seconds")


def _slow_dispatch(state, folder, file_list, params, on_progress=None):
    """Mock dispatcher that sleeps so the task stays running long enough to cancel."""
    for i in range(100):
        if state.cancelled:
            break
        if on_progress:
            on_progress(i, f"step {i}")
        time.sleep(0.01)
    return {"errors": [], "cancelled": state.cancelled}


def test_task_cancel(client, tmp_image_dir):
    """Create a task and cancel it."""
    with patch.dict("imgbatch.api.routes.tasks.DISPATCHERS", {"compress": _slow_dispatch}):
        resp = client.post("/tasks", json={
            "type": "compress",
            "folder": tmp_image_dir,
            "file_list": ["dummy.png"],
            "params": {"quality": 50, "do_backup": False, "replace": True},
        })
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        # Cancel while task is still running
        cancel_resp = client.delete(f"/tasks/{task_id}")
        assert cancel_resp.status_code == 200

        # Wait for the task to notice cancellation and finish
        for _ in range(30):
            time.sleep(0.2)
            status = client.get(f"/tasks/{task_id}")
            if status.json()["done"]:
                break
        else:
            pytest.fail("Task did not complete after cancellation")

        status = client.get(f"/tasks/{task_id}")
        data = status.json()
        assert data["done"] is True


def test_duplicate_task_rejected(client, tmp_image_dir):
    """A second task should be rejected while the first is running."""
    with patch.dict("imgbatch.api.routes.tasks.DISPATCHERS", {"compress": _slow_dispatch}):
        # Start first task
        resp = client.post("/tasks", json={
            "type": "compress",
            "folder": tmp_image_dir,
            "file_list": ["dummy.png"],
            "params": {"quality": 50, "do_backup": False, "replace": True},
        })
        assert resp.status_code == 200
        task_id_1 = resp.json()["task_id"]

        # Try to start a second immediately — should be rejected
        resp2 = client.post("/tasks", json={
            "type": "compress",
            "folder": tmp_image_dir,
            "file_list": ["dummy.png"],
            "params": {"quality": 50, "do_backup": False, "replace": True},
        })
        assert resp2.status_code == 409  # Conflict — task already running

        # Cancel the first task so it doesn't block other tests
        client.delete(f"/tasks/{task_id_1}")
        for _ in range(30):
            time.sleep(0.2)
            status = client.get(f"/tasks/{task_id_1}")
            if status.json()["done"]:
                break


# ── Preview ───────────────────────────────────────────────────────────────

def test_preview_thumb(client, tmp_image_dir):
    scan_resp = client.post("/scan", json={"folder": tmp_image_dir, "recursive": False})
    files = scan_resp.json()["files"]
    first_file = files[0]

    resp = client.post("/preview/thumb", json={"path": first_file["path"], "max_size": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_url"].startswith("data:image/png;base64,")


# ── Undo status ───────────────────────────────────────────────────────────

def test_undo_status(client):
    resp = client.get("/undo")
    assert resp.status_code == 200
    assert "can_undo" in resp.json()
