#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Document format conversion — Office, PDF, text, CSV, etc."""

from __future__ import annotations

import csv
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from ..infra.logger import get_logger
from .extensions import find_libreoffice, is_libreoffice_installed

DOCUMENT_EXT: Set[str] = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.rtf', '.txt', '.md', '.markdown', '.html', '.htm', '.csv',
}

OFFICE_INPUT_EXT: Set[str] = {
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.rtf',
}

LO_CONVERT_EXT: Set[str] = {
    '.pdf', '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
    '.html', '.htm', '.txt', '.csv', '.png', '.jpg', '.jpeg',
}

RASTER_EXT: Set[str] = {'.png', '.jpg', '.jpeg', '.webp'}

DOC_CONVERT_PRESETS = [
    {
        'id': 'office_pdf',
        'label': '办公→PDF',
        'target_fmt': '.pdf',
        'hint': 'Word / Excel / PPT / ODF 转 PDF',
    },
    {
        'id': 'pdf_jpg',
        'label': 'PDF→JPG',
        'target_fmt': '.jpg',
        'hint': 'PDF 每页导出为 JPG 图片',
    },
    {
        'id': 'pdf_png',
        'label': 'PDF→PNG',
        'target_fmt': '.png',
        'hint': 'PDF 每页导出为 PNG 图片',
    },
    {
        'id': 'pdf_txt',
        'label': 'PDF→TXT',
        'target_fmt': '.txt',
        'hint': '提取 PDF 纯文本',
    },
    {
        'id': 'pdf_docx',
        'label': 'PDF→Word',
        'target_fmt': '.docx',
        'hint': 'PDF 转为 DOCX（需 LibreOffice）',
    },
    {
        'id': 'csv_xlsx',
        'label': 'CSV→Excel',
        'target_fmt': '.xlsx',
        'hint': 'CSV 转为 XLSX 工作簿',
    },
    {
        'id': 'txt_pdf',
        'label': 'TXT→PDF',
        'target_fmt': '.pdf',
        'hint': '纯文本转为 PDF',
    },
    {
        'id': 'md_pdf',
        'label': 'MD→PDF',
        'target_fmt': '.pdf',
        'hint': 'Markdown 渲染后导出 PDF',
    },
    {
        'id': 'md_html',
        'label': 'MD→HTML',
        'target_fmt': '.html',
        'hint': 'Markdown 转为网页 HTML',
    },
    {
        'id': 'md_docx',
        'label': 'MD→Word',
        'target_fmt': '.docx',
        'hint': 'Markdown 转为 DOCX（需 LibreOffice）',
    },
    {
        'id': 'html_md',
        'label': 'HTML→MD',
        'target_fmt': '.md',
        'hint': 'HTML 转为 Markdown 文本',
    },
    {
        'id': 'html_pdf',
        'label': 'HTML→PDF',
        'target_fmt': '.pdf',
        'hint': '网页 HTML 导出 PDF',
    },
]

DOC_TARGET_GROUPS = {
    'common': ['.pdf', '.docx', '.xlsx', '.pptx', '.png', '.jpg', '.html'],
    'other': ['.txt', '.md', '.htm', '.csv', '.odt', '.ods', '.odp'],
}

MARKDOWN_EXT: Set[str] = {'.md', '.markdown'}
HTML_EXT: Set[str] = {'.html', '.htm'}


def is_document(path: str) -> bool:
    return Path(path).suffix.lower() in DOCUMENT_EXT


def scan_documents(folder: str, recursive: bool = False) -> List[dict]:
    """Scan folder for supported documents."""
    from .common import fmt_size

    result: List[dict] = []
    folder_path = Path(folder)
    if not folder_path.is_dir():
        return result

    files = sorted(folder_path.rglob('*') if recursive else folder_path.iterdir())
    for f in files:
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in DOCUMENT_EXT:
            continue
        try:
            size = f.stat().st_size
        except OSError:
            continue
        result.append({
            'name': str(f.relative_to(folder_path)),
            'path': str(f),
            'size': size,
            'size_str': fmt_size(size),
            'dimensions': '-',
            'format': ext.lstrip('.').upper(),
        })
    return result


def probe_documents(paths: List[str]) -> List[dict]:
    from .common import fmt_size

    result: List[dict] = []
    seen: Set[str] = set()
    for path_str in paths:
        key = path_str.strip().strip('"').lower()
        if not key or key in seen:
            continue
        seen.add(key)
        f = Path(path_str.strip().strip('"'))
        if not f.is_file() or f.suffix.lower() not in DOCUMENT_EXT:
            continue
        try:
            size = f.stat().st_size
        except OSError:
            continue
        result.append({
            'name': f.name,
            'path': str(f),
            'size': size,
            'size_str': fmt_size(size),
            'dimensions': '-',
            'format': f.suffix.lstrip('.').upper(),
        })
    return result


def _pick_engine(src_ext: str, target_ext: str) -> Optional[str]:
    src_ext = src_ext.lower()
    target_ext = target_ext.lower()
    if src_ext == '.csv' and target_ext == '.xlsx':
        return 'openpyxl'
    if src_ext == '.txt' and target_ext == '.pdf':
        return 'text_pdf'
    if src_ext in MARKDOWN_EXT:
        if target_ext == '.html' and _markdown_available():
            return 'markdown_html'
        if target_ext == '.pdf' and _markdown_available() and _pymupdf_available():
            return 'markdown_pdf'
        if target_ext == '.txt' and _markdown_available() and _html2text_available():
            return 'markdown_txt'
        if target_ext in LO_CONVERT_EXT and find_libreoffice() and _markdown_available():
            return 'markdown_lo'
    if src_ext in HTML_EXT:
        if target_ext == '.md' and _html2text_available():
            return 'html_markdown'
        if target_ext == '.pdf' and _pymupdf_available():
            return 'html_pdf'
        if target_ext in LO_CONVERT_EXT and find_libreoffice():
            return 'libreoffice'
    if find_libreoffice():
        if src_ext == '.pdf' and target_ext in {'.docx', '.xlsx', '.pptx', '.odt', '.html', '.htm'}:
            return 'libreoffice'
        if src_ext in OFFICE_INPUT_EXT | {'.html', '.htm', '.csv', '.txt'}:
            if target_ext in LO_CONVERT_EXT:
                return 'libreoffice'
        if src_ext in OFFICE_INPUT_EXT and target_ext == '.pdf':
            return 'libreoffice'
    if src_ext == '.pdf':
        if target_ext == '.txt':
            return 'pymupdf_text'
        if target_ext in RASTER_EXT:
            return 'pymupdf_raster'
    if src_ext == '.pdf' and target_ext == '.pdf':
        return None
    return None


def get_doc_catalog() -> dict:
    lo = is_libreoffice_installed()
    pymupdf = _pymupdf_available()
    md = _markdown_available()
    h2t = _html2text_available()
    targets = []
    for ext in _all_target_exts(lo, pymupdf, md, h2t):
        group = 'common' if ext in DOC_TARGET_GROUPS.get('common', []) else 'other'
        targets.append({
            'ext': ext,
            'label': ext.lstrip('.').upper(),
            'group': group,
        })

    presets = []
    for preset in DOC_CONVERT_PRESETS:
        target = preset['target_fmt']
        preset_id = preset['id']
        if preset_id == 'office_pdf' and not lo:
            continue
        if preset_id == 'pdf_docx' and not lo:
            continue
        if preset_id == 'md_docx' and not lo:
            continue
        if preset_id in {'pdf_jpg', 'pdf_png', 'pdf_txt'} and not pymupdf:
            continue
        if preset_id == 'txt_pdf' and not (lo or pymupdf):
            continue
        if preset_id in {'md_pdf', 'html_pdf'} and not pymupdf:
            continue
        if preset_id == 'md_html' and not md:
            continue
        if preset_id == 'html_md' and not h2t:
            continue
        if target in RASTER_EXT and not pymupdf:
            continue
        presets.append(dict(preset))

    return {
        'targets': targets,
        'presets': presets,
        'features': {
            'libreoffice': lo,
            'pymupdf': pymupdf,
            'markdown': md,
            'html2text': h2t,
        },
        'inputs': sorted(DOCUMENT_EXT),
    }


def _all_target_exts(lo: bool, pymupdf: bool, md: bool, h2t: bool) -> List[str]:
    exts: Set[str] = set()
    if lo:
        exts |= LO_CONVERT_EXT
    if pymupdf:
        exts |= RASTER_EXT | {'.txt', '.pdf'}
    if md:
        exts.add('.html')
    if h2t:
        exts.add('.md')
    exts.add('.xlsx')  # csv via openpyxl
    ordered = list(DOC_TARGET_GROUPS['common']) + list(DOC_TARGET_GROUPS['other'])
    return [e for e in ordered if e in exts] + sorted(exts - set(ordered))


def _pymupdf_available() -> bool:
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def _markdown_available() -> bool:
    try:
        import markdown  # noqa: F401
        return True
    except ImportError:
        return False


def _html2text_available() -> bool:
    try:
        import html2text  # noqa: F401
        return True
    except ImportError:
        return False


_MD_HTML_CSS = """
body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #222; }
h1, h2, h3 { margin-top: 1.2em; margin-bottom: 0.5em; }
code { background: #f4f4f4; padding: 0.15em 0.35em; border-radius: 3px; font-size: 0.92em; }
pre { background: #f4f4f4; padding: 0.8em 1em; overflow: auto; border-radius: 4px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #ccc; padding: 0.35em 0.6em; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }
img { max-width: 100%; }
"""


def _markdown_to_html_content(src: str) -> str:
    import markdown as md_lib

    text = Path(src).read_text(encoding='utf-8', errors='replace')
    body = md_lib.markdown(
        text,
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'],
    )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<style>{_MD_HTML_CSS}</style></head><body>{body}</body></html>'
    )


def _convert_markdown_html(src: str, dst: str) -> str:
    Path(dst).write_text(_markdown_to_html_content(src), encoding='utf-8')
    return dst


def _convert_html_pdf_content(html: str, dst: str) -> str:
    import fitz

    if '<html' not in html.lower():
        html = f'<!DOCTYPE html><html><body>{html}</body></html>'

    story = fitz.Story(html=html, user_css=_MD_HTML_CSS)
    writer = fitz.DocumentWriter(dst)
    mediabox = fitz.paper_rect('a4')
    margin = 50
    where = mediabox + (margin, margin, -margin, -margin)
    try:
        while True:
            device = writer.begin_page(mediabox)
            more, _filled = story.place(where)
            story.draw(device)
            writer.end_page()
            if not more:
                break
    finally:
        writer.close()
    return dst


def _convert_markdown_pdf(src: str, dst: str) -> str:
    return _convert_html_pdf_content(_markdown_to_html_content(src), dst)


def _convert_markdown_txt(src: str, dst: str) -> str:
    import html2text

    html = _markdown_to_html_content(src)
    text = html2text.html2text(html, bodywidth=0)
    Path(dst).write_text(text.strip() + '\n', encoding='utf-8')
    return dst


def _convert_html_markdown(src: str, dst: str) -> str:
    import html2text

    html = Path(src).read_text(encoding='utf-8', errors='replace')
    text = html2text.html2text(html, bodywidth=0)
    Path(dst).write_text(text.strip() + '\n', encoding='utf-8')
    return dst


def _convert_html_pdf(src: str, dst: str) -> str:
    html = Path(src).read_text(encoding='utf-8', errors='replace')
    return _convert_html_pdf_content(html, dst)


def _convert_markdown_lo(src: str, dst: str, target_ext: str) -> List[str]:
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.html', delete=False) as tmp:
        tmp.write(_markdown_to_html_content(src))
        tmp_path = tmp.name
    try:
        return _convert_libreoffice(tmp_path, dst, target_ext)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _lo_format(ext: str) -> str:
    ext = ext.lower().lstrip('.')
    if ext == 'jpeg':
        return 'jpg'
    return ext


def _convert_libreoffice(src: str, dst: str, target_ext: str) -> List[str]:
    soffice = find_libreoffice()
    if not soffice:
        raise RuntimeError('LibreOffice not found')

    out_dir = os.path.dirname(dst) or '.'
    os.makedirs(out_dir, exist_ok=True)
    lo_fmt = _lo_format(target_ext)

    proc = subprocess.run(
        [
            soffice,
            '--headless',
            '--norestore',
            '--convert-to',
            lo_fmt,
            '--outdir',
            out_dir,
            src,
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or '').strip()
        raise RuntimeError(detail or f'LibreOffice failed ({proc.returncode})')

    base = os.path.splitext(os.path.basename(src))[0]
    produced = os.path.join(out_dir, f'{base}.{lo_fmt}')
    if not os.path.isfile(produced):
        # LO sometimes uses alternate extension
        candidates = [
            p for p in Path(out_dir).glob(f'{base}.*')
            if p.suffix.lower() in {target_ext.lower(), f'.{lo_fmt}'}
        ]
        if not candidates:
            raise RuntimeError('LibreOffice produced no output file')
        produced = str(candidates[0])

    outputs = [produced]
    if os.path.abspath(produced) != os.path.abspath(dst):
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(produced, dst)
        outputs = [dst]
    return outputs


def _convert_csv_xlsx(src: str, dst: str) -> str:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    with open(src, newline='', encoding='utf-8-sig') as handle:
        for row in csv.reader(handle):
            ws.append(row)
    wb.save(dst)
    return dst


def _convert_text_pdf(src: str, dst: str) -> str:
    text = Path(src).read_text(encoding='utf-8', errors='replace')
    if find_libreoffice():
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', delete=False) as tmp:
            tmp.write(text)
            tmp_path = tmp.name
        try:
            return _convert_libreoffice(tmp_path, dst, '.pdf')[0]
        except RuntimeError:
            pass
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(50, 50, 545, 792)
    page.insert_textbox(rect, text, fontsize=11, align=fitz.TEXT_ALIGN_LEFT)
    doc.save(dst)
    doc.close()
    return dst


def _convert_pdf_text(src: str, dst: str) -> str:
    import fitz

    doc = fitz.open(src)
    chunks = [page.get_text() for page in doc]
    doc.close()
    Path(dst).write_text('\n\n'.join(chunks).strip(), encoding='utf-8')
    return dst


def _convert_pdf_raster(
    src: str,
    dst: str,
    target_ext: str,
    *,
    dpi: int = 150,
    page_mode: str = 'all',
    quality: int = 85,
) -> List[str]:
    import fitz

    doc = fitz.open(src)
    outputs: List[str] = []
    base, _ = os.path.splitext(dst)
    ext = target_ext.lower()
    pages = range(doc.page_count) if page_mode != 'first' else range(min(1, doc.page_count))

    for idx in pages:
        page = doc.load_page(idx)
        pix = page.get_pixmap(dpi=max(72, min(600, dpi)))
        if len(pages) == 1 and page_mode == 'first':
            out_path = dst
        elif doc.page_count == 1:
            out_path = dst
        else:
            out_path = f'{base}_p{idx + 1:03d}{ext}'

        if ext in {'.jpg', '.jpeg'}:
            pix.save(out_path, output='jpeg', jpg_quality=max(1, min(100, quality)))
        elif ext == '.webp':
            pix.save(out_path, output='webp')
        else:
            pix.save(out_path)
        outputs.append(out_path)

    doc.close()
    return outputs


def convert_document(
    src: str,
    dst: str,
    target_fmt: str,
    *,
    dpi: int = 150,
    page_mode: str = 'all',
    quality: int = 85,
) -> Tuple[List[str], int]:
    """Convert one document. Returns (output paths, total bytes)."""
    src_ext = os.path.splitext(src)[1].lower()
    target_ext = target_fmt.lower()
    engine = _pick_engine(src_ext, target_ext)
    if not engine:
        raise ValueError(f'Unsupported conversion: {src_ext} → {target_ext}')

    if engine == 'openpyxl':
        out = _convert_csv_xlsx(src, dst)
    elif engine == 'text_pdf':
        out = _convert_text_pdf(src, dst)
    elif engine == 'markdown_html':
        out = _convert_markdown_html(src, dst)
    elif engine == 'markdown_pdf':
        out = _convert_markdown_pdf(src, dst)
    elif engine == 'markdown_txt':
        out = _convert_markdown_txt(src, dst)
    elif engine == 'markdown_lo':
        outputs = _convert_markdown_lo(src, dst, target_ext)
        total = sum(os.path.getsize(p) for p in outputs)
        return outputs, total
    elif engine == 'html_markdown':
        out = _convert_html_markdown(src, dst)
    elif engine == 'html_pdf':
        out = _convert_html_pdf(src, dst)
    elif engine == 'pymupdf_text':
        out = _convert_pdf_text(src, dst)
    elif engine == 'pymupdf_raster':
        outputs = _convert_pdf_raster(
            src, dst, target_ext, dpi=dpi, page_mode=page_mode, quality=quality,
        )
        total = sum(os.path.getsize(p) for p in outputs)
        return outputs, total
    elif engine == 'libreoffice':
        outputs = _convert_libreoffice(src, dst, target_ext)
        total = sum(os.path.getsize(p) for p in outputs)
        return outputs, total
    else:
        raise ValueError(f'Unknown engine: {engine}')

    if isinstance(out, list):
        outputs = out
    else:
        outputs = [out]
    total = sum(os.path.getsize(p) for p in outputs)
    return outputs, total


def run_doc_convert_batch(
    state,
    folder: str,
    file_list: List[str],
    target_fmt: str,
    do_backup: bool,
    replace: bool,
    out: Optional[str],
    dpi: int = 150,
    page_mode: str = 'all',
    quality: int = 85,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_file_done: Optional[Callable[[str, str, int], None]] = None,
    backup_fn: Optional[Callable[[str, List[str]], str]] = None,
) -> dict:
    logger = get_logger()
    errors: List[str] = []
    total_before = 0
    total_after = 0
    total = len(file_list)
    target_ext = target_fmt.lower()

    backup_dir = None
    if do_backup and backup_fn:
        try:
            backup_dir = backup_fn(folder, file_list)
        except OSError as exc:
            logger.error('Backup failed: %s', exc)
            return {
                'total_before': 0,
                'total_after': 0,
                'errors': [f'Backup failed: {exc}'],
                'cancelled': False,
                'backup_dir': None,
            }

    if not replace and out:
        os.makedirs(out, exist_ok=True)

    for i, fname in enumerate(file_list):
        if state.cancelled:
            break

        src = os.path.join(folder, fname)
        if not os.path.exists(src):
            errors.append(f'{fname}: source not found')
            continue

        try:
            sb = os.path.getsize(src)
        except OSError as exc:
            errors.append(f'{fname}: {exc}')
            continue

        total_before += sb
        base = os.path.splitext(fname)[0]
        src_ext = os.path.splitext(fname)[1].lower()
        new_name = base + target_ext
        dst = src if (replace and target_ext == src_ext) else (
            os.path.join(folder, new_name) if replace else os.path.join(out or folder, new_name)
        )

        try:
            outputs, added = convert_document(
                src, dst, target_fmt, dpi=dpi, page_mode=page_mode, quality=quality,
            )
            total_after += added

            if replace and target_ext != src_ext and os.path.exists(src):
                try:
                    os.remove(src)
                except OSError:
                    pass

            if on_file_done:
                label = outputs[0] if len(outputs) == 1 else f'{len(outputs)} files'
                on_file_done(fname, label, added)
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f'{fname}: {exc}')

        if on_progress:
            on_progress((i + 1) / total * 100, f'{i + 1}/{total}')

    return {
        'total_before': total_before,
        'total_after': total_after,
        'errors': errors,
        'cancelled': state.cancelled,
        'backup_dir': backup_dir,
    }
