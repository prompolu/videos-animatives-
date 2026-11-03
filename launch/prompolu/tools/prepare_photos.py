"""Crop the 4x EDSR-upscaled photos into the film's tiles and build the
golden-hour twin of the day shot (same pixels, regraded, so both align)."""
import numpy as np
from PIL import Image, ImageFilter
SRC, OUT = 'assets/photos/src', 'assets/photos'
def crop(p, x0, side, out, size):
    im = Image.open(f'{SRC}/{p}.png').convert('RGB'); s = 4
    im.crop((x0 * s, 0, (x0 + side) * s, side * s)).resize((size, size), Image.LANCZOS).save(f'{OUT}/{out}.jpg', quality=92)
tiles = [('p1', 100, 288), ('p2', 0, 288), ('p3', 20, 288), ('p2', 340, 288), ('p3', 300, 288),
         ('p4', 200, 145), ('p5', 20, 288), ('p5', 360, 288), ('p1', 406, 288)]
for i, (p, x, side) in enumerate(tiles):
    crop(p, x, side, f't{i}', 1152)
crop('p3', 300, 288, 'day', 1440)
crop('p4', 200, 145, 'art', 480)
Image.open(f'{SRC}/p1.png').convert('RGB').save(f'{OUT}/hero.jpg', quality=92)

day = np.asarray(Image.open(f'{OUT}/day.jpg'), np.float32) / 255
H, W = day.shape[:2]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / W
lum = (day @ np.array([.299, .587, .114], np.float32))[..., None]
sun = np.exp(-(((xx - 0.78) ** 2) / 0.35 + ((yy - 0.38) ** 2) / 0.12))[..., None]
g = day ** 1.12
g = g * np.array([1.12, 0.93, 0.70], np.float32)
hi = np.clip((lum - 0.55) / 0.4, 0, 1)
g = g * (1 - hi * 0.5) + hi * 0.5 * np.array([1.0, 0.72, 0.42], np.float32) * (0.75 + 0.5 * lum)
g = g * (0.62 + 0.55 * sun) + 0.10 * sun * np.array([1.0, 0.55, 0.2], np.float32)
g = g * (1 - 0.35 * np.clip(yy - 0.55, 0, 1)[..., None])
Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/gold.jpg', quality=92)
