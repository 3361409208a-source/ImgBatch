#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for watermark, trim, and normalize logic."""

import os

from PIL import Image

from imgbatch.core.watermark import add_text_watermark, add_image_watermark
from imgbatch.core.trim import trim_image
from imgbatch.core.normalize import normalize_image
from imgbatch.core.inspect import inspect_single


class TestTextWatermark:
    def test_add_text_watermark_returns_rgba(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        with Image.open(src) as img:
            result = add_text_watermark(img, 'test', opacity=0.5)
            assert result.mode == 'RGBA'

    def test_watermark_preserves_size(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        with Image.open(src) as img:
            result = add_text_watermark(img, 'test')
            assert result.size == img.size


class TestImageWatermark:
    def test_add_image_watermark(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        wm_path = os.path.join(tmp_image_dir, 'test3.png')
        with Image.open(src) as img:
            with Image.open(wm_path) as wm:
                result = add_image_watermark(img, wm.convert('RGBA'), scale_pct=20)
                assert result.size == img.size
                assert result.mode == 'RGBA'


class TestTrimImage:
    def test_trim_reduces_size(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'border1.png')
        dst = os.path.join(tmp_png_dir, 'trimmed.png')
        original_size = os.path.getsize(src)

        new_size = trim_image(src, dst, padding=2)

        assert os.path.exists(dst)
        with Image.open(dst) as img:
            # Content was 100x70 with padding 2 → ~104x74
            assert img.width <= 110
            assert img.height <= 80

    def test_trim_fully_transparent(self, tmp_png_dir):
        """Fully transparent image should be saved as-is."""
        src = os.path.join(tmp_png_dir, 'empty.png')
        dst = os.path.join(tmp_png_dir, 'empty_out.png')

        trim_image(src, dst, padding=4)
        assert os.path.exists(dst)

    def test_trim_solid_image(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'solid.png')
        dst = os.path.join(tmp_png_dir, 'solid_out.png')

        trim_image(src, dst, padding=4)
        with Image.open(dst) as img:
            # Solid 80x60 + padding 4 on each side → 88x68
            assert img.width <= 90
            assert img.height <= 70


class TestNormalizeImage:
    def test_normalize_height(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'border1.png')
        dst = os.path.join(tmp_png_dir, 'norm.png')

        normalize_image(src, dst, alpha_threshold=28, target_height=100, padding=4)

        with Image.open(dst) as img:
            # Canvas height should be target_height + 2*padding
            assert img.height == 108  # 100 + 2*4

    def test_normalize_empty_image(self, tmp_png_dir):
        """Fully transparent image should be saved as-is."""
        src = os.path.join(tmp_png_dir, 'empty.png')
        dst = os.path.join(tmp_png_dir, 'empty_norm.png')

        normalize_image(src, dst, target_height=100)
        assert os.path.exists(dst)


class TestInspect:
    def test_inspect_with_content(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'border1.png')
        info = inspect_single(src)
        assert info['name'] == 'border1.png'
        assert 'x' in info['canvas']
        assert info['content'] != 'transparent'

    def test_inspect_empty(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'empty.png')
        info = inspect_single(src)
        assert info['content'] == 'transparent'
