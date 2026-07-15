#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for file list filtering."""

from imgbatch.core.common import (
    filter_files, parse_dimensions, parse_kb_to_bytes, SIZE_PRESETS,
)


def _file(name, size, dims='100x100', fmt='PNG'):
    return {
        'name': name,
        'path': f'/tmp/{name}',
        'size': size,
        'size_str': str(size),
        'dimensions': dims,
        'format': fmt,
    }


SAMPLE = [
    _file('a.png', 20 * 1024, '200x100', 'PNG'),
    _file('photo.jpg', 800 * 1024, '1920x1080', 'JPEG'),
    _file('banner.webp', 50 * 1024, '640x200', 'WEBP'),
    _file('icon.png', 5 * 1024, '64x64', 'PNG'),
    _file('big.bmp', 2 * 1024 * 1024, '4000x3000', 'BMP'),
]


class TestParseHelpers:
    def test_parse_dimensions(self):
        assert parse_dimensions('575x497') == (575, 497)
        assert parse_dimensions('100X200') == (100, 200)
        assert parse_dimensions('?') == (None, None)
        assert parse_dimensions('') == (None, None)

    def test_parse_kb_to_bytes(self):
        assert parse_kb_to_bytes('100') == 100 * 1024
        assert parse_kb_to_bytes('') is None
        assert parse_kb_to_bytes('abc') is None
        assert parse_kb_to_bytes('-1') is None


class TestFilterFiles:
    def test_no_filter_returns_all(self):
        assert len(filter_files(SAMPLE)) == 5

    def test_name_query(self):
        out = filter_files(SAMPLE, name_query='photo')
        assert [d['name'] for d in out] == ['photo.jpg']

    def test_name_case_insensitive(self):
        out = filter_files(SAMPLE, name_query='PNG')
        assert len(out) == 2

    def test_format_png(self):
        out = filter_files(SAMPLE, formats={'PNG'})
        assert {d['name'] for d in out} == {'a.png', 'icon.png'}

    def test_format_jpeg_matches_jpg(self):
        out = filter_files(SAMPLE, formats={'JPEG'})
        assert [d['name'] for d in out] == ['photo.jpg']

    def test_size_min(self):
        out = filter_files(SAMPLE, min_size=100 * 1024)
        assert all(d['size'] >= 100 * 1024 for d in out)
        assert len(out) == 2  # photo.jpg, big.bmp

    def test_size_max(self):
        out = filter_files(SAMPLE, max_size=50 * 1024)
        assert all(d['size'] <= 50 * 1024 for d in out)
        assert len(out) == 3

    def test_size_preset_lt_100kb(self):
        lo, hi = SIZE_PRESETS['lt_100kb']
        out = filter_files(SAMPLE, min_size=lo, max_size=hi)
        assert {d['name'] for d in out} == {'a.png', 'banner.webp', 'icon.png'}

    def test_size_preset_gt_1mb(self):
        lo, hi = SIZE_PRESETS['gt_1mb']
        out = filter_files(SAMPLE, min_size=lo, max_size=hi)
        assert [d['name'] for d in out] == ['big.bmp']

    def test_min_dimensions(self):
        out = filter_files(SAMPLE, min_width=1000, min_height=1000)
        assert [d['name'] for d in out] == ['photo.jpg', 'big.bmp']

    def test_combined(self):
        out = filter_files(
            SAMPLE,
            name_query='a',
            formats={'PNG'},
            max_size=30 * 1024,
        )
        assert [d['name'] for d in out] == ['a.png']

    def test_empty_input(self):
        assert filter_files([]) == []
