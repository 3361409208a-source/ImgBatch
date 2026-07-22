from PIL import Image
import tempfile
import os

# lossy animated RGBA webp like production
imgs = []
for i in range(8):
    img = Image.new('RGBA', (977, 453), (0, 0, 0, 0))
    for x in range(100, 900):
        for y in range(50, 400):
            img.putpixel((x, y), (80 + i * 10, 40, 180, 200))
    imgs.append(img)

d = tempfile.mkdtemp()
src = os.path.join(d, 'big.webp')
imgs[0].save(src, format='WEBP', save_all=True, append_images=imgs[1:], duration=[83]*8, loop=0, lossless=True)
print('src size', os.path.getsize(src))

from imgbatch.core.balanced_compress import compress_anim_to_target
dst = os.path.join(d, 'out.webp')
compress_anim_to_target(src, dst, int(0.6 * 1024 * 1024))
with Image.open(dst) as out:
    print('out frames', out.n_frames, 'animated', out.is_animated, 'size', os.path.getsize(dst))

# test seek-based load vs iterator for edge case
src2 = os.path.join(d, 'seek.webp')
imgs[0].save(src2, format='WEBP', save_all=True, append_images=imgs[1:], duration=[83]*8, loop=0, quality=80)
with Image.open(src2) as im:
    print('lossy src frames', im.n_frames)
