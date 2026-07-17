# -*- coding: utf-8 -*-
"""Document conversion metadata routes."""

from fastapi import APIRouter

from imgbatch.core.doc_convert import get_doc_catalog

from ..schemas import DocCatalogResponse, DocPreset, DocTarget

router = APIRouter()


@router.get("/doc/formats", response_model=DocCatalogResponse)
async def doc_formats() -> DocCatalogResponse:
    catalog = get_doc_catalog()
    return DocCatalogResponse(
        targets=[DocTarget(**t) for t in catalog['targets']],
        presets=[DocPreset(**p) for p in catalog['presets']],
        features=catalog['features'],
        inputs=catalog['inputs'],
    )
