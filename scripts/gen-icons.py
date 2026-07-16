#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate ImgBatch app icons (teal brand, no purple)."""

import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "src-tauri", "icons")
os.makedirs(OUT, exist_ok=True)

size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

pad = 28
radius = 96
bg = (15, 118, 110, 255)  # #0F766E
d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=radius, fill=bg)

inner = 88
d.rounded_rectangle(
    [inner, inner, size - inner, size - inner],
    radius=64,
    fill=(248, 255, 254, 255),
)

frame = (15, 118, 110, 255)
d.rounded_rectangle([160, 150, 352, 300], radius=28, outline=frame, width=18)
d.rounded_rectangle([190, 250, 300, 272], radius=8, fill=(13, 148, 136, 255))
d.rounded_rectangle([310, 320, 380, 390], radius=18, fill=(51, 65, 85, 255))
d.rounded_rectangle([326, 336, 364, 374], radius=8, fill=(248, 255, 254, 255))

png_path = os.path.join(OUT, "icon.png")
img.save(png_path, "PNG")
print("wrote", png_path)

for s in (32, 128, 256):
    img.resize((s, s), Image.Resampling.LANCZOS).save(
        os.path.join(OUT, f"{s}x{s}.png")
    )

ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ico_images = [img.resize(sz, Image.Resampling.LANCZOS) for sz in ico_sizes]
ico_path = os.path.join(OUT, "icon.ico")
ico_images[0].save(
    ico_path, format="ICO", sizes=ico_sizes, append_images=ico_images[1:]
)
print("wrote", ico_path)
