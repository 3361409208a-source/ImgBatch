# -*- coding: utf-8 -*-
"""Tests for document conversion."""

from pathlib import Path

import pytest
from PIL import Image

from imgbatch.core.doc_convert import (
    convert_document,
    get_doc_catalog,
    run_doc_convert_batch,
    scan_documents,
)


class _State:
    cancelled = False


def test_doc_catalog():
    catalog = get_doc_catalog()
    assert catalog['targets']
    assert catalog['presets']
    assert 'csv_xlsx' in {p['id'] for p in catalog['presets']}


def test_scan_documents(tmp_path):
    (tmp_path / 'a.pdf').write_bytes(b'%PDF-1.4\n')
    (tmp_path / 'b.png').write_bytes(b'not a doc')
    files = scan_documents(str(tmp_path))
    assert len(files) == 1
    assert files[0]['name'] == 'a.pdf'


def test_csv_to_xlsx(tmp_path):
    src = tmp_path / 'data.csv'
    dst = tmp_path / 'data.xlsx'
    src.write_text('name,age\nAlice,30\n', encoding='utf-8')

    outputs, size = convert_document(str(src), str(dst), '.xlsx')
    assert outputs[0] == str(dst)
    assert size > 0
    assert dst.exists()


def test_txt_to_pdf(tmp_path):
    pymupdf = get_doc_catalog()['features']['pymupdf']
    if not pymupdf:
        pytest.skip('PyMuPDF not installed')

    src = tmp_path / 'note.txt'
    dst = tmp_path / 'note.pdf'
    src.write_text('Hello document conversion', encoding='utf-8')

    outputs, size = convert_document(str(src), str(dst), '.pdf')
    assert size > 0
    assert Path(outputs[0]).exists()


def test_pdf_to_png(tmp_path):
    pymupdf = get_doc_catalog()['features']['pymupdf']
    if not pymupdf:
        pytest.skip('PyMuPDF not installed')

    import fitz

    src = tmp_path / 'page.pdf'
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), 'PDF page')
    doc.save(str(src))
    doc.close()

    dst = tmp_path / 'page.png'
    outputs, size = convert_document(str(src), str(dst), '.png', dpi=120)
    assert size > 0
    assert Path(outputs[0]).exists()
    with Image.open(outputs[0]) as img:
        assert img.width > 0


def test_doc_convert_batch_csv(tmp_path):
    src = tmp_path / 'sheet.csv'
    src.write_text('a,b\n1,2\n', encoding='utf-8')

    result = run_doc_convert_batch(
        _State(),
        str(tmp_path),
        ['sheet.csv'],
        target_fmt='.xlsx',
        do_backup=False,
        replace=True,
        out=None,
    )
    assert result['errors'] == []
    assert (tmp_path / 'sheet.xlsx').exists()
    assert not src.exists()
