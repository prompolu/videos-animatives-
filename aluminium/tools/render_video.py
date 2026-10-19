#!/usr/bin/env python3
"""PROMPOLU ALUMINIUM — 60-second B2B motion-design film (FR/EN), 1080p60.

Render one language:  python3 aluminium/tools/render_video.py --lang fr
Review stills only:   python3 aluminium/tools/render_video.py --lang fr --stills
Texts, logo and colours live in aluminium/brand.json; drawings live in tools/art.py.
The cut times below match the music in tools/compose_music.py (120 BPM).
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

from art import (ILLUS, PRODUCT_KEYS, back, ease, line_icon, paste, profile_section,
                 rgb, rgba, rounded_mask)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
BRAND = json.loads((ROOT / "brand.json").read_text())
W, H, FPS, DURATION = 1920, 1080, 60, 60
COLORS = BRAND["colors"]
BRONZE, BRONZE_LIGHT = COLORS["accent"], COLORS["accent_light"]
INK, PAPER = COLORS["ink"], COLORS["paper"]
WHITE, GRAY, MUTED = "#FFFFFF", "#6A6862", "#BDBAB3"
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
FONT_PATHS = {
    "black": FONT_DIR / "InterDisplay-Black.otf",
    "bold": FONT_DIR / "InterDisplay-Bold.otf",
    "semi": FONT_DIR / "Inter-SemiBold.otf",
    "medium": FONT_DIR / "Inter-Medium.otf",
    "regular": FONT_DIR / "Inter-Regular.otf",
}
LANG = "fr"
T: dict = {}


def set_lang(lang):
    global LANG, T
    LANG, T = lang, BRAND["text"][lang]


# --------------------------------------------------------------- timeline

def build_scenes():
    scenes = [("hook", 0, 4, None), ("intro", 4, 10, None), ("chain", 10, 16, None)]
    scenes += [("product", 16+3*i, 19+3*i, i) for i in range(10)]
    scenes += [("recap", 46, 52, None), ("cta", 52, 56, None), ("end", 56, 60, None)]
    return scenes


SCENES = build_scenes()
GROUP_OF = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2]
# Cut time -> (transition, duration). Product cuts land on the beat with a whoosh.
TRANSITIONS = {4: ("zoom", .5), 10: ("wipe", .6), 16: ("push", .45), 46: ("zoom", .5),
               52: ("wipe", .6), 56: ("zoom", .5)}
for _i in range(1, 10):
    _cut = 16 + 3*_i
    TRANSITIONS[_cut] = ("push_up", .5) if _cut in (25, 34) else ("push", .45)
# Each product's art starts mid-motion so something moves during its 3 seconds.
ART_START = {"sliding": .4, "casement": .2, "door": 0, "curtain": 0, "cladding": 0, "stacbond": 0,
             "kitchen": .3, "dressing": .2, "shutter": .3, "pergola": .3}


def inout(x):
    x = min(1.0, max(0.0, x))
    return 4*x**3 if x < .5 else 1-(-2*x+2)**3/2


def expo(x):
    x = min(1.0, max(0.0, x))
    return 1 if x >= 1 else 1-2**(-10*x)


# ------------------------------------------------------------- typography

@functools.lru_cache(maxsize=100)
def font(size, weight="regular"):
    return ImageFont.truetype(str(FONT_PATHS[weight]), size)


@functools.lru_cache(maxsize=800)
def text_sprite(text, size, color, weight="regular", tracking=0):
    f = font(size, weight)
    width = int(sum(f.getlength(c) for c in text) + tracking*max(0, len(text)-1)) + 12 \
        if tracking else int(f.getlength(text)) + 12
    result = Image.new("RGBA", (max(1, width), int(size*1.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(result)
    ascent = f.getmetrics()[0]
    if tracking:
        # Per-glyph drawing on a shared baseline keeps accented capitals (Ê, Ç) intact.
        x = 3
        for c in text:
            d.text((x, ascent), c, font=f, fill=color, anchor="ls")
            x += f.getlength(c) + tracking
    else:
        d.text((3, ascent), text, font=f, fill=color, anchor="ls")
    return result


def txt(im, text, xy, size=38, color=INK, weight="regular", opacity=1, tracking=0, align="left"):
    sprite = text_sprite(text, size, color, weight, tracking)
    x = xy[0] - (sprite.width/2 if align == "center" else sprite.width if align == "right" else 0)
    paste(im, sprite, (x, xy[1]), opacity)


def wrap(text, size, maxw, weight="regular"):
    out = [""]
    for word in text.split():
        trial = (out[-1] + " " + word).strip()
        if out[-1] and font(size, weight).getlength(trial) > maxw:
            out.append(word)
        else:
            out[-1] = trial
    return "\n".join(out)


def kinetic(im, text, xy, size, color, age, delay=0, weight="bold", align="left", maxw=None,
            leading=1.08, stagger=.055, dur=.5):
    """Word-by-word reveal: each word rises from under its own baseline mask."""
    lines = text.split("\n")
    if maxw:
        while size > 18 and max(font(size, weight).getlength(l) for l in lines) > maxw:
            size -= 2
    f = font(size, weight)
    space = f.getlength(" ")
    y, k = xy[1], 0
    for line in lines:
        words = line.split(" ")
        total = sum(f.getlength(w) for w in words) + space*(len(words)-1)
        x = xy[0] - (total/2 if align == "center" else total if align == "right" else 0)
        for word in words:
            pr = (age-delay-k*stagger)/dur
            if pr > 0:
                e = 1-(1-min(1, pr))**4
                sprite = text_sprite(word, size, color, weight)
                dy = (1-e)*size*.95
                visible = int(sprite.height-dy)
                if visible > 0:
                    paste(im, sprite.crop((0, 0, sprite.width, visible)), (x-3, y+dy), min(1, pr*2.2))
            x += f.getlength(word) + space
            k += 1
        y += size*leading
    return y


def pill(im, text, xy, age, style="light", delay=0, align="left"):
    if age < delay:
        return
    p = back((age-delay)/.45)
    color = {"light": BRONZE, "dark": BRONZE_LIGHT, "bronze": PAPER}[style]
    sprite = text_sprite(text, 22, color, "semi", 3)
    width, hgt = sprite.width+50, 56
    card = Image.new("RGBA", (width, hgt))
    fill = {"light": rgba(BRONZE, 26), "dark": (255, 255, 255, 18), "bronze": (255, 255, 255, 34)}[style]
    edge = {"light": rgba(BRONZE, 90), "dark": rgba(BRONZE_LIGHT, 110), "bronze": (255, 255, 255, 120)}[style]
    ImageDraw.Draw(card).rounded_rectangle((0, 0, width-1, hgt-1), hgt//2, fill=fill, outline=edge, width=2)
    paste(card, sprite, ((width-sprite.width)/2+2, (hgt-sprite.height*.66)/2-4))
    x = xy[0] - (width/2 if align == "center" else 0)
    paste(im, card, (x, xy[1]+18*(1-min(1, p))), min(1, (age-delay)/.2))


# ----------------------------------------------------------------- brand

@functools.lru_cache(maxsize=20)
def logo_asset(key, width, height):
    with Image.open(ROOT / BRAND["logo"][key]) as logo:
        logo = logo.convert("RGBA")
    f = min(width/logo.width, height/logo.height)
    return logo.resize((round(logo.width*f), round(logo.height*f)), Image.Resampling.LANCZOS)


@functools.lru_cache(maxsize=10)
def brand_mark(size):
    """Site icon: paper "P" on an ink square, with a hairline so it reads on ink backgrounds."""
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size-1, size-1), size*.10, fill=INK, outline=(241, 240, 236, 80), width=2)
    p = logo_asset("icon", int(size*.56), int(size*.56))
    im.alpha_composite(p, ((size-p.width)//2, (size-p.height)//2))
    return im


def header(im, dark):
    wordmark = logo_asset("on_dark" if dark else "on_light", 300, 46)
    paste(im, wordmark, (100, 70-wordmark.height/2))
    txt(im, T["category"], (1820, 60), 18, "#A9A69F" if dark else GRAY, "semi", tracking=3, align="right")


# ------------------------------------------------------------ backgrounds

@functools.lru_cache(maxsize=4)
def base_bg(kind):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    if kind == "dark":
        a, b, cx, cy, sx, sy = INK, "#2E3136", 1400, 380, 950, 800
    elif kind == "bronze":
        a, b, cx, cy, sx, sy = "#5E4529", "#A07B52", 960, 420, 1100, 700
    else:
        a, b, cx, cy, sx, sy = "#E2DFD8", PAPER, 1300, 420, 1100, 850
    glow = np.exp(-(((x-cx)/sx)**2 + ((y-cy)/sy)**2))[..., None]
    arr = np.array(rgb(a), np.float32)*(1-glow) + np.array(rgb(b), np.float32)*glow
    return Image.fromarray(np.uint8(arr), "RGB").convert("RGBA")


@functools.lru_cache(maxsize=2)
def light_band(warm=True):
    w = 640
    x = np.linspace(-1, 1, w, dtype=np.float32)
    band = np.zeros((H, w, 4), np.uint8)
    band[..., :3] = rgb("#FFE7C4") if warm else rgb("#FFFFFF")
    band[..., 3] = np.uint8(np.exp(-(x/.35)**2)*46)[None, :]
    # Skew the band so it travels diagonally.
    return Image.fromarray(band, "RGBA").transform((w+500, H), Image.Transform.AFFINE,
                                                   (1, .46, 0, 0, 1, 0), Image.Resampling.BILINEAR)


@functools.lru_cache(maxsize=1)
def particle_field():
    rng = np.random.default_rng(42)
    n = 70
    return (rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(-14, 14, n),
            rng.uniform(-30, -8, n), rng.uniform(1.5, 4.2, n), rng.uniform(0, 6.28, n))


def particles(im, t, color):
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    x0, y0, vx, vy, r, ph = particle_field()
    xs, ys = (x0+vx*t) % W, (y0+vy*t) % H
    c = rgb(color)
    for x, y, rr, p in zip(xs, ys, r, ph):
        d.ellipse((x-rr, y-rr, x+rr, y+rr), fill=c+(int(60+60*math.sin(t*1.7+p)),))
    im.alpha_composite(layer)


def scene_bg(kind, t):
    im = base_bg(kind).copy()
    if kind == "paper":
        d = ImageDraw.Draw(im)
        off = (t*14) % 80
        for x in np.arange(-80+off, W, 80):
            d.line((x, 0, x, H), fill="#E4E1DA")
        for y in np.arange(-80+off*.6, H, 80):
            d.line((0, y, W, y), fill="#E4E1DA")
    else:
        band = light_band(kind == "dark")
        paste(im, band, ((t*330) % (W+band.width+600) - band.width, 0))
        particles(im, t, BRONZE_LIGHT if kind == "dark" else PAPER)
    return im


def camera(im, scale, cx=W/2, cy=H/2):
    if abs(scale-1) < 1e-3:
        return im
    return im.transform((W, H), Image.Transform.AFFINE,
                        (1/scale, 0, cx-cx/scale, 0, 1/scale, cy-cy/scale), Image.Resampling.BILINEAR)


# ----------------------------------------------------------------- cards

@functools.lru_cache(maxsize=20)
def card_shell(width, height, dark=False, radius=26):
    card = Image.new("RGBA", (width+40, height+48))
    shadow = Image.new("RGBA", card.size)
    ImageDraw.Draw(shadow).rounded_rectangle((20, 30, width+20, height+34), radius,
                                             fill=(0, 0, 0, 120 if dark else 55))
    card.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(card).rounded_rectangle((20, 14, width+19, height+13), radius, fill=WHITE,
                                           outline="#E2DFD8", width=1)
    return card


def art_card(art, dark=False, pad=14):
    w, h = art.size
    card = card_shell(w+2*pad, h+2*pad, dark).copy()
    card.paste(art, (20+pad, 14+pad), rounded_mask(w, h, 16))
    return card


def scaled(sprite, s):
    if abs(s-1) < .003:
        return sprite
    return sprite.resize((max(1, int(sprite.width*s)), max(1, int(sprite.height*s))), Image.Resampling.BILINEAR)


def paste_center(im, sprite, cx, cy, opacity=1):
    paste(im, sprite, (cx-sprite.width/2, cy-sprite.height/2), opacity)


# ----------------------------------------------------------------- scenes

def logo_slam(im, a, cy, size=170):
    """The P icon lands with an overshoot, a ring and a short flash."""
    if a < 0:
        return
    s = 2.0 - back(a/.42, 2.4)
    paste_center(im, scaled(brand_mark(size), max(.05, s)), W/2, cy, min(1, a/.1))
    u = ease(a/.75)
    if u < 1:
        layer = Image.new("RGBA", (W, H))
        r = 100 + 760*u
        ImageDraw.Draw(layer).ellipse((W/2-r, cy-r, W/2+r, cy+r), outline=rgba(BRONZE_LIGHT, int(220*(1-u))), width=5)
        im.alpha_composite(layer)


def scene_hook(age, t, _):
    im = scene_bg("dark", t)
    starts, logo_at = [.05, 1.0, 2.0], 3.0
    for j, word in enumerate(T["hook"]):
        a = age - starts[j]
        end = (starts[j+1] if j < 2 else logo_at) - starts[j]
        if a < 0 or a > end + .05:
            continue
        s = 1 + .45*(1-expo(a/.35)) + .04*a
        op = min(1, a/.08)
        dy = 0
        if a > end-.14:
            u = (a-(end-.14))/.19
            op *= max(0, 1-u)
            dy = -90*u*u
        sprite = text_sprite(word, 168, BRONZE_LIGHT if j == 2 else PAPER, "black")
        paste_center(im, scaled(sprite, s), W/2, H/2-30+dy, op)
        lw = 560*expo((a-.1)/.4)
        if lw > 2 and op > 0:
            ImageDraw.Draw(im).rectangle((W/2-lw/2, H/2+105+dy, W/2+lw/2, H/2+111+dy), fill=rgba(BRONZE, int(255*op)))
    a = age - logo_at
    logo_slam(im, a, H/2-80)
    if a > .15:
        p = expo((a-.15)/.5)
        paste_center(im, logo_asset("on_dark", 620, 100), W/2, H/2+110+40*(1-p), p)
    return camera(im, 1+.02*age)


def scene_intro(age, t, _):
    im = scene_bg("dark", t)
    card = art_card(profile_section(760, 600, age), dark=True)
    p = expo(age/.6)
    paste(im, card, (1010+260*(1-p), 205), min(1, age/.25))
    pill(im, T["s2_pill"], (110, 250), age, "dark", .15)
    y = kinetic(im, T["s2_title"], (106, 345), 108, WHITE, age, .3, maxw=820)
    kinetic(im, T["s2_sub"], (112, y+40), 36, MUTED, age, .85, "regular", maxw=820, leading=1.4)
    im = camera(im, 1+.045*inout(age/6), 1240, 540)
    header(im, True)
    return im


@functools.lru_cache(maxsize=6)
def chain_card(i, title, desc):
    w, h = 470, 410
    card = card_shell(w, h).copy()
    d = ImageDraw.Draw(card)
    if i == 0:
        d.rounded_rectangle((20, 14, w+19, h+13), 26, outline=BRONZE, width=4)
    txt(card, f"0{i+1}", (52, 40), 30, BRONZE, "bold")
    size = 40
    while font(size, "bold").getlength(title) > w-60:
        size -= 2
    txt(card, title, (w/2+20, 250), size, INK, "bold", align="center")
    for j, line in enumerate(wrap(desc, 26, w-80).split("\n")):
        txt(card, line, (w/2+20, 312+j*36), 26, GRAY, align="center")
    return card


def scene_chain(age, t, _):
    im = scene_bg("paper", t)
    kinetic(im, T["s3_title"].replace("\n", " "), (W/2, 170), 90, INK, age, .1, align="center", maxw=1700)
    xs = [175, 725, 1275]
    icons = ["profile", "gear", "house"]
    for i, (title, desc) in enumerate(T["chain"]):
        a = age - (.45 + .5*i)
        if a < 0:
            continue
        card = chain_card(i, title, desc).copy()
        icon = line_icon(icons[i], 140, BRONZE if i == 0 else INK)
        if i == 1:
            icon = icon.rotate(-age*70, Image.Resampling.BICUBIC)
        paste(card, icon, (255-70, 70+6*math.sin(age*4+i)))
        sp = scaled(card, .78 + .22*back(a/.45))
        paste(im, sp, (xs[i]+255-sp.width/2, 380+225-sp.height/2), min(1, a/.15))
        if i > 0:
            # Supply-chain arrow drawing in, with dots flowing along it.
            x0, x1, y = xs[i-1]+500, xs[i]+30, 600
            g = expo(a/.4)
            d = ImageDraw.Draw(im)
            d.line((x0, y, x0+(x1-x0)*g, y), fill=BRONZE, width=5)
            if g > .9:
                d.polygon([(x1+8, y), (x1-14, y-13), (x1-14, y+13)], fill=BRONZE)
                for k in range(3):
                    px = x0 + (x1-x0)*((age*1.1 + k/3) % 1)
                    d.ellipse((px-6, y-6, px+6, y+6), fill=BRONZE_LIGHT)
    im = camera(im, 1+.03*inout(age/6))
    header(im, False)
    return im


def two_lines(name, size, maxw, weight="bold"):
    if font(size, weight).getlength(name) <= maxw or " " not in name:
        return name
    words = name.split(" ")
    best = min(range(1, len(words)), key=lambda k: abs(font(size, weight).getlength(" ".join(words[:k])) -
                                                      font(size, weight).getlength(" ".join(words[k:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def scene_product(age, t, i):
    key = PRODUCT_KEYS[i]
    dark = i % 2 == 0
    im = scene_bg("dark" if dark else "paper", t)
    fg, muted = (WHITE, MUTED) if dark else (INK, GRAY)
    tx, cx = (100, 700) if dark else (1310, 70)
    paste(im, text_sprite(f"{i+1:02d}", 560, PAPER if dark else INK, "black"), (tx-40-60*age/3, 150), .06)
    AW, AH = 1100, 760
    art = ILLUS[key](int(AW*1.08), int(AH*1.08), age + ART_START[key])
    # Ken Burns: the crop window drifts across the slightly larger drawing.
    u = inout(age/3)
    ox, oy = int(AW*.08*(u if i % 3 else 1-u)), int(AH*.08*(1-u if i % 2 else u))
    paste(im, art_card(art.crop((ox, oy, ox+AW, oy+AH)), dark), (cx, 128))
    pill(im, T["groups"][GROUP_OF[i]], (tx, 300), age, "dark" if dark else "light", .05)
    kinetic(im, f"{i+1:02d} / 10", (tx+2, 385), 30, BRONZE_LIGHT if dark else BRONZE, age, .1, "semi")
    name, sub = T["products"][i]
    y = kinetic(im, two_lines(name, 104, 520), (tx-4, 440), 104, fg, age, .15, maxw=540, leading=1.02)
    lw = 150*expo((age-.35)/.4)
    ImageDraw.Draw(im).rectangle((tx, y+26, tx+lw, y+32), fill=BRONZE_LIGHT if dark else BRONZE)
    kinetic(im, wrap(sub, 34, 520), (tx, y+64), 34, muted, age, .45, "regular", leading=1.35)
    s = 1.06-.06*inout(age/3) if i % 2 == 0 else 1+.05*inout(age/3)
    im = camera(im, s, cx+AW/2, H/2)
    header(im, dark)
    return im


TILE_W, TILE_H, TILE_ART = 316, 262, 196


def tile_origin(k):
    return 122 + (k % 5)*(TILE_W+24), 318 + (k//5)*(TILE_H+30)


def scene_recap(age, t, _):
    im = scene_bg("paper", t)
    for k, key in enumerate(PRODUCT_KEYS):
        x, y = tile_origin(k)
        card = card_shell(TILE_W, TILE_H).copy()
        art = ILLUS[key](TILE_W-20, TILE_ART-10, age + ART_START[key] + k*.4)
        card.paste(art, (30, 24), rounded_mask(TILE_W-20, TILE_ART-10, 12))
        size = 23
        name = T["products"][k][0]
        while font(size, "semi").getlength(name) > TILE_W-24:
            size -= 1
        txt(card, name, (20+TILE_W/2, 14+TILE_ART+22), size, INK, "semi", align="center")
        if age > 1.9 and int((age-1.9)/.22) % 10 == k:
            ImageDraw.Draw(card).rounded_rectangle((20, 14, TILE_W+19, TILE_H+13), 26, outline=BRONZE, width=5)
        paste(im, card, (x-20, y-14))
    # The camera starts on the pergola tile (the last product shot) and pulls back.
    tx, ty = tile_origin(9)
    im = camera(im, 1+2.4*(1-inout(age/1.5)), tx+TILE_W/2, ty+TILE_H/2)
    kinetic(im, T["recap_title"], (W/2, 150), 84, INK, age, 1.15, align="center", maxw=1700)
    header(im, False)
    return im


def website_button(size, scale):
    site = text_sprite(BRAND["website"][LANG], size, INK, "bold")
    width, hgt = max(560, site.width+170), int(size*2.4)
    btn = Image.new("RGBA", (width, hgt))
    bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle((0, 0, width-1, hgt-1), hgt//2, fill=PAPER)
    paste(btn, site, ((width-60-site.width)/2, hgt/2-size*.78))
    ax = width-72 + 8*math.sin(scale*7)
    bd.line((ax-22, hgt/2, ax+18, hgt/2), fill=INK, width=4)
    bd.line((ax+5, hgt/2-14, ax+19, hgt/2, ax+5, hgt/2+14), fill=INK, width=4)
    return btn


def scene_cta(age, t, _):
    im = scene_bg("bronze", t)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    off = (t*160) % 220
    for x in np.arange(-H-220+off, W+220, 220):
        d.polygon([(x, H), (x+70, H), (x+70+H*.6, 0), (x+H*.6, 0)], fill=(255, 255, 255, 14))
    im.alpha_composite(layer)
    pill(im, T["cta_pill"], (W/2, 230), age, "bronze", .05, align="center")
    y = kinetic(im, T["cta_title"], (W/2, 330), 112, PAPER, age, .15, align="center", maxw=1700, leading=1.05)
    kinetic(im, T["cta_sub"], (W/2, y+30), 38, "#F1E6D6", age, .75, "regular", align="center")
    a = age-1.2
    if a > 0:
        paste_center(im, scaled(website_button(46, age), .7+.3*back(a/.45)), W/2, y+190, min(1, a/.15))
    return camera(im, 1+.035*inout(age/4))


def scene_end(age, t, _):
    im = scene_bg("dark", t)
    d = ImageDraw.Draw(im)
    for r in (300, 400, 500):
        d.ellipse((W/2-r, 400-r*.55, W/2+r, 400+r*.55), outline="#33363B", width=1)
    logo_slam(im, age-.05, 190, 140)
    p = expo((age-.3)/.6)
    paste_center(im, logo_asset("on_dark", 760, 120), W/2, 360+30*(1-p), p)
    y = kinetic(im, T["end_tagline"], (W/2, 470), 40, "#D2CFC8", age, .6, "regular", align="center", leading=1.35)
    a = age-1.0
    if a > 0:
        paste_center(im, scaled(website_button(42, 0), .7+.3*back(a/.45)), W/2, y+90, min(1, a/.15))
        yy = y+180
        if BRAND.get("phone"):
            txt(im, f"{T['phone_label']} {BRAND['phone']}", (W/2, yy), 34, WHITE, "semi", min(1, a/.3), align="center")
            yy += 60
        txt(im, T["end_cta"], (W/2, yy), 21, "#A9A69F", "semi", min(1, max(0, (a-.3)/.4)), 4, "center")
    im = camera(im, 1+.025*inout(age/4))
    if t > 59.6:
        im = Image.blend(im, Image.new("RGBA", (W, H), rgb(INK)+(255,)), min(1, (t-59.6)/.4))
    return im


SCENE_FUNCS = {"hook": scene_hook, "intro": scene_intro, "chain": scene_chain, "product": scene_product,
               "recap": scene_recap, "cta": scene_cta, "end": scene_end}


def render_scene(index, t):
    kind, start, _, meta = SCENES[index]
    return SCENE_FUNCS[kind](t-start, t, meta).convert("RGB")


# ------------------------------------------------------------ transitions

def directional_blur(im, radius, axis):
    if radius < 2:
        return im
    a = np.asarray(im, np.int32)
    pad = [(0, 0), (0, 0), (0, 0)]
    pad[axis] = (radius+1, radius)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    n, size = 2*radius+1, c.shape[axis]
    out = (np.take(c, range(n, size), axis=axis) - np.take(c, range(0, size-n), axis=axis))//n
    return Image.fromarray(out.astype(np.uint8), "RGB")


@functools.lru_cache(maxsize=1)
def xy_grid():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    return x, y


def transition(kind, A, B, u):
    e = inout(u)
    if kind in ("push", "push_up"):
        out = Image.new("RGB", (W, H))
        if kind == "push":
            off = int(e*W)
            out.paste(A, (-off, 0))
            out.paste(B, (W-off, 0))
        else:
            off = int(e*H)
            out.paste(A, (0, -off))
            out.paste(B, (0, H-off))
        return directional_blur(out, int(55*math.sin(math.pi*u)), 1 if kind == "push" else 0)
    if kind == "wipe":
        x, y = xy_grid()
        band = 260
        edge = -700 + e*(W+1400) + (H-y)*.38
        a, b = np.asarray(A, np.float32), np.asarray(B, np.float32)
        show_b = (x < edge-band)[..., None]
        in_band = ((x >= edge-band) & (x < edge))[..., None]
        v = np.clip((x-(edge-band))/band, 0, 1)[..., None]
        col = np.array(rgb("#6E5233"), np.float32)*(1-v) + np.array(rgb("#C9A57C"), np.float32)*v
        return Image.fromarray(np.uint8(np.where(show_b, b, np.where(in_band, col, a))), "RGB")
    # Zoom-through with a short flash at the cut.
    out = Image.blend(camera(A, 1+.35*e), camera(B, 1.18-.18*e), min(1, max(0, (u-.35)/.3)))
    f = math.sin(math.pi*u)**6*.55
    return Image.blend(out, Image.new("RGB", (W, H), "#FFF6EA"), f) if f > .01 else out


# ---------------------------------------------------------------- grading

@functools.lru_cache(maxsize=1)
def grade_tables():
    x = np.arange(256, dtype=np.float32)/255
    curve = .012 + (x*(1-.35) + (3*x**2-2*x**3)*.35)*.978
    hl, sh = curve**2, (1-curve)**2
    lut = np.stack([curve + .035*hl - .015*sh, curve + .008*hl, curve - .03*hl + .03*sh], axis=1)
    lut = np.uint8(np.clip(lut*255, 0, 255))
    y, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xg-W/2)/(W*.62))**2 + ((y-H/2)/(H*.62))**2)
    vignette = (1 - .30*np.clip(r, 0, 1.4)**2.4)[..., None].astype(np.float32)
    rng = np.random.default_rng(9)
    grain = [rng.normal(0, 2.6, (H, W, 1)).astype(np.float32) for _ in range(6)]
    return lut, vignette, grain


def grade(im, frame_index):
    """Warm highlights, cool shadows, gentle S-curve, +10 % saturation, vignette and grain."""
    lut, vignette, grain = grade_tables()
    a = np.asarray(im, np.float32)
    lum = (a @ np.array([.299, .587, .114], np.float32))[..., None]
    a = np.clip(lum + (a-lum)*1.10, 0, 255).astype(np.uint8)
    a = np.stack([lut[a[..., c], c] for c in range(3)], axis=2).astype(np.float32)
    a = a*vignette + grain[frame_index % 6]
    return Image.fromarray(np.uint8(np.clip(a, 0, 255)), "RGB")


def progress(im, t):
    d = ImageDraw.Draw(im)
    d.rectangle((0, H-5, W, H), fill="#3B3D41")
    d.rectangle((0, H-5, W*t/DURATION, H), fill=BRONZE_LIGHT)


def scene_index(t):
    return max(i for i, s in enumerate(SCENES) if s[1] <= t)


def frame(t, frame_index=0):
    im = None
    for cut, (kind, d) in TRANSITIONS.items():
        if cut-d/2 <= t < cut+d/2:
            i = scene_index(cut)
            im = transition(kind, render_scene(i-1, t), render_scene(i, t), (t-(cut-d/2))/d)
            break
    if im is None:
        im = render_scene(scene_index(t), t)
    progress(im, t)
    return grade(im, frame_index)


def frame_bytes(i):
    return frame(i/FPS, i).tobytes()


# ---------------------------------------------------------------- outputs

def name(kind):
    return OUT / f"aluminium-60s-{LANG}-{kind}"


def scene_label(i):
    kind, _, _, meta = SCENES[i]
    return T["products"][meta][0] if kind == "product" else T["scene_labels"][kind]


def make_stills():
    review = OUT / "frames" / LANG
    review.mkdir(parents=True, exist_ok=True)
    for old in review.glob("*.png"):
        old.unlink()
    cols, tw, th = 4, 480, 270
    sheet = Image.new("RGB", (cols*(tw+16)+16, 4*(th+52)+16), "#E8E6E1")
    d = ImageDraw.Draw(sheet)
    for i, (kind, start, end, meta) in enumerate(SCENES):
        t = start + (end-start)*.62
        im = frame(t)
        im.save(review / f"{i+1:02d}-{t:05.2f}s.png")
        x, y = 16+(i % cols)*(tw+16), 16+(i//cols)*(th+52)
        sheet.paste(im.resize((tw, th), Image.Resampling.LANCZOS), (x, y))
        d.text((x+4, y+th+10), f"{start:02d}–{end:02d} s  {scene_label(i)}", font=font(20), fill=INK)
    sheet.save(OUT / f"storyboard-{LANG}.jpg", quality=92)
    frame(5.8).save(OUT / f"affiche-{LANG}.jpg", quality=94)


def render(workers):
    OUT.mkdir(exist_ok=True)
    silent = name("sans-son.mp4")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-metadata",
           f"title=PROMPOLU ALUMINIUM — {T['category']}", str(silent)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        with Pool(workers, initializer=set_lang, initargs=(LANG,)) as pool:
            for i, data in enumerate(pool.imap(frame_bytes, range(FPS*DURATION), chunksize=8)):
                proc.stdin.write(data)
                if i % (FPS*10) == 0:
                    print(f"[{LANG}] rendered {i/FPS:.0f}/{DURATION}s", flush=True)
    finally:
        proc.stdin.close()
    if proc.wait():
        raise RuntimeError("FFmpeg video render failed")
    music = ROOT / "assets/aluminium-original-60s.wav"
    if music.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
                        "-i", str(silent), "-i", str(music), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-t", "60",
                        "-movflags", "+faststart", str(name("musique.mp4"))], check=True)
    (OUT / f"timeline-{LANG}.json").write_text(json.dumps({
        "width": W, "height": H, "fps": FPS, "duration": DURATION, "language": LANG, "bpm": 120,
        "scenes": [{"start": s, "end": e, "name": scene_label(i)} for i, (_, s, e, _) in enumerate(SCENES)],
        "transitions": {str(k): v[0] for k, v in sorted(TRANSITIONS.items())},
        "company": "PROMPOLU ALUMINIUM", "website": BRAND["website"][LANG],
        "illustrations": "original procedural 2D drawings (tools/art.py)",
        "voiceover": "none", "music": "original synthesized 120 BPM cue synced to cuts"},
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
