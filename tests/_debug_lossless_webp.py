from PIL import Image
import tempfile
import os

imgs = []
for i in range(8):
    img = Image.new('RGBA', (400, 200), (0, 0, 0, 0))
    for x in range(20 + i * 5, 380):
        for y in range(20, 180):
            img.putpixel((x, y), (50 + i * 20, 100, 200, 255))
    imgs.append(img)

d = tempfile.mkdtemp()
durations = [83] * 8

for q in [30, 36, 80]:
    path = os.path.join(d, f'q{q}.webp')
    imgs[0].save(
        path, format='WEBP', save_all=True, append_images=imgs[1:],
        duration=durations, loop=0, quality=q, method=4,
    )
    with Image.open(path) as out:
        print('quality', q, 'frames', out.n_frames, 'animated', out.is_animated, 'size', os.path.getsize(path))

# lossless
path = os.path.join(d, 'lossless.webp')
imgs[0].save(
    path, format='WEBP', save_all=True, append_images=imgs[1:],
    duration=durations, loop=0, lossless=True, method=4,
)
with Image.open(path) as out:
    print('lossless frames', out.n_frames, 'size', os.path.getsize(path))
