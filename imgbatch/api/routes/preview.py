# -*- coding: utf-8 -*-
"""Thumbnail preview route — returns a data-URL for a given image."""

import base64
import io

from fastapi import APIRouter
from PIL import Image

from ..schemas import PreviewRequest, PreviewResponse

router = APIRouter()


@router.post("/thumb")
async def thumb(req: PreviewRequest) -> PreviewResponse:
    try:
        with Image.open(req.path) as img:
            img = img.convert("RGBA")
            max_dim = req.max_size or 300
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
            return PreviewResponse(data_url=f"data:image/png;base64,{data}")
    except Exception as exc:
        return PreviewResponse(data_url="")
