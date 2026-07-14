#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for compression logic."""

import os

from PIL import Image

from imgbatch.core.compress import compress_image, estimate_compressed_size
from imgbatch.core.common import fmt_size


class TestCompressImage:
    def test_compress_jpeg_reduces_size(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        dst = os.path.join(tmp_image_dir, 'out.jpg')
        original_size = os.path.getsize(src)

        new_size = compress_image(src, dst, quality=30, resize_pct=50)

        assert os.path.exists(dst)
        assert new_size < original_size

    def test_compress_png_preserves_format(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test3.png')
        dst = os.path.join(tmp_image_dir, 'out.png')

        compress_image(src, dst, quality=75, resize_pct=100)

        with Image.open(dst) as img:
            assert img.format == 'PNG'

    def test_compress_rgba_to_jpeg(self, tmp_image_dir):
        """RGBA PNG compressed to JPEG should convert to RGB."""
        src = os.path.join(tmp_image_dir, 'test3.png')
        dst = os.path.join(tmp_image_dir, 'out.jpg')

        compress_image(src, dst, quality=75)

        with Image.open(dst) as img:
            assert img.mode == 'RGB'

    def test_compress_resize_changes_dimensions(self, tmp_image_dir):
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        dst = os.path.join(tmp_image_dir, 'resized.jpg')

        compress_image(src, dst, quality=85, resize_pct=50)

        with Image.open(dst) as img:
            assert img.width == 50
            assert img.height == 40

    def test_compress_quality_1(self, tmp_image_dir):
        """Quality=1 should produce a very small file."""
        src = os.path.join(tmp_image_dir, 'test1.jpg')
        dst = os.path.join(tmp_image_dir, 'q1.jpg')

        new_size = compress_image(src, dst, quality=1)
        assert new_size > 0
        assert new_size < os.path.getsize(src)


class TestEstimateCompressedSize:
    def test_estimate_returns_positive(self, tmp_image_dir):
        files = [
            {'name': 'test1.jpg', 'path': os.path.join(tmp_image_dir, 'test1.jpg'),
             'size': os.path.getsize(os.path.join(tmp_image_dir, 'test1.jpg'))},
            {'name': 'test2.jpg', 'path': os.path.join(tmp_image_dir, 'test2.jpg'),
             'size': os.path.getsize(os.path.join(tmp_image_dir, 'test2.jpg'))},
        ]
        before, after = estimate_compressed_size(files, quality=50, resize_pct=100)
        assert before > 0
        assert after > 0
        assert after <= before

    def test_estimate_empty_list(self):
        before, after = estimate_compressed_size([], quality=75)
        assert before == 0
        assert after == 0
