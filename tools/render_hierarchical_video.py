#!/usr/bin/env python3
"""Render the French category/subcategory catalogue using the user's original art."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw
import render_catalogue as c
import render_video as d

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/catalogue-hierarchique"
W, H, FPS = 1920, 1080, 30
LOGO = "assets/user/logo-original.jpg"
INTRO = "assets/user/laboratoire.jpg"
MUSIC = "assets/saraproc-ambient-loop.wav"
NAME = "saraproc-maroc-categories-sous-categories"


def category_image(slug):
    return f"assets/user/category-{slug}.jpg"


def build_timeline(hierarchy):
    scenes = [{"kind": "intro", "duration": 9, "user_image": INTRO},
              {"kind": "overview", "duration": 10}]
    for category in hierarchy["ranges"]:
        slug = category["slug"]
        scenes.append({"kind": "chapter", "range": slug, "duration": 7,
                       "user_image": category_image(slug)})
        for section in category["sections"]:
            scenes.append({"kind": "subcategory", "range": slug,
                           "section_id": section["id"], "section_name": section["display_name"],
                           "duration": max(4, math.ceil(len(section["display_name"].split())/3))})
            products = section["products"]
            pages = math.ceil(len(products)/6)
            for page, pos in enumerate(range(0, len(products), 6), 1):
                batch = products[pos:pos+6]
                words = sum(len(p["name"].split()) for p in batch)
                scenes.append({"kind": "products", "range": slug,
                               "section_id": section["id"], "section_name": section["display_name"],
                               "page": page, "pages": pages,
                               "duration": max(12, math.ceil(words/2.5)+2),
                               "product_ids": [p["id"] for p in batch],
                               "on_screen_names": [p["name"] for p in batch]})
    scenes.extend([{"kind": "clients", "duration": 10}, {"kind": "salon", "duration": 8},
                   {"kind": "closing", "duration": 10}])
    offset = 0
    for i, scene in enumerate(scenes):
        scene.update(index=i, start=offset, end=offset+scene["duration"], logo_path=LOGO)
        offset = scene["end"]
    index = json.loads((ROOT/"output/catalogue/catalogue-index.json").read_text())
    return {"duration": offset, "fps": FPS, "width": W, "height": H,
            "scenes": scenes, "category_entries": index["category_entries"],
            "unique_normalized_names": index["unique_normalized_names"],
            "range_counts": {r["slug"]: r["count"] for r in index["ranges"]},
            "music": MUSIC, "voice_over": False, "layout_checks": [], "logo_path": LOGO,
            "user_image_policy": {"fit": "contain", "crop": False, "recolor": False,
                                  "preserve_aspect_ratio": True},
            "logo_policy": "Original supplied JPG, complete, proportional fit; no crop, redraw or recolouring"}


def exact_logo(layer, box):
    x, y, width, height = box
    # The complete original JPG is fitted. There is no source crop or colour transform.
    logo = d.fitted_asset(LOGO, width, height)
    d.paste(layer, logo, (x+(width-logo.width)/2, y+(height-logo.height)/2))


def header(base, dark, category=None):
    color = "#BED0E8" if dark else c.GRAY
    exact_logo(base, (95, 10, 280, 160))
    if category:
        lines, size, lead = c.fit(category["title"], 1350, 80, 30, 27)
        c.text_lines(base, lines, (430, 65), size, color, leading=lead)
    else:
        d.txt(base, "CATALOGUE PROFESSIONNEL  ·  7 GAMMES", (865, 78), 24, color)
    draw = ImageDraw.Draw(base)
    draw.line((112, 985, 1808, 985), fill="#3B5A7E" if dark else "#CDD9E5", width=1)
    d.txt(base, "SARAPROC MAROC  ·  saraprocmaroc.com", (110, 1011), 18, color)


def make_layers(scene, hierarchy):
    category = next((r for r in hierarchy["ranges"] if r["slug"] == scene.get("range")), None)
    section = next((s for s in category["sections"] if s["id"] == scene.get("section_id")), None) if category else None
    kind = scene["kind"]
    dark = kind in ["subcategory", "clients", "closing"]
    theme = "dark" if dark else ("cosmetic" if category and category["theme"] == "cosmetic" else "light")
    base = d.background(theme).copy()
    title = Image.new("RGBA", (W, H))
    body = Image.new("RGBA", (W, H))
    checks = []
    if kind in ("intro", "chapter"):
        # All supplied banners appear whole, including their embedded original logo.
        base = Image.new("RGB", (W, H), "#FFFFFF")
        image = d.fitted_asset(scene["user_image"], W, H)
        d.paste(base, image, ((W-image.width)/2, (H-image.height)/2))
        return base, title, body, checks
    header(base, dark, category)
    if kind == "products":
        ancestors = section["path"][:-1]
        breadcrumb = "  /  ".join(ancestors)
        if breadcrumb:
            parts, size, lead = c.fit(breadcrumb, 1680, 52, 22, 18, "regular")
            c.text_lines(title, parts, (110, 160), size, c.GRAY, "regular", lead)
        lines, size, lead = c.fit(section["display_name"], 1680, 112, 52, 37)
        c.text_lines(title, lines, (110, 217 if breadcrumb else 190), size, leading=lead)
        products = {p["id"]: p for p in section["products"]}
        for j, ident in enumerate(scene["product_ids"]):
            product = dict(products[ident])
            product["subcategories"] = [section["display_name"]]
            card, check = c.reference_card(product)
            d.paste(body, card, (106+(j%3)*576, 337+(j//3)*314))
            check.update(scene_index=scene["index"], section_id=section["id"])
            checks.append(check)
        d.txt(base, f"ÉCRAN {scene['page']:02d} / {scene['pages']:02d}", (1608, 1012), 17, c.GRAY)
    elif kind == "subcategory":
        d.pill(title, "SOUS-CATÉGORIE" if section["depth"] <= 1 else "SOUS-FAMILLE", (110, 227), dark=True)
        lines, size, lead = c.fit(section["display_name"], 875, 330, 80, 47)
        c.text_lines(title, lines, (107, 335), size, "#FFFFFF", leading=lead)
        ancestors = section["path"][:-1]
        if ancestors:
            lines, size, lead = c.fit("  /  ".join(ancestors), 875, 110, 27, 21, "regular")
            c.text_lines(body, lines, (110, 730), size, "#BED0E8", "regular", lead)
        candidates = list(section["products"])
        if not candidates:
            for child in category["sections"]:
                if child["path"][:len(section["path"])] == section["path"]:
                    candidates += child["products"]
        selected = c.representatives({"products": candidates})
        if selected:
            c.hero_cards(body, selected)
        else:
            # No product photograph is invented for raw materials or empty web families.
            image = d.fitted_asset(category_image(category["slug"]), 735, 420)
            d.paste(body, image, (1040+(735-image.width)/2, 330+(420-image.height)/2))
        if not section["products"] and not candidates:
            d.txt(body, "Échangeons sur vos besoins.", (110, 875), 28, "#BED0E8", "regular")
    elif kind == "overview":
        d.pill(title, "L’OFFRE SARAPROC MAROC", (110, 220))
        c.text_lines(title, ["Plus de"], (110, 335), 74)
        c.text_lines(title, ["320"], (103, 430), 198, c.BLUE)
        c.text_lines(title, ["produits"], (110, 641), 76)
        d.txt(body, "au catalogue Saraproc.", (110, 757), 34, c.GRAY)
        d.txt(body, "Catégories, sous-catégories et produits", (110, 835), 26, c.BLUE)
        for j, r in enumerate(hierarchy["ranges"]):
            parts, size, lead = c.fit(r["title"], 670, 72, 29, 26)
            y = 248+j*92
            d.txt(body, f"{j+1:02d}", (1020, y+4), 22, c.BLUE, "bold")
            c.text_lines(body, parts, (1082, y), size, leading=lead)
    elif kind == "clients":
        c.text_lines(title, ["Ils nous font confiance."], (960, 228), 88, "#FFFFFF", center=True)
        d.txt(title, "Les références présentées sur le site Saraproc Maroc.", (960, 342), 30, "#C0D2E9", center=True)
        d.client_wall(body, 4)
    elif kind == "salon":
        d.pill(title, "À VOTRE RENCONTRE", (110, 225))
        c.text_lines(title, ["Parlons de", "vos besoins."], (105, 342), 101, c.NAVY, leading=113)
        c.text_lines(body, ["Retrouvons-nous au Salon", "international de l’hygiène."],
                     (110, 620), 39, c.BLUE, "regular", 58)
        image = d.fitted_asset(INTRO, 760, 480)
        d.paste(body, image, (1020, 340))
    elif kind == "closing":
        exact_logo(title, (555, 195, 810, 463))
        c.text_lines(body, ["Des solutions professionnelles pour vos activités."], (960, 720),
                     40, "#D2E1F4", "regular", 64, True)
        d.txt(body, "saraprocmaroc.com", (960, 830), 46, "#FFFFFF", "bold", center=True)
    else:
        raise ValueError(kind)
    return base, title, body, checks


def write_reviews(hierarchy, timeline):
    folder = OUT/"apercus"
    folder.mkdir(parents=True, exist_ok=True)
    selected = [s for s in timeline["scenes"] if s["kind"] in ("intro", "overview", "chapter", "clients", "closing")]
    for category in hierarchy["ranges"]:
        selected += [next(s for s in timeline["scenes"] if s["kind"] == "products" and s["range"] == category["slug"])]
    for slug in ["hygiene-en-milieu-medicale", "matiere-premiere-cosmetique"]:
        selected.append(next(s for s in timeline["scenes"] if s["kind"] == "subcategory" and s["range"] == slug))
    selected.sort(key=lambda s:s["index"])
    sheet = Image.new("RGB", (1584, math.ceil(len(selected)/2)*490+24), "#E6EBF1")
    draw = ImageDraw.Draw(sheet)
    for i, scene in enumerate(selected):
        im = c.composite(make_layers(scene, hierarchy))
        im.save(folder/f"{scene['index']:03d}-{scene['kind']}.jpg", quality=94)
        x, y = 16+(i%2)*784, 16+(i//2)*490
        sheet.paste(im.resize((768, 432), Image.Resampling.LANCZOS), (x, y))
        caption = scene.get("section_name", scene.get("range", scene["kind"]))
        draw.text((x+5, y+442), c.timecode(scene["start"])+"  "+caption[:67], font=d.font(18), fill=c.NAVY)
    sheet.save(OUT/"storyboard.jpg", quality=92)


def write_chapters(hierarchy, timeline):
    with (OUT/"chapitres.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Début", "Catégorie", "Sous-catégorie"])
        for s in timeline["scenes"]:
            if s["kind"] in ("chapter", "subcategory"):
                r = next(r for r in hierarchy["ranges"] if r["slug"] == s["range"])
                writer.writerow([c.timecode(s["start"]), r["title"], s.get("section_name", "")])
    with (OUT/"produits-par-sous-categorie.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Catégorie", "Sous-catégorie", "Produit ou matière", "ID", "Photographie", "Source"])
        for r in hierarchy["ranges"]:
            for section in r["sections"]:
                for p in section["products"]:
                    writer.writerow([r["title"], " / ".join(section["path"]), p["name"], p["id"],
                                     p.get("local_image", ""), p.get("url", "")])


def render(hierarchy, timeline, sample=False):
    scenes = timeline["scenes"]
    if sample:
        scenes = [scenes[0], next(s for s in scenes if s["kind"] == "subcategory"),
                  next(s for s in scenes if s["kind"] == "products")]
    with tempfile.TemporaryDirectory(prefix="saraproc-hierarchy-", dir="/tmp") as tmp:
        work = Path(tmp)
        checks = []
        for scene in scenes:
            layers = make_layers(scene, hierarchy)
            for j, layer in enumerate(layers[:3]):
                layer.save(work/f"{scene['index']:03d}-{j}.png")
            checks.extend(layers[3])
        timeline["layout_checks"] = checks
        print(f"Prepared {len(scenes)} segments; duration {c.timecode(timeline['duration'])}", flush=True)
        segments = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(c.encode_segment, scene, work) for scene in scenes]
            for i, future in enumerate(as_completed(jobs), 1):
                n, path = future.result()
                segments[n] = path
                print(f"Encoded {i}/{len(scenes)}", flush=True)
        concat = work/"segments.txt"
        concat.write_text("\n".join(f"file '{segments[s['index']]}'" for s in scenes)+"\n")
        name = NAME if not sample else "apercu-animation"
        silent = OUT/(name+"-sans-son.mp4")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(concat), "-c:v", "copy", "-an", "-movflags", "+faststart", str(silent)], check=True)
        if not sample:
            duration = timeline["duration"]
            musical = OUT/(name+"-musique.mp4")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent),
                            "-stream_loop", "-1", "-i", str(ROOT/MUSIC), "-map", "0:v:0", "-map", "1:a:0",
                            "-c:v", "copy", "-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={duration-3}:d=3",
                            "-c:a", "aac", "-ar", "48000", "-b:a", "128k", "-t", str(duration),
                            "-movflags", "+faststart", "-metadata",
                            "title=Saraproc Maroc — Catégories, sous-catégories et produits", str(musical)], check=True)
            # One ready-to-play film in the archive keeps a normal GitHub download below its file limit.
            archive_path = OUT/"Saraproc-Maroc-categories-sous-categories.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                for path in [musical, OUT/"produits-par-sous-categorie.csv", OUT/"chapitres.csv", OUT/"storyboard.jpg"]:
                    archive.write(path, arcname=path.name)
            if any(p.stat().st_size >= 100_000_000 for p in [musical, silent, archive_path]):
                raise RuntimeError("Export exceeds ordinary GitHub file limit")
            (OUT/"timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+"\n")
    print("Export complete:", silent, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    hierarchy = json.loads((OUT/"hierarchy.json").read_text())
    timeline = build_timeline(hierarchy)
    write_reviews(hierarchy, timeline)
    write_chapters(hierarchy, timeline)
    (OUT/"timeline-plan.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+"\n")
    print(f"{len(timeline['scenes'])} sequences, {c.timecode(timeline['duration'])}", flush=True)
    if not args.stills:
        render(hierarchy, timeline, args.sample)


if __name__ == "__main__":
    main()
