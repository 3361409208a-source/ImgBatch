"""Normalize promo title PNGs so visible glyph height is identical.

1. Crop to opaque content (alpha threshold)
2. Scale so content height == TARGET_CONTENT_HEIGHT
3. Wrap with uniform transparent padding
"""

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

PROMO_DIR = Path(__file__).resolve().parents[1] / "public" / "promo"

TARGET_CONTENT_HEIGHT = 280
PADDING = 6
# Ignore soft anti-alias fringe so bbox is stable across titles
ALPHA_THRESHOLD = 28

TITLE_FILES = [
    "purple-title-daily-zh.png",
    "purple-title-daily-en.png",
    "purple-title-daily-ms.png",
    "purple-title-vip-zh.png",
    "purple-title-vip-en.png",
    "purple-title-vip-ms.png",
    "purple-title-invite-zh.png",
    "purple-title-invite-en.png",
    "purple-title-announcement-en.png",
    "purple-title-strip.png",
    "purple-title-relief-en.png",
    "purple-title-relief-ms.png",
    "purple-relief-title.png",
    "purple-daily-title.png",
]


def content_bbox(img: Image.Image) -> Optional[Tuple[int, int, int, int]]:
    """BBox of pixels with alpha above threshold."""
    alpha = img.getchannel("A")
    mask = alpha.point(lambda a: 255 if a >= ALPHA_THRESHOLD else 0)
    return mask.getbbox()


def normalize_image(path: Path) -> None:
    with Image.open(path) as img:
        img = img.convert("RGBA")
        bbox = content_bbox(img)
        if not bbox:
            print(f"{path.name}: empty, skipped")
            return

        content = img.crop(bbox)
        cw, ch = content.size
        if ch <= 0:
            return

        scale = TARGET_CONTENT_HEIGHT / ch
        new_w = max(1, round(cw * scale))
        new_h = TARGET_CONTENT_HEIGHT
        scaled = content.resize((new_w, new_h), Image.LANCZOS)

        # Re-crop soft fringe after scale, then pad uniformly
        scaled_bbox = content_bbox(scaled)
        if scaled_bbox:
            scaled = scaled.crop(scaled_bbox)
            # Force exact glyph height again after fringe trim
            sw, sh = scaled.size
            if sh != TARGET_CONTENT_HEIGHT:
                scaled = scaled.resize(
                    (max(1, round(sw * TARGET_CONTENT_HEIGHT / sh)), TARGET_CONTENT_HEIGHT),
                    Image.LANCZOS,
                )

        canvas = Image.new(
            "RGBA",
            (scaled.width + PADDING * 2, TARGET_CONTENT_HEIGHT + PADDING * 2),
            (0, 0, 0, 0),
        )
        canvas.paste(scaled, (PADDING, PADDING), scaled)
        canvas.save(path, optimize=True)
        print(
            f"{path.name}: content {cw}x{ch} -> canvas {canvas.width}x{canvas.height} "
            f"(glyph_h={TARGET_CONTENT_HEIGHT})"
        )


def main() -> None:
    for name in TITLE_FILES:
        path = PROMO_DIR / name
        if path.exists():
            normalize_image(path)
        else:
            print(f"{name}: missing")


if __name__ == "__main__":
    main()
