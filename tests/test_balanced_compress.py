#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for balanced animated compression."""

import os
import tempfile

import pytest
from PIL import Image

from imgbatch.core.balanced_compress import (
    compress_anim_to_target,
    is_animated_media,
    pick_best_variant,
    run_balanced_compress_batch,
)


def _make_anim_webp(path: str, frames: int = 4, size: tuple = (400, 300)) -> None:
    imgs = []
    for i in range(frames):
        img = Image.new('RGBA', size, (255, 255, 255, 0))
        for x in range(80 + i * 10, 320):
            for y in range(60, 240):
                img.putpixel((x, y), (30 + i * 20, 100, 200, 255))
        imgs.append(img)
    imgs[0].save(
        path,
        format='WEBP',
        save_all=True,
        append_images=imgs[1:],
        duration=[80] * frames,
        loop=0,
        lossless=True,
    )


def _make_anim_gif(path: str, frames: int = 4, size: tuple = (200, 150)) -> None:
    imgs = []
    for i in range(frames):
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        for x in range(40 + i * 5, 160):
            for y in range(30, 120):
                img.putpixel((x, y), (200, 50 + i * 30, 50, 255))
        imgs.append(img)
    imgs[0].save(
        path,
        format='GIF',
        save_all=True,
        append_images=imgs[1:],
        duration=100,
        loop=0,
        disposal=2,
    )


def _make_static_webp(path: str) -> None:
    Image.new('RGB', (120, 90), (255, 0, 0)).save(path, format='WEBP', quality=80)


class TestPickBestVariant:
    def test_prefers_under_target_highest_quality(self):
        variants = [
            (900_000, 800, 30),
            (1_100_000, 900, 35),
            (1_200_000, 977, 36),
        ]
        best = pick_best_variant(variants, 1_150_000)
        assert best == (1_100_000, 900, 35)

    def test_closest_when_all_over(self):
        variants = [
            (1_300_000, 800, 30),
            (1_180_000, 900, 32),
            (1_250_000, 850, 31),
        ]
        best = pick_best_variant(variants, 1_150_000)
        assert best == (1_180_000, 900, 32)


class TestBalancedCompress:
    def test_animated_webp_compresses_toward_target(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'anim.webp')
            dst = os.path.join(d, 'out.webp')
            _make_anim_webp(src)
            orig = os.path.getsize(src)
            target = max(8_000, orig // 4)
            meta = compress_anim_to_target(src, dst, target)
            assert os.path.exists(dst)
            assert meta['format'] == 'webp'
            assert meta['size'] > 0
            assert meta['width'] > 0

    def test_animated_gif_compresses_toward_target(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'anim.gif')
            dst = os.path.join(d, 'out.gif')
            _make_anim_gif(src)
            orig = os.path.getsize(src)
            target = max(4_000, orig // 3)
            meta = compress_anim_to_target(src, dst, target)
            assert os.path.exists(dst)
            assert meta['format'] == 'gif'
            assert meta['size'] <= orig * 1.1

    def test_static_webp_skipped_in_batch(self):
        with tempfile.TemporaryDirectory() as d:
            static = os.path.join(d, 'still.webp')
            anim = os.path.join(d, 'anim.gif')
            _make_static_webp(static)
            _make_anim_gif(anim)

            class _State:
                cancelled = False

            result = run_balanced_compress_batch(
                _State(), d, ['still.webp', 'anim.gif'],
                target_mb=0.05,
                do_backup=False,
                replace=False,
                out=os.path.join(d, 'out'),
            )
            assert 'still.webp' in result['skipped']
            assert len(result['results']) == 1
            assert result['results'][0]['name'] == 'anim.gif'

    def test_is_animated_media(self):
        with tempfile.TemporaryDirectory() as d:
            static = os.path.join(d, 'still.webp')
            anim = os.path.join(d, 'anim.gif')
            _make_static_webp(static)
            _make_anim_gif(anim)
            assert not is_animated_media(static)
            assert is_animated_media(anim)
