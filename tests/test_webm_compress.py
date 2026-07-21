#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for WebM alpha compression."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from imgbatch.core.webm_compress import (
    build_ffmpeg_cmd,
    compress_webm,
    run_webm_compress_batch,
)


class TestBuildFfmpegCmd:
    def test_alpha_flags(self):
        cmd = build_ffmpeg_cmd('/usr/bin/ffmpeg', 'in.webm', 'out.webm', keep_alpha=True)
        assert '-pix_fmt' in cmd
        assert 'yuva420p' in cmd
        assert '-auto-alt-ref' in cmd

    def test_no_alpha_uses_yuv420p(self):
        cmd = build_ffmpeg_cmd('/usr/bin/ffmpeg', 'in.webm', 'out.webm', keep_alpha=False)
        assert 'yuv420p' in cmd
        assert 'yuva420p' not in cmd


class TestCompressWebm:
    @patch('imgbatch.core.webm_compress.subprocess.run')
    @patch('imgbatch.core.webm_compress.find_ffmpeg', return_value='/ffmpeg')
    def test_compress_success(self, _find, mock_run):
        def _fake_run(cmd, **kwargs):
            dst = cmd[-1]
            with open(dst, 'wb') as f:
                f.write(b'\x00' * 500)
            return MagicMock(returncode=0, stderr='', stdout='')

        mock_run.side_effect = _fake_run
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'a.webm')
            dst = os.path.join(d, 'b.webm')
            with open(src, 'wb') as f:
                f.write(b'\x00' * 1000)
            size = compress_webm(src, dst, max_edge=256, crf=40)
            assert size == 500
            mock_run.assert_called_once()

    @patch('imgbatch.core.webm_compress.find_ffmpeg', return_value=None)
    def test_missing_ffmpeg_raises(self, _find):
        with pytest.raises(RuntimeError, match='ffmpeg not found'):
            compress_webm('a.webm', 'b.webm')


class TestWebmBatch:
    @patch('imgbatch.core.webm_compress.compress_webm', return_value=500)
    @patch('imgbatch.core.webm_compress.find_ffmpeg', return_value='/ffmpeg')
    def test_batch_processes_webm_only(self, _find, _compress):
        with tempfile.TemporaryDirectory() as d:
            webm = os.path.join(d, 'anim.webm')
            png = os.path.join(d, 'still.png')
            with open(webm, 'wb') as f:
                f.write(b'x' * 800)
            with open(png, 'wb') as f:
                f.write(b'y' * 100)

            class _State:
                cancelled = False

            out_dir = os.path.join(d, 'out')
            result = run_webm_compress_batch(
                _State(), d, ['anim.webm', 'still.png'],
                max_edge=256, crf=40, fps=24, keep_alpha=True,
                do_backup=False, replace=False, out=out_dir,
            )
            assert 'still.png' in result['skipped']
            assert len(result['results']) == 1
            assert result['results'][0]['name'] == 'anim.webm'

    @patch('imgbatch.core.webm_compress.find_ffmpeg', return_value=None)
    def test_batch_no_ffmpeg(self, _find):
        class _State:
            cancelled = False

        result = run_webm_compress_batch(
            _State(), '/tmp', ['a.webm'],
            max_edge=256, crf=40, fps=24, keep_alpha=True,
            do_backup=False, replace=True, out=None,
        )
        assert result['errors']
        assert 'ffmpeg' in result['errors'][0].lower()
