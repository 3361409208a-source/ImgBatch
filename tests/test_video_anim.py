#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for video → animated WebP/GIF conversion."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from imgbatch.core.video_anim import (
    VIDEO_EXT,
    _white_key_filter,
    clean_fringe_frame,
    convert_video_to_anim,
    is_video,
    patch_webp_anmf_disposal,
    run_video_anim_batch,
)


class TestHelpers:
    def test_is_video(self):
        assert is_video('a.webm')
        assert is_video('b.MP4')
        assert not is_video('c.png')
        assert VIDEO_EXT >= {'.webm', '.mp4'}

    def test_white_key_filter(self):
        assert _white_key_filter() == 'colorkey=0xFFFFFF:0.120:0.040,format=rgba'
        assert _white_key_filter(0.2, 0.06) == 'colorkey=0xFFFFFF:0.200:0.060,format=rgba'

    def test_clean_fringe_removes_dark_halo(self):
        im = Image.new('RGBA', (4, 4), (0, 0, 0, 0))
        px = im.load()
        px[1, 1] = (20, 20, 20, 80)  # dark semi-transparent fringe
        px[2, 2] = (200, 180, 160, 255)  # solid content
        out = clean_fringe_frame(im)
        assert out.getpixel((1, 1))[3] == 0
        assert out.getpixel((2, 2))[3] == 255

    def test_patch_webp_anmf(self):
        # Distinct frames so Pillow keeps animation (identical frames collapse).
        frames = []
        for i in range(3):
            im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            im.putpixel((2 + i, 2), (255, 40 * i, 0, 200))
            frames.append(im)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'a.webp')
            frames[0].save(
                path, format='WEBP', save_all=True, append_images=frames[1:],
                duration=40, loop=0, quality=80,
            )
            n = patch_webp_anmf_disposal(path)
            assert n >= 1
            data = Path(path).read_bytes()
            i = 12
            checked = 0
            while i + 8 <= len(data) and checked < 5:
                tag = data[i : i + 4]
                size = int.from_bytes(data[i + 4 : i + 8], 'little')
                if tag == b'ANMF' and size >= 16:
                    flags = data[i + 8 + 15]
                    assert flags & 1 == 1  # disposal
                    assert (flags >> 1) & 1 == 0  # no blend
                    checked += 1
                i += 8 + size + (size & 1)
            assert checked >= 1


class TestConvert:
    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value=None)
    def test_missing_ffmpeg(self, _find):
        with pytest.raises(RuntimeError, match='ffmpeg not found'):
            convert_video_to_anim('a.webm', 'b.webp')

    @patch('imgbatch.core.video_anim._ffmpeg_direct_webp')
    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value='/ffmpeg')
    def test_direct_webp_path(self, _find, mock_direct):
        def _fake(ffmpeg, src, dst, **kwargs):
            Path(dst).write_bytes(b'RIFF' + b'\x00' * 20)

        mock_direct.side_effect = _fake
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'a.webm')
            dst = os.path.join(d, 'a.webp')
            Path(src).write_bytes(b'x' * 100)
            size = convert_video_to_anim(
                src, dst, target='.webp', clean_fringe=False, keep_alpha=True,
            )
            assert size > 0
            mock_direct.assert_called_once()

    @patch('imgbatch.core.video_anim._save_webp_from_frames')
    @patch('imgbatch.core.video_anim._extract_frames')
    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value='/ffmpeg')
    def test_clean_fringe_uses_frames(self, _find, mock_extract, mock_save):
        def _save(paths, dst, **kwargs):
            Path(dst).write_bytes(b'ok')

        mock_extract.return_value = ['f0.png']
        mock_save.side_effect = _save
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'a.webm')
            dst = os.path.join(d, 'a.webp')
            Path(src).write_bytes(b'x' * 50)
            convert_video_to_anim(src, dst, clean_fringe=True)
            mock_extract.assert_called_once()
            mock_save.assert_called_once()

    @patch('imgbatch.core.video_anim._run_ffmpeg')
    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value='/ffmpeg')
    def test_white_key_gif_uses_colorkey(self, _find, mock_run):
        def _fake_run(cmd):
            dst = cmd[-1]
            Path(dst).write_bytes(b'GIF89a' + b'\x00' * 20)

        mock_run.side_effect = _fake_run
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'a.mp4')
            dst = os.path.join(d, 'a.gif')
            Path(src).write_bytes(b'x' * 50)
            convert_video_to_anim(
                src, dst, target='.gif', white_key=True,
                white_key_similarity=0.12, white_key_blend=0.04,
            )
            cmd = mock_run.call_args[0][0]
            assert '-vf' in cmd
            vf = cmd[cmd.index('-vf') + 1]
            assert 'colorkey=0xFFFFFF:0.120:0.040' in vf
            assert 'reserve_transparent=1' in vf


class TestBatch:
    @patch('imgbatch.core.video_anim.convert_video_to_anim', return_value=400)
    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value='/ffmpeg')
    def test_batch_videos_only(self, _find, mock_convert):
        with tempfile.TemporaryDirectory() as d:
            Path(os.path.join(d, 'a.webm')).write_bytes(b'x' * 800)
            Path(os.path.join(d, 'b.png')).write_bytes(b'y' * 100)
            out = os.path.join(d, 'out')

            class _State:
                cancelled = False

            result = run_video_anim_batch(
                _State(), d, ['a.webm', 'b.png'],
                target='.webp', do_backup=False, replace=False, out=out,
            )
            assert 'b.png' in result['skipped']
            assert len(result['results']) == 1
            assert result['results'][0]['name'] == 'a.webp'
            mock_convert.assert_called_once()

    @patch('imgbatch.core.video_anim.find_ffmpeg', return_value=None)
    def test_batch_no_ffmpeg(self, _find):
        class _State:
            cancelled = False

        result = run_video_anim_batch(
            _State(), '/tmp', ['a.webm'],
            do_backup=False, replace=True, out=None,
        )
        assert result['errors']
        assert 'ffmpeg' in result['errors'][0].lower()
