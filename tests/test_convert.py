# -*- coding: utf-8 -*-
"""Tests for format conversion."""

import os
from pathlib import Path

import pytest
from PIL import Image

from imgbatch.core.common import get_convert_catalog
from imgbatch.core.convert import convert_image, run_convert_batch


class _State:
    cancelled = False


def test_convert_catalog_has_presets():
    catalog = get_convert_catalog()
    assert catalog['targets']
    assert catalog['presets']
    assert 'web_jpg' in {p['id'] for p in catalog['presets']}


def test_convert_png_to_jpg(tmp_path):
    src = tmp_path / 'sample.png'
    dst = tmp_path / 'sample.jpg'
    Image.new('RGBA', (32, 32), (255, 0, 0, 128)).save(src)

    size = convert_image(str(src), str(dst), '.jpg', quality=90)
    assert size > 0
    assert dst.exists()
    with Image.open(dst) as img:
        assert img.mode == 'RGB'


def test_convert_batch_replace_ext(tmp_path):
    src = tmp_path / 'a.png'
    Image.new('RGB', (16, 16), 'blue').save(src)

    result = run_convert_batch(
        _State(),
        str(tmp_path),
        ['a.png'],
        target_fmt='.webp',
        do_backup=False,
        replace=True,
        out=None,
        quality=80,
    )
    assert result['errors'] == []
    assert not src.exists()
    assert (tmp_path / 'a.webp').exists()
    assert result['total_after'] > 0