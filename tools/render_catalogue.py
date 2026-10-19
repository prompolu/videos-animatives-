#!/usr/bin/env python3
"""Render the complete seven-range catalogue as a long, animated Full HD film.

python3 tools/prepare_catalogue.py
python3 tools/render_catalogue.py --stills
python3 tools/render_catalogue.py
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import math
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw, ImageFilter
import render_video as d

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"output/catalogue"
W, H, FPS = 1920, 1080, 30
INDEX_PATH = OUT/"catalogue-index.json"
BLUE, NAVY, GRAY = d.TEAL, d.NAVY, d.GRAY


def wrap(text, size, width, weight="bold"):
    f = d.font(size, weight)
    result, line = [], ""
    for word in str(text).split():
        trial = (line+" "+word).strip()
        if f.getlength(trial) <= width:
            line = trial
        else:
            if line:
                result.append(line)
            line = word
            # Break only if a single catalogue token exceeds the available width.
            while f.getlength(line) > width:
                n = len(line)
                while n>1 and f.getlength(line[:n]) > width:
                    n -= 1
                result.append(line[:n])
                line = line[n:]
    if line:
        result.append(line)
    return result


def fit(text, width, height, size=34, minimum=26, weight="bold"):
    while size >= minimum:
        parts = wrap(text, size, width, weight)
        leading = round(size*1.23)
        if len(parts)*leading <= height:
            return parts, size, leading
        size -= 1
    raise ValueError(f"Text would be too small: {text}")


def text_lines(layer, parts, xy, size, color=NAVY, weight="bold", leading=None, center=False):
    leading = leading or round(size*1.23)
    for j, line in enumerate(parts):
        d.txt(layer, line, (xy[0], xy[1]+j*leading), size, color, weight, center=center)


def timecode(seconds):
    s = round(seconds)
    return f"{s//60:02d}:{s%60:02d}"


def build_timeline(index):
    scenes = [{"kind": "intro", "duration": 9}, {"kind": "overview", "duration": 9}]
    for category in index["ranges"]:
        scenes.append({"kind": "chapter", "range": category["slug"], "duration": 5})
        products = category["products"]
        page_count = math.ceil(len(products)/6)
        for page, pos in enumerate(range(0, len(products), 6)):
            batch = products[pos:pos+6]
            words = sum(len(p["name"].split()) for p in batch)
            duration = max(12, math.ceil(words/2.5)+2)
            scenes.append({"kind": "products", "range": category["slug"], "page": page+1,
                           "pages": page_count, "duration": duration,
                           "product_ids": [p["id"] for p in batch],
                           "on_screen_names": [p["name"] for p in batch]})
    scenes.extend([{"kind": "clients", "duration": 10}, {"kind": "salon", "duration": 8},
                   {"kind": "closing", "duration": 10}])
    offset = 0
    for i, scene in enumerate(scenes):
        scene.update({"index": i, "start": offset, "end": offset+scene["duration"]})
        offset += scene["duration"]
    return {"duration": offset, "fps": FPS, "width": W, "height": H, "scenes": scenes,
            "category_entries": index["category_entries"], "unique_normalized_names": index["unique_normalized_names"],
            "range_counts": {r["slug"]: r["count"] for r in index["ranges"]},
            "music": "Original seamless 20-second loop; no voice-over", "layout_checks": []}


def header(base, dark, category=None, page=None, pages=None):
    logo = d.fitted_asset("assets/site/branding/"+("logo_footer.png" if dark else "saraproc-logo.png"), 235, 113)
    d.paste(base, logo, (112, 34))
    d.txt(base, "CATALOGUE PROFESSIONNEL  /  7 GAMMES", (1233, 83), 20,
          "#AFC6E0" if dark else GRAY, tracking=1)
    draw = ImageDraw.Draw(base)
    draw.line((112, 985, 1808, 985), fill="#3B5A7E" if dark else "#CDD9E5", width=1)
    d.txt(base, "SARAPROC MAROC  ·  saraprocmaroc.com", (110, 1011), 18,
          "#BED0E8" if dark else GRAY)
    if page is not None:
        d.txt(base, f"GAMME {category+1:02d} / 07     ÉCRAN {page:02d} / {pages:02d}",
              (1425, 1012), 17, "#BED0E8" if dark else GRAY)


def panel(width, height):
    result = Image.new("RGBA", (width+22, height+26))
    shadow = Image.new("RGBA", result.size)
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((10, 14, width+8, height+16), 22, fill=(15, 35, 62, 35))
    result.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(result).rounded_rectangle((3, 2, width+2, height+1), 20,
                                            fill="#FFFFFF", outline="#DCE5ED", width=1)
    return result


def reference_card(product):
    width, height = 546, 294
    card = panel(width, height)
    image = product.get("local_image")
    if image:
        try:
            parts, size, leading = fit(product["name"], 300, 196, 32, 27)
        except ValueError:
            image = None
    if image:
        pic = d.fitted_asset(image, 190, 244)
        d.paste(card, pic, (16+(190-pic.width)/2, 22+(244-pic.height)/2))
        x, text_width = 225, 300
        y = 26+max(0, (196-len(parts)*leading)/2)
    else:
        parts, size, leading = fit(product["name"], 477, 190, 38, 29)
        x, text_width = 31, 477
        y = 37+max(0, (172-len(parts)*leading)/2)
        ImageDraw.Draw(card).rounded_rectangle((31, 22, 87, 27), 2, fill=BLUE)
    text_lines(card, parts, (x, y), size, leading=leading)
    label = "Huile citée sur le site" if product["source_kind"] == "exemple cité" else (
        product["subcategories"][0] if product["subcategories"] else "Solutions professionnelles")
    label_lines, label_size, label_lead = fit(label, text_width, 44, 18, 15, "regular")
    text_lines(card, label_lines, (x, 246), label_size, GRAY, "regular", label_lead)
    check = {"id": product["id"], "name": product["name"], "font_size": size,
             "lines": parts, "photograph_shown": bool(image), "text_width": text_width,
             "name_bounds": [x, y, x+text_width, y+len(parts)*leading]}
    return card, check


def representatives(category):
    selected, hashes = [], set()
    for p in category["products"]:
        if p.get("local_image") and p["local_image"] not in hashes:
            selected.append(p)
            hashes.add(p["local_image"])
        if len(selected) == 3:
            break
    return selected


def hero_cards(body, selected):
    for j, p in enumerate(selected[:3]):
        width, height = (370, 460) if j == 0 else (316, 285)
        xy = (1030, 325) if j == 0 else (1444, 234+(j-1)*323)
        card = panel(width, height)
        pic = d.fitted_asset(p["local_image"], width-34, height-112)
        d.paste(card, pic, (4+(width-pic.width)/2, 16+(height-112-pic.height)/2))
        lines, size, lead = fit(p["name"], width-36, 69, 23, 18)
        text_lines(card, lines, (width/2, height-84), size, leading=lead, center=True)
        d.paste(body, card, xy)


def make_layers(scene, index):
    categories = index["ranges"]
    by_slug = {r["slug"]: r for r in categories}
    category = by_slug.get(scene.get("range"))
    cat_no = next((i for i, r in enumerate(categories) if r["slug"] == scene.get("range")), None)
    kind = scene["kind"]
    dark = kind in ["intro", "clients", "closing", "chapter"]
    theme = "dark" if dark else ("cosmetic" if category and category["theme"] == "cosmetic" else "light")
    base = d.background(theme).copy()
    header(base, dark, cat_no, scene.get("page"), scene.get("pages"))
    title = Image.new("RGBA", (W, H))
    body = Image.new("RGBA", (W, H))
    fg = "#FFFFFF" if dark else NAVY
    muted = "#C0D2E9" if dark else GRAY
    checks = []
    if kind == "products":
        title_parts, size, lead = fit(category["title"], 1660, 105, 56, 44)
        text_lines(title, title_parts, (960, 178), size, leading=lead, center=True)
        product_map = {p["id"]: p for p in category["products"]}
        for j, ident in enumerate(scene["product_ids"]):
            card, check = reference_card(product_map[ident])
            d.paste(body, card, (106+(j%3)*576, 337+(j//3)*314))
            checks.append(check)
    elif kind == "chapter":
        d.pill(title, f"GAMME {cat_no+1:02d} / 07", (110, 227), dark=True)
        parts, size, lead = fit(category["title"], 870, 300, 88, 63)
        text_lines(title, parts, (107, 356), size, fg, leading=lead)
        d.txt(body, "Découvrez les références et matières", (110, 732), 33, muted)
        d.txt(body, "présentées au catalogue.", (110, 785), 33, muted)
        selected = representatives(category)
        hero_cards(body, selected)
        if not selected:
            d.orbits(body, (1450, 525), 2, True, .9)
            logo = d.fitted_asset("assets/site/branding/logo_footer.png", 400, 185)
            d.paste(body, logo, (1250, 437))
    elif kind == "intro":
        d.pill(title, "LES SOLUTIONS PROFESSIONNELLES", (110, 225), dark=True)
        text_lines(title, ["L’expertise au service", "des professionnels."], (107, 351), 88, fg, leading=105)
        text_lines(body, ["Hygiène · Cosmétique · Industrie", "Eaux industrielles · Entretien des véhicules"],
                   (110, 635), 31, muted, "regular", 51)
        selected = []
        for i in [0, 1, 6]:
            selected += representatives(categories[i])[:1]
        hero_cards(body, selected)
    elif kind == "overview":
        d.pill(title, "LA RICHESSE DU CATALOGUE", (110, 220))
        text_lines(title, ["Plus de"], (110, 335), 74)
        text_lines(title, ["320"], (103, 430), 198, BLUE)
        text_lines(title, ["produits"], (110, 641), 76)
        d.txt(body, "au catalogue Saraproc.", (110, 757), 34, GRAY)
        d.txt(body, "7 gammes présentées dans ce film", (110, 835), 27, BLUE)
        for j, r in enumerate(categories):
            parts, size, lead = fit(r["title"], 670, 72, 29, 26)
            y = 248+j*92
            d.txt(body, f"{j+1:02d}", (1020, y+4), 22, BLUE, "bold")
            text_lines(body, parts, (1082, y), size, leading=lead)
    elif kind == "clients":
        text_lines(title, ["Ils nous font confiance."], (960, 228), 88, fg, center=True)
        d.txt(title, "Les références présentées sur le site Saraproc Maroc.", (960, 342), 30, muted, center=True)
        d.client_wall(body, 4)
    elif kind == "salon":
        d.pill(title, "À VOTRE RENCONTRE", (110, 225))
        text_lines(title, ["Parlons de", "vos besoins."], (105, 342), 101, NAVY, leading=113)
        text_lines(body, ["Retrouvons-nous au Salon", "international de l’hygiène."],
                   (110, 620), 39, BLUE, "regular", 58)
        selected = []
        for i in [2, 3, 5]:
            selected += representatives(categories[i])[:1]
        hero_cards(body, selected)
    else:
        logo = d.fitted_asset("assets/site/branding/logo_footer.png", 564, 260)
        d.paste(title, logo, (960-logo.width/2, 210))
        text_lines(body, ["Des solutions professionnelles", "pour vos activités."], (960, 528),
                   43, "#D2E1F4", "regular", 64, True)
        card = Image.new("RGBA", (724, 106))
        ImageDraw.Draw(card).rounded_rectangle((0, 0, 723, 105), 53, fill=d.MINT)
        d.txt(card, "saraprocmaroc.com", (362, 32), 39, NAVY, "bold", center=True)
        d.paste(body, card, (598, 730))
        d.txt(body, "ÉCHANGEONS SUR VOS BESOINS", (960, 887), 21, "#B1C9E5", tracking=3, center=True)
    return base, title, body, checks


def composite(layers):
    base, title, body, checks = layers
    result = base.copy()
    d.paste(result, title, (0, 0))
    d.paste(result, body, (0, 0))
    return result


def make_review(index, timeline):
    folder = OUT/"apercus"
    folder.mkdir(parents=True, exist_ok=True)
    selected = [s for s in timeline["scenes"] if s["kind"] in ["intro", "overview", "clients", "closing"]]
    for r in index["ranges"]:
        selected.append(next(s for s in timeline["scenes"] if s["kind"] == "products" and s["range"] == r["slug"]))
    selected.sort(key=lambda s:s["start"])
    sheet = Image.new("RGB", (1584, math.ceil(len(selected)/2)*490+24), "#E6EBF1")
    draw = ImageDraw.Draw(sheet)
    for i, scene in enumerate(selected):
        im = composite(make_layers(scene, index))
        im.save(folder/f"{scene['index']:03d}-{scene['kind']}.jpg", quality=94)
        x, y = 16+(i%2)*784, 16+(i//2)*490
        sheet.paste(im.resize((768, 432), Image.Resampling.LANCZOS), (x, y))
        title = next((r["title"] for r in index["ranges"] if r["slug"] == scene.get("range")), scene["kind"])
        draw.text((x+5, y+442), timecode(scene["start"])+"  "+title, font=d.font(19), fill=NAVY)
    sheet.save(OUT/"storyboard-catalogue.jpg", quality=92)


def encode_segment(scene, work):
    n, duration = scene["index"], scene["duration"]
    paths = [work/f"{n:03d}-{k}.png" for k in range(3)]
    output = work/f"segment-{n:03d}.mp4"
    fades = []
    for i, label in [(1, "title"), (2, "body")]:
        delay = .05 if i == 1 else .18
        fades.append(f"[{i}:v]loop=loop=-1:size=1:start=0,setpts=N/({FPS}*TB),format=rgba,"
                     f"fade=t=in:st={delay}:d=0.55:alpha=1,fade=t=out:st={duration-.25}:d=0.25:alpha=1[{label}]")
    filters = ";".join([f"[0:v]loop=loop=-1:size=1:start=0,setpts=N/({FPS}*TB),format=rgba[bg]", *fades,
        "[bg][title]overlay=x=0:y='18*pow(1-min(t/0.7,1),3)':shortest=1[mid]",
        "[mid][body]overlay=x=0:y='24*pow(1-min(max((t-0.15)/0.8,0),1),3)':shortest=1,format=yuv420p,setsar=1[out]"])
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-filter_complex_threads", "1"]
    for path in paths:
        command += ["-framerate", str(FPS), "-i", str(path)]
    command += ["-filter_complex", filters, "-map", "[out]", "-an", "-frames:v", str(duration*FPS),
                "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-threads", "2",
                "-g", "300", "-pix_fmt", "yuv420p", str(output)]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Segment {n}: {result.stderr}")
    return n, output


def render(index, timeline, sample=False):
    duration = timeline["duration"]
    scenes = timeline["scenes"]
    if sample:
        scenes = [scenes[0], next(s for s in scenes if s["kind"] == "products")]
    with tempfile.TemporaryDirectory(prefix="saraproc-catalogue-", dir="/tmp") as tmp:
        work = Path(tmp)
        checks = []
        for scene in scenes:
            layers = make_layers(scene, index)
            for j, layer in enumerate(layers[:3]):
                layer.save(work/f"{scene['index']:03d}-{j}.png")
            checks.extend(layers[3])
        timeline["layout_checks"] = checks
        print(f"Prepared {len(scenes)} animated segments; duration {timecode(duration)}", flush=True)
        segments = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(encode_segment, scene, work) for scene in scenes]
            for i, future in enumerate(as_completed(jobs), 1):
                n, path = future.result()
                segments[n] = path
                print(f"Encoded {i}/{len(scenes)} segments", flush=True)
        concat = work/"segments.txt"
        concat.write_text("\n".join(f"file '{segments[s['index']]}'" for s in scenes)+"\n")
        name = "saraproc-catalogue-apercu" if sample else "saraproc-maroc-catalogue-complet"
        silent = OUT/(name+"-sans-son.mp4")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(concat), "-c:v", "copy", "-an", "-movflags", "+faststart", str(silent)], check=True)
        if not sample:
            musical = OUT/(name+"-musique.mp4")
            loop = ROOT/"assets/saraproc-catalogue-loop-20s.wav"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent),
                            "-stream_loop", "-1", "-i", str(loop), "-map", "0:v:0", "-map", "1:a:0",
                            "-c:v", "copy", "-af", f"afade=t=in:st=0:d=0.9,afade=t=out:st={duration-2.5}:d=2.5",
                            "-c:a", "aac", "-b:a", "128k", "-t", str(duration), "-movflags", "+faststart",
                            "-metadata", "title=Saraproc Maroc — Catalogue professionnel complet — 7 gammes",
                            str(musical)], check=True)
            archive_path = OUT/"Saraproc-Maroc-catalogue-complet.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                for path in [musical, silent, OUT/"catalogue-complet-fr.csv"]:
                    archive.write(path, arcname=path.name)
            if archive_path.stat().st_size >= 100_000_000:
                raise RuntimeError("Combined ZIP is too large for ordinary GitHub; split archives before publication")
    if not sample:
        (OUT/"timeline-catalogue.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+"\n")
    print("Export complete:", silent, flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Encode intro and one product page to verify the pipeline")
    args = parser.parse_args()
    index = json.loads(INDEX_PATH.read_text())
    timeline = build_timeline(index)
    make_review(index, timeline)
    (OUT/"timeline-catalogue-plan.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+"\n")
    with (OUT/"chapitres.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Début", "Gamme"])
        for scene in timeline["scenes"]:
            if scene["kind"] == "chapter":
                category = next(r for r in index["ranges"] if r["slug"] == scene["range"])
                writer.writerow([timecode(scene["start"]), category["title"]])
    print(f"Catalogue: {index['category_entries']} mentions, {len(timeline['scenes'])} sequences, {timecode(timeline['duration'])}", flush=True)
    if not args.stills:
        render(index, timeline, args.sample)


if __name__ == "__main__":
    main()
