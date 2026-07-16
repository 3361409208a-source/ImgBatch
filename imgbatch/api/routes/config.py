# -*- coding: utf-8 -*-
"""Config read / write routes."""

from typing import Any, Dict

from fastapi import APIRouter

from ..deps import get_config, save_config_dict

router = APIRouter()


@router.get("")
async def get_config_route() -> Dict[str, Any]:
    return get_config()


@router.put("")
async def save_config_route(config: Dict[str, Any]) -> dict:
    save_config_dict(config)
    return {"ok": True}
