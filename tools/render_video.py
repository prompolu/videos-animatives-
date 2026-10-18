#!/usr/bin/env python3
"""Saraproc Maroc — original, editable 60-second 2D motion-design film.

Render: python3 tools/render_video.py
Review frames first: python3 tools/render_video.py --stills
Requires Python, Pillow, NumPy, FFmpeg, and the system Open Sans/Nimbus fonts.
All product drawings and the wordmark are provisional illustrations.
"""
from __future__ import annotations

import argparse
import functools
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
W, H, FPS, DURATION = 1920, 1080, 30, 60
NAVY = "#102F3B"
TEAL = "#138E8C"
MINT = "#BCEDE1"
IVORY = "#F5F7F3"
GRAY = "#61787D"
WHITE = "#FFFFFF"
LAVENDER = "#DDE0F2"
FONT_PATHS = {
    "bold": "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf",
    "regular": "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf",
    "light": "/usr/share/fonts/truetype/open-sans/OpenSans-Light.ttf",
}
SCENES = [
    {"start": 0, "end": 7, "name": "L’hygiène inspire la confiance", "theme": "dark"},
    {"start": 7, "end": 15, "name": "Des produits pour les professionnels", "theme": "light"},
    {"start": 15, "end": 24, "name": "Hygiène médicale", "theme": "medical"},
    {"start": 24, "end": 33, "name": "Hygiène cosmétique", "theme": "cosmetic"},
    {"start": 33, "end": 43, "name": "La confiance des entreprises", "theme": "dark"},
    {"start": 43, "end": 51, "name": "Rencontrons-nous au salon", "theme": "light"},
    {"start": 51, "end": 60, "name": "Saraproc Maroc · Contact", "theme": "dark"},
]


def rgb(value):
    if isinstance(value, tuple):
        return value[:3]
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1-x)**3


@functools.lru_cache(maxsize=100)
def font(size, weight="regular"):
    return ImageFont.truetype(FONT_PATHS[weight], size)


@functools.lru_cache(maxsize=400)
def text_sprite(text, size, color, weight="regular", tracking=0):
    f = font(size, weight)
    if tracking:
        width = int(sum(f.getlength(c) for c in text) + tracking*max(0, len(text)-1)) + 12
    else:
        width = int(f.getlength(text)) + 12
    result = Image.new("RGBA", (max(1, width), size*2), (0, 0, 0, 0))
    d = ImageDraw.Draw(result)
    if tracking:
        x = 3
        for c in text:
            d.text((x, 0), c, font=f, fill=color, anchor="lt")
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


def txt(im, text, xy, size=38, color=NAVY, weight="regular", opacity=1,
        tracking=0, center=False):
    sprite = text_sprite(text, size, color, weight, tracking)
    x, y = xy
    if center:
        x -= sprite.width/2
    paste(im, sprite, (x, y), opacity)


def lines(im, content, xy, size, color, age=3, delay=.3, leading=None,
          weight="bold", center=False):
    if isinstance(content, str):
        content = content.split("\n")
    leading = leading or int(size*1.11)
    for i, line in enumerate(content):
        p = ease((age-delay-i*.11)/.8)
        txt(im, line, (xy[0], xy[1]+i*leading+28*(1-p)), size,
            color, weight, p, center=center)


def pill(im, text, xy, age=4, dark=False, delay=.4, width=None):
    p = ease((age-delay)/.7)
    sprite = text_sprite(text, 23, MINT if dark else TEAL, "regular", 1)
    width = width or sprite.width+56
    card = Image.new("RGBA", (width, 60))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, width-1, 59), 30,
                        fill=(35, 78, 88, 255) if dark else (226, 241, 235, 255))
    paste(card, sprite, ((width-sprite.width)/2, (60-sprite.height)/2-1))
    paste(im, card, (xy[0], xy[1]+15*(1-p)), p)


@functools.lru_cache(maxsize=5)
def background(theme):
    y, x = np.mgrid[0:H, 0:W]
    if theme == "dark":
        a, b = np.array(rgb("#0C2633")), np.array(rgb("#1C5059"))
        glow = np.exp(-(((x-1530)/900)**2 + ((y-400)/800)**2))*.75
    elif theme == "medical":
        a, b = np.array(rgb("#F1F7F3")), np.array(rgb("#D2EEE7"))
        glow = np.exp(-(((x-1400)/700)**2 + ((y-500)/650)**2))*.9
    elif theme == "cosmetic":
        a, b = np.array(rgb("#F8F6F1")), np.array(rgb("#E4E2F2"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-500)/700)**2))*.88
    else:
        a, b = np.array(rgb(IVORY)), np.array(rgb("#DDEFE6"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-470)/750)**2))*.65
    result = a[None, None, :]*(1-glow[..., None]) + b[None, None, :]*glow[..., None]
    return Image.fromarray(np.uint8(result), "RGB")


def header(im, dark, age, scene):
    color = WHITE if dark else NAVY
    txt(im, "SARAPROC", (110, 65), 34, color, "bold", tracking=1)
    txt(im, "M A R O C", (113, 106), 16, MINT if dark else TEAL)
    txt(im, "HYGIÈNE MÉDICALE  /  COSMÉTIQUE", (1285, 84), 20,
        "#A6C8CA" if dark else GRAY, tracking=1)
    d = ImageDraw.Draw(im)
    d.line((112, 985, 1808, 985), fill="#36555F" if dark else "#D5E1DB", width=1)
    txt(im, "SARAPROC MAROC  ·  HYGIÈNE PROFESSIONNELLE", (110, 1010), 17,
        "#AAC2C5" if dark else GRAY, tracking=1)
    for k in range(7):
        x = 1634+k*26
        color = MINT if dark else TEAL
        d.ellipse((x, 1018, x+6, 1024), fill=color if k == scene else ("#3D606A" if dark else "#CCD9D3"))


def sparkle(im, x, y, radius, color, alpha=1):
    layer = Image.new("RGBA", (radius*2+6, radius*2+6))
    d = ImageDraw.Draw(layer)
    r, c = radius, radius+3
    d.polygon([(c, 3), (c+r*.20, c-r*.20), (2*r+3, c),
               (c+r*.20, c+r*.20), (c, 2*r+3), (c-r*.20, c+r*.20),
               (3, c), (c-r*.20, c-r*.20)], fill=color)
    paste(im, layer, (x-c, y-c), alpha)


def orbits(im, center, age, dark=False, scale=1):
    x, y = center
    d = ImageDraw.Draw(im)
    ring = "#3E6A70" if dark else "#C0DDD2"
    for r in [240, 310, 375]:
        r *= scale
        d.ellipse((int(x-r), int(y-r), int(x+r), int(y+r)), outline=ring, width=1)
    for j in range(3):
        r = (240+j*67)*scale
        a = age*.12+j*2.05
        px, py = x+math.cos(a)*r, y+math.sin(a)*r
        d.ellipse((px-5, py-5, px+5, py+5), fill=MINT if dark else TEAL)


@functools.lru_cache(maxsize=10)
def product(kind):
    # Draw at twice the delivery size for smooth illustrated contours.
    s = 2
    im = Image.new("RGBA", (460*s, 760*s))
    d = ImageDraw.Draw(im)
    def rr(box, radius, fill, outline=None, width=1):
        d.rounded_rectangle(tuple(int(v*s) for v in box), int(radius*s), fill,
                            outline, int(width*s))
    def el(box, fill, outline=None, width=1):
        d.ellipse(tuple(int(v*s) for v in box), fill, outline, int(width*s))
    def ln(points, fill, width):
        d.line([(int(x*s), int(y*s)) for x, y in points], fill, int(width*s))
    def pt(text, x, y, size, color, weight="regular"):
        f = font(int(size*s), weight)
        d.text((x*s, y*s), text, font=f, fill=color, anchor="mt")
    shadow = Image.new("RGBA", im.size)
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((54*s, 692*s, 421*s, 735*s), fill=(13, 48, 56, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(17*s))
    im.alpha_composite(shadow)
    d = ImageDraw.Draw(im)
    if kind == "medical":
        rr((85, 218, 376, 697), 66, "#FDFEFE", "#D2E0DC", 2)
        rr((99, 238, 132, 650), 14, "#EEF5F1")
        rr((159, 166, 302, 240), 16, "#E3EDE9", "#CEDBD8", 2)
        rr((200, 113, 255, 173), 7, "#E8F1EE", "#C9DAD4", 2)
        rr((176, 87, 359, 121), 11, "#EDF6F1", "#C9DAD4", 2)
        rr((325, 104, 364, 137), 5, "#E1EEEA")
        rr((113, 358, 348, 535), 17, "#D7EEE7")
        rr((113, 358, 348, 406), 14, TEAL)
        d.rectangle((113*s, 385*s, 348*s, 407*s), fill=TEAL)
        pt("HYGIÈNE", 230, 374, 18, WHITE, "bold")
        # A neutral sparkle, without certification or pharmaceutical symbols.
        for a in [0, math.pi/2]:
            xx, yy = math.cos(a)*16, math.sin(a)*16
            ln([(230-xx, 450-yy), (230+xx, 450+yy)], TEAL, 3)
        pt("MÉDICALE", 230, 486, 19, NAVY, "bold")
        ln([(181, 594), (280, 594)], "#CCDDD6", 3)
        ln([(204, 607), (257, 607)], "#E3EDE8", 2)
    elif kind == "cosmetic":
        rr((114, 269, 356, 698), 42, "#FEFCF9", "#DBD8DE", 2)
        rr((135, 290, 152, 655), 9, "#F3EEE8")
        rr((168, 202, 300, 290), 15, "#C9C9DA", "#B2B5C9", 2)
        rr((205, 154, 262, 217), 9, "#E6E4ED", "#C2C1D0", 2)
        rr((187, 127, 338, 165), 9, "#F3F1F6", "#C6C5D2", 2)
        rr((310, 149, 339, 184), 5, "#DCD9E6")
        rr((139, 386, 333, 555), 15, "#E9E5F0")
        el((218, 415, 255, 452), "#B0A6C5")
        pt("HYGIÈNE", 236, 474, 18, NAVY, "bold")
        pt("COSMÉTIQUE", 236, 508, 14, "#696782")
    elif kind == "jar":
        rr((44, 446, 417, 690), 59, "#FFFEFC", "#DAD7E2", 2)
        rr((38, 407, 423, 488), 28, "#B8B6CC", "#A8A7BE", 2)
        rr((50, 413, 411, 444), 15, "#D3D0E0")
        rr((75, 513, 106, 650), 14, "#F5F2F3")
        el((211, 535, 251, 575), "#D8D2E6")
        pt("HYGIÈNE", 231, 592, 19, NAVY, "bold")
        pt("COSMÉTIQUE", 231, 626, 14, "#77718B")
    return im.resize((460, 760), Image.Resampling.LANCZOS)


@functools.lru_cache(maxsize=100)
def scaled_product(kind, scale):
    im = product(kind)
    return im.resize((int(im.width*scale), int(im.height*scale)), Image.Resampling.LANCZOS)


def prod(im, kind, xy, scale, age, delay=.35, float_phase=0):
    p = ease((age-delay)/1.1)
    sprite = scaled_product(kind, scale)
    drift = math.sin(age*.85+float_phase)*7
    paste(im, sprite, (xy[0], xy[1]+45*(1-p)+drift), p)


def hero(im, age, dark=False, focus=None):
    orbits(im, (1435, 510), age, dark, .94)
    if focus == "medical":
        prod(im, "medical", (1080, 156), 1.04, age, .3)
        prod(im, "medical", (1445, 350), .65, age, .6, 1)
        sparkle(im, 1655, 330, 25, TEAL, ease((age-.8)/.7))
    elif focus == "cosmetic":
        prod(im, "cosmetic", (1120, 150), 1.01, age, .3)
        prod(im, "jar", (1420, 300), .86, age, .6, 1)
        sparkle(im, 1660, 340, 23, "#B2A9CC", ease((age-.8)/.7))
    else:
        prod(im, "cosmetic", (1330, 205), .87, age, .6, 1.5)
        prod(im, "medical", (1080, 170), .98, age, .3)
        prod(im, "jar", (1445, 403), .65, age, .9, 3)
        sparkle(im, 1695, 300, 23, MINT if dark else TEAL,
                 ease((age-1.1)/.7))


def building(im, x, y, radius, dark=True, variant=0, alpha=1):
    s = radius*2+6
    icon = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(icon)
    c = radius+3
    d.ellipse((3, 3, s-4, s-4), fill="#1D4853" if dark else "#E8F3ED",
              outline="#4C7B7D" if dark else "#A3C9BA", width=2)
    fg = MINT if dark else TEAL
    bw = int(radius*.75)
    top, bottom = int(c-radius*.55), int(c+radius*.55)
    d.rounded_rectangle((c-bw//2, top, c+bw//2, bottom), 3, outline=fg, width=3)
    for row in range(3):
        for col in range(2):
            xx = c-bw*.28+col*bw*.40
            yy = top+radius*.22+row*radius*.27
            d.rectangle((xx, yy, xx+radius*.13, yy+radius*.10), fill=fg)
    d.line((c, bottom, c, bottom-radius*.22), fill=fg, width=3)
    paste(im, icon, (x-c, y-c), alpha)


def network(im, age):
    cx, cy = 1450, 520
    orbits(im, (cx, cy), age, True, .92)
    d = ImageDraw.Draw(im)
    for j, (dx, dy, r) in enumerate([(-230, -175, 61), (190, -220, 72),
                                    (260, 90, 61), (10, 290, 67), (-255, 130, 72)]):
        p = ease((age-.6-j*.17)/1.1)
        d.line((cx, cy, cx+dx*p, cy+dy*p), fill="#54878A", width=2)
        building(im, cx+dx, cy+dy, r, alpha=p)
    p = ease((age-.2)/1)
    badge = Image.new("RGBA", (270, 270))
    bd = ImageDraw.Draw(badge)
    bd.ellipse((3, 3, 267, 267), fill="#E0F6EA", outline="#A9E3D1", width=4)
    txt(badge, "S", (135, 52), 140, TEAL, "bold", center=True)
    paste(im, badge, (cx-135, cy-135), p)
    sparkle(im, 1668, 694, 16, MINT, p)


def render_scene(index, age):
    theme = SCENES[index]["theme"]
    dark = theme == "dark"
    im = background(theme).copy()
    fg = WHITE if dark else NAVY
    muted = "#B1CDCD" if dark else GRAY
    header(im, dark, age, index)
    if index == 0:
        pill(im, "L’HYGIÈNE PROFESSIONNELLE", (110, 225), age, True, .1)
        lines(im, "L’hygiène inspire\nla confiance.", (105, 344), 98, fg, age, .3, 112)
        lines(im, "Des produits pour les professionnels\ndu médical et de la cosmétique.",
              (110, 620), 35, muted, age, .9, 52, "regular")
        hero(im, age, True)
    elif index == 1:
        pill(im, "SARAPROC MAROC", (110, 225), age, False, .1)
        lines(im, "Des produits d’hygiène\npour les\nprofessionnels.", (105, 339), 83, fg, age, .3, 95)
        lines(im, "Deux univers.\nUne même attention à l’hygiène.",
              (110, 681), 34, muted, age, 1, 51, "regular")
        hero(im, age)
    elif index == 2:
        pill(im, "UNIVERS MÉDICAL", (110, 225), age, False, .1)
        lines(im, "L’hygiène\nmédicale.", (104, 355), 114, fg, age, .3, 124)
        lines(im, "Des produits pour les besoins\ndes professionnels du secteur médical.",
              (110, 665), 33, muted, age, .9, 51, "regular")
        hero(im, age, focus="medical")
    elif index == 3:
        pill(im, "UNIVERS COSMÉTIQUE", (110, 225), age, False, .1)
        lines(im, "L’hygiène\ncosmétique.", (104, 355), 110, fg, age, .3, 124)
        lines(im, "Des produits pour les besoins\ndes professionnels de la cosmétique.",
              (110, 665), 33, muted, age, .9, 51, "regular")
        hero(im, age, focus="cosmetic")
    elif index == 4:
        pill(im, "UNE RELATION DE CONFIANCE", (110, 225), age, True, .1)
        lines(im, "La confiance\ndes grandes entreprises\nau Maroc.",
              (105, 340), 83, fg, age, .3, 102)
        lines(im, "Saraproc Maroc,\naux côtés des professionnels.",
              (110, 699), 33, muted, age, 1, 50, "regular")
        network(im, age)
    elif index == 5:
        pill(im, "À VOTRE RENCONTRE", (110, 225), age, False, .1)
        lines(im, "Parlons de\nvos besoins.", (105, 342), 101, fg, age, .3, 113)
        lines(im, "Retrouvons-nous au Salon\ninternational de l’hygiène.",
              (110, 620), 39, TEAL, age, .9, 58, "regular")
        hero(im, age)
    else:
        # Closing card is held long enough to read and type the website.
        p = ease((age-.15)/1)
        d = ImageDraw.Draw(im)
        for r in [160, 250, 350]:
            d.ellipse((960-r, 450-r*.6, 960+r, 450+r*.6), outline="#2B515A", width=1)
        txt(im, "SARAPROC MAROC", (960, 300+20*(1-p)), 102, WHITE,
            "bold", p, tracking=2, center=True)
        lines(im, "L’hygiène médicale et cosmétique\nau service des professionnels.",
              (960, 476), 44, "#C4E4DD", age, .6, 66, "regular", True)
        cp = ease((age-1.1)/.8)
        card = Image.new("RGBA", (724, 106))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 723, 105), 53, fill=MINT)
        txt(card, "saraprocmaroc.com", (344, 32), 39, NAVY, "bold", center=True)
        cd.line((630, 52, 671, 52), fill=NAVY, width=3)
        cd.line((659, 39, 672, 52, 659, 65), fill=NAVY, width=3)
        paste(im, card, (598, 700+20*(1-cp)), cp)
        txt(im, "ÉCHANGEONS SUR VOS BESOINS", (960, 852), 21,
            "#A9CAC9", tracking=3, opacity=cp, center=True)
    return im


def frame(t):
    index = max(i for i, scene in enumerate(SCENES) if scene["start"] <= t)
    age = t-SCENES[index]["start"]
    im = render_scene(index, age)
    # Overlap both animated scenes for clean editorial dissolves.
    if index > 0 and age < .65:
        prev_age = SCENES[index-1]["end"]-SCENES[index-1]["start"]+age
        im = Image.blend(render_scene(index-1, prev_age), im, ease(age/.65))
    # A gentle end-to-start dissolve makes the silent salon version loopable.
    if t > 59.45:
        im = Image.blend(im, render_scene(0, 0), ease((t-59.45)/.55))
    return im


def make_stills():
    OUT.mkdir(exist_ok=True)
    review = OUT / "frames"
    review.mkdir(exist_ok=True)
    thumbs = []
    for i, scene in enumerate(SCENES):
        t = scene["start"] + min(4, (scene["end"]-scene["start"])/2)
        im = frame(t)
        im.save(review / f"{i+1:02d}-{int(t):02d}s.png")
        thumbs.append((im.resize((768, 432), Image.Resampling.LANCZOS), scene))
    sheet = Image.new("RGB", (1584, 4*498+36), "#E5E9E7")
    d = ImageDraw.Draw(sheet)
    for i, (thumb, scene) in enumerate(thumbs):
        x, y = 16+(i%2)*784, 18+(i//2)*498
        sheet.paste(thumb, (x, y))
        label = f"{scene['start']:02d}–{scene['end']:02d} s   {scene['name']}"
        d.text((x+8, y+449), label, font=font(21), fill=NAVY)
    # Keep the final spare cell useful to the reviewer, outside the film itself.
    x, y = 800, 1512
    d.text((x+30, y+35), "SARAPROC MAROC", font=font(39, "bold"), fill=NAVY)
    for k, line in enumerate(["60 secondes · Full HD · 16:9", "Hygiène médicale et cosmétique",
                              "Identité et illustrations provisoires", "Références clients à confirmer"]):
        d.text((x+30, y+115+k*47), line, font=font(25), fill=GRAY)
    sheet.save(OUT / "storyboard-saraproc.jpg", quality=93)
    frame(5).save(OUT / "affiche-saraproc.jpg", quality=94)


def render():
    OUT.mkdir(exist_ok=True)
    video = OUT / "saraproc-maroc-60s-sans-son.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-threads", "3",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-metadata",
           "title=Saraproc Maroc — Hygiène médicale et cosmétique — Maquette", str(video)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(FPS*DURATION):
            proc.stdin.write(frame(i/FPS).tobytes())
            if i % (FPS*5) == 0:
                print(f"Rendered {i/FPS:.0f}/{DURATION}s", flush=True)
    except Exception:
        proc.stdin.close()
        proc.wait()
        raise
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("FFmpeg video render failed")
    music = ROOT / "assets/saraproc-original-60s.wav"
    if music.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
                        "-i", str(video), "-i", str(music), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "60",
                        "-movflags", "+faststart", str(OUT/"saraproc-maroc-60s-musique.mp4")], check=True)
    (OUT / "timeline.json").write_text(json.dumps({"width": W, "height": H, "fps": FPS,
        "duration": DURATION, "scenes": SCENES, "brand_status": "provisional",
        "product_images": "original generic illustrations, not a verified catalogue",
        "client_claim": "provided by user; verify before external release",
        "voiceover": "not recorded", "music": "original synthesized instrumental"},
        ensure_ascii=False, indent=2)+"\n")
    print("Export complete:", video, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stills", action="store_true", help="Generate review stills only")
    args = parser.parse_args()
    make_stills()
    if not args.stills:
        render()


if __name__ == "__main__":
    main()
