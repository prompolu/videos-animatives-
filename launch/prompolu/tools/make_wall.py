"""Procedural stand-in for the wall footage: a plaster wall in late sun with
swaying plant shadows. Writes a 1440x1440 30 fps H.264 clip; the film loads
it like any real clip (all-intra re-encode, blob URL, seek per frame)."""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1440
FPS, SEC = 30, 6
S = 0.5  # shadow mask render scale
rng = np.random.default_rng(7)

# static wall: warm plaster, low-frequency mottling, fine grain
def smooth_noise(scale, seed):
    r = np.random.default_rng(seed)
    n = r.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255
mott = 0.6 * smooth_noise(180, 1) + 0.3 * smooth_noise(60, 2) + 0.1 * smooth_noise(14, 3)
grain = rng.normal(0, 1, (H, W)).astype(np.float32)
base = np.array([236, 229, 217], np.float32) / 255
wall = base[None, None] * (0.95 + 0.07 * (mott[..., None] - 0.5)) + 0.006 * grain[..., None]

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# sun patch: a soft slanted window of light
u = (xx - 0.18 * yy) / W
v = yy / H
patch = np.clip((u + 0.05) / 0.08, 0, 1) * np.clip((1.02 - u) / 0.12, 0, 1) * np.clip((v + 0.02) / 0.1, 0, 1)
patch = np.asarray(Image.fromarray((patch * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30)), np.float32) / 255
sun = np.array([1.0, 0.93, 0.80], np.float32)
ambient = np.array([0.80, 0.81, 0.84], np.float32)

# plant: stems with paired leaflets (palm/kentia-like), each stem sways
stems = []
for i in range(9):
    stems.append(dict(
        root=(rng.uniform(-0.15, 0.25) * W, rng.uniform(1.0, 1.25) * H),
        ang=math.radians(rng.uniform(-80, -30)), length=rng.uniform(0.75, 1.15) * W,
        curl=rng.uniform(0.25, 0.6), f=rng.uniform(0.18, 0.32), ph=rng.uniform(0, 6.28),
        amp=math.radians(rng.uniform(1.5, 3.5)), depth=rng.uniform(0, 1)))

def draw_stem(d, st, t, sc):
    sway = st['amp'] * math.sin(2 * math.pi * st['f'] * t + st['ph']) + 0.5 * st['amp'] * math.sin(2 * math.pi * 0.71 * t + st['ph'] * 1.7)
    x, y = st['root']; a = st['ang'] + sway
    n = 26; seg = st['length'] / n
    pts = []
    for k in range(n):
        a += st['curl'] / n + 0.25 * sway / n
        x += seg * math.cos(a); y += seg * math.sin(a)
        pts.append((x, y, a))
    d.line([(p[0] * sc, p[1] * sc) for p in pts], fill=255, width=max(1, int(7 * sc)))
    for k, (px, py, pa) in enumerate(pts[3:], 3):
        flut = 0.12 * math.sin(2 * math.pi * 0.9 * t + k * 0.6 + st['ph'])
        L = st['length'] * 0.20 * math.sin(math.pi * k / n) ** 0.6
        for side in (-1, 1):
            la = pa + side * (1.05 + flut)
            tipx, tipy = px + L * math.cos(la + side * 0.25), py + L * math.sin(la + side * 0.25)
            nx, ny = -math.sin(la), math.cos(la)
            wdt = L * 0.07
            mx, my = px + 0.5 * L * math.cos(la), py + 0.5 * L * math.sin(la)
            poly = [(px, py), (mx + nx * wdt, my + ny * wdt), (tipx, tipy), (mx - nx * wdt, my - ny * wdt)]
            d.polygon([(qx * sc, qy * sc) for qx, qy in poly], fill=255)

def shadow(t):
    out = np.zeros((H, W), np.float32)
    for layer, blur, strength in ((lambda s: s['depth'] > 0.5, 22, 0.55), (lambda s: s['depth'] <= 0.5, 9, 0.8)):
        im = Image.new('L', (int(W * S), int(H * S)), 0)
        d = ImageDraw.Draw(im)
        for st in stems:
            if layer(st): draw_stem(d, st, t, S)
        im = im.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))
        out = np.maximum(out, strength * np.asarray(im, np.float32) / 255)
    return out

ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', sys.argv[1]], stdin=subprocess.PIPE)
for f in range(FPS * SEC):
    t = f / FPS
    lit = patch * (1 - shadow(t))
    light = ambient[None, None] + 0.42 * lit[..., None] * sun[None, None]
    img = np.clip(wall * light * 255, 0, 255).astype(np.uint8)
    ff.stdin.write(img.tobytes())
ff.stdin.close(); ff.wait()
