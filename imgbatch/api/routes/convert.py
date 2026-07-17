# -*- coding: utf-8 -*-
"""Format conversion metadata routes."""

from fastapi import APIRouter

from imgbatch.core.common import get_convert_catalog

from ..schemas import ConvertCatalogResponse, ConvertPreset, ConvertTarget

router = APIRouter()


@router.get("/convert/formats", response_model=ConvertCatalogResponse)
async def convert_formats() -> ConvertCatalogResponse:
    catalog = get_convert_catalog()
    return ConvertCatalogResponse(
        targets=[ConvertTarget(**t) for t in catalog['targets']],
        presets=[ConvertPreset(**p) for p in catalog['presets']],
        features=catalog['features'],
    )
