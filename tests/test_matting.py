# -*- coding: utf-8 -*-
"""Unit tests for smart background removal / matting module."""

import os
from PIL import Image
from imgbatch.core.matting import matting_image, parse_hex_color, run_matting_batch
from imgbatch.api.tasks import TaskState


def test_parse_hex_color():
    assert parse_hex_color('#FFFFFF') == (255, 255, 255)
    assert parse_hex_color('#DC2626') == (220, 38, 38)
    assert parse_hex_color('red') == (220, 38, 38)
    assert parse_hex_color('blue') == (37, 99, 235)


def test_matting_image_transparent(tmp_path):
    src = str(tmp_path / "sample.png")
    dst = str(tmp_path / "out.png")

    # Create a 50x50 test image with white background and red square in center
    img = Image.new('RGB', (50, 50), (255, 255, 255))
    for x in range(15, 35):
        for y in range(15, 35):
            img.putpixel((x, y), (255, 0, 0))
    img.save(src)

    size = matting_image(src, dst, engine='smart', bg_mode='transparent', sensitivity=30)
    assert os.path.exists(dst)
    assert size > 0

    with Image.open(dst) as res:
        assert res.mode == 'RGBA'
        # Center should be opaque red
        r, g, b, a = res.getpixel((25, 25))
        assert r > 200 and a > 200
        # Corner should be transparent
        _, _, _, a_corner = res.getpixel((0, 0))
        assert a_corner == 0


def test_matting_image_color(tmp_path):
    src = str(tmp_path / "sample.png")
    dst = str(tmp_path / "out_blue.jpg")

    img = Image.new('RGB', (50, 50), (255, 255, 255))
    for x in range(15, 35):
        for y in range(15, 35):
            img.putpixel((x, y), (0, 255, 0))
    img.save(src)

    size = matting_image(src, dst, engine='smart', bg_mode='color', bg_color='#2563EB', sensitivity=30)
    assert os.path.exists(dst)
    assert size > 0

    with Image.open(dst) as res:
        # Corner should now be blue (#2563EB)
        r, g, b = res.getpixel((0, 0))
        assert b > 200 and r < 50


def test_run_matting_batch(tmp_path):
    folder = str(tmp_path)
    f1 = "pic1.png"
    img = Image.new('RGB', (30, 30), (255, 255, 255))
    img.save(os.path.join(folder, f1))

    state = TaskState()
    res = run_matting_batch(
        state, folder, [f1],
        engine='smart',
        bg_mode='transparent',
        do_backup=False,
        replace=True,
    )
    assert res['total_after'] > 0
    assert len(res['errors']) == 0
