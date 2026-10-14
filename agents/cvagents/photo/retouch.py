"""Make a camera photo look professional: background removed (rembg) and made neutral grey, square crop on head and shoulders,
even light. Run as `python -m cvagents.photo.retouch <photo> <result>` so that rembg (slow to load) stays out of the other commands."""
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageOps, ImageStat
from rembg import new_session, remove

BACKGROUND = (236, 238, 241)
SIZE = 600
MODEL = "u2net_human_seg"
MODELS = Path(__file__).resolve().parents[2] / "data" / "models"


def head_and_shoulders(mask):
    """Square box: centred on the head, starting a little above it, as wide as the shoulders allow inside the picture."""
    width, height = mask.size
    left, top, right, bottom = mask.getbbox() or (0, 0, width, height)
    side = min(width, height, max(right - left, (bottom - top) * 3 // 4))
    head = mask.crop((0, top, width, min(height, top + side // 4))).getbbox()
    centre = (head[0] + head[2]) // 2 if head else (left + right) // 2
    x = min(max(0, centre - side // 2), width - side)
    y = min(max(0, top - side // 8), height - side)
    return x, y, x + side, y + side


def fill_holes(mask):
    """Holes inside the person (e.g. a burnt-out cheek, as white as the wall) become person: what the background,
    flooded from the top corners, cannot reach. Done on a small copy, flood fill is slow on big images."""
    small = mask.resize((max(1, mask.width // 4), max(1, mask.height // 4)))
    for corner in ((0, 0), (small.width - 1, 0)):
        if small.getpixel(corner) == 0:
            ImageDraw.floodfill(small, corner, 128)
    return ImageChops.lighter(mask, small.point(lambda v: 0 if v == 128 else 255).resize(mask.size))


def even_light(image, mask):
    """Brightness of the person towards a mid level (within limits), never brighter if parts are already burnt out."""
    gray = image.convert("L")
    histogram = gray.histogram(mask)
    factor = min(1.25, max(0.85, 120 / (ImageStat.Stat(gray, mask).mean[0] or 1)))
    if sum(histogram[245:]) > 0.02 * max(1, sum(histogram)):
        factor = min(factor, 1.0)
    return ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(factor)).enhance(1.05)


def professional(src, dest):
    """Write the professional version of `src` to `dest` (square PNG) and return its path."""
    os.environ.setdefault("U2NET_HOME", str(MODELS))  # ~176 MB downloaded the first time: in data/, not in a small home
    image = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    alpha = remove(image, session=new_session(MODEL)).getchannel("A").point(lambda a: 0 if a < 40 else a)
    holes = fill_holes(alpha.point(lambda a: 255 if a > 128 else 0))
    alpha, mask = ImageChops.lighter(alpha, holes), holes
    result = Image.new("RGB", image.size, BACKGROUND)
    result.paste(even_light(image, mask), mask=alpha)
    result.crop(head_and_shoulders(mask)).resize((SIZE, SIZE), Image.LANCZOS).save(dest)
    return str(dest)


if __name__ == "__main__":
    print(professional(sys.argv[1], sys.argv[2]))
