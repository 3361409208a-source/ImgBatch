from PIL import Image
import os

icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src-tauri", "icons")
os.makedirs(icons_dir, exist_ok=True)

img = Image.new('RGBA', (256, 256), (124, 58, 237, 255))
for x in range(60, 196):
    for y in range(60, 196):
        img.putpixel((x, y), (255, 255, 255, 255))
for x in range(80, 176):
    for y in range(100, 156):
        img.putpixel((x, y), (236, 72, 153, 255))

ico_path = os.path.join(icons_dir, "icon.ico")
png_path = os.path.join(icons_dir, "icon.png")
img.save(ico_path, format='ICO')
img.save(png_path, format='PNG')
print(f"Icons created: {ico_path}, {png_path}")
