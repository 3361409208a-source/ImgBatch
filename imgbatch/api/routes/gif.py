# -*- coding: utf-8 -*-
"""GIF metadata and preview routes."""

from fastapi import APIRouter

from ..schemas import GifInfoRequest, GifInfoResponse
from imgbatch.core.gif import is_gif_path, probe_gif

router = APIRouter()


@router.post("/info", response_model=GifInfoResponse)
async def gif_info(req: GifInfoRequest) -> GifInfoResponse:
    items = []
    for path in req.paths:
        if not is_gif_path(path):
            continue
        try:
            items.append(probe_gif(path))
        except Exception:
            continue
    return GifInfoResponse(items=items)
