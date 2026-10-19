#!/usr/bin/env python3
"""Independently verify the hierarchy, names, original artwork and video exports.

--data-only checks the frozen catalogue, source files, hierarchy and any planned
timeline. The default run also checks measured product typography, completely
decodes both MP4 exports, verifies archive bytes and writes validation.json.
"""
from __future__ import annotations

import argparse
from array import array
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave
from zipfile import ZipFile

from PIL import Image, ImageFont

import validate_catalogue as legacy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/catalogue-hierarchique"
INDEX_PATH = ROOT / "output/catalogue/catalogue-index.json"
VIDEO_STEM = "saraproc-maroc-categories-sous-categories"
ARCHIVE_NAME = "Saraproc-Maroc-categories-sous-categories.zip"

# These fingerprints were recorded directly from the nine user attachments,
# independently of the renderer and the editable manifest it consumes.
ORIGINALS = {
    "assets/user/logo-original.jpg": "e00e285b29829ea60172dca0d487572b6d08066491b0ed31bf40cf2977359e11",
    "assets/user/category-hygiene-professionnelle-et-institutionnelle.jpg": "c72631cb167ab54b3182c8bfe1ac46e320a37eb4e01d6cc786a18335ccc72298",
    "assets/user/category-hygiene-professionnelle-ecologique.jpg": "af6af4f13875734db0e20df5941aedad4fdd016025c101335e9819445c1a72ce",
    "assets/user/category-matiere-premiere-cosmetique.jpg": "33b6dc1820f6d7d145b2ef880ed974fca2467492ef482f100e966d97157d347c",
    "assets/user/category-produits-chimiques-industriels.jpg": "833b3380f2e1af084084303a64edd05fdbd58ae9f43c48ec2a1d97f82eccf763",
    "assets/user/category-traitement-des-eaux.jpg": "d0c2ae4c27c7b1adf8cf3a4110ff5a2256776fcca0751ea349fc2bd24f129b0f",
    "assets/user/category-produits-de-lavage-et-dentretien-des-vehicules.jpg": "5b0936c93adfc6111c2d63814481c0fd09fe16bcbd147260fe6ff3c40c456e47",
    "assets/user/laboratoire.jpg": "c90e1d6d59ae15d5899c61cab6fae292463529eaa24b23a111043371450a6f80",
    "assets/user/category-hygiene-en-milieu-medicale.jpg": "a66f0d472e3bf40c5dfe4bcb7b49b60367dc27df3183687fe4e2538a1cb5465a",
}

# Editorially equivalent labels in the PDFs and the website. Keeping the list
# explicit prevents a broad token/fuzzy match from silently moving a product.
SECTION_EQUIVALENTS = {
    "Hémodialyse — traitement interne et boucles d’eau": "TRAITEMENT INTERNE",
    "Bases cosmétiques": "LES BASES COSMETIQUES NEUTRES ET NATURELLES",
    "Huiles végétales": "LES HUILES VEGETALES GRADE COSMETIQUE",
    "Huiles minérales": "LES HUILES MINERALES GRADE COSMETIQUE",
    "Huiles siliconées": "LES HUILES DE SILICONE GRADE COSMETIQUE",
    "Alcools gras": "LES ALCOOLS GRAS POUR LA COSMETIQUE",
    "Acides gras": "Acides gras pour formulations cosmétiques",
    "Beurres cosmétiques": "Beurres cosmétiques pour soins nourrissants",
    "Cires cosmétiques naturelles": "CIRES NATURELLES POUR FORMULATIONS COSMETIQUES",
    "Cires cosmétiques synthétiques": "Cires synthétiques pour formulations cosmétiques",
    "Huiles essentielles": "Huiles essentielles pour cosmétiques naturels",
    "Colorants": "Colorants pour formulations cosmétiques",
    "Conservateurs cosmétiques": "Conservateurs pour cosmétiques",
    "Antioxydants": "Antioxydants pour cosmétiques",
    "Émulsifiants": "ÉMULSIFIANTS, CO-EMULSIFIANTS ET BASES AUTO-EMULSIFIANTES",
    "Épaississants": "Épaississants pour formulations cosmétiques",
    "Argiles": "Argiles pour soins cosmétiques",
    "Charbon actif": "Charbon actif en cosmétique",
    "Vitamines": "Les vitamines en cosmétique",
    "Microbilles, exfoliation et gommage": "Microbilles & gommage",
}
require = legacy.require
read_json = legacy.read_json
file_digest = legacy.file_digest


def check_original_artwork():
    manifest = read_json(ROOT / "assets/user/manifest.json")
    images = manifest["images"]
    require(len(images) == 9, "Expected the nine user-supplied photographs/logo")
    require(Counter(i["path"] for i in images) == Counter(ORIGINALS.keys()),
            "User artwork manifest must contain exactly the nine supplied images")
    original_directory = Path("/tmp/codex-remote-attachments")
    records = []
    for record in images:
        relative = record["path"]
        path = ROOT / relative
        actual = file_digest(path)
        require(actual == ORIGINALS[relative] == record["sha256"],
                f"User-supplied original was changed: {relative}")
        require(path.stat().st_size == record["bytes"], f"Artwork byte count changed: {relative}")
        with Image.open(path) as image:
            require(image.size == (record["width"], record["height"]),
                    f"Artwork dimensions changed: {relative}")
            image.verify()
        copies = list(original_directory.rglob(record["original_source_filename"])) if original_directory.exists() else []
        if copies:
            require(any(file_digest(copy) == actual for copy in copies),
                    f"Archived image differs from the original attached file: {relative}")
        records.append({"file": relative, "sha256": actual,
                        "compared_to_available_user_attachment": bool(copies)})
    return {"original_files": 9, "byte_exact_originals": True, "files": records}


def check_membership_evidence(slug, product, section, source_manifest):
    audit = product["membership_audit"]
    require(audit["source_index_product_id"] == product["id"]
            and audit["source_index_subcategories"] == product["subcategories"]
            and audit["assigned_node_id"] == section["id"],
            f"Membership audit identifies a different product or section: {product['id']}")
    evidence = audit["evidence"]
    require(evidence, f"Missing membership evidence: {product['id']}")
    methods = []
    for item in evidence:
        method = item["method"]
        methods.append(method)
        require(method in ("source_subcategory_label", "official_grouped_product_context", "explicit_product_name"),
                f"Unreviewed product-assignment method: {method}")
        if method == "explicit_product_name":
            require(slug == "matiere-premiere-cosmetique"
                    and "melt" in legacy.normalized(product["name"]).split()
                    and "pour" in legacy.normalized(product["name"]).split()
                    and "melt" in legacy.normalized(section["name"]).split(),
                    "Only the two explicitly named Melt and Pour bases use the product-name grouping exception")
            require(item["source_record_name"] == product["name"], "Explicit-name grouping changes the source name")
            continue
        source_pointer = item["source_record"]
        filename, separator, pointer = source_pointer.partition("#")
        require(separator and filename == f"assets/site/catalog/{slug}.json", "Membership source points outside its range")
        record = source_manifest
        for part in pointer.split("/"):
            record = record[int(part)] if isinstance(record, list) else record[part]
        require(isinstance(record, dict) and record.get("include_in_video") is not False,
                f"Membership points to a missing/excluded source record: {source_pointer}")
        source_name = record.get("name", record.get("product_name"))
        require(source_name == item["source_record_name"], "Membership evidence does not match its frozen source record")
        aliases = record.get("aliases", [])
        aliases = [aliases] if isinstance(aliases, str) else aliases
        require(legacy.normalized(product["name"]) in {legacy.normalized(v) for v in [source_name, *aliases]},
                f"Membership evidence names a different source product: {product['name']}")
        if method == "official_grouped_product_context":
            require(slug == "matiere-premiere-cosmetique" and "huiles vegetales" in legacy.normalized(section["name"]),
                    "Grouped-product context is limited to the three named vegetable-oil examples")
            require(product["source_kind"] == "exemple cité", "Grouped material must retain its example status")
            continue
        labels = record.get("subcategories", record.get("subcategory", []))
        labels = [labels] if isinstance(labels, str) else labels
        labels = [label["name"] if isinstance(label, dict) else label for label in labels]
        source_label = item["source_subcategory_name"]
        require(source_label in labels, "Audited subcategory label is absent from the actual source record")
        allowed_target = SECTION_EQUIVALENTS.get(source_label, source_label)
        require(legacy.normalized(allowed_target) == legacy.normalized(section["name"]),
                f"Product source label does not support this section assignment: {source_label} -> {section['name']}")
    return methods


def check_hierarchy(index, hierarchy):
    require([r["slug"] for r in hierarchy["ranges"]] == legacy.RANGES,
            "Hierarchy must contain exactly the seven requested ranges in order")
    products = {p["id"]: (r["slug"], p) for r in index["ranges"] for p in r["products"]}
    sections, memberships, coverage = {}, {}, Counter()
    summary = []
    evidence_methods = Counter()
    for category in hierarchy["ranges"]:
        slug = category["slug"]
        source_manifest = read_json(ROOT / "assets/site/catalog" / (slug + ".json"))
        parent_positions = {}
        range_sections = category["sections"]
        require(range_sections, f"Range lacks subcategories: {slug}")
        for position, section in enumerate(range_sections):
            ident = section["id"]
            key = (slug, ident)
            require(key not in sections, f"Duplicate hierarchy section ID in {slug}: {ident}")
            require(section["name"] and section["display_name"], f"Empty section name: {key}")
            require(isinstance(section["depth"], int) and section["depth"] >= 0,
                    f"Invalid section depth: {key}")
            parent_id = section.get("parent_id")
            if parent_id:
                require(parent_id in parent_positions, f"Missing or out-of-order section parent: {key}")
                parent = sections[(slug, parent_id)]
                require(section["depth"] == parent["depth"] + 1,
                        f"Section depth differs from its parent: {key}")
                require(section["path"] == parent["path"] + [section["display_name"]],
                        f"Section breadcrumb differs from its parent: {key}")
            else:
                require(section["depth"] == 0 and section["path"] == [section["display_name"]],
                        f"Root section has an invalid breadcrumb/depth: {key}")
            sections[key] = section
            parent_positions[ident] = position
            member_ids = []
            for product in section["products"]:
                product_id = product["id"]
                require(product_id in products, f"Hierarchy contains unknown product: {product_id}")
                expected_slug, original = products[product_id]
                require(expected_slug == slug, f"Hierarchy product assigned to the wrong range: {product_id}")
                for field in ("name", "local_image", "subcategories"):
                    require(product.get(field) == original.get(field),
                            f"Hierarchy changes the original product {field}: {product_id}")
                require(product.get("membership_audit"), f"Missing auditable section assignment: {product_id}")
                evidence_methods.update(check_membership_evidence(slug, product, section, source_manifest))
                coverage[product_id] += 1
                member_ids.append(product_id)
            require(len(member_ids) == len(set(member_ids)), f"Repeated product within a section: {key}")
            memberships[key] = set(member_ids)
        site_urls = {section["source_url"] for section in range_sections if section["node_kind"] == "website_subcategory"}
        for original_section in source_manifest.get("subcategories", []):
            require(original_section["url"] in site_urls,
                    f"Website subcategory was omitted from the hierarchy: {original_section['url']}")
        summary.append({"range": slug, "sections": len(range_sections),
                        "section_product_appearances": sum(len(s["products"]) for s in range_sections)})
    require(set(coverage) == set(products), "Hierarchy must include every one of the 503 source-index IDs")
    require(len(products) == 503, "Unexpected frozen source-index coverage; review the changed scope")
    return ({"source_product_ids": len(products), "sections": len(sections),
             "product_section_memberships": sum(coverage.values()),
             "source_pointer_membership_evidence": dict(evidence_methods),
             "products_repeated_in_several_sections": sum(n > 1 for n in coverage.values()),
             "all_source_products_retained": True, "ranges": summary}, products, sections, memberships)


def check_exported_csvs(hierarchy, timeline=None):
    expected = Counter()
    for category in hierarchy["ranges"]:
        for section in category["sections"]:
            for product in section["products"]:
                expected[(category["title"], " / ".join(section["path"]), product["name"], product["id"],
                          product.get("local_image") or "", product.get("url") or "")] += 1
    with (OUT / "produits-par-sous-categorie.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == ["Catégorie", "Sous-catégorie", "Produit ou matière", "ID", "Photographie", "Source"],
                "Unexpected product CSV columns")
        actual = Counter(tuple(row[field] for field in reader.fieldnames) for row in reader)
    require(actual == expected, "Product CSV must contain exactly every current product/subcategory membership")
    result = {"catalogue_rows": sum(actual.values()), "exact_hierarchy_membership_match": True}
    if timeline is not None:
        ranges = {category["slug"]: category for category in hierarchy["ranges"]}
        expected_chapters = []
        for scene in timeline["scenes"]:
            if scene["kind"] in ("chapter", "subcategory"):
                start = scene["start"]
                expected_chapters.append((f"{start//60:02d}:{start%60:02d}", ranges[scene["range"]]["title"],
                                          scene.get("section_name", "")))
        with (OUT / "chapitres.csv").open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames == ["Début", "Catégorie", "Sous-catégorie"], "Unexpected chapter CSV columns")
            actual_chapters = [tuple(row[field] for field in reader.fieldnames) for row in reader]
        require(actual_chapters == expected_chapters, "Chapter CSV differs from actual scene times/names/order")
        result.update(chapter_rows=len(actual_chapters), exact_timeline_chapters_match=True)
    return result


def check_timeline(timeline, products, sections, memberships, layout_required):
    require((timeline["width"], timeline["height"], timeline["fps"]) == (1920, 1080, 30),
            "Timeline must be 1920×1080 at 30 fps")
    require(timeline.get("voice_over") is False, "This version must use ambient music without an undeclared voice-over")
    scenes = timeline["scenes"]
    chapter_count, intro_count, shown = Counter(), Counter(), Counter()
    scene_cards = Counter()
    pages = defaultdict(list)
    seen_sections, used_images = set(), set()
    if timeline.get("logo_path"):
        used_images.add(timeline["logo_path"])
    policy = timeline.get("user_image_policy", {})
    require(policy.get("fit") == "contain" and policy.get("crop") is False
            and policy.get("recolor") is False and policy.get("preserve_aspect_ratio") is True,
            "Renderer must explicitly preserve whole artwork, colour and proportions")
    offset = 0
    for position, scene in enumerate(scenes):
        duration = scene["duration"]
        require(isinstance(duration, int) and duration > 0, f"Invalid scene duration: {position}")
        require((scene["index"], scene["start"], scene["end"]) == (position, offset, offset + duration),
                f"Non-contiguous scene timing: {position}")
        offset += duration
        for field in ("user_image", "logo_path"):
            if scene.get(field):
                require(scene[field] in ORIGINALS, f"Scene uses unrecognised user artwork: {scene[field]}")
                used_images.add(scene[field])
        kind, slug = scene["kind"], scene.get("range")
        if kind == "chapter":
            chapter_count[slug] += 1
            require(scene.get("user_image") == f"assets/user/category-{slug}.jpg",
                    f"Category chapter must display its supplied category image: {slug}")
        elif kind == "subcategory":
            key = (slug, scene["section_id"])
            require(key in sections, f"Unknown subcategory intro: {key}")
            require(scene["section_name"] == sections[key]["display_name"], "Subcategory intro displays a different section name")
            intro_count[key] += 1
            seen_sections.add(key)
        elif kind == "products":
            key = (slug, scene["section_id"])
            require(key in sections and key in seen_sections, f"Products precede their subcategory intro: {key}")
            require(scene["section_name"] == sections[key]["display_name"], "Product page displays a different section name")
            ids, names = scene["product_ids"], scene["on_screen_names"]
            require(1 <= len(ids) <= 6 and len(ids) == len(names), f"Invalid product page at scene {position}")
            require(len(ids) == len(set(ids)), f"Duplicate product card within a page: {position}")
            for ident, name in zip(ids, names):
                require(ident in products, f"Unknown on-screen product ID: {ident}")
                product_slug, original = products[ident]
                require(product_slug == slug and ident in memberships[key],
                        f"Product shown in the wrong range/subcategory: {name}")
                require(name == original["name"], f"On-screen name differs from the frozen source: {name}")
                shown[(slug, scene["section_id"], ident)] += 1
                scene_cards[(position, scene["section_id"], ident)] += 1
            pages[key].append(scene)
    require(offset == timeline["duration"], "Timeline total differs from its contiguous scenes")
    require(chapter_count == Counter({slug: 1 for slug in legacy.RANGES}),
            "Each requested range must have exactly one category chapter")
    require(intro_count == Counter({key: 1 for key in sections}),
            "Each hierarchy section must have exactly one subcategory introduction")
    expected = Counter((slug, section_id, ident) for (slug, section_id), ids in memberships.items() for ident in ids)
    require(shown == expected, "Timeline must show every expected product/subcategory membership exactly once")
    for key, section_pages in pages.items():
        require([s["page"] for s in section_pages] == list(range(1, len(section_pages) + 1)),
                f"Skipped/repeated product page in {key}")
        require(all(s["pages"] == len(section_pages) for s in section_pages),
                f"Wrong product-page total in {key}")
    require(used_images == set(ORIGINALS), "Timeline must use the logo and all eight other user images")
    result = {"scenes": len(scenes), "duration_seconds": offset, "sections_introduced": len(intro_count),
              "product_section_cards": sum(shown.values()), "all_503_product_ids_shown": True,
              "all_nine_user_images_used": True, "whole_original_artwork_policy": policy}
    if layout_required:
        checks = timeline["layout_checks"]
        require(Counter((c["scene_index"], c["section_id"], c["id"]) for c in checks) == scene_cards,
                "Rendered layout records must cover each actual product card exactly once")
        fonts = {}
        for check in checks:
            original = products[check["id"]][1]
            require(check["name"] == original["name"], f"Wrong rendered name: {check['id']}")
            lines = check["lines"]
            require(lines and all(isinstance(line, str) and line for line in lines), "Empty name line")
            require(legacy.unwrapped("".join(lines)) == legacy.unwrapped(original["name"]),
                    f"Lost character, accent or code in product wrapping: {original['name']}")
            size = check["font_size"]
            require(isinstance(size, int) and size >= 26, f"Product font smaller than 26 px: {original['name']}")
            if size not in fonts:
                fonts[size] = ImageFont.truetype(legacy.BOLD_FONT, size)
            font = fonts[size]
            left, top, right, bottom = check["name_bounds"]
            require(0 <= left < right <= 546 and 0 <= top < bottom <= 246,
                    f"Product name overlaps the card/caption: {original['name']}")
            require(math.isclose(right - left, check["text_width"], abs_tol=.01), "Wrong text-width record")
            leading = round(size * 1.23)
            require(math.isclose(bottom - top, len(lines) * leading, abs_tol=.01), "Wrong name height")
            for number, line in enumerate(lines):
                require(font.getlength(line) <= right - left + .01,
                        f"Product-name line wider than its allocated region: {original['name']}")
                x0, y0, x1, y1 = font.getbbox(line, anchor="lt")
                require(left + 3 + x0 >= 0 and left + 3 + x1 <= 546
                        and top + number * leading + y0 >= 0 and top + number * leading + y1 < 246,
                        f"Actual product-name glyph exceeds the card region: {original['name']}")
        result["product_typography"] = {"checked_cards": len(checks),
            "minimum_font_px": min(c["font_size"] for c in checks),
            "exact_characters_after_wrapping": True, "measured_glyph_bounds": "passed"}
    return result


def check_soundtrack(timeline):
    relative = timeline["music"]
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT / "assets") and path.is_file(), "Missing ambient soundtrack source")
    with wave.open(str(path), "rb") as soundtrack:
        channels, rate, width, frames = (soundtrack.getnchannels(), soundtrack.getframerate(),
                                         soundtrack.getsampwidth(), soundtrack.getnframes())
        require((channels, rate, width) == (2, 48000, 2), "Ambient source must be stereo PCM16 at 48 kHz")
        samples = array("h", soundtrack.readframes(frames))
    if sys.byteorder != "little":
        samples.byteswap()
    require(len(samples) == frames * channels and frames >= rate, "Truncated or too short ambient source")
    peak = max(abs(value) for value in samples)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    require(0 < rms < peak < 32767, "Ambient source is silent or clipped")
    return {"file": relative, "sha256": file_digest(path), "duration_seconds": frames / rate,
            "sample_rate": rate, "channels": channels, "peak_dbfs": round(20 * math.log10(peak / 32768), 3),
            "rms_dbfs": round(20 * math.log10(rms / 32768), 3), "signal_present_without_clipping": True}


def check_video(version, duration):
    path = OUT / f"{VIDEO_STEM}-{version}.mp4"
    require(path.is_file(), f"Missing video: {path.name}")
    print(f"Fully decoding {path.name}", flush=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                           text=True, capture_output=True, check=True)
    metadata = json.loads(probe.stdout)
    videos = [stream for stream in metadata["streams"] if stream["codec_type"] == "video"]
    audios = [stream for stream in metadata["streams"] if stream["codec_type"] == "audio"]
    require(len(videos) == 1, f"Wrong number of video streams: {path.name}")
    video = videos[0]
    require(video["codec_name"] == "h264" and (video["width"], video["height"]) == (1920, 1080),
            f"Wrong video codec or dimensions: {path.name}")
    require(Fraction(video["avg_frame_rate"]) == 30 and Fraction(video["r_frame_rate"]) == 30,
            f"Video must have constant 30 fps: {path.name}")
    require(abs(float(metadata["format"]["duration"]) - duration) < .001
            and abs(float(video["duration"]) - duration) < .001, f"Wrong video duration: {path.name}")
    require(len(audios) == (1 if version == "musique" else 0), f"Wrong audio stream count: {path.name}")
    if audios:
        audio = audios[0]
        require((audio["codec_name"], int(audio["sample_rate"]), audio["channels"]) == ("aac", 48000, 2),
                f"Musical export must have AAC stereo audio at 48 kHz: {path.name}")
        require(abs(float(audio["duration"]) - duration) < .05, "Ambient soundtrack must cover the whole movie")
    decoded = subprocess.run(["ffmpeg", "-xerror", "-v", "error", "-nostdin", "-nostats", "-stats_period", "30",
        "-i", str(path), "-map", "0:v:0", "-map", "0:a?", "-fps_mode", "passthrough",
        "-progress", "pipe:1", "-f", "null", "-"], text=True, capture_output=True, check=True)
    require(not decoded.stderr.strip(), f"Full decode reported an error: {decoded.stderr[-1500:]}")
    frame_counts = re.findall(r"^frame=(\d+)\s*$", decoded.stdout, flags=re.MULTILINE)
    require(frame_counts and "progress=end" in decoded.stdout, f"Decode did not complete: {path.name}")
    frames = int(frame_counts[-1])
    require(frames == duration * 30, f"Wrong actual decoded frame count: {path.name}: {frames}")
    if video.get("nb_frames") not in (None, "N/A"):
        require(int(video["nb_frames"]) == frames, f"Container and decoded frame counts differ: {path.name}")
    print(f"Passed full decode: {path.name}, {frames} frames", flush=True)
    return {"file": path.name, "duration_seconds": duration, "decoded_frames": frames,
            "dimensions": [1920, 1080], "fps": 30, "video_codec": "h264",
            "audio": "AAC stereo 48 kHz" if audios else None,
            "full_ffmpeg_xerror_decode": "passed", "bytes": path.stat().st_size, "sha256": file_digest(path)}


def check_archive(videos):
    path = OUT / ARCHIVE_NAME
    require(path.is_file(), f"Missing ZIP delivery: {path.name}")
    require(path.stat().st_size < 100_000_000, "Delivery ZIP exceeds the repository's per-file size limit")
    expected_movie = next(v for v in videos if v["file"].endswith("-musique.mp4"))
    members = {}
    with ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "ZIP has duplicate member names")
        require(set(names) == {expected_movie["file"], "produits-par-sous-categorie.csv", "chapitres.csv", "storyboard.jpg"},
                "ZIP must contain exactly the musical movie, product CSV, chapter CSV and storyboard")
        for name in names:
            require(Path(name).name == name, f"Unexpected nested/unsafe archive member: {name}")
            actual_file = OUT / name
            require(actual_file.is_file(), f"Archive member has no matching current output: {name}")
            require(actual_file.suffix.lower() in (".mp4", ".csv", ".md", ".json", ".jpg"),
                    f"Unexpected archive member type: {name}")
            expected_hash = file_digest(actual_file)
            with archive.open(name) as stream:
                require(legacy.digest(stream) == expected_hash, f"Archive contains stale or altered output: {name}")
            members[name] = expected_hash
        require(members[expected_movie["file"]] == expected_movie["sha256"], "Archive movie differs from validated export")
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": file_digest(path),
            "member_sha256": members, "members_match_current_files": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-only", action="store_true", help="Check frozen inputs without certifying exports")
    args = parser.parse_args()
    index = read_json(INDEX_PATH)
    coverage, source_paths = legacy.check_data(index)
    hierarchy = read_json(OUT / "hierarchy.json")
    hierarchy_report, products, sections, memberships = check_hierarchy(index, hierarchy)
    report = {"validated_at_utc": datetime.now(timezone.utc).isoformat(), "coverage": coverage,
              "source_assets": legacy.check_source_hashes(source_paths),
              "user_artwork": check_original_artwork(), "hierarchy": hierarchy_report}
    timeline_path = OUT / ("timeline-plan.json" if args.data_only else "timeline.json")
    if timeline_path.exists() or not args.data_only:
        timeline = read_json(timeline_path)
        report["timeline"] = check_timeline(timeline, products, sections, memberships, layout_required=not args.data_only)
    else:
        timeline = None
    report["csv_exports"] = check_exported_csvs(hierarchy, timeline)
    if timeline is not None:
        report["ambient_source"] = check_soundtrack(timeline)
    print(f"Inputs passed: {len(products)} source reference IDs, {len(sections)} hierarchy sections, nine original images", flush=True)
    if args.data_only:
        print("Data-only mode does not certify videos, typography or archive; no final report written.", flush=True)
        return
    with ThreadPoolExecutor(max_workers=2) as pool:
        report["videos"] = list(pool.map(lambda version: check_video(version, timeline["duration"]), ["musique", "sans-son"]))
    report["archive"] = check_archive(report["videos"])
    report["artifact_sha256"] = {path.name: file_digest(path) for path in [
        OUT / "hierarchy.json", OUT / "timeline.json", ROOT / "assets/user/manifest.json"]}
    report["status"] = "passed"
    temporary = OUT / "validation.json.tmp"
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUT / "validation.json")
    print("All checks passed; saved output/catalogue-hierarchique/validation.json", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (legacy.ValidationError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
