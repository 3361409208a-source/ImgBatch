"""Tests for document preview."""

from pathlib import Path

import pytest

from imgbatch.core.doc_preview import preview_document


def test_preview_markdown_text(tmp_path):
    md = tmp_path / 'note.md'
    md.write_text('# Hello\n\nWorld', encoding='utf-8')
    result = preview_document(str(md))
    assert result['kind'] == 'text'
    assert 'Hello' in result['text']


def test_preview_txt_text(tmp_path):
    txt = tmp_path / 'readme.txt'
    txt.write_text('line one\nline two', encoding='utf-8')
    result = preview_document(str(txt))
    assert result['kind'] == 'text'
    assert 'line one' in result['text']


def test_preview_unknown_doc(tmp_path):
    doc = tmp_path / 'legacy.doc'
    doc.write_bytes(b'fake')
    result = preview_document(str(doc))
    assert result['kind'] == 'text'
    assert '暂不支持' in result['text']


def test_preview_pdf_image(tmp_path):
    fitz = pytest.importorskip('fitz')

    pdf = tmp_path / 'page.pdf'
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.insert_text((50, 50), 'PDF preview')
    doc.save(str(pdf))
    doc.close()

    result = preview_document(str(pdf), max_size=120)
    assert result['kind'] == 'image'
    assert result['data_url'].startswith('data:image/png;base64,')
