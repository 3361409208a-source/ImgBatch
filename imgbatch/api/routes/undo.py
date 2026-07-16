# -*- coding: utf-8 -*-
"""Undo route — pop last operation and reverse it."""

from fastapi import APIRouter

from ..deps import get_history
from ..schemas import UndoResponse

router = APIRouter()


@router.post("")
async def undo() -> UndoResponse:
    """Pop the most recent operation and undo it."""
    history = get_history()
    record = history.pop()
    if not record:
        return UndoResponse(success=False, message="no_operation_to_undo")

    from imgbatch.history import undo_operation
    result = undo_operation(record)
    return UndoResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
    )


@router.get("")
async def undo_status() -> dict:
    """Check if undo is available."""
    history = get_history()
    return {"can_undo": history.can_undo}
