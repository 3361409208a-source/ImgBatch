from PIL import Image, ImageSequence
import tempfile
import os

from imgbatch.core.balanced_compress import load_animation, compress_anim_to_target

imgs = []
for i in range(4):
    img = Image.new('RGBA', (200, 100), (0, 0, 0, 0))
    for x in range(20, 180):
        for y in range(20, 80):
            img.putpixel((x, y), (50 + i * 40, 100, 200, 255))
    imgs.append(img)

d = tempfile.mkdtemp()
src = os.path.join(d, 'a.webp')
imgs[0].save(
    src, format='WEBP', save_all=True, append_images=imgs[1:],
    duration=[80] * 4, loop=0, lossless=True,
)

with Image.open(src) as im:
    print('src n_frames', getattr(im, 'n_frames', 1), 'animated', getattr(im, 'is_animated', False))
    print('iterator frames', len(list(ImageSequence.Iterator(im))))

frames, durs, loop, fmt = load_animation(src)
print('loaded', len(frames), fmt)
dst = os.path.join(d, 'out.webp')
meta = compress_anim_to_target(src, dst, 50_000)
with Image.open(dst) as out:
    print('out n_frames', getattr(out, 'n_frames', 1), 'animated', getattr(out, 'is_animated', False), 'meta', meta)
