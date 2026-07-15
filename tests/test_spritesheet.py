#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for sprite sheet builder."""

import json
import os

from PIL import Image

from imgbatch.core.spritesheet import (
    build_spritesheet,
    natural_sort_key,
    next_power_of_2,
    save_spritesheet,
    run_spritesheet_build,
    trim_frame,
    LAYOUT_AUTO,
    LAYOUT_GRID,
    LAYOUT_HORIZONTAL,
    LAYOUT_VERTICAL,
)
from imgbatch.infra.threading import TaskState


class TestNaturalSort:
    def test_numeric_order(self):
        names = ['frame_10.png', 'frame_2.png', 'frame_1.png']
        assert sorted(names, key=natural_sort_key) == [
            'frame_1.png', 'frame_2.png', 'frame_10.png',
        ]


class TestPowerOfTwo:
    def test_values(self):
        assert next_power_of_2(1) == 1
        assert next_power_of_2(100) == 128
        assert next_power_of_2(128) == 128
        assert next_power_of_2(129) == 256


class TestTrimFrame:
    def test_trims_transparent_border(self):
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        for x in range(30, 70):
            for y in range(20, 60):
                img.putpixel((x, y), (255, 0, 0, 255))
        trimmed = trim_frame(img, padding=2, alpha_threshold=28)
        assert trimmed.width <= 50
        assert trimmed.height <= 50


class TestBuildSpritesheet:
    def _make_frames(self, tmp_path, count=4):
        paths = []
        for i in range(count):
            img = Image.new('RGBA', (40 + i * 10, 30 + i * 5), (0, 0, 0, 0))
            for x in range(5, 35 + i * 10):
                for y in range(5, 25 + i * 5):
                    img.putpixel((x, y), (i * 50, 100, 200, 255))
            path = os.path.join(tmp_path, f'frame_{i:02d}.png')
            img.save(path)
            paths.append(path)
        return paths

    def test_auto_layout(self, tmp_path):
        paths = self._make_frames(tmp_path)
        canvas, meta = build_spritesheet(paths, layout=LAYOUT_AUTO, spacing=2)
        assert canvas.mode == 'RGBA'
        assert meta['meta']['size']['w'] > 0
        assert len(meta['frames']) == 4

    def test_grid_layout(self, tmp_path):
        paths = self._make_frames(tmp_path)
        canvas, meta = build_spritesheet(paths, layout=LAYOUT_GRID, columns=2, spacing=2)
        assert len(meta['frames']) == 4
        assert canvas.width > 0

    def test_horizontal_strip(self, tmp_path):
        paths = self._make_frames(tmp_path, count=3)
        canvas, meta = build_spritesheet(
            paths, layout=LAYOUT_HORIZONTAL, spacing=0, trim=False,
        )
        total_w = sum(40 + i * 10 for i in range(3))
        assert canvas.width == total_w

    def test_vertical_strip(self, tmp_path):
        paths = self._make_frames(tmp_path, count=3)
        canvas, meta = build_spritesheet(
            paths, layout=LAYOUT_VERTICAL, spacing=0, trim=False,
        )
        total_h = sum(30 + i * 5 for i in range(3))
        assert canvas.height == total_h

    def test_power_of_two(self, tmp_path):
        paths = self._make_frames(tmp_path, count=2)
        canvas, meta = build_spritesheet(paths, power_of_two=True)
        w, h = meta['meta']['size']['w'], meta['meta']['size']['h']
        assert w & (w - 1) == 0
        assert h & (h - 1) == 0

    def test_save_with_json(self, tmp_path):
        paths = self._make_frames(tmp_path, count=2)
        canvas, meta = build_spritesheet(paths)
        out = os.path.join(tmp_path, 'atlas.png')
        size, json_path = save_spritesheet(canvas, meta, out, export_json=True)
        assert os.path.exists(out)
        assert os.path.exists(json_path)
        assert size > 0
        with open(json_path, encoding='utf-8') as fh:
            data = json.load(fh)
        assert 'frames' in data
        assert len(data['frames']) == 2


class TestRunSpritesheetBuild:
    def test_needs_two_images(self, tmp_path):
        path = os.path.join(tmp_path, 'solo.png')
        Image.new('RGBA', (10, 10), (255, 0, 0, 255)).save(path)
        state = TaskState()
        result = run_spritesheet_build(
            state, [path], os.path.join(tmp_path, 'out.png'),
        )
        assert result['errors']
        assert not result.get('output_path')

    def test_builds_from_multiple(self, tmp_path):
        paths = []
        for i in range(3):
            p = os.path.join(tmp_path, f'sprite_{i}.png')
            Image.new('RGBA', (20, 20), (255, i * 80, 0, 255)).save(p)
            paths.append(p)
        out = os.path.join(tmp_path, 'sheet.png')
        state = TaskState()
        result = run_spritesheet_build(state, paths, out)
        assert result.get('output_path') == out
        assert result['frame_count'] == 3
        assert os.path.exists(out)
