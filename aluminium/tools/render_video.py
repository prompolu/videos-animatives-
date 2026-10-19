#!/usr/bin/env python3
"""Aluminium joinery — editable 60-second 2D motion-design film.

Render one language:  python3 aluminium/tools/render_video.py --lang fr
Review stills only:   python3 aluminium/tools/render_video.py --lang fr --stills
Texts, company name, website, phone and colours live in aluminium/brand.json.
All illustrations (windows, doors, façades, verandas, railings) are drawn here
with Pillow and NumPy; no photos, stock footage or external services are used.
"""
from __future__ import annotations

import argparse
import functools
import json
import math
from multiprocessing import Pool
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
BRAND = json.loads((ROOT / "brand.json").read_text())
W, H, FPS, DURATION = 1920, 1080, 30, 60
COLORS = BRAND["colors"]
ACCENT, ACCENT_LIGHT = COLORS["accent"], COLORS["accent_light"]
INK = COLORS.get("ink", "#1B2329")
PAPER = COLORS.get("paper", "#F3F4F5")
GRAY = "#6A6862"
WHITE = "#FFFFFF"
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
FONT_PATHS = {
    "bold": FONT_DIR / "InterDisplay-Bold.otf",
    "semi": FONT_DIR / "Inter-SemiBold.otf",
    "medium": FONT_DIR / "Inter-Medium.otf",
    "regular": FONT_DIR / "Inter-Regular.otf",
}
SCENES = [
    {"start": 0, "end": 7, "name": "Aluminium sur mesure", "theme": "dark"},
    {"start": 7, "end": 15, "name": "De la mesure à la pose", "theme": "light"},
    {"start": 15, "end": 24, "name": "Fenêtres et portes", "theme": "steel"},
    {"start": 24, "end": 33, "name": "Façades, vérandas, garde-corps", "theme": "warm"},
    {"start": 33, "end": 43, "name": "Pourquoi l’aluminium", "theme": "dark"},
    {"start": 43, "end": 51, "name": "Parlons de votre projet", "theme": "light"},
    {"start": 51, "end": 60, "name": "Contact", "theme": "dark"},
]
# Profile finishes: base, highlight, shadow, groove.
TONES = {
    "anth": ("#3A4148", "#66717B", "#1F2428", "#4A535B"),
    "silver": ("#B9C0C6", "#EEF1F3", "#858D94", "#A3ABB2"),
}
LANG = "fr"
T: dict = {}


def set_lang(lang):
    global LANG, T
    LANG, T = lang, BRAND["text"][lang]


def rgb(value):
    if isinstance(value, tuple):
        return value[:3]
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def rgba(value, alpha):
    return rgb(value) + (alpha,)


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1-x)**3


def wave(age, period, phase=0.0):
    """0 → 1 → 0, starting closed, for opening sashes and leaves."""
    return 0.5 - 0.5*math.cos(2*math.pi*(age/period) + phase)


# ---------------------------------------------------------------- typography

@functools.lru_cache(maxsize=100)
def font(size, weight="regular"):
    return ImageFont.truetype(str(FONT_PATHS[weight]), size)


@functools.lru_cache(maxsize=600)
def text_sprite(text, size, color, weight="regular", tracking=0):
    f = font(size, weight)
    width = int(sum(f.getlength(c) for c in text) + tracking*max(0, len(text)-1)) + 12 \
        if tracking else int(f.getlength(text)) + 12
    result = Image.new("RGBA", (max(1, width), size*2), (0, 0, 0, 0))
    d = ImageDraw.Draw(result)
    if tracking:
        # Per-glyph drawing on a shared baseline keeps accented capitals (Ê, Ç) intact.
        x, ascent = 3, f.getmetrics()[0]
        for c in text:
            d.text((x, ascent), c, font=f, fill=color, anchor="ls")
            x += f.getlength(c) + tracking
    else:
        d.text((3, 0), text, font=f, fill=color, anchor="lt")
    box = result.getbbox()
    return result.crop((0, 0, width, (box[3] if box else size) + 5))


def paste(im, sprite, xy, opacity=1):
    if opacity <= 0:
        return
    if opacity < 0.995:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a*opacity)))
    im.paste(sprite, (int(xy[0]), int(xy[1])), sprite)


def txt(im, text, xy, size=38, color=INK, weight="regular", opacity=1,
        tracking=0, center=False, right=False):
    sprite = text_sprite(text, size, color, weight, tracking)
    x, y = xy
    if center:
        x -= sprite.width/2
    elif right:
        x -= sprite.width
    paste(im, sprite, (x, y), opacity)


def lines(im, content, xy, size, color, age=3, delay=.3, leading=None,
          weight="bold", center=False, maxw=None):
    content = content.split("\n") if isinstance(content, str) else content
    leading = leading or int(size*1.11)
    if maxw:
        # Shrink the whole block together so long translations never overflow.
        start = size
        while size > 20 and max(text_sprite(l, size, color, weight).width for l in content) > maxw:
            size -= 2
        leading = int(leading*size/start)
    for i, line in enumerate(content):
        p = ease((age-delay-i*.11)/.8)
        txt(im, line, (xy[0], xy[1]+i*leading+28*(1-p)), size, color, weight, p, center=center)


def pill(im, text, xy, age=4, dark=False, delay=.4):
    p = ease((age-delay)/.7)
    sprite = text_sprite(text, 22, ACCENT_LIGHT if dark else ACCENT, "medium", 2)
    width = sprite.width+56
    card = Image.new("RGBA", (width, 58))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, width-1, 57), 29,
                        fill=(255, 255, 255, 26) if dark else rgba(ACCENT, 30),
                        outline=(255, 255, 255, 60) if dark else rgba(ACCENT, 70))
    paste(card, sprite, ((width-sprite.width)/2, (58-sprite.height)/2))
    paste(im, card, (xy[0], xy[1]+15*(1-p)), p)


# ------------------------------------------------------------- drawing utils

def supersample(w, h, k=3):
    return Image.new("RGBA", (w*k, h*k), (0, 0, 0, 0)), k


def down(im, w, h):
    return im.convert("RGBa").resize((w, h), Image.Resampling.LANCZOS).convert("RGBA")


def vgrad(w, h, top, bottom, alpha=255):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = np.array(rgb(top), np.float32)*(1-t) + np.array(rgb(bottom), np.float32)*t
    arr = np.repeat(arr, w, axis=1)
    a = np.full((h, w, 1), alpha, np.float32)
    return Image.fromarray(np.uint8(np.concatenate([arr, a], axis=2)), "RGBA")


@functools.lru_cache(maxsize=6)
def background(theme):
    y, x = np.mgrid[0:H, 0:W]
    if theme == "dark":
        a, b = np.array(rgb(COLORS["dark"])), np.array(rgb(COLORS["dark_2"]))
        glow = np.exp(-(((x-1500)/900)**2 + ((y-420)/780)**2))*.85
    elif theme == "steel":
        a, b = np.array(rgb("#F4F3F0")), np.array(rgb("#DCDDDC"))
        glow = np.exp(-(((x-1400)/700)**2 + ((y-500)/650)**2))*.9
    elif theme == "warm":
        a, b = np.array(rgb("#F5F3EE")), np.array(rgb("#E3DED5"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-500)/700)**2))*.88
    else:
        a, b = np.array(rgb(PAPER)), np.array(rgb("#E0DDD6"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-470)/750)**2))*.7
    result = a[None, None, :]*(1-glow[..., None]) + b[None, None, :]*glow[..., None]
    return Image.fromarray(np.uint8(result), "RGB").convert("RGBA")


@functools.lru_cache(maxsize=40)
def sweep_grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return (x + y*.55)/(w + h*.55)


def sweep(im, mask, pos, strength=.42, width=.06, xy=(0, 0)):
    """Moving light reflection across glass or anodised metal, clipped by mask."""
    w, h = mask.size
    band = np.exp(-((sweep_grid(w, h)-pos)/width)**2)*strength
    band += np.exp(-((sweep_grid(w, h)-pos-.09)/(width*.35))**2)*strength*.6
    alpha = np.uint8(np.clip(band*np.asarray(mask, np.float32), 0, 255))
    layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    layer.putalpha(Image.fromarray(alpha, "L"))
    im.alpha_composite(layer, (int(xy[0]), int(xy[1])))


def sweep_pos(age, speed=.24, phase=0.0):
    return ((age*speed + phase) % 1.7) - .35


@functools.lru_cache(maxsize=40)
def rounded_mask(w, h, r):
    m, k = Image.new("L", (w*3, h*3), 0), 3
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w*k-1, h*k-1), r*k, fill=255)
    return m.resize((w, h), Image.Resampling.LANCZOS)


# ------------------------------------------------------- aluminium components

@functools.lru_cache(maxsize=120)
def metal_ring(w, h, t, tone="anth"):
    """Rectangular aluminium frame with a bevel and a central groove."""
    base, hi, lo, mid = TONES[tone]
    im, k = supersample(w, h)
    d = ImageDraw.Draw(im)
    W2, H2, T2, lw = w*k, h*k, t*k, k
    d.rectangle((0, 0, W2-1, H2-1), fill=base)
    d.rectangle((T2, T2, W2-1-T2, H2-1-T2), fill=(0, 0, 0, 0))
    m = T2//2
    d.rectangle((m, m, W2-1-m, H2-1-m), outline=mid, width=lw)
    d.line((0, lw, W2-1, lw), fill=hi, width=lw*2)
    d.line((lw, 0, lw, H2-1), fill=hi, width=lw*2)
    d.line((0, H2-1-lw, W2-1, H2-1-lw), fill=lo, width=lw*2)
    d.line((W2-1-lw, 0, W2-1-lw, H2-1), fill=lo, width=lw*2)
    d.line((T2, T2, W2-1-T2, T2), fill=lo, width=lw*2)
    d.line((T2, T2, T2, H2-1-T2), fill=lo, width=lw*2)
    d.line((T2, H2-1-T2, W2-1-T2, H2-1-T2), fill=hi, width=lw)
    d.line((W2-1-T2, T2, W2-1-T2, H2-1-T2), fill=hi, width=lw)
    return down(im, w, h)


@functools.lru_cache(maxsize=120)
def glass(w, h, alpha=150):
    im = vgrad(w, h, "#9CC9E2", "#D3E8F3", alpha)
    over, k = supersample(w, h)
    d = ImageDraw.Draw(over)
    W2, H2 = w*k, h*k
    d.polygon([(W2*.18, 0), (W2*.42, 0), (W2*.08, H2), (-W2*.16, H2)], fill=(255, 255, 255, 55))
    d.polygon([(W2*.50, 0), (W2*.56, 0), (W2*.22, H2), (W2*.16, H2)], fill=(255, 255, 255, 38))
    im.alpha_composite(down(over, w, h))
    return im


@functools.lru_cache(maxsize=120)
def sash(w, h, t, tone="anth", handle=None):
    im = Image.new("RGBA", (w, h))
    im.alpha_composite(glass(max(1, w-2*t+2), max(1, h-2*t+2)), (t-1, t-1))
    im.alpha_composite(metal_ring(w, h, t, tone))
    if handle:
        d = ImageDraw.Draw(im)
        hx = t*.5 if handle == "left" else w-t*.5
        hw, hh = max(3, t*.32), max(10, h*.12)
        d.rounded_rectangle((hx-hw/2, h*.48-hh/2, hx+hw/2, h*.48+hh/2), hw/2,
                            fill="#D9DEE2", outline="#7F8890")
    return im


@functools.lru_cache(maxsize=40)
def outside_view(w, h):
    im = vgrad(w, h, "#B8D9EE", "#EEF5F9")
    over, k = supersample(w, h)
    d = ImageDraw.Draw(over)
    W2, H2 = w*k, h*k
    d.ellipse((W2*.68, H2*.14, W2*.84, H2*.14+W2*.16), fill=(255, 249, 226, 210))
    for level, color, amp, freq in [(.66, (186, 208, 203, 255), .06, 2.3), (.76, (160, 187, 178, 255), .05, 3.4)]:
        pts = [(x, H2*(level - amp*math.sin(x/W2*freq*math.pi + level*7))) for x in np.linspace(0, W2, 40)]
        d.polygon(pts + [(W2, H2), (0, H2)], fill=color)
    im.alpha_composite(down(over, w, h))
    return im


@functools.lru_cache(maxsize=40)
def interior_view(w, h):
    im = vgrad(w, h, "#6F7780", "#454C53")
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h*.86), w, h), fill="#8C7863")
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((w*.55, -h*.3, w*1.05, h*.55), fill=(255, 226, 170, 70))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(2, w//14))))
    return im


@functools.lru_cache(maxsize=10)
def cloud(w):
    h, k = int(w*.42), 3
    mask = Image.new("L", (w*k, h*k), 0)
    d = ImageDraw.Draw(mask)
    W2, H2 = w*k, h*k
    for x, y, r in [(.28, .62, .20), (.48, .46, .26), (.70, .60, .20), (.50, .70, .23)]:
        d.ellipse((W2*(x-r), H2*y-W2*r, W2*(x+r), H2*y+W2*r*.8), fill=215)
    im = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    im.putalpha(mask.resize((w, h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)))
    return im


def clouds(im, w, h, age, top=.08, scale=1.0, seed=0):
    for i in range(3):
        cw = int(w*(.20+.06*((i+seed) % 2))*scale)
        span = w + cw
        x = ((i*.38 + seed*.17)*span + age*w*.018*(1+i*.3)) % span - cw
        y = h*(top + .09*i)
        paste(im, cloud(cw), (x, y), .9)


def sky(w, h, top="#AFD3EA", bottom="#EAF3F8"):
    return vgrad(w, h, top, bottom)


def wood(d, box, k=1, slats=7):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill="#B88B5E")
    step = (x1-x0)/slats
    for i in range(1, slats):
        x = x0 + i*step
        d.line((x, y0, x, y1), fill="#94693F", width=max(1, k))


def plant(d, box, k=1):
    x0, y0, x1, y1 = box
    w, h = x1-x0, y1-y0
    d.polygon([(x0+w*.22, y0+h*.62), (x0+w*.78, y0+h*.62), (x0+w*.70, y1), (x0+w*.30, y1)], fill="#CFC7BC")
    for cx, cy, r, c in [(.50, .30, .30, "#5D7D69"), (.30, .42, .22, "#6F8F79"), (.70, .40, .22, "#4F6E5B"),
                         (.50, .48, .20, "#77977F")]:
        d.ellipse((x0+w*(cx-r), y0+h*cy-w*r, x0+w*(cx+r), y0+h*cy+w*r), fill=c)


def find_coeffs(dst, src):
    rows, rhs = [], []
    for (x, y), (X, Y) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -X*x, -X*y])
        rows.append([0, 0, 0, x, y, 1, -Y*x, -Y*y])
        rhs += [X, Y]
    return tuple(np.linalg.solve(np.array(rows, float), np.array(rhs, float)))


def shade(im, factor):
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] *= factor
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)), "RGBA")


# ------------------------------------------------------------ illustrations

def place_sliding(im, box, opening, view):
    """Two-rail sliding window; the right sash glides over the fixed one."""
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1-x0, y1-y0
    f, s = max(6, int(w*.04)), max(5, int(w*.032))
    im.alpha_composite(view(w-2*f, h-2*f), (x0+f, y0+f))
    iw, ih = w-2*f, h-2*f
    sw = iw//2 + s//2
    im.alpha_composite(sash(sw, ih, s), (x0+f, y0+f))
    x = x0+f + iw - sw - opening*(iw-sw)*.82
    im.alpha_composite(sash(sw, ih, s, handle="left"), (int(x), y0+f))
    im.alpha_composite(metal_ring(w, h, f), (x0, y0))


@functools.lru_cache(maxsize=10)
def sliding_base(w, h):
    im = vgrad(w, h, "#F1EFEB", "#E4E1DB")
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h*.87), w, h), fill="#D3C5B1")
    d.line((0, int(h*.87), w, int(h*.87)), fill="#BBAA93", width=2)
    plant(d, (w*.83, h*.50, w*.98, h*.87))
    return im


def illus_sliding(w, h, age):
    im = sliding_base(w, h).copy()
    place_sliding(im, (w*.08, h*.08, w*.80, h*.87), wave(age, 6.5), outside_view)
    return im


@functools.lru_cache(maxsize=10)
def casement_base(w, h):
    im = vgrad(w, h, "#F1EFEB", "#E6E2DC")
    box = [int(w*.30), int(h*.07), int(w*.70), int(h*.78)]
    bw, bh = box[2]-box[0], box[3]-box[1]
    f = max(6, int(bw*.06))
    im.alpha_composite(outside_view(bw-2*f, bh-2*f), (box[0]+f, box[1]+f))
    im.alpha_composite(metal_ring(bw, bh, f), (box[0], box[1]))
    d = ImageDraw.Draw(im)
    d.rectangle((w*.27, h*.78, w*.73, h*.83), fill="#D6D0C7", outline="#C2BAAE")
    for cx in (.16, .84):
        d.rectangle((w*(cx-.075), 0, w*(cx+.075), h), fill="#E3DACE")
        for j in range(4):
            x = w*(cx-.06+j*.04)
            d.line((x, 0, x, h), fill="#D3C8B9", width=2)
    d.rectangle((0, int(h*.93), w, h), fill="#D3C5B1")
    return im, (box[0]+f, box[1]+f, box[2]-f, box[3]-f)


def illus_casement(w, h, age):
    base, (ix0, iy0, ix1, iy1) = casement_base(w, h)
    im = base.copy()
    lw, ih = (ix1-ix0)//2, iy1-iy0
    s = max(5, int(lw*.10))
    theta = math.radians(58)*wave(age, 6.5, .4)
    c, sn = math.cos(theta), math.sin(theta)
    d = ih*.09*sn
    src = [(0, 0), (lw, 0), (lw, ih), (0, ih)]
    for side in ("left", "right"):
        leaf = sash(lw, ih, s, handle="right" if side == "left" else "left")
        if side == "left":
            dst = [(ix0, iy0), (ix0+lw*c, iy0-d), (ix0+lw*c, iy1+d), (ix0, iy1)]
        else:
            dst = [(ix1-lw*c, iy0-d), (ix1, iy0), (ix1, iy1), (ix1-lw*c, iy1+d)]
        out = leaf.transform((w, h), Image.Transform.PERSPECTIVE, find_coeffs(dst, src),
                             Image.Resampling.BICUBIC)
        im.alpha_composite(shade(out, 1-.28*sn))
    return im


@functools.lru_cache(maxsize=10)
def door_base(w, h):
    im = vgrad(w, h, "#EEEBE6", "#E2DED7")
    d = ImageDraw.Draw(im)
    wood(d, (0, 0, int(w*.22), h), slats=6)
    d.rectangle((w*.20, h*.05, w*.86, h*.11), fill="#3A4148")
    d.line((w*.20, h*.11, w*.86, h*.11), fill="#6F7A84", width=2)
    door = [int(w*.30), int(h*.16), int(w*.58), int(h*.90)]
    dw, dh = door[2]-door[0], door[3]-door[1]
    f = max(5, int(dw*.06))
    leaf = Image.new("RGBA", (dw-2*f, dh-2*f), "#3D444B")
    ld = ImageDraw.Draw(leaf)
    lw, lh = leaf.size
    ld.rectangle((lw*.12, lh*.06, lw*.22, lh*.94), fill=(156, 196, 219, 255))
    ld.line((lw*.12, lh*.06, lw*.22, lh*.06), fill="#2A3035", width=2)
    for gy in (.36, .50, .64):
        ld.line((lw*.32, lh*gy, lw*.95, lh*gy), fill="#56606A", width=2)
    ld.rounded_rectangle((lw*.80, lh*.24, lw*.85, lh*.76), 4, fill="#D8DDE1", outline="#8A939A")
    im.alpha_composite(leaf, (door[0]+f, door[1]+f))
    im.alpha_composite(metal_ring(dw, dh, f), (door[0], door[1]))
    side = [int(w*.60), int(h*.16), int(w*.72), int(h*.90)]
    sw_, sh_ = side[2]-side[0], side[3]-side[1]
    im.alpha_composite(interior_view(sw_, sh_), side[:2])
    im.alpha_composite(sash(sw_, sh_, f), side[:2])
    d.rectangle((w*.25, h*.90, w*.79, h*.96), fill="#D0CBC3", outline="#BDB6AC")
    d.rectangle((0, int(h*.96), w, h), fill="#C9CED2")
    plant(d, (w*.80, h*.60, w*.96, h*.96))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((door[0]+f, door[1]+f, door[2]-f, door[3]-f), fill=255)
    lamp = (int(w*.765), int(h*.36))
    return im, mask, lamp


def illus_door(w, h, age):
    base, mask, (lx, ly) = door_base(w, h)
    im = base.copy()
    glow = Image.new("RGBA", (w, h))
    ImageDraw.Draw(glow).polygon([(lx-6, ly+12), (lx+6, ly+12), (lx+40, ly+130), (lx-40, ly+130)],
                                 fill=(255, 226, 160, int(60+30*math.sin(age*2))))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((lx-8, ly-14, lx+8, ly+14), 3, fill="#3A4148")
    d.rectangle((lx-6, ly+10, lx+6, ly+14), fill="#FFE9B8")
    sweep(im, mask, sweep_pos(age, .26), .30)
    return im


@functools.lru_cache(maxsize=10)
def curtain_base(w, h):
    im = sky(w, h)
    return im


@functools.lru_cache(maxsize=10)
def curtain_front(w, h):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rectangle((0, h*.40, w*.20, h*.88), fill="#D3CFC6")
    d.rectangle((w*.84, h*.30, w, h*.88), fill="#D6D3CC")
    for x in np.arange(w*.025, w*.19, w*.045):
        for y in np.arange(h*.45, h*.84, h*.08):
            d.rectangle((x, y, x+w*.025, y+h*.045), fill="#B3C3CF")
    tower = (int(w*.24), int(h*.07), int(w*.80), int(h*.88))
    tw, th = tower[2]-tower[0], tower[3]-tower[1]
    panel = vgrad(tw, th, "#5F95BC", "#BCD8E9")
    rng = np.random.default_rng(7)
    cols, rows = 5, 7
    for c in range(cols):
        for r in range(rows):
            # Some panes catch more sky than others, as on a real glazed façade.
            if rng.random() < .35:
                tint = Image.new("RGBA", (int(tw/cols), int(th/rows)), (255, 255, 255, int(18+rng.random()*22)))
                panel.alpha_composite(tint, (int(c*tw/cols), int(r*th/rows)))
    im.alpha_composite(panel, tower[:2])
    for c in range(cols+1):
        x = tower[0] + c*tw/cols
        d.rectangle((x-2, tower[1], x+2, tower[3]), fill="#C9CFD4")
    for r in range(rows+1):
        y = tower[1] + r*th/rows
        d.rectangle((tower[0], y-1.5, tower[2], y+1.5), fill="#C9CFD4")
    d.rectangle((tower[0]-6, tower[1]-12, tower[2]+6, tower[1]), fill="#3A4148")
    d.rectangle((0, int(h*.88), w, h), fill="#CDD3D7")
    for tx in (.10, .91):
        d.rectangle((w*tx-3, h*.74, w*tx+3, h*.88), fill="#7B6A58")
        d.ellipse((w*tx-30, h*.58, w*tx+30, h*.80), fill="#87A796")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle(tower, fill=255)
    return im, mask


def illus_curtain(w, h, age):
    im = curtain_base(w, h).copy()
    clouds(im, w, h, age, .05, .9, 1)
    front, mask = curtain_front(w, h)
    im.alpha_composite(front)
    sweep(im, mask, sweep_pos(age, .22, .3), .40, .07)
    return im


@functools.lru_cache(maxsize=10)
def veranda_front(w, h):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h*.85), w, h), fill="#C7D5C2")
    d.rectangle((0, h*.12, w*.34, h*.85), fill="#EFE9E0")
    d.rectangle((0, h*.09, w*.36, h*.12), fill="#3A4148")
    win = (int(w*.08), int(h*.36), int(w*.24), int(h*.62))
    ww, wh = win[2]-win[0], win[3]-win[1]
    im.alpha_composite(interior_view(ww, wh), win[:2])
    im.alpha_composite(sash(ww, wh, max(5, ww//12)), win[:2])
    x0, x1, ytop0, ytop1, yb = w*.34, w*.94, h*.30, h*.46, h*.85
    inside = Image.new("RGBA", (w, h))
    idr = ImageDraw.Draw(inside)
    idr.rectangle((w*.50, h*.66, w*.66, h*.69), fill="#8E979E")
    for lx in (.52, .64):
        idr.line((w*lx, h*.69, w*lx, h*.83), fill="#8E979E", width=3)
    plant(idr, (w*.72, h*.58, w*.84, h*.84))
    im.alpha_composite(inside)
    pane = Image.new("RGBA", (w, h))
    pane.alpha_composite(glass(int(x1-x0), int(yb-ytop0), 120), (int(x0), int(ytop0)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x0, ytop0), (x1, ytop1), (x1, yb), (x0, yb)], fill=255)
    pane.putalpha(Image.fromarray(np.minimum(np.asarray(pane.getchannel("A")), np.asarray(mask)), "L"))
    im.alpha_composite(pane)
    for i in range(5):
        x = x0 + (x1-x0)*i/4
        ytop = ytop0 + (ytop1-ytop0)*i/4
        d.rectangle((x-3, ytop, x+3, yb), fill="#3A4148")
    d.rectangle((x0, h*.70, x1, h*.71), fill="#3A4148")
    d.rectangle((x0, yb-8, x1, yb), fill="#3A4148")
    t = h*.035
    d.polygon([(x0-4, ytop0-t), (x1+18, ytop1-t), (x1+18, ytop1+4), (x0-4, ytop0+4)], fill="#3A4148")
    d.line((x0-4, ytop0-t, x1+18, ytop1-t), fill="#6F7A84", width=2)
    d.rectangle((x1+10, ytop1-t, x1+24, ytop1+10), fill="#2C3237")
    d.rounded_rectangle((x0+(x1-x0)*.5-3, h*.74, x0+(x1-x0)*.5+3, h*.80), 2, fill="#D8DDE1")
    return im, mask


def illus_veranda(w, h, age):
    im = sky(w, h, "#B5D7EC", "#EDF5F9")
    clouds(im, w, h, age, .02, .8, 2)
    front, mask = veranda_front(w, h)
    im.alpha_composite(front)
    sweep(im, mask, sweep_pos(age, .25, .8), .38)
    return im


@functools.lru_cache(maxsize=10)
def railing_layers(w, h):
    city = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(city)
    rng = np.random.default_rng(3)
    x = 0
    while x < w:
        bw = w*(.06+rng.random()*.07)
        top = h*(.36+rng.random()*.2)
        d.rectangle((x, top, x+bw, h*.80), fill=(196, 212, 224, 255))
        x += bw + w*.01
    front = Image.new("RGBA", (w, h))
    fd = ImageDraw.Draw(front)
    fd.rectangle((0, int(h*.72), w, int(h*.79)), fill="#C9B79F")
    gl = glass(w, int(h*.30), 95)
    front.alpha_composite(gl, (0, int(h*.44)))
    fd.rectangle((0, int(h*.79), w, int(h*.87)), fill="#DAD7D2", outline="#C3BFB8")
    fd.rectangle((0, int(h*.87), w, h), fill="#E7E3DD")
    fd.rectangle((0, int(h*.87), w, int(h*.89)), fill="#C9C5BF")
    for px in np.linspace(w*.05, w*.95, 5):
        fd.rectangle((px-w*.011, h*.42, px+w*.011, h*.79), fill="#B9C0C6", outline="#858D94")
        fd.rectangle((px-w*.016, h*.62, px+w*.016, h*.66), fill="#D3D8DC")
    fd.rounded_rectangle((-10, h*.40, w+10, h*.445), int(h*.02), fill="#C4CBD0", outline="#858D94")
    fd.line((0, h*.408, w, h*.408), fill="#F1F3F5", width=2)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((0, int(h*.44), w, int(h*.79)), fill=255)
    return city, front, mask


def illus_railing(w, h, age):
    im = sky(w, h, "#93C3E3", "#E7F2F8")
    clouds(im, w, h, age, .03, .9, 0)
    city, front, mask = railing_layers(w, h)
    im.alpha_composite(city)
    im.alpha_composite(front)
    sweep(im, mask, sweep_pos(age, .24, 1.2), .40)
    return im


@functools.lru_cache(maxsize=4)
def house_layers(w, h):
    back = sky(w, h, "#A9D1EA", "#EAF3F8")
    front = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(front)
    d.rectangle((w*.036, h*.45, w*.048, h*.86), fill="#7B6A58")
    for cx, cy, r in [(.04, .36, .075), (.085, .44, .06), (.005, .46, .06)]:
        d.ellipse((w*(cx-r), h*cy-w*r, w*(cx+r), h*cy+w*r), fill="#88A897")
    d.rectangle((0, int(h*.86), w, h), fill="#D3D9DC")
    d.rectangle((0, int(h*.86), w, int(h*.875)), fill="#BEC6CA")
    d.rectangle((w*.06, h*.46, w*.94, h*.86), fill="#F3F2EF")
    d.rectangle((w*.30, h*.185, w*.82, h*.46), fill="#F8F7F4")
    wood(d, (int(w*.30), int(h*.185), int(w*.42), int(h*.46)), slats=5)
    d.rectangle((w*.04, h*.44, w*.96, h*.47), fill="#3A4148")
    d.rectangle((w*.27, h*.15, w*.85, h*.185), fill="#3A4148")
    d.line((w*.27, h*.185, w*.85, h*.185), fill="#6F7A84", width=2)
    d.line((w*.04, h*.47, w*.96, h*.47), fill="#6F7A84", width=2)
    up = (int(w*.46), int(h*.23), int(w*.79), int(h*.405))
    uw, uh = up[2]-up[0], up[3]-up[1]
    front.alpha_composite(interior_view(uw, uh), up[:2])
    for i in range(3):
        x = up[0] + i*uw//3
        front.alpha_composite(sash(uw//3 + (uw % 3 if i == 2 else 0), uh, 7), (x, up[1]))
    rail = (int(w*.065), int(h*.375), int(w*.29), int(h*.44))
    front.alpha_composite(glass(rail[2]-rail[0], rail[3]-rail[1], 110), rail[:2])
    for px in np.linspace(rail[0], rail[2], 4):
        d.rectangle((px-2, rail[1], px+2, rail[3]), fill="#B9C0C6")
    d.rounded_rectangle((rail[0]-3, rail[1]-5, rail[2]+3, rail[1]+2), 3, fill="#C4CBD0", outline="#858D94")
    door = (int(w*.11), int(h*.56), int(w*.23), int(h*.86))
    d.rectangle(door, fill="#3D444B", outline="#262B30", width=3)
    d.rectangle((door[0]+8, door[1]+10, door[0]+16, door[3]-10), fill=(156, 196, 219, 255))
    d.rounded_rectangle((door[2]-14, h*.64, door[2]-10, h*.78), 2, fill="#D8DDE1")
    small = (int(w*.26), int(h*.58), int(w*.35), int(h*.71))
    front.alpha_composite(interior_view(small[2]-small[0], small[3]-small[1]), small[:2])
    front.alpha_composite(sash(small[2]-small[0], small[3]-small[1], 6), small[:2])
    for sx in (.07, .97):
        d.ellipse((w*sx-30, h*.80, w*sx+30, h*.90), fill="#7F9F8C")
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle(up, fill=255)
    md.rectangle(rail, fill=200)
    return back, front, mask


def house_hero(w, h, age):
    back, front, mask = house_layers(w, h)
    im = back.copy()
    clouds(im, w, h, age, .02, .9, 3)
    im.alpha_composite(front)
    place_sliding(im, (w*.40, h*.55, w*.90, h*.86), wave(age, 7, .0), interior_view)
    sweep(im, mask, sweep_pos(age, .22, .5), .45)
    return im


ILLUS = {
    "sliding": illus_sliding, "casement": illus_casement, "door": illus_door,
    "curtain": illus_curtain, "veranda": illus_veranda, "railing": illus_railing,
}


# ----------------------------------------------------------------- icons

def line_icon(kind, size, color, stroke=None):
    im, k = supersample(size, size, 4)
    d = ImageDraw.Draw(im)
    S = size*k
    sw = int((stroke or size*.055)*k)

    def P(*pts):
        return [(x*S, y*S) for x, y in pts]

    if kind == "measure":
        d.rounded_rectangle((S*.10, S*.34, S*.46, S*.70), S*.08, outline=color, width=sw)
        d.ellipse((S*.20, S*.44, S*.36, S*.60), outline=color, width=sw)
        d.rectangle((S*.46, S*.50, S*.90, S*.62), outline=color, width=sw)
        for x in np.linspace(.54, .86, 5):
            d.line((S*x, S*.50, S*x, S*.56), fill=color, width=max(1, sw//2))
        d.line(P((.90, .62), (.90, .68)), fill=color, width=sw)
    elif kind == "design":
        d.rectangle((S*.20, S*.28, S*.74, S*.88), outline=color, width=sw)
        d.line(P((.47, .28), (.47, .88)), fill=color, width=sw)
        d.line(P((.20, .14), (.74, .14)), fill=color, width=max(1, sw//2))
        for x in (.20, .74):
            d.line(P((x, .09), (x, .19)), fill=color, width=max(1, sw//2))
        d.line(P((.86, .28), (.86, .88)), fill=color, width=max(1, sw//2))
        for y in (.28, .88):
            d.line(P((.81, y), (.91, y)), fill=color, width=max(1, sw//2))
    elif kind == "gear":
        pts = []
        for i in range(48):
            a = i/48*2*math.pi
            r = .36 if (i % 6) in (0, 1, 2) else .27
            pts.append((S*(.5+r*math.cos(a)), S*(.5+r*math.sin(a))))
        d.polygon(pts, outline=color, width=sw)
        d.ellipse((S*.38, S*.38, S*.62, S*.62), outline=color, width=sw)
    elif kind == "house":
        d.line(P((.10, .50), (.50, .14), (.90, .50)), fill=color, width=sw, joint="curve")
        d.line(P((.20, .42), (.20, .88), (.80, .88), (.80, .42)), fill=color, width=sw, joint="curve")
        d.line(P((.34, .62), (.46, .74), (.68, .52)), fill=color, width=sw, joint="curve")
    elif kind == "shield":
        d.line(P((.50, .10), (.84, .22), (.80, .56), (.50, .90), (.20, .56), (.16, .22), (.50, .10)),
               fill=color, width=sw, joint="curve")
        d.line(P((.34, .50), (.46, .62), (.68, .38)), fill=color, width=sw, joint="curve")
    elif kind == "feather":
        pts = []
        for i in range(41):
            t = i/40
            pts.append((.5 + .16*math.sin(t*math.pi), t))
        for i in range(41):
            t = 1-i/40
            pts.append((.5 - .16*math.sin(t*math.pi), t))
        rot = [(.5+(x-.5)*.75-(y-.5)*.65, .5+(x-.5)*.65+(y-.5)*.75) for x, y in pts]
        d.polygon([(x*S, y*S) for x, y in rot], outline=color, width=sw)
        d.line(P((.22, .80), (.78, .20)), fill=color, width=sw)
    elif kind == "thermo":
        d.rounded_rectangle((S*.40, S*.10, S*.60, S*.66), S*.10, outline=color, width=sw)
        d.ellipse((S*.32, S*.58, S*.68, S*.92), outline=color, width=sw)
        d.line(P((.50, .40), (.50, .72)), fill=color, width=sw)
        for y in (.22, .32, .42):
            d.line(P((.66, y), (.76, y)), fill=color, width=max(1, sw//2))
    elif kind == "recycle":
        for i in range(3):
            a0 = i*120 + 15
            d.arc((S*.16, S*.16, S*.84, S*.84), a0, a0+85, fill=color, width=sw)
            a = math.radians(a0+85)
            cx, cy = S*(.5+.34*math.cos(a)), S*(.5+.34*math.sin(a))
            tx, ty = -math.sin(a), math.cos(a)
            nx, ny = math.cos(a), math.sin(a)
            L = S*.11
            d.polygon([(cx+tx*L, cy+ty*L), (cx+nx*L*.7, cy+ny*L*.7), (cx-nx*L*.7, cy-ny*L*.7)], fill=color)
    elif kind == "sparkle":
        for cx, cy, r in [(.44, .52, .34), (.78, .22, .14)]:
            pts = []
            for i in range(8):
                a = i/8*2*math.pi - math.pi/2
                rr = r if i % 2 == 0 else r*.24
                pts.append((S*(cx+rr*math.cos(a)), S*(cy+rr*math.sin(a))))
            d.polygon(pts, outline=color, width=sw)
    elif kind == "ruler":
        d.polygon(P((.14, .70), (.70, .14), (.86, .30), (.30, .86)), outline=color, width=sw)
        for i in range(1, 6):
            t = i/6
            x, y = .14+.56*t, .70-.56*t
            ln = .10 if i % 2 else .16
            d.line((S*x, S*y, S*(x+ln*.7), S*(y+ln*.7)), fill=color, width=max(1, sw//2))
    return down(im, size, size)


# ----------------------------------------------------------------- brand

@functools.lru_cache(maxsize=20)
def logo_asset(key, width, height):
    with Image.open(ROOT / BRAND["logo"][key]) as logo:
        logo = logo.convert("RGBA")
    f = min(width/logo.width, height/logo.height)
    return logo.resize((round(logo.width*f), round(logo.height*f)), Image.Resampling.LANCZOS)


@functools.lru_cache(maxsize=10)
def brand_mark(size):
    if BRAND.get("logo"):
        # Site icon: paper "P" on an ink square, with a hairline so it reads on ink backgrounds.
        im = Image.new("RGBA", (size, size))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, size-1, size-1), size*.10, fill=INK, outline=(241, 240, 236, 70), width=2)
        p = logo_asset("icon", int(size*.56), int(size*.56))
        im.alpha_composite(p, ((size-p.width)//2, (size-p.height)//2))
        return im
    im, k = supersample(size, size, 4)
    S = size*k
    metal = vgrad(S, S, "#F1F4F6", "#97A1A9")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S-1, S-1), S*.22, fill=255)
    im.paste(metal, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, S-1, S-1), S*.22, outline="#7E8890", width=max(2, k))
    a, b = S*.24, S*.76
    d.rectangle((a, a, b, b), fill=ACCENT)
    d.polygon([(a, a), (a+S*.20, a), (a, a+S*.30)], fill=rgba(WHITE, 90))
    d.rectangle((a, a, b, b), outline="#2E353B", width=int(S*.065))
    d.rectangle((S*.5-S*.032, a, S*.5+S*.032, b), fill="#2E353B")
    d.rectangle((S*.56, S*.47, S*.59, S*.56), fill="#E6EAED")
    return down(im, size, size)


def company():
    return BRAND["company"][LANG]


def header(im, dark, age, scene):
    if BRAND.get("logo"):
        wordmark = logo_asset("on_dark" if dark else "on_light", 330, 52)
        paste(im, wordmark, (112, 76-wordmark.height/2))
    else:
        paste(im, brand_mark(62), (112, 44))
        txt(im, company(), (192, 58), 27, WHITE if dark else INK, "bold", tracking=1)
    txt(im, T["category"], (1808, 70), 19, "#A9A69F" if dark else GRAY, "medium", tracking=2, right=True)
    d = ImageDraw.Draw(im)
    d.line((112, 985, 1808, 985), fill="#34373C" if dark else "#D6D3CC", width=1)
    txt(im, f"{company()}  ·  {T['footer']}", (110, 1010), 17,
        "#9B9890" if dark else GRAY, "medium", tracking=1)
    for k in range(len(SCENES)):
        x = 1634+k*26
        on = ACCENT_LIGHT if dark else ACCENT
        d.ellipse((x, 1018, x+6, 1024), fill=on if k == scene else ("#43464B" if dark else "#CFCBC3"))


def sparkle(im, x, y, radius, color, alpha=1):
    layer = Image.new("RGBA", (radius*2+6, radius*2+6))
    d = ImageDraw.Draw(layer)
    r, c = radius, radius+3
    d.polygon([(c, 3), (c+r*.20, c-r*.20), (2*r+3, c), (c+r*.20, c+r*.20), (c, 2*r+3),
               (c-r*.20, c+r*.20), (3, c), (c-r*.20, c-r*.20)], fill=color)
    paste(im, layer, (x-c, y-c), alpha)


def orbits(im, center, age, dark=False, scale=1):
    x, y = center
    d = ImageDraw.Draw(im)
    ring = "#3A3D42" if dark else "#D3CFC6"
    for r in [250, 330, 400]:
        r *= scale
        d.ellipse((int(x-r), int(y-r), int(x+r), int(y+r)), outline=ring, width=1)
    for j in range(3):
        r = (250+j*75)*scale
        a = age*.12+j*2.05
        px, py = x+math.cos(a)*r, y+math.sin(a)*r
        d.ellipse((px-5, py-5, px+5, py+5), fill=ACCENT_LIGHT if dark else ACCENT)


# ----------------------------------------------------------------- cards

@functools.lru_cache(maxsize=40)
def card_shell(width, height, title="", subtitle="", footer=109, dark=False):
    card = Image.new("RGBA", (width+24, height+32))
    shadow = Image.new("RGBA", card.size)
    ImageDraw.Draw(shadow).rounded_rectangle((12, 20, width+10, height+20), 24,
                                             fill=(8, 18, 28, 90 if dark else 38))
    card.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(card).rounded_rectangle((6, 3, width+5, height+2), 23, fill=WHITE,
                                           outline="#E2DFD8", width=1)
    if title:
        size = 29
        while text_sprite(title, size, INK, "bold").width > width-30:
            size -= 1
        txt(card, title, (width/2+6, height-82), size, INK, "bold", center=True)
    if subtitle:
        size = 21
        while text_sprite(subtitle, size, GRAY).width > width-30:
            size -= 1
        txt(card, subtitle, (width/2+6, height-41), size, GRAY, center=True)
    return card


def art_card(kind, width, height, title, subtitle, age, footer=109, dark=False):
    card = card_shell(width, height, title, subtitle, footer, dark).copy()
    aw, ah = width-36, height-footer-24 if footer else height-24
    art = ILLUS[kind](aw, ah, age) if isinstance(kind, str) else kind(aw, ah, age)
    card.paste(art, (24, 14+ (12 if footer else 10)), rounded_mask(aw, ah, 16))
    return card


def float_card(im, card, xy, age, delay=.3, phase=0):
    p = ease((age-delay)/.85)
    paste(im, card, (xy[0], xy[1]+30*(1-p)+4*math.sin(age*.8+phase)), p)


def hero(im, age, dark=False):
    orbits(im, (1410, 545), age, dark, .95)
    card = art_card(house_hero, 760, 590, "", "", age, footer=0, dark=dark)
    float_card(im, card, (1028, 252), age, .25)
    sparkle(im, 1786, 214, 20, ACCENT_LIGHT if dark else ACCENT, ease((age-.9)/.7))


def gallery(im, age, kinds, labels):
    for j, (kind, (title, sub)) in enumerate(zip(kinds, labels)):
        card = art_card(kind, 520, 470, title, sub, age + j*1.3)
        float_card(im, card, (136+j*564, 416), age, .45+j*.18, j)


@functools.lru_cache(maxsize=10)
def step_card(i, title, desc):
    card = card_shell(380, 400).copy()
    txt(card, f"0{i+1}", (34, 30), 30, ACCENT, "bold")
    icon = line_icon(["measure", "design", "gear", "house"][i], 132, INK)
    paste(card, icon, (196-66, 70))
    size = 31
    while text_sprite(title, size, INK, "bold").width > 340:
        size -= 1
    txt(card, title, (196, 250), size, INK, "bold", center=True)
    size = 22
    while text_sprite(desc, size, GRAY).width > 340:
        size -= 1
    txt(card, desc, (196, 304), size, GRAY, center=True)
    return card


def process(im, age):
    d = ImageDraw.Draw(im)
    y = 885
    d.line((150, y, 1770, y), fill="#D3CFC6", width=3)
    p = ease((age-.8)/4.2)
    d.line((150, y, 150+1620*p, y), fill=ACCENT, width=3)
    for i, (title, desc) in enumerate(T["steps"]):
        x = 140 + i*420
        float_card(im, step_card(i, title, desc), (x, 422), age, .5+i*.35, i)
        cx = x+200
        done = 150+1620*p >= cx
        d.ellipse((cx-9, y-9, cx+9, y+9), fill=ACCENT if done else "#D3CFC6", outline=WHITE, width=3)


@functools.lru_cache(maxsize=10)
def benefit_tile(i, title, desc):
    tile = Image.new("RGBA", (500, 190))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, 499, 189), 26, fill=(255, 255, 255, 16), outline=(255, 255, 255, 46))
    d.ellipse((30, 40, 140, 150), fill=rgba(ACCENT, 70), outline=rgba(ACCENT_LIGHT, 140), width=2)
    kind = ["shield", "feather", "thermo", "recycle", "sparkle", "ruler"][i]
    paste(tile, line_icon(kind, 70, WHITE), (50, 60))
    size = 33
    while text_sprite(title, size, WHITE, "bold").width > 320:
        size -= 1
    txt(tile, title, (168, 52), size, WHITE, "bold")
    for j, line in enumerate(wrap(desc, 22, 320)):
        txt(tile, line, (169, 104+j*32), 22, "#BDBAB3")
    return tile


def wrap(text, size, maxw, weight="regular"):
    out = [""]
    for word in text.split():
        trial = (out[-1] + " " + word).strip()
        if out[-1] and font(size, weight).getlength(trial) > maxw:
            out.append(word)
        else:
            out[-1] = trial
    return out


def benefits(im, age):
    for i, (title, desc) in enumerate(T["benefits"]):
        x, y = 180 + (i % 3)*530, 418 + (i//3)*222
        p = ease((age-.6-i*.14)/.8)
        paste(im, benefit_tile(i, title, desc), (x, y+26*(1-p)), p)


# ----------------------------------------------------------------- scenes

def render_scene(index, age):
    theme = SCENES[index]["theme"]
    dark = theme == "dark"
    im = background(theme).copy()
    fg = WHITE if dark else INK
    muted = "#BDBAB3" if dark else GRAY
    if index != 6:
        header(im, dark, age, index)
    if index == 0:
        pill(im, T["s1_pill"], (110, 225), age, True, .1)
        lines(im, T["s1_title"], (105, 344), 96, fg, age, .3, 110, maxw=860)
        lines(im, T["s1_sub"], (110, 620), 34, muted, age, .9, 50, "regular", maxw=860)
        hero(im, age, True)
    elif index == 1:
        lines(im, T["s2_title"], (960, 218), 84, fg, age, .2, center=True, maxw=1650)
        lines(im, T["s2_sub"], (960, 330), 32, muted, age, .6, weight="regular", center=True)
        process(im, age)
    elif index == 2:
        lines(im, T["s3_title"], (960, 218), 84, fg, age, .2, center=True, maxw=1650)
        lines(im, T["s3_sub"], (960, 330), 32, muted, age, .6, weight="regular", center=True, maxw=1650)
        gallery(im, age, ["sliding", "casement", "door"], T["s3_cards"])
    elif index == 3:
        lines(im, T["s4_title"], (960, 218), 84, fg, age, .2, center=True, maxw=1650)
        lines(im, T["s4_sub"], (960, 330), 32, muted, age, .6, weight="regular", center=True, maxw=1650)
        gallery(im, age, ["curtain", "veranda", "railing"], T["s4_cards"])
    elif index == 4:
        lines(im, T["s5_title"], (960, 218), 84, fg, age, .2, center=True, maxw=1650)
        lines(im, T["s5_sub"], (960, 330), 32, muted, age, .6, weight="regular", center=True)
        benefits(im, age)
    elif index == 5:
        pill(im, T["s6_pill"], (110, 225), age, False, .1)
        lines(im, T["s6_title"], (105, 342), 98, fg, age, .3, 112, maxw=860)
        lines(im, T["s6_sub"], (110, 620), 40, ACCENT, age, .9, 58, "regular", maxw=860)
        hero(im, age + 7)
    else:
        closing(im, age)
    return im


def closing(im, age):
    """Closing card is held long enough to read and note the contact details."""
    d = ImageDraw.Draw(im)
    for r in [260, 350, 440]:
        d.ellipse((960-r, 380-r*.6, 960+r, 380+r*.6), outline="#34373C", width=1)
    p = ease((age-.15)/1)
    mark = brand_mark(126 if BRAND.get("logo") else 150)
    my = 118 if BRAND.get("logo") else 150
    paste(im, mark, (960-mark.width/2, my+20*(1-p)), p)
    if p > .05:
        m = mark.getchannel("A")
        layer = Image.new("RGBA", mark.size)
        sweep(layer, m, sweep_pos(age, .30, .1), .55)
        paste(im, layer, (960-mark.width/2, my+20*(1-p)), p)
    if BRAND.get("logo"):
        wp = ease((age-.35)/.9)
        wordmark = logo_asset("on_dark", 760, 120)
        paste(im, wordmark, (960-wordmark.width/2, 292+24*(1-wp)), wp)
    else:
        lines(im, company(), (960, 336), 80, WHITE, age, .35, center=True, maxw=1500)
    lines(im, T["s7_tagline"], (960, 478), 38, "#D2CFC8", age, .6, 56, "regular", True, maxw=1500)
    cp = ease((age-1.1)/.8)
    site = BRAND["website"][LANG]
    sprite = text_sprite(site, 40, INK, "bold")
    width = max(640, sprite.width+180)
    card = Image.new("RGBA", (width, 106))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, width-1, 105), 53, fill=PAPER)
    paste(card, sprite, ((width-60-sprite.width)/2, (106-sprite.height)/2))
    ax = width-70
    cd.line((ax-20, 53, ax+20, 53), fill=INK, width=3)
    cd.line((ax+8, 40, ax+21, 53, ax+8, 66), fill=INK, width=3)
    paste(im, card, (960-width/2, 650+20*(1-cp)), cp)
    y = 800
    if BRAND.get("phone"):
        txt(im, f"{T['phone_label']} {BRAND['phone']}", (960, y), 36, WHITE, "semi", cp, center=True)
        y += 70
    txt(im, T["s7_cta"], (960, y+12), 21, "#A9A69F", "medium", tracking=4, opacity=cp, center=True)
    for k in range(len(SCENES)):
        x = 1634+k*26
        d.ellipse((x, 1018, x+6, 1024), fill=ACCENT_LIGHT if k == 6 else "#43464B")


def frame(t):
    index = max(i for i, scene in enumerate(SCENES) if scene["start"] <= t)
    age = t-SCENES[index]["start"]
    im = render_scene(index, age)
    if index > 0 and age < .65:
        prev_age = SCENES[index-1]["end"]-SCENES[index-1]["start"]+age
        im = Image.blend(render_scene(index-1, prev_age), im, ease(age/.65))
    # A gentle end-to-start dissolve makes the silent version loopable.
    if t > 59.45:
        im = Image.blend(im, render_scene(0, 0), ease((t-59.45)/.55))
    return im.convert("RGB")


def frame_bytes(i):
    return frame(i/FPS).tobytes()


# ----------------------------------------------------------------- outputs

def name(kind):
    return OUT / f"aluminium-60s-{LANG}-{kind}"


def make_stills():
    OUT.mkdir(exist_ok=True)
    review = OUT / "frames" / LANG
    review.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for i, scene in enumerate(SCENES):
        t = scene["start"] + min(4, (scene["end"]-scene["start"])/2)
        im = frame(t)
        im.save(review / f"{i+1:02d}-{int(t):02d}s.png")
        thumbs.append((im.resize((768, 432), Image.Resampling.LANCZOS), scene))
    sheet = Image.new("RGB", (1584, 4*498+36), "#E8E6E1")
    d = ImageDraw.Draw(sheet)
    for i, (thumb, scene) in enumerate(thumbs):
        x, y = 16+(i % 2)*784, 18+(i//2)*498
        sheet.paste(thumb, (x, y))
        d.text((x+8, y+449), f"{scene['start']:02d}–{scene['end']:02d} s   {T['scene_names'][i]}",
               font=font(21), fill=INK)
    x, y = 800, 1512
    d.text((x+30, y+35), company(), font=font(39, "bold"), fill=INK)
    for k, line in enumerate(T["sheet"]):
        d.text((x+30, y+115+k*47), line, font=font(25), fill=GRAY)
    sheet.save(OUT / f"storyboard-{LANG}.jpg", quality=93)
    frame(5).save(OUT / f"affiche-{LANG}.jpg", quality=94)


def render(workers):
    OUT.mkdir(exist_ok=True)
    silent = name("sans-son.mp4")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-metadata",
           f"title={company()} — {T['footer']}", str(silent)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        with Pool(workers, initializer=set_lang, initargs=(LANG,)) as pool:
            for i, data in enumerate(pool.imap(frame_bytes, range(FPS*DURATION), chunksize=6)):
                proc.stdin.write(data)
                if i % (FPS*5) == 0:
                    print(f"[{LANG}] rendered {i/FPS:.0f}/{DURATION}s", flush=True)
    finally:
        proc.stdin.close()
    if proc.wait():
        raise RuntimeError("FFmpeg video render failed")
    music = ROOT / "assets/aluminium-original-60s.wav"
    if music.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
                        "-i", str(silent), "-i", str(music), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "60",
                        "-movflags", "+faststart", str(name("musique.mp4"))], check=True)
    (OUT / f"timeline-{LANG}.json").write_text(json.dumps({
        "width": W, "height": H, "fps": FPS, "duration": DURATION, "language": LANG,
        "scenes": [dict(scene, name=T["scene_names"][i]) for i, scene in enumerate(SCENES)],
        "company": company(), "website": BRAND["website"][LANG],
        "illustrations": "original procedural 2D drawings (tools/render_video.py)",
        "voiceover": "none", "music": "original synthesized instrumental"},
        ensure_ascii=False, indent=2)+"\n")
    print("Export complete:", silent, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default="fr", choices=sorted(BRAND["text"]))
    parser.add_argument("--stills", action="store_true", help="Generate review stills only")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    set_lang(args.lang)
    make_stills()
    if not args.stills:
        render(args.workers)


if __name__ == "__main__":
    main()
