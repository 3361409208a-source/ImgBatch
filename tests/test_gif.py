# -*- coding: utf-8 -*-
"""Tests for animated GIF editing."""

import os
import tempfile

from PIL import Image

from imgbatch.core.gif import (
    compose_gif_from_images,
    load_gif,
    merge_gifs,
    probe_gif,
    process_gif_file,
    save_gif,
)


def _make_test_gif(path: str, frames: int = 4) -> None:
    images = []
    for i in range(frames):
        img = Image.new('RGBA', (40, 30), (255, 0, 0, 255))
        img.paste(Image.new('RGBA', (10, 10), (0, 255, 0, 255)), (i * 5, 5))
        images.append(img)
    save_gif(images, [100] * frames, path, loop=0)


def test_probe_and_reverse_gif():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'test.gif')
        dst = os.path.join(tmp, 'rev.gif')
        _make_test_gif(src, 3)
        info = probe_gif(src)
        assert info['n_frames'] == 3
        assert info['is_animated'] is True
        process_gif_file(src, dst, 'reverse', {})
        frames, durations, _ = load_gif(dst)
        assert len(frames) == 3
        assert len(durations) == 3


def test_compose_and_merge_gif():
    with tempfile.TemporaryDirectory() as tmp:
        pngs = []
        for i in range(3):
            p = os.path.join(tmp, f'frame_{i:02d}.png')
            Image.new('RGBA', (20, 20), (i * 40, 100, 200, 255)).save(p)
            pngs.append(p)
        out1 = os.path.join(tmp, 'a.gif')
        meta = compose_gif_from_images(pngs, out1, frame_duration=50)
        assert meta['n_frames'] == 3

        src2 = os.path.join(tmp, 'b.gif')
        _make_test_gif(src2, 2)
        merged = os.path.join(tmp, 'merged.gif')
        m = merge_gifs([out1, src2], merged)
        assert m['n_frames'] == 5


def test_speed_and_extract_gif():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'speed.gif')
        dst = os.path.join(tmp, 'fast.gif')
        _make_test_gif(src, 2)
        process_gif_file(src, dst, 'speed', {'speed_factor': 2.0})
        _, durations, _ = load_gif(dst)
        assert durations[0] == 50

        extract_dir = os.path.join(tmp, 'frames')
        process_gif_file(src, extract_dir, 'extract', {'extract_dir': extract_dir})
        assert len(os.listdir(extract_dir)) == 2
