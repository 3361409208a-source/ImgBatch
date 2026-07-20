#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for watermark, trim, and normalize logic."""

import os

from PIL import Image

from imgbatch.core.watermark import add_text_watermark, add_image_watermark
from imgbatch.core.trim import trim_image, run_trim_batch
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

    def test_trim_webp_transparent_border(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'border1.png')
        webp_src = os.path.join(tmp_png_dir, 'border1.webp')
        webp_dst = os.path.join(tmp_png_dir, 'trimmed.webp')

        with Image.open(src) as img:
            img.save(webp_src, format='WEBP', lossless=True)

        trim_image(webp_src, webp_dst, padding=2)

        assert os.path.exists(webp_dst)
        with Image.open(webp_dst) as img:
            assert img.width <= 110
            assert img.height <= 80

    def test_trim_webp_white_border(self, tmp_png_dir):
        webp_src = os.path.join(tmp_png_dir, 'white_border.webp')
        webp_dst = os.path.join(tmp_png_dir, 'white_border_trimmed.webp')

        img = Image.new('RGB', (200, 150), (255, 255, 255))
        for x in range(50, 150):
            for y in range(40, 110):
                img.putpixel((x, y), (0, 255, 0))
        img.save(webp_src, format='WEBP', quality=85)

        trim_image(webp_src, webp_dst, padding=0)

        assert os.path.exists(webp_dst)
        with Image.open(webp_dst) as trimmed:
            assert trimmed.width <= 110
            assert trimmed.height <= 80

    def test_trim_lossy_webp_noisy_white_border(self, tmp_png_dir):
        """Lossy WebP borders are rarely pure white — still must trim."""
        webp_src = os.path.join(tmp_png_dir, 'noisy_white.webp')
        webp_dst = os.path.join(tmp_png_dir, 'noisy_white_trimmed.webp')

        img = Image.new('RGB', (220, 160), (255, 255, 255))
        # Simulate compression noise on the canvas.
        for x in range(0, 220, 3):
            for y in range(0, 160, 3):
                img.putpixel((x, y), (248 + (x + y) % 7, 250, 252))
        for x in range(60, 160):
            for y in range(45, 115):
                img.putpixel((x, y), (20, 120, 200))
        img.save(webp_src, format='WEBP', quality=60)

        trim_image(webp_src, webp_dst, padding=0)

        with Image.open(webp_dst) as trimmed:
            assert trimmed.width < 180
            assert trimmed.height < 130

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


class TestTrimBatch:
    def test_run_trim_batch_includes_webp(self, tmp_png_dir):
        src = os.path.join(tmp_png_dir, 'border1.png')
        webp_name = 'border1.webp'
        webp_src = os.path.join(tmp_png_dir, webp_name)
        with Image.open(src) as img:
            img.save(webp_src, format='WEBP', lossless=True)

        out_dir = os.path.join(tmp_png_dir, 'out')
        os.makedirs(out_dir)

        class _State:
            cancelled = False

        result = run_trim_batch(
            _State(), tmp_png_dir, [webp_name, 'solid.png'],
            padding=2, do_backup=False, replace=False, out=out_dir,
        )
        assert result['total_before'] > 0
        trimmed = os.path.join(out_dir, webp_name)
        assert os.path.exists(trimmed)
        with Image.open(trimmed) as img:
            assert img.width <= 110
            assert img.height <= 80


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
