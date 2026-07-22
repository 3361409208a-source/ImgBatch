from PIL import Image, ImageSequence
import tempfile
import os

from imgbatch.core.balanced_compress import load_animation

imgs = []
for i in range(8):
    img = Image.new('RGBA', (400, 200), (0, 0, 0, 0))
    for x in range(20 + i * 5, 380):
        for y in range(20, 180):
            img.putpixel((x, y), (50 + i * 20, 100, 200, 255))
    imgs.append(img)

d = tempfile.mkdtemp()
p = os.path.join(d, 't.webp')
imgs[0].save(p, format='WEBP', save_all=True, append_images=imgs[1:], duration=[83] * 8, loop=0, lossless=True)

with Image.open(p) as im:
    print('n_frames attr', im.n_frames)
    print('iterator', len(list(ImageSequence.Iterator(im))))
    for i in range(im.n_frames):
        im.seek(i)
        print('seek', i, 'size', im.size)

frames, durs, loop, fmt = load_animation(p)
print('loaded', len(frames), 'durs', len(durs))
