# -*- coding: utf-8 -*-
"""Extension pack routes — optional user-installed capabilities."""

from fastapi import APIRouter, HTTPException

from imgbatch.core.extensions import (
    get_extensions_catalog,
    get_install_status,
    set_extension_path,
    start_install_extension,
)

from ..schemas import ExtensionCatalogResponse, ExtensionItem, ExtensionPathRequest

router = APIRouter()


@router.get("/extensions", response_model=ExtensionCatalogResponse)
async def list_extensions() -> ExtensionCatalogResponse:
    catalog = get_extensions_catalog()
    return ExtensionCatalogResponse(
        extensions=[ExtensionItem(**item) for item in catalog['extensions']],
        locked_count=catalog['locked_count'],
        unlocked_count=catalog['unlocked_count'],
        total_count=catalog['total_count'],
        install=catalog.get('install'),
    )


@router.post("/extensions/{ext_id}/install")
async def install_extension(ext_id: str) -> dict:
    try:
        return start_install_extension(ext_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/extensions/install-status")
async def extension_install_status() -> dict:
    return get_install_status()


@router.post("/extensions/{ext_id}/path")
async def configure_extension_path(ext_id: str, req: ExtensionPathRequest) -> dict:
    try:
        return set_extension_path(ext_id, req.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
