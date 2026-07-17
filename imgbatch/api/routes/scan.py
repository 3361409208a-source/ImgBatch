# -*- coding: utf-8 -*-
"""Folder scan and file filter routes."""

from fastapi import APIRouter

from imgbatch.core.common import (
    SIZE_PRESETS,
    filter_files,
    parse_kb_to_bytes,
    probe_files,
    scan_folder,
    parse_dimensions,
)

from ..schemas import (
    AiRenameParseRequest,
    AiRenameParseResponse,
    CompressEstimateRequest,
    CompressEstimateResponse,
    FileInfo,
    FilterRequest,
    FilterResponse,
    ProbeRequest,
    RenamePreviewRequest,
    RenamePreviewResponse,
    ScanRequest,
    ScanResponse,
)

router = APIRouter()


@router.post("/scan")
async def scan(req: ScanRequest) -> ScanResponse:
    files: list = []
    if req.kind in ("image", "all"):
        files.extend(scan_folder(req.folder, recursive=req.recursive))
    if req.kind in ("document", "all"):
        from imgbatch.core.doc_convert import scan_documents
        files.extend(scan_documents(req.folder, recursive=req.recursive))
    if req.kind == "all":
        seen = set()
        deduped = []
        for item in files:
            key = item["path"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        files = deduped
    return ScanResponse(files=[FileInfo(**f) for f in files])


@router.post("/probe")
async def probe(req: ProbeRequest) -> ScanResponse:
    files: list = []
    if req.kind in ("image", "all"):
        files.extend(probe_files(req.paths))
    if req.kind in ("document", "all"):
        from imgbatch.core.doc_convert import probe_documents
        files.extend(probe_documents(req.paths))
    if req.kind == "all":
        seen = set()
        deduped = []
        for item in files:
            key = item["path"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        files = deduped
    return ScanResponse(files=[FileInfo(**f) for f in files])


@router.post("/filter")
async def filter(req: FilterRequest) -> FilterResponse:
    files = [f.model_dump() for f in req.files]

    # Build format set
    fmt = (req.format or "ALL").upper()
    formats = None
    if fmt != "ALL":
        formats = {fmt}

    # Size bounds from preset
    preset_key = req.size_preset or "all"
    min_b, max_b = SIZE_PRESETS.get(preset_key, (None, None))

    # Override with custom values
    if req.size_min_kb or req.size_max_kb or preset_key == "custom":
        custom_min = parse_kb_to_bytes(req.size_min_kb)
        custom_max = parse_kb_to_bytes(req.size_max_kb)
        min_b = custom_min if custom_min is not None else min_b
        max_b = custom_max if custom_max is not None else max_b

    # Dimension bounds
    min_w, min_h = None, None
    if req.min_width:
        try:
            min_w = int(req.min_width)
        except ValueError:
            pass
    if req.min_height:
        try:
            min_h = int(req.min_height)
        except ValueError:
            pass

    filtered = filter_files(
        files,
        name_query=req.name_query,
        formats=formats,
        min_size=min_b,
        max_size=max_b,
        min_width=min_w,
        min_height=min_h,
    )
    return FilterResponse(files=[FileInfo(**f) for f in filtered])


@router.post("/compress/estimate")
async def compress_estimate(req: CompressEstimateRequest) -> CompressEstimateResponse:
    from imgbatch.core.compress import estimate_compressed_size

    file_data = [f.model_dump() for f in req.files]
    before, after = estimate_compressed_size(file_data, req.quality, req.resize_pct)
    return CompressEstimateResponse(total_before=before, total_after=after)


@router.post("/rename/preview")
async def rename_preview(req: RenamePreviewRequest) -> RenamePreviewResponse:
    from imgbatch.core.rename import generate_rename_map

    file_data = [f.model_dump() for f in req.files]
    mapping = generate_rename_map(
        file_data,
        mode=req.mode,
        prefix=req.prefix,
        suffix=req.suffix,
        find=req.find,
        replace=req.replace,
        seq_template=req.seq_template,
        seq_start=req.seq_start,
        seq_digits=req.seq_digits,
        lowercase=req.lowercase,
        uppercase=req.uppercase,
    )
    return RenamePreviewResponse(mapping=mapping)


@router.post("/rename/ai-parse")
async def ai_rename_parse(req: AiRenameParseRequest) -> AiRenameParseResponse:
    from imgbatch.core.ai_rename import parse_ai_rename_response

    if not req.content.strip():
        return AiRenameParseResponse(mapping={}, errors=["Empty content"])
    if not req.file_list:
        return AiRenameParseResponse(mapping={}, errors=["Empty file list"])

    mapping = parse_ai_rename_response(req.content, req.file_list)
    if not any(orig != new for orig, new in mapping.items()):
        return AiRenameParseResponse(
            mapping=mapping,
            errors=["Could not parse any rename suggestions from the pasted text"],
        )
    return AiRenameParseResponse(mapping=mapping)
