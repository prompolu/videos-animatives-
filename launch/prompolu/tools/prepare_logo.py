"""The official logo from prompolu.com is a 602x83 PNG. Rebuild it at 4x:
upsample its alpha, blur away the palette stair-steps, then re-sharpen the edge with a smoothstep around 50%
coverage so strokes stay crisp at film size. Black ink on transparent."""
import numpy as np
from PIL import Image, ImageFilter
src = Image.open('assets/brand/logo-prompolu-original.png').convert('RGBA')
a = src.getchannel('A')
S = 4
big = np.asarray(a.resize((src.width * S, src.height * S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
lo, hi = 0.38, 0.62
x = np.clip((big - lo) / (hi - lo), 0, 1)
alpha = x * x * (3 - 2 * x)
out = np.zeros(alpha.shape + (4,), np.uint8)
out[..., :3] = 11                      # the film's ink, #0B0B0C
out[..., 3] = (alpha * 255).astype(np.uint8)
# trim to the ink bounds
ys, xs = np.nonzero(out[..., 3] > 8)
out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
Image.fromarray(out).save('assets/brand/prompolu-logo@4x.png', optimize=True)
print(out.shape)
