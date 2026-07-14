"""Inspect promo title PNGs: canvas size + non-transparent content bbox."""

from pathlib import Path
from PIL import Image

PROMO_DIR = Path(__file__).resolve().parents[1] / "public" / "promo"

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


def main() -> None:
    for name in TITLE_FILES:
        path = PROMO_DIR / name
        if not path.exists():
            print(f"{name}: MISSING")
            continue
        with Image.open(path) as img:
            img = img.convert("RGBA")
            bbox = img.getbbox()
            cw = ch = 0
            if bbox:
                cw = bbox[2] - bbox[0]
                ch = bbox[3] - bbox[1]
            print(
                f"{name}: canvas={img.width}x{img.height} "
                f"content={cw}x{ch} top_pad={bbox[1] if bbox else '-'} "
                f"bot_pad={img.height - bbox[3] if bbox else '-'}"
            )


if __name__ == "__main__":
    main()
