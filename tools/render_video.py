#!/usr/bin/env python3
"""Saraproc Maroc — original, editable 60-second 2D motion-design film.

Render: python3 tools/render_video.py
Review frames first: python3 tools/render_video.py --stills
Requires Python, Pillow, NumPy, FFmpeg, and the system Open Sans/Nimbus fonts.
Uses the original logo, product photos, and reference logos from the official site.
All source assets are retained unchanged under assets/site for offline rendering.
"""
from __future__ import annotations

import argparse
import functools
import json
import math
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
W, H, FPS, DURATION = 1920, 1080, 30, 60
NAVY = "#102F3B"
TEAL = "#26547F"
MINT = "#D9E8F8"
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
    {"start": 7, "end": 15, "name": "Plus de 320 produits au catalogue", "theme": "light"},
    {"start": 15, "end": 24, "name": "Hygiène médicale", "theme": "medical"},
    {"start": 24, "end": 33, "name": "Bases cosmétiques", "theme": "cosmetic"},
    {"start": 33, "end": 43, "name": "Ils nous font confiance", "theme": "dark"},
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
                        fill=(38, 69, 105, 255) if dark else (226, 235, 246, 255))
    paste(card, sprite, ((width-sprite.width)/2, (60-sprite.height)/2-1))
    paste(im, card, (xy[0], xy[1]+15*(1-p)), p)


@functools.lru_cache(maxsize=5)
def background(theme):
    y, x = np.mgrid[0:H, 0:W]
    if theme == "dark":
        a, b = np.array(rgb("#10263F")), np.array(rgb("#26547F"))
        glow = np.exp(-(((x-1530)/900)**2 + ((y-400)/800)**2))*.75
    elif theme == "medical":
        a, b = np.array(rgb("#F3F6FA")), np.array(rgb("#D9E8F8"))
        glow = np.exp(-(((x-1400)/700)**2 + ((y-500)/650)**2))*.9
    elif theme == "cosmetic":
        a, b = np.array(rgb("#F8F6F1")), np.array(rgb("#E4E2F2"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-500)/700)**2))*.88
    else:
        a, b = np.array(rgb(IVORY)), np.array(rgb("#E0EAF7"))
        glow = np.exp(-(((x-1450)/850)**2 + ((y-470)/750)**2))*.65
    result = a[None, None, :]*(1-glow[..., None]) + b[None, None, :]*glow[..., None]
    return Image.fromarray(np.uint8(result), "RGB")


def header(im, dark, age, scene):
    logo = fitted_asset("assets/site/branding/" + ("logo_footer.png" if dark else "saraproc-logo.png"), 235, 113)
    paste(im, logo, (112, 34))
    txt(im, "HYGIÈNE MÉDICALE  /  COSMÉTIQUE", (1285, 84), 20,
        "#AFC6E0" if dark else GRAY, tracking=1)
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
    ring = "#466990" if dark else "#C0D2E7"
    for r in [240, 310, 375]:
        r *= scale
        d.ellipse((int(x-r), int(y-r), int(x+r), int(y+r)), outline=ring, width=1)
    for j in range(3):
        r = (240+j*67)*scale
        a = age*.12+j*2.05
        px, py = x+math.cos(a)*r, y+math.sin(a)*r
        d.ellipse((px-5, py-5, px+5, py+5), fill=MINT if dark else TEAL)


PHOTO_PRODUCTS = {
    "gel": ("biomaseptol-gel-hydoalcoolique.jpg", "BIOMASEPTOL", "Hygiène des mains"),
    "scrub": ("bioma-cidex-d1-scrub-5-pcmx-cg.jpg", "BIOMA CIDEX D1 SCRUB", "Hygiène des mains"),
    "dermo": ("dermo-cidex.jpg", "DERMO-CIDEX", "Crème protectrice des mains"),
    "instrument": ("germacid-e4-blend-quadrizymes.jpg", "GERMACID E4", "Entretien des instruments"),
    "surface": ("germa-surf-ndd.jpg", "GERMA-SURF NDD", "Sols, surfaces et matériel"),
    "soap": ("bioma-luxury-soap-melt-pour.jpg", "BIOMA luxury SOAP", "Base pour savon"),
    "hair": ("bioma-luxury-hair-care-free-sulfate.jpg", "BIOMA luxury HAIR CARE", "Base pour shampooing"),
    "cream": ("bioma-luxury-ec-90-full-care-make-cream.jpg", "BIOMA luxury EC 90", "Base pour crème"),
}
CLIENTS = json.loads((ROOT / "assets/site/brand-client-sources.json").read_text())["clients"]


@functools.lru_cache(maxsize=80)
def fitted_asset(path, width, height, viewport=None):
    # Originals stay unchanged. Camera viewports omit empty backdrop in the film.
    with Image.open(ROOT / path) as original:
        result = original.convert("RGBA")
    if viewport is not None:
        l, t, r, b = viewport
        result = result.crop((round(l*result.width), round(t*result.height),
                              round(r*result.width), round(b*result.height)))
    factor = min(width/result.width, height/result.height)
    return result.resize((max(1, round(result.width*factor)), max(1, round(result.height*factor))),
                         Image.Resampling.LANCZOS)


@functools.lru_cache(maxsize=80)
def photo_card(path, width, height, title, subtitle="", logo=False):
    card = Image.new("RGBA", (width+24, height+32))
    shadow = Image.new("RGBA", card.size)
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((12, 20, width+10, height+20), 24, fill=(12, 35, 60, 35))
    card.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((6, 3, width+5, height+2), 23, fill=WHITE,
                        outline="#DBE4EF", width=1)
    photo_height = height-(59 if logo else 109)
    viewport = None
    if "/products/" in path:
        if "dermo-cidex.jpg" in path:
            viewport = (.41, .16, .65, .81)
        elif "bioma-luxury-" in path:
            viewport = (.26, .17, .73, .90)
        else:
            viewport = (.20, .16, .82, .83)
    elif logo and "01M4V1BMEJXFYRGBATBKS2M741" in path:
        viewport = (.07, .28, .95, .56)
    pic = fitted_asset(path, width-36, photo_height-24, viewport)
    paste(card, pic, (6+(width-pic.width)/2, 14+(photo_height-pic.height)/2))
    title_size = 21 if logo else (27 if width>400 else 21)
    while text_sprite(title, title_size, NAVY, "bold").width > width-30:
        title_size -= 1
    txt(card, title, (width/2+6, height-(38 if logo else 81)),
        title_size, NAVY, "bold", center=True)
    if subtitle:
        subtitle_size = 23 if width>400 else 18
        while text_sprite(subtitle, subtitle_size, GRAY).width > width-30:
            subtitle_size -= 1
        txt(card, subtitle, (width/2+6, height-41), subtitle_size, GRAY, center=True)
    return card


def product_card(key, width, height):
    filename, name, subtitle = PHOTO_PRODUCTS[key]
    return photo_card("assets/site/products/"+filename, width, height, name, subtitle)


def float_card(im, card, xy, age, delay=.3, phase=0):
    p = ease((age-delay)/.85)
    paste(im, card, (xy[0], xy[1]+30*(1-p)+4*math.sin(age*.8+phase)), p)


def photo_hero(im, age, dark=False):
    orbits(im, (1435, 530), age, dark, .95)
    float_card(im, product_card("gel", 386, 530), (1035, 285), age, .25)
    float_card(im, product_card("soap", 314, 306), (1455, 230), age, .5, 1)
    float_card(im, product_card("hair", 314, 306), (1455, 570), age, .75, 2)
    sparkle(im, 1762, 196, 20, MINT if dark else TEAL, ease((age-.9)/.7))


def product_gallery(im, age, cosmetic=False):
    keys = ["soap", "hair", "cream"] if cosmetic else ["gel", "surface", "instrument"]
    for j, key in enumerate(keys):
        card = product_card(key, 520, 470)
        if not cosmetic and j>0 and age>4.6:
            # Show the other two medical references without inventing product types.
            alternative = product_card("scrub" if j==1 else "dermo", 520, 470)
            card = Image.blend(card, alternative, ease((age-4.6)/.6))
        float_card(im, card, (136+j*564, 416), age, .45+j*.18, j)


def client_wall(im, age):
    for i, client in enumerate(CLIENTS):
        if i<4:
            x, y = 207+i*385, 414
        else:
            x, y = 400+(i-4)*385, 654
        # Company references are exactly those displayed on the official site.
        card = photo_card(client["local_path"], 350, 200, client["name"], logo=True)
        float_card(im, card, (x, y), age, .6+i*.12, i)


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
        photo_hero(im, age, True)
    elif index == 1:
        pill(im, "LA RICHESSE DU CATALOGUE", (110, 225), age, False, .1)
        lines(im, "Plus de", (108, 340), 77, fg, age, .25)
        lines(im, "320", (100, 436), 206, TEAL, age, .45, 210)
        lines(im, "produits", (110, 648), 79, fg, age, .65)
        lines(im, "au catalogue Saraproc.", (110, 757), 35, muted, age, .9,
              weight="regular")
        lines(im, "Focus : hygiène médicale et cosmétique.", (110, 844), 27,
              TEAL, age, 1.1, weight="regular")
        photo_hero(im, age)
    elif index == 2:
        lines(im, "L’hygiène médicale.", (960, 228), 88, fg, age, .2, center=True)
        lines(im, "Des produits pour les mains, les surfaces et les instruments.",
              (960, 342), 32, muted, age, .6, weight="regular", center=True)
        product_gallery(im, age)
    elif index == 3:
        lines(im, "L’univers cosmétique.", (960, 228), 88, fg, age, .2, center=True)
        lines(im, "Des bases pour savon, shampooing et crème.",
              (960, 342), 34, muted, age, .6, weight="regular", center=True)
        product_gallery(im, age, cosmetic=True)
    elif index == 4:
        lines(im, "Ils nous font confiance.", (960, 228), 88, fg, age, .2, center=True)
        lines(im, "Saraproc Maroc, aux côtés des professionnels.",
              (960, 342), 32, muted, age, .6, weight="regular", center=True)
        client_wall(im, age)
    elif index == 5:
        pill(im, "À VOTRE RENCONTRE", (110, 225), age, False, .1)
        lines(im, "Parlons de\nvos besoins.", (105, 342), 101, fg, age, .3, 113)
        lines(im, "Retrouvons-nous au Salon\ninternational de l’hygiène.",
              (110, 620), 39, TEAL, age, .9, 58, "regular")
        photo_hero(im, age)
    else:
        # Closing card is held long enough to read and type the website.
        p = ease((age-.15)/1)
        d = ImageDraw.Draw(im)
        for r in [260, 350, 440]:
            d.ellipse((960-r, 425-r*.6, 960+r, 425+r*.6), outline="#365A83", width=1)
        logo = fitted_asset("assets/site/branding/logo_footer.png", 564, 260)
        paste(im, logo, (960-logo.width/2, 210+20*(1-p)), p)
        lines(im, "L’hygiène médicale et cosmétique\nau service des professionnels.",
              (960, 531), 41, "#D2E1F4", age, .6, 62, "regular", True)
        cp = ease((age-1.1)/.8)
        card = Image.new("RGBA", (724, 106))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 723, 105), 53, fill=MINT)
        txt(card, "saraprocmaroc.com", (344, 32), 39, NAVY, "bold", center=True)
        cd.line((630, 52, 671, 52), fill=NAVY, width=3)
        cd.line((659, 39, 672, 52, 659, 65), fill=NAVY, width=3)
        paste(im, card, (598, 730+20*(1-cp)), cp)
        txt(im, "ÉCHANGEONS SUR VOS BESOINS", (960, 887), 21,
            "#B1C9E5", tracking=3, opacity=cp, center=True)
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
                              "Logo et photos issus du site officiel", "7 références clients du site officiel"]):
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
           "title=Saraproc Maroc — Plus de 320 produits — Hygiène médicale et cosmétique", str(video)]
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
    exports = [video]
    if music.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
                        "-i", str(video), "-i", str(music), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "60",
                        "-movflags", "+faststart", str(OUT/"saraproc-maroc-60s-musique.mp4")], check=True)
        exports.append(OUT/"saraproc-maroc-60s-musique.mp4")
    (OUT / "timeline.json").write_text(json.dumps({"width": W, "height": H, "fps": FPS,
        "duration": DURATION, "scenes": SCENES, "brand_status": "official website logo",
        "product_images": "8 original medical hygiene and cosmetic-base photos from official catalogue",
        "product_count_claim": "Plus de 320 produits au catalogue Saraproc — user-provided, whole catalogue",
        "client_claim": "7 reference logos displayed under Ils nous font confiance on official website",
        "asset_sources": ["assets/site/brand-client-sources.json", "assets/site/products/product-sources.json"],
        "voiceover": "not recorded", "music": "original synthesized instrumental"},
        ensure_ascii=False, indent=2)+"\n")
    with ZipFile(OUT/"Saraproc-Maroc-videos.zip", "w", ZIP_DEFLATED) as archive:
        for exported in exports:
            archive.write(exported, arcname=exported.name)
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
