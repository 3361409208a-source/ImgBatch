from pathlib import Path
from PIL import Image

p = Path(__file__).resolve().parents[1] / "public" / "promo" / "purple-section-base.png"
img = Image.open(p).convert("RGBA")
w, h = img.size

# left shelf top at x=10%
x = int(w * 0.1)
top = next(y for y in range(h) if img.getpixel((x, y))[3] > 20)
# bottom inner padding
bottom = next(y for y in range(h - 1, -1, -1) if img.getpixel((x, y))[3] > 20)
# left/right inset at mid content
ym = int(h * 0.5)
left = next(x for x in range(w) if img.getpixel((x, ym))[3] > 20)
right = next(x for x in range(w - 1, -1, -1) if img.getpixel((x, ym))[3] > 20)

print(f"canvas {w}x{h}")
print(f"left_shelf_top={top}px = {100*top/h:.2f}%H = {100*top/w:.2f}%W (cqw)")
print(f"bottom_opaque={bottom} bottom_pad={h-1-bottom} = {100*(h-1-bottom)/w:.2f}%W")
print(f"left_inset={left} = {100*left/w:.2f}%W  right_inset={w-1-right} = {100*(w-1-right)/w:.2f}%W")

# title tab height (right side full) - find where left shelf is
print(f"cutout_depth_for_title_overlap ≈ shelf {top}px / {w} ≈ {100*top/w:.2f}cqw")
