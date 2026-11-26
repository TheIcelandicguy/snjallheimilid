"""The batch's pictures as the page's: python tools/lines3d/to_webp.py <folder of PNGs>

lines3d.py --batch renders each frame with 22 mm of see-through wall round it, at 4 px to the millimetre. This trims that to MARGIN mm, which still holds
the shadow, and writes img/lines3d/<same name>.webp with its transparency. tools/lines_view.py lays the pictures out with the same MARGIN. Needs Pillow.
"""
import os
import sys

from PIL import Image

PX, RENDERED, MARGIN = 4, 22, 12
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'img', 'lines3d')


def main():
    src = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    cut, n, size = (RENDERED - MARGIN) * PX, 0, 0
    for f in sorted(os.listdir(src)):
        if not f.endswith('.png'):
            continue
        im = Image.open(os.path.join(src, f)).convert('RGBA')
        im = im.crop((cut, cut, im.width - cut, im.height - cut))
        out = os.path.join(OUT, f[:-4] + '.webp')
        im.save(out, 'WEBP', quality=82, method=6)
        n, size = n + 1, size + os.path.getsize(out)
    print(n, 'pictures,', size // 1024, 'KB')


if __name__ == '__main__':
    main()
