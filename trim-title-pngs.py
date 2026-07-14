from pathlib import Path
from PIL import Image

PROMO_DIR = Path(__file__).resolve().parents[1] / "public" / "promo"
PADDING = 4


def trim_image(path: Path) -> None:
    with Image.open(path) as img:
        img = img.convert("RGBA")
        bbox = img.getbbox()
        if not bbox:
            return

        left = max(0, bbox[0] - PADDING)
        top = max(0, bbox[1] - PADDING)
        right = min(img.width, bbox[2] + PADDING)
        bottom = min(img.height, bbox[3] + PADDING)
        cropped = img.crop((left, top, right, bottom))
        cropped.save(path, optimize=True)
        print(f"{path.name}: {cropped.width}x{cropped.height}")


def main() -> None:
    files = sorted(
        {
            *PROMO_DIR.glob("purple-title-*.png"),
            PROMO_DIR / "purple-relief-title.png",
            PROMO_DIR / "purple-daily-title.png",
        }
    )
    for file in files:
        if file.exists():
            trim_image(file)


if __name__ == "__main__":
    main()
