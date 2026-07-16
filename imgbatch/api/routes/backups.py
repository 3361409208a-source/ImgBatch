# -*- coding: utf-8 -*-
"""Backup management routes."""

from fastapi import APIRouter

from ..schemas import BackupClearRequest, BackupRestoreRequest

router = APIRouter()


@router.get("")
async def list_backups(folder: str = "") -> dict:
    """List backup directories for a given folder."""
    from imgbatch.infra.backup import find_backups
    backups = find_backups(folder) if folder else []
    return {"backups": backups}


@router.post("/restore")
async def restore_backup(req: BackupRestoreRequest) -> dict:
    from imgbatch.infra.backup import do_restore
    count = do_restore(req.backup_dir, req.folder)
    return {"restored": count}


@router.delete("")
async def clear_backups(req: BackupClearRequest) -> dict:
    from imgbatch.infra.backup import do_clear_backups
    count = do_clear_backups(req.backups)
    return {"deleted": count}
