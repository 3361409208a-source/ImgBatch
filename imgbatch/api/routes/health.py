# -*- coding: utf-8 -*-
"""Health check endpoint."""

from fastapi import APIRouter

from ..schemas import FileInfo

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Return ok so Tauri / frontend can verify the sidecar is alive."""
    return {"ok": True}
