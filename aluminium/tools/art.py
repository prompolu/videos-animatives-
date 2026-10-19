"""Procedural 2D illustrations for the Prompolu film: aluminium windows, doors,
façades, interiors and outdoor products, plus line icons. Pillow + NumPy only."""
from __future__ import annotations

import functools
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Profile finishes: base, highlight, shadow, groove.
TONES = {
    "anth": ("#3A4148", "#66717B", "#1F2428", "#4A535B"),
    "silver": ("#B9C0C6", "#EEF1F3", "#858D94", "#A3ABB2"),
    "bronze": ("#8C6A45", "#B8946A", "#5E4529", "#7A5C3B"),
}
BRONZE = "#8C6A45"


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
    elif kind == "profile":
        d.rectangle((S*.10, S*.30, S*.40, S*.82), outline=color, width=sw)
        d.rectangle((S*.60, S*.30, S*.90, S*.82), outline=color, width=sw)
        d.rectangle((S*.40, S*.40, S*.60, S*.46), fill=color)
        d.rectangle((S*.40, S*.66, S*.60, S*.72), fill=color)
        d.rectangle((S*.10, S*.14, S*.18, S*.30), fill=color)
        d.rectangle((S*.82, S*.10, S*.90, S*.30), fill=color)
        d.line(P((.18, .56), (.32, .56)), fill=color, width=max(1, sw//2))
        d.line(P((.68, .56), (.82, .56)), fill=color, width=max(1, sw//2))
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


def paste(im, sprite, xy, opacity=1):
    if opacity <= 0:
        return
    if opacity < 0.995:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a*opacity)))
    im.paste(sprite, (int(xy[0]), int(xy[1])), sprite)


def back(x, s=1.9):
    """Ease-out with a small overshoot, for parts that snap into place."""
    x = min(1.0, max(0.0, x))
    return 1 + (s+1)*(x-1)**3 + s*(x-1)**2


def flash(im, mask, strength, xy=(0, 0)):
    if strength <= .01:
        return
    layer = Image.new("RGBA", mask.size, (255, 248, 236, 0))
    layer.putalpha(mask.point(lambda a: int(a*strength)))
    im.alpha_composite(layer, (int(xy[0]), int(xy[1])))


@functools.lru_cache(maxsize=20)
def framed_glass(w, h, t, tint="#7D8A93", alpha=120, tone="anth"):
    im = Image.new("RGBA", (w, h))
    pane = vgrad(max(1, w-2*t+2), max(1, h-2*t+2), tint, "#E8E2D8", alpha)
    over, k = supersample(pane.width, pane.height)
    d = ImageDraw.Draw(over)
    W2, H2 = pane.width*k, pane.height*k
    d.polygon([(W2*.15, 0), (W2*.38, 0), (W2*.05, H2), (-W2*.18, H2)], fill=(255, 255, 255, 50))
    pane.alpha_composite(down(over, pane.width, pane.height))
    im.alpha_composite(pane, (t-1, t-1))
    im.alpha_composite(metal_ring(w, h, t, tone))
    return im


def swing(im, leaf, box, theta, hinge="right", lift=.08):
    """Paste a leaf (door, sash) rotated about a vertical hinge, towards the viewer."""
    x0, y0, x1, y1 = box
    lw, lh = leaf.size
    c, sn = math.cos(theta), math.sin(theta)
    d = lh*lift*sn
    if hinge == "left":
        dst = [(x0, y0), (x0+lw*c, y0-d), (x0+lw*c, y1+d), (x0, y1)]
    else:
        dst = [(x1-lw*c, y0-d), (x1, y0), (x1, y1), (x1-lw*c, y1+d)]
    out = leaf.transform(im.size, Image.Transform.PERSPECTIVE,
                         find_coeffs(dst, [(0, 0), (lw, 0), (lw, lh), (0, lh)]), Image.Resampling.BICUBIC)
    im.alpha_composite(shade(out, 1-.30*sn))


# ------------------------------------------------- profile section (hero)

# Vertical section of a thermally broken window, in unit coordinates.
SECTION = {
    "frame": ([(.16, .62, .40, .92), (.16, .50, .21, .62), (.52, .62, .84, .92), (.79, .46, .84, .62)],
              [(.20, .66, .36, .76), (.20, .79, .36, .88), (.56, .66, .80, .76), (.56, .79, .80, .88)],
              [(.39, .665, .53, .705), (.39, .835, .53, .875)]),
    "sash": ([(.24, .30, .40, .58), (.52, .30, .76, .58), (.36, .18, .385, .30), (.535, .16, .56, .30)],
             [(.27, .34, .37, .54), (.55, .34, .73, .54)],
             [(.39, .34, .53, .38), (.39, .50, .53, .54), (.385, .22, .405, .28), (.515, .22, .535, .28),
              (.21, .55, .245, .60), (.745, .55, .79, .60)]),
}


@functools.lru_cache(maxsize=4)
def grid_paper(w, h, dark=False):
    im = vgrad(w, h, "#23262B" if dark else "#F8F7F3", "#1A1C20" if dark else "#EEECE6")
    d = ImageDraw.Draw(im)
    step = max(12, w//24)
    for i, x in enumerate(range(0, w, step)):
        d.line((x, 0, x, h), fill=("#33373D" if i % 5 else "#3F444B") if dark else ("#E6E3DC" if i % 5 else "#DAD6CD"))
    for i, y in enumerate(range(0, h, step)):
        d.line((0, y, w, y), fill=("#33373D" if i % 5 else "#3F444B") if dark else ("#E6E3DC" if i % 5 else "#DAD6CD"))
    return im


def metal_fill(mask):
    w, h = mask.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (x/w*.65 + y/h*.35)[..., None]
    col = np.array(rgb("#F2F4F5"), np.float32)*(1-t) + np.array(rgb("#8A939A"), np.float32)*t
    col += (6*np.sin(y/h*90))[..., None]
    out = np.dstack([np.clip(col, 0, 255), np.asarray(mask, np.float32)]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    edge = mask.filter(ImageFilter.FIND_EDGES).point(lambda a: min(255, a*2))
    line = Image.new("RGBA", (w, h), rgb("#4E565D") + (0,))
    line.putalpha(edge)
    im.alpha_composite(line)
    return im


@functools.lru_cache(maxsize=4)
def section_layers(w, h):
    S, k = min(w, h)*.95, 3
    ox, oy = (w-S)/2, (h-S)/2 + h*.02

    def box(r):
        return [(ox+r[0]*S)*k, (oy+r[1]*S)*k, (ox+r[2]*S)*k, (oy+r[3]*S)*k]
    layers = {}
    for part, (solids, holes, darks) in SECTION.items():
        m = Image.new("L", (w*k, h*k), 0)
        d = ImageDraw.Draw(m)
        for r in solids:
            d.rounded_rectangle(box(r), S*k*.008, fill=255)
        for r in holes:
            d.rounded_rectangle(box(r), S*k*.006, fill=0)
        metal_mask = m.resize((w, h), Image.Resampling.LANCZOS)
        layer = metal_fill(metal_mask)
        dk, _ = supersample(w, h)
        dd = ImageDraw.Draw(dk)
        for r in darks:
            dd.rounded_rectangle(box(r), S*k*.006, fill="#2B2F33")
        layer.alpha_composite(down(dk, w, h))
        layers[part] = (layer, layer.getchannel("A"), metal_mask)
    g, _ = supersample(w, h)
    gd = ImageDraw.Draw(g)
    for r in [(.405, -.30, .425, .30), (.495, -.30, .515, .30)]:
        gd.rectangle(box(r), fill=(150, 200, 225, 170))
        gd.line([box(r)[0], box(r)[1], box(r)[0], box(r)[3]], fill=(255, 255, 255, 200), width=k*2)
    gd.rectangle(box((.425, .24, .495, .30)), fill="#5A6066")
    gd.rectangle(box((.425, -.30, .495, .24)), fill=(190, 222, 238, 60))
    glass_layer = down(g, w, h)
    layers["glass"] = (glass_layer, glass_layer.getchannel("A"), None)
    shadow = Image.new("RGBA", (w, h))
    ImageDraw.Draw(shadow).ellipse((ox+.14*S, oy+.90*S, ox+.86*S, oy+.98*S), fill=(0, 0, 0, 70))
    layers["shadow"] = shadow.filter(ImageFilter.GaussianBlur(max(4, w//60)))
    return layers


def profile_section(w, h, age, dark=False):
    """Frame, sash and glazing snap together on the beat, then light sweeps the metal."""
    im = grid_paper(w, h, dark).copy()
    L = section_layers(w, h)
    p_shadow = ease(age/.6)
    paste(im, L["shadow"], (0, 0), p_shadow)
    timeline = [("frame", .05, .32), ("sash", .55, -.32), ("glass", 1.05, -.7)]
    for part, start, travel in timeline:
        layer, alpha, metal = L[part]
        p = back((age-start)/.45)
        if age < start:
            continue
        dy = (1-p)*travel*h
        paste(im, layer, (0, dy), min(1, (age-start)/.15))
        snap = age-(start+.45)
        if snap > 0:
            flash(im, alpha, .7*math.exp(-snap/.12), (0, dy))
        if metal is not None and age > 1.6:
            sweep(im, metal, sweep_pos(age-1.6, .45, -.2), .55, .05, (0, dy))
    return im


# --------------------------------------------------------- façade products

@functools.lru_cache(maxsize=6)
def cladding_base(w, h):
    im = sky(w, h, "#B3D3EA", "#EEF4F7")
    d = ImageDraw.Draw(im)
    top, bottom = int(h*.10), int(h*.90)
    bw = w/20
    tones = ["#8C6A45", "#9A774F", "#7D5D3C", "#93704A"]
    for i in range(21):
        x0 = i*bw
        d.rectangle((x0, top, x0+bw, bottom), fill=tones[(i*7) % 4])
        d.line((x0+2, top, x0+2, bottom), fill="#B08B62", width=max(1, w//500))
        d.line((x0+bw-2, top, x0+bw-2, bottom), fill="#4A3826", width=max(2, w//300))
    d.rectangle((0, top-int(h*.03), w, top), fill="#2E3338")
    win = (int(w*.56), int(h*.30), int(w*.86), int(h*.72))
    ww, wh = win[2]-win[0], win[3]-win[1]
    d.rectangle((win[0]-8, win[1]-8, win[2]+8, win[3]+8), fill="#3A2C1E")
    im.alpha_composite(interior_view(ww, wh), win[:2])
    im.alpha_composite(sash(ww, wh, max(6, ww//22)), win[:2])
    door = (int(w*.12), int(h*.46), int(w*.26), int(h*.90))
    d.rectangle(door, fill="#2F3439", outline="#1E2226", width=3)
    d.rounded_rectangle((door[2]-w*.022, h*.58, door[2]-w*.016, h*.76), 3, fill="#D8DDE1")
    d.rectangle((0, bottom, w, h), fill="#CFC9C0")
    d.line((0, bottom, w, bottom), fill="#B5AEA3", width=2)
    plant(d, (w*.34, h*.70, w*.44, h*.92))
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, top, w, bottom), fill=255)
    md.rectangle(win, fill=0)
    md.rectangle(door, fill=0)
    return im, mask


def illus_cladding(w, h, age):
    base, mask = cladding_base(w, h)
    im = base.copy()
    sweep(im, mask, sweep_pos(age, .32, .1), .38, .07)
    return im


@functools.lru_cache(maxsize=6)
def stacbond_base(w, h):
    im = sky(w, h, "#A8CDE6", "#EDF3F7")
    d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = w*.06, w*.94, h*.08, h*.86
    cols, rows = 5, 6
    jw = max(3, w//220)
    rng = np.random.default_rng(11)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    d.rectangle((x0, y0, x1, y1), fill="#2C3136")
    for r in range(rows):
        for c in range(cols):
            bx0 = x0 + c*(x1-x0)/cols + jw
            by0 = y0 + r*(y1-y0)/rows + jw
            bx1 = x0 + (c+1)*(x1-x0)/cols - jw
            by1 = y0 + (r+1)*(y1-y0)/rows - jw
            if r in (2, 4) and 0 < c < cols-1:
                panel = vgrad(int(bx1-bx0), int(by1-by0), "#5F8DB0", "#B6D3E6")
            elif c == 0:
                panel = vgrad(int(bx1-bx0), int(by1-by0), "#4A5259", "#353B41")
                md.rectangle((bx0, by0, bx1, by1), fill=255)
            else:
                v = rng.uniform(-8, 8)
                top = tuple(int(np.clip(a+v, 0, 255)) for a in rgb("#D3D8DC"))
                panel = vgrad(int(bx1-bx0), int(by1-by0), "#%02X%02X%02X" % top, "#AAB1B7")
                md.rectangle((bx0, by0, bx1, by1), fill=255)
            im.alpha_composite(panel, (int(bx0), int(by0)))
    d.rectangle((0, y1, w, h), fill="#D2CFC9")
    d.line((0, y1, w, y1), fill="#B9B4AC", width=2)
    return im, mask


@functools.lru_cache(maxsize=6)
def composite_sample(w, h):
    """Corner of a composite panel: two aluminium skins around a dark core."""
    im, k = supersample(w, h)
    d = ImageDraw.Draw(im)
    S = w*k
    A, B, C, D = (0, .30*S), (.55*S, 0), (S, .22*S), (.45*S, .52*S)
    t = .12*S
    d.polygon([A, B, C, D], fill="#E1E5E8", outline="#8E969C")
    for (p, q) in [(A, D), (D, C)]:
        for frac0, frac1, col in [(0, .25, "#C9CED2"), (.25, .75, "#26292C"), (.75, 1, "#AEB4B9")]:
            d.polygon([(p[0], p[1]+t*frac0), (q[0], q[1]+t*frac0), (q[0], q[1]+t*frac1), (p[0], p[1]+t*frac1)], fill=col)
    d.line([A, B, C], fill="#F7F9FA", width=k*2)
    return down(im, w, h)


def illus_stacbond(w, h, age):
    base, mask = stacbond_base(w, h)
    im = base.copy()
    sweep(im, mask, sweep_pos(age, .30, .4), .45, .06)
    sw = int(w*.30)
    sample = composite_sample(sw, int(sw*.70))
    bob = math.sin(age*2.2)*h*.015
    sh = Image.new("RGBA", (w, h))
    ImageDraw.Draw(sh).ellipse((w*.64, h*.90, w*.64+sw*.95, h*.97), fill=(0, 0, 0, int(60-20*math.sin(age*2.2))))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(3, w//80))))
    paste(im, sample, (w*.64, h*.66+bob))
    return im


# ---------------------------------------------------- interiors & outdoor

@functools.lru_cache(maxsize=6)
def kitchen_base(w, h):
    im = vgrad(w, h, "#EFECE6", "#E3DED6")
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h*.91), w, h), fill="#CDBFAD")
    ux0, ux1, uy0, uy1 = w*.06, w*.94, h*.07, h*.38
    dw = (ux1-ux0)/4
    boxes = []
    for i in range(4):
        box = (int(ux0+i*dw+3), int(uy0), int(ux0+(i+1)*dw-3), int(uy1))
        if i in (0, 3):
            d.rectangle(box, fill="#F6F4F0", outline="#D8D2C8")
            d.rectangle((box[0]+dw*.18, box[3]-h*.02, box[2]-dw*.18, box[3]-h*.012), fill=BRONZE)
        else:
            d.rectangle(box, fill="#D6CEC1")
            for sy in (.17, .27):
                d.rectangle((box[0], h*sy, box[2], h*sy+3), fill="#BDB3A4")
                for j in range(4):
                    cx = box[0] + (j+.5)*(box[2]-box[0])/4
                    d.ellipse((cx-dw*.07, h*sy-h*.055, cx+dw*.07, h*sy), fill=["#F4F1EA", "#9DB3BF", "#E9E2D3", "#C9B79C"][j])
            boxes.append(box)
    d.rectangle((ux0, h*.38, ux1, h*.555), fill="#E6E1D9")
    for x in np.arange(ux0, ux1, dw/3):
        d.line((x, h*.38, x, h*.555), fill="#DAD4CA")
    d.rectangle((ux0-w*.01, h*.555, ux1+w*.01, h*.595), fill="#D5CFC6", outline="#BDB6AB")
    d.rectangle((ux0, h*.595, ux1, h*.612), fill=BRONZE)
    d.rectangle((ux0, h*.612, ux1, h*.91), fill="#363C42")
    for i in range(1, 4):
        x = ux0+i*dw
        d.line((x, h*.612, x, h*.91), fill="#22272B", width=max(2, w//300))
    d.line((ux0, h*.76, ux1, h*.76), fill="#22272B", width=max(2, w//300))
    d.rectangle((ux0, h*.745, ux1, h*.755), fill=BRONZE)
    fx = w*.60
    d.line((fx, h*.555, fx, h*.47), fill="#AEB5BB", width=max(3, w//160))
    d.arc((fx-w*.04, h*.44, fx+w*.0, h*.50), 180, 360, fill="#AEB5BB", width=max(3, w//160))
    plant(d, (w*.78, h*.40, w*.88, h*.56))
    return im, boxes


def illus_kitchen(w, h, age):
    base, (b1, b2) = kitchen_base(w, h)
    im = base.copy()
    t = max(4, (b1[2]-b1[0])//14)
    im.alpha_composite(framed_glass(b1[2]-b1[0], b1[3]-b1[1], t), b1[:2])
    leaf = framed_glass(b2[2]-b2[0], b2[3]-b2[1], t)
    swing(im, leaf, b2, math.radians(70)*wave(age, 4.0), "right", .10)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((b1[0], b1[1], b1[2], b1[3]), fill=255)
    sweep(im, mask, sweep_pos(age, .35, .2), .35)
    return im


@functools.lru_cache(maxsize=6)
def dressing_base(w, h):
    im = vgrad(w, h, "#EEEBE6", "#E4DFD8")
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(h*.93), w, h), fill="#CDBFAD")
    box = (int(w*.08), int(h*.05), int(w*.92), int(h*.93))
    t = max(8, w//70)
    ix0, iy0, ix1, iy1 = box[0]+t, box[1]+t, box[2]-t, box[3]-t
    d.rectangle((ix0, iy0, ix1, iy1), fill="#DCD3C6")
    d.rectangle((ix0, h*.19, ix1, h*.205), fill="#C8BDAD")
    for j in range(6):
        cx = ix0 + (j+.5)*(ix1-ix0)/6
        d.rectangle((cx-w*.03, h*.13, cx+w*.03, h*.19), fill=["#B7A58C", "#8E9AA3", "#D8CBB7", "#6E5B4A", "#A3B1B8", "#C9B49A"][j])
    d.line((ix0, h*.25, ix1, h*.25), fill="#A9B0B6", width=max(3, w//200))
    colors = ["#5B6770", "#B7A58C", "#8E9AA3", "#D8CBB7", "#6E5B4A", "#A3B1B8", "#3F464D", "#C9B49A", "#7C8A7F", "#B9A08A"]
    rng = np.random.default_rng(5)
    n = 10
    for j in range(n):
        cx = ix0 + (j+.5)*(ix1-ix0)/n
        gw = (ix1-ix0)/n*.82
        d.line((cx-gw*.42, h*.30, cx, h*.255, cx+gw*.42, h*.30), fill="#8E959B", width=2)
        d.rounded_rectangle((cx-gw/2, h*.30, cx+gw/2, h*(.55+rng.random()*.22)), int(gw*.18), fill=colors[j])
    d.rectangle((ix0, h*.80, ix1, iy1), fill="#CFC5B6")
    for j in range(3):
        x0 = ix0 + j*(ix1-ix0)/3
        d.rectangle((x0+4, h*.81, x0+(ix1-ix0)/3-4, iy1-4), outline="#BCB0A0", width=2)
        d.rectangle((x0+(ix1-ix0)/6-w*.03, h*.83, x0+(ix1-ix0)/6+w*.03, h*.84), fill=BRONZE)
    im.alpha_composite(metal_ring(box[2]-box[0], box[3]-box[1], t), box[:2])
    return im, (ix0, iy0, ix1, int(h*.80))


def illus_dressing(w, h, age):
    base, (ix0, iy0, ix1, iy1) = dressing_base(w, h)
    im = base.copy()
    dw = (ix1-ix0)//2 + max(4, w//120)
    dh = iy1-iy0
    t = max(5, w//110)
    door = framed_glass(dw, dh, t, "#8C6A45", 105, "anth")
    im.alpha_composite(door, (ix1-dw, iy0))
    x = ix0 + wave(age, 4.5)*(ix1-ix0-dw)*.92
    im.alpha_composite(door, (int(x), iy0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((ix0, iy0, ix1, iy1), fill=255)
    sweep(im, mask, sweep_pos(age, .33, .7), .30)
    return im


@functools.lru_cache(maxsize=6)
def shutter_layers(w, h):
    im = vgrad(w, h, "#EDE9E3", "#E2DDD5")
    d = ImageDraw.Draw(im)
    win = (int(w*.25), int(h*.21), int(w*.75), int(h*.84))
    ww, wh = win[2]-win[0], win[3]-win[1]
    im.alpha_composite(interior_view(ww, wh), win[:2])
    t = max(6, ww//28)
    for i in range(2):
        im.alpha_composite(sash(ww//2, wh, t, handle="right" if i == 0 else "left"), (win[0]+i*ww//2, win[1]))
    d.rectangle((w*.21, h*.84, w*.79, h*.875), fill="#D6D0C7", outline="#C0B8AC")
    d.rectangle((w*.30, h*.875, w*.70, h*.95), fill="#5C6167")
    for j in range(7):
        cx = w*(.32 + j*.06)
        d.ellipse((cx-w*.035, h*.83, cx+w*.035, h*.90), fill=["#6F8F79", "#5D7D69", "#C98B6B", "#77977F", "#D9A35F", "#5D7D69", "#6F8F79"][j])
    top = Image.new("RGBA", (w, h))
    td = ImageDraw.Draw(top)
    td.rectangle((w*.22, h*.11, w*.78, h*.21), fill="#3A4148")
    td.line((w*.22, h*.115, w*.78, h*.115), fill="#6F7A84", width=2)
    td.line((w*.22, h*.21, w*.78, h*.21), fill="#1F2428", width=2)
    for x0 in (.22, .755):
        td.rectangle((w*x0, h*.21, w*(x0+.025), h*.845), fill="#B9C0C6", outline="#858D94")
    return im, top, (int(w*.245), int(h*.21), int(w*.755), int(h*.84))


def illus_shutter(w, h, age):
    base, top, (x0, y0, x1, y1) = shutter_layers(w, h)
    im = base.copy()
    closed = .97*wave(age, 5.0)
    bottom = y0 + closed*(y1-y0)
    d = ImageDraw.Draw(im)
    sh = max(6, int(h*.03))
    y = bottom - sh*.9
    while y > y0 - sh:
        d.rectangle((x0, y, x1, y+sh), fill="#C3C8CC")
        d.line((x0, y+1, x1, y+1), fill="#ECEEF0", width=max(1, sh//6))
        d.line((x0, y+sh-1, x1, y+sh-1), fill="#8C9399", width=max(1, sh//6))
        y -= sh
    if closed > .02:
        d.rectangle((x0, bottom-sh*.9, x1, bottom), fill="#3A4148")
    im.alpha_composite(top)
    return im


@functools.lru_cache(maxsize=6)
def pergola_layers(w, h):
    im = sky(w, h, "#A9D0EA", "#F1EEE6")
    d = ImageDraw.Draw(im)
    d.rectangle((0, h*.60, w, h*.80), fill="#9DB59F")
    for j in range(9):
        cx = w*(j/8)
        d.ellipse((cx-w*.08, h*.50, cx+w*.08, h*.68), fill="#86A38C")
    d.rectangle((0, int(h*.80), w, h), fill="#D3C5B1")
    for y in np.arange(h*.80, h, h*.035):
        d.line((0, y, w, y), fill="#C2B39D", width=1)
    d.rectangle((0, h*.08, w*.10, h*.80), fill="#EFE9E0")
    front = Image.new("RGBA", (w, h))
    fd = ImageDraw.Draw(front)
    fd.rounded_rectangle((w*.30, h*.66, w*.60, h*.80), int(h*.02), fill="#CFC7BA")
    fd.rounded_rectangle((w*.30, h*.60, w*.60, h*.68), int(h*.02), fill="#E2DCD1")
    for cx in (.36, .45, .54):
        fd.rounded_rectangle((w*(cx-.04), h*.57, w*(cx+.04), h*.65), int(h*.02), fill="#F1ECE3")
    fd.rectangle((w*.65, h*.71, w*.76, h*.73), fill="#8C6A45")
    fd.rectangle((w*.68, h*.73, w*.73, h*.80), fill="#7A5C3B")
    for px in (.14, .835):
        fd.rectangle((w*px, h*.28, w*(px+.025), h*.84), fill="#3A4148")
        fd.line((w*px+2, h*.28, w*px+2, h*.84), fill="#66717B", width=2)
    fd.rectangle((w*.12, h*.20, w*.88, h*.225), fill="#3A4148")
    fd.rectangle((w*.12, h*.305, w*.88, h*.335), fill="#3A4148")
    fd.line((w*.12, h*.205, w*.88, h*.205), fill="#66717B", width=2)
    plant(fd, (w*.86, h*.62, w*.97, h*.86))
    plant(fd, (w*.17, h*.66, w*.26, h*.86))
    return im, front


def illus_pergola(w, h, age):
    base, front = pergola_layers(w, h)
    im = base.copy()
    open_ = wave(age, 4.5)
    theta = math.radians(78)*open_
    light = Image.new("RGBA", (w, h))
    ld = ImageDraw.Draw(light)
    n = 12
    span0, span1 = w*.17, w*.83
    sp = (span1-span0)/n
    if open_ > .05:
        for i in range(n):
            xi = span0 + (i+.5)*sp
            g = sp*.5*math.sin(theta)
            ld.polygon([(xi-g/2, h*.33), (xi+g/2, h*.33), (xi+g/2+w*.06, h*.84), (xi-g/2+w*.06, h*.84)],
                       fill=(255, 240, 200, int(70*open_)))
    im.alpha_composite(light.filter(ImageFilter.GaussianBlur(max(3, w//120))))
    im.alpha_composite(front)
    d = ImageDraw.Draw(im)
    c, t, cy = sp*1.12, max(4, h*.012), h*.2625
    for i in range(n):
        cx = span0 + (i+.5)*sp
        ux, uy = math.cos(theta)*c/2, math.sin(theta)*c/2
        vx, vy = -math.sin(theta)*t/2, math.cos(theta)*t/2
        d.polygon([(cx-ux-vx, cy-uy-vy), (cx+ux-vx, cy+uy-vy), (cx+ux+vx, cy+uy+vy), (cx-ux+vx, cy-uy+vy)],
                  fill="#C7CCD0", outline="#7E868D")
    return im


ILLUS = {
    "sliding": illus_sliding, "casement": illus_casement, "door": illus_door,
    "curtain": illus_curtain, "cladding": illus_cladding, "stacbond": illus_stacbond,
    "kitchen": illus_kitchen, "dressing": illus_dressing, "shutter": illus_shutter,
    "pergola": illus_pergola,
}
PRODUCT_KEYS = list(ILLUS)
