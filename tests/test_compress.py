#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for compression logic."""

import os

from PIL import Image

from imgbatch.core.compress import compress_image, estimate_compressed_size, run_compress_batch
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

    def test_compress_png_preserves_transparency(self, tmp_image_dir):
        """RGBA PNG compression must keep transparent pixels transparent."""
        src = os.path.join(tmp_image_dir, 'test3.png')
        dst = os.path.join(tmp_image_dir, 'out_alpha.png')

        with Image.open(src) as original:
            corner = original.getpixel((0, 0))
            assert corner[3] == 0  # fully transparent corner

        compress_image(src, dst, quality=75, resize_pct=100)

        with Image.open(dst) as img:
            assert img.mode in ('RGBA', 'LA')
            assert img.getpixel((0, 0))[3] == 0

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


class TestRunCompressBatch:
    def test_compress_nested_paths(self, tmp_path):
        sub = tmp_path / "assets" / "icons"
        sub.mkdir(parents=True)
        src = sub / "big.png"
        img = Image.new("RGBA", (800, 600), (255, 0, 0, 255))
        img.save(src, optimize=True)

        rel_name = "assets/icons/big.png"
        out_dir = tmp_path / "out"
        state = type("S", (), {"cancelled": False})()

        result = run_compress_batch(
            state,
            str(tmp_path),
            [rel_name],
            quality=60,
            resize_pct=70,
            do_backup=False,
            replace=False,
            out=str(out_dir),
            exif_mode="keep",
        )

        assert result["errors"] == []
        assert result["total_before"] > 0
        assert result["total_after"] > 0
        assert (out_dir / "assets" / "icons" / "big.png").is_file()
