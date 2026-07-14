#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def tmp_image_dir():
    """Create a temp directory with test images of various formats."""
    with tempfile.TemporaryDirectory() as d:
        # Create a small RGB JPEG
        img = Image.new('RGB', (100, 80), (255, 100, 50))
        img.save(os.path.join(d, 'test1.jpg'), quality=85)
        img.save(os.path.join(d, 'test2.jpg'), quality=85)

        # Create a PNG with transparency
        img_png = Image.new('RGBA', (120, 90), (0, 0, 0, 0))
        for x in range(20, 100):
            for y in range(15, 75):
                img_png.putpixel((x, y), (255, 0, 0, 200))
        img_png.save(os.path.join(d, 'test3.png'))
        img_png.save(os.path.join(d, 'test4.png'))

        # Create a WEBP
        img.save(os.path.join(d, 'test5.webp'), quality=80)

        yield d


@pytest.fixture
def tmp_png_dir():
    """Create a temp directory with PNG files of various sizes for trim/normalize tests."""
    with tempfile.TemporaryDirectory() as d:
        # PNG with transparent border
        img = Image.new('RGBA', (200, 150), (0, 0, 0, 0))
        for x in range(50, 150):
            for y in range(40, 110):
                img.putpixel((x, y), (0, 255, 0, 255))
        img.save(os.path.join(d, 'border1.png'))

        # Fully transparent PNG
        Image.new('RGBA', (100, 100), (0, 0, 0, 0)).save(os.path.join(d, 'empty.png'))

        # Solid PNG
        Image.new('RGBA', (80, 60), (255, 0, 0, 255)).save(os.path.join(d, 'solid.png'))

        yield d
