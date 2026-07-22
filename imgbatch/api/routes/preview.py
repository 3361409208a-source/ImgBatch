# -*- coding: utf-8 -*-
"""Thumbnail preview route — image raster or document text/first page."""

import base64
import io

from fastapi import APIRouter
from PIL import Image, UnidentifiedImageError

from imgbatch.core.doc_convert import is_document
from imgbatch.core.doc_preview import preview_document

from ..schemas import PreviewRequest, PreviewResponse

router = APIRouter()


def _image_thumb(path: str, max_dim: int) -> PreviewResponse:
    with Image.open(path) as img:
        img = img.convert("RGBA")
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.LANCZOS,
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        return PreviewResponse(
            data_url=f"data:image/png;base64,{data}",
            kind="image",
        )


@router.post("/thumb")
async def thumb(req: PreviewRequest) -> PreviewResponse:
    max_dim = req.max_size or 300
    try:
        return _image_thumb(req.path, max_dim)
    except (UnidentifiedImageError, OSError):
        pass

    if is_document(req.path):
        result = preview_document(req.path, max_dim)
        return PreviewResponse(**result)

    return PreviewResponse()
