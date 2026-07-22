#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Document preview — text snippet or first-page raster."""

from __future__ import annotations

import base64
import io
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from PIL import Image, UnidentifiedImageError

from .doc_convert import DOCUMENT_EXT, RASTER_EXT, _pymupdf_available

_TEXT_EXT = {'.txt', '.md', '.markdown', '.html', '.htm', '.csv', '.rtf'}
_MAX_TEXT_CHARS = 12000
_W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _truncate(text: str) -> str:
    text = text.strip()
    if len(text) <= _MAX_TEXT_CHARS:
        return text
    return text[:_MAX_TEXT_CHARS] + '\n\n…'


def _image_data_url(img: Image.Image, max_dim: int) -> str:
    img = img.convert('RGBA')
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.LANCZOS,
        )
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    data = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/png;base64,{data}'


def _preview_image(path: str, max_size: int) -> Dict[str, str]:
    with Image.open(path) as img:
        return {
            'kind': 'image',
            'data_url': _image_data_url(img, max_size),
            'text': '',
        }


def _preview_text_file(path: str) -> Dict[str, str]:
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    return {'kind': 'text', 'data_url': '', 'text': _truncate(text)}


def _preview_pdf(path: str, max_size: int) -> Dict[str, str]:
    if not _pymupdf_available():
        return {'kind': 'text', 'data_url': '', 'text': _truncate(_pdf_text_fallback(path))}

    import fitz

    doc = fitz.open(path)
    try:
        if doc.page_count == 0:
            return {'kind': 'none', 'data_url': '', 'text': ''}

        page = doc.load_page(0)
        rect = page.rect
        scale = max_size / max(rect.width, rect.height, 1)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        return {
            'kind': 'image',
            'data_url': _image_data_url(img, max_size),
            'text': '',
        }
    finally:
        doc.close()


def _pdf_text_fallback(path: str) -> str:
    if not _pymupdf_available():
        return '（未安装 PyMuPDF，无法预览 PDF）'
    import fitz

    doc = fitz.open(path)
    try:
        chunks = [page.get_text() for page in doc]
        return '\n\n'.join(chunks)
    finally:
        doc.close()


def _preview_docx_text(path: str) -> Dict[str, str]:
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read('word/document.xml')
        root = ET.fromstring(xml)
        parts = [node.text for node in root.iter(f'{_W_NS}t') if node.text]
        text = ''.join(parts)
        if text.strip():
            return {'kind': 'text', 'data_url': '', 'text': _truncate(text)}
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError):
        pass
    return {'kind': 'text', 'data_url': '', 'text': '（无法读取 Word 文档内容）'}


def _preview_xlsx_text(path: str) -> Dict[str, str]:
    try:
        import openpyxl
    except ImportError:
        return {'kind': 'text', 'data_url': '', 'text': '（未安装 openpyxl，无法预览 Excel）'}

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        lines: list[str] = []
        for sheet in wb.worksheets[:3]:
            lines.append(f'[{sheet.title}]')
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                if row_idx >= 30:
                    lines.append('…')
                    break
                cells = [str(c) if c is not None else '' for c in row]
                if any(cells):
                    lines.append('\t'.join(cells))
        wb.close()
        return {'kind': 'text', 'data_url': '', 'text': _truncate('\n'.join(lines))}
    except Exception:
        return {'kind': 'text', 'data_url': '', 'text': '（无法读取 Excel 内容）'}


def preview_document(path: str, max_size: int = 300) -> Dict[str, str]:
    """Preview a document path. Returns kind, data_url, text."""
    p = Path(path)
    if not p.is_file():
        return {'kind': 'none', 'data_url': '', 'text': ''}

    ext = p.suffix.lower()
    if ext not in DOCUMENT_EXT:
        return {'kind': 'none', 'data_url': '', 'text': ''}

    try:
        if ext in RASTER_EXT:
            return _preview_image(path, max_size)
        if ext in _TEXT_EXT:
            return _preview_text_file(path)
        if ext == '.pdf':
            return _preview_pdf(path, max_size)
        if ext == '.docx':
            return _preview_docx_text(path)
        if ext in {'.xls', '.xlsx'}:
            return _preview_xlsx_text(path)
        if ext in {'.doc', '.ppt', '.pptx', '.odt', '.ods', '.odp'}:
            return {
                'kind': 'text',
                'data_url': '',
                'text': f'（{ext.upper()} 格式暂不支持内嵌预览，可转换后查看）',
            }
    except (OSError, UnidentifiedImageError, ValueError):
        return {'kind': 'none', 'data_url': '', 'text': ''}

    return {'kind': 'none', 'data_url': '', 'text': ''}
