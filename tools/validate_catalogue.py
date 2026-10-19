#!/usr/bin/env python3
"""Check source coverage and the actual complete-catalogue delivery.

--data-only checks frozen input coverage, CSV, source hashes and, when present,
the planned timeline. It does not certify exports or write the final report.
The default run additionally checks the rendered timeline, product typography,
both complete decodes, and the ZIP, then writes validation-catalogue.json.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from zipfile import ZipFile

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/catalogue"
RANGES = [
    "hygiene-professionnelle-et-institutionnelle",
    "hygiene-en-milieu-medicale",
    "hygiene-professionnelle-ecologique",
    "matiere-premiere-cosmetique",
    "produits-chimiques-industriels",
    "traitement-des-eaux",
    "produits-de-lavage-et-dentretien-des-vehicules",
]
BOLD_FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"


class ValidationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def read_json(path):
    require(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", " ", value).strip()


def unwrapped(value):
    # Wrapping may split an unusually long token. Preserve every other character,
    # including accents, punctuation, numerical codes and letter case.
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value))


def digest(stream):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(chunk)
    return result.hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def inputs(manifest):
    for field in ("products", "supplementary_products", "named_materials"):
        records = manifest.get(field, [])
        if isinstance(records, dict):
            records = records.get("items", records.get("materials", []))
        for record in records:
            record = {"name": record} if isinstance(record, str) else record
            name = str(record.get("name", record.get("product_name", ""))).strip()
            require(bool(name), f"Unnamed source record in {field}")
            yield record, name


def check_data(index):
    ranges = index["ranges"]
    require([r["slug"] for r in ranges] == RANGES, "The seven requested ranges/order do not match")
    summary, expected_csv, identifiers = [], Counter(), set()
    distinct_names, source_paths = set(), []
    for category in ranges:
        slug = category["slug"]
        source_path = ROOT / "assets/site/catalog" / (slug + ".json")
        require(category["source_manifest"] == str(source_path.relative_to(ROOT)),
                f"Unexpected source manifest for {slug}")
        source_paths.append(source_path)
        manifest = read_json(source_path)
        require(category["root_url"] == manifest["root_url"], f"Wrong root URL for {slug}")
        output = {}
        for product in category["products"]:
            name, ident = product["name"], product["id"]
            key = normalized(name)
            require(key not in output, f"Repeated normalized output name in {slug}: {name}")
            require(ident not in identifiers, f"Repeated product ID: {ident}")
            identifiers.add(ident)
            output[key] = product
            distinct_names.add(key)
            expected_csv[(category["title"], name)] += 1
        require(category["count"] == len(output), f"Wrong range count: {slug}")
        mapped, excluded, alias_matches = defaultdict(list), [], []
        included = 0
        for record, name in inputs(manifest):
            key = normalized(name)
            if record.get("include_in_video") is False:
                require(key not in output, f"Excluded source name leaked into {slug}: {name}")
                excluded.append(name)
                continue
            included += 1
            aliases = record.get("aliases", [])
            aliases = [aliases] if isinstance(aliases, str) else aliases
            # Exact normalized names take precedence over shared source aliases:
            # the co-listed Polyquaternium-7 and -10 remain distinct products.
            matches = [key] if key in output else list({normalized(a) for a in aliases} & output.keys())
            require(len(matches) == 1, f"Missing/ambiguous included source name in {slug}: {name}")
            mapped[matches[0]].append(name)
            if matches[0] != key:
                alias_matches.append({"source_name": name, "display_name": output[matches[0]]["name"]})
        require(set(mapped) == set(output), f"Output contains names absent from included {slug} sources")
        collisions = [{"input_names": names, "display_name": output[key]["name"],
                       "basis": "same normalized spelling (case, accents or punctuation)"}
                      for key, names in mapped.items() if len(names) > 1]
        # A specific audited duplicate is retained as evidence rather than silently
        # interpreting the 116 source rows as 116 different industrial products.
        if slug == "produits-chimiques-industriels":
            require(len(collisions) == 1 and {normalized(n) for n in collisions[0]["input_names"]}
                    == {normalized("Propylène glycol")}, "Unexpected industrial name collision")
        summary.append({"range": slug, "included_source_rows": included,
                        "displayed_reference_names": len(output), "excluded_names": excluded,
                        "normalization_collisions": collisions, "explicit_alias_matches": alias_matches})
    total = sum(r["count"] for r in ranges)
    require(index["category_entries"] == total, "Wrong total category mention count")
    require(index["unique_normalized_names"] == len(distinct_names), "Wrong distinct normalized-name count")
    medical = next(r for r in ranges if r["slug"] == "hygiene-en-milieu-medicale")
    require(any(p["name"] == "OXYCIDE QUICK AP/15 CIDEX/DHN" for p in medical["products"]),
            "The separately named /DHN reference must be displayed, not hidden in aliases")
    with (OUT / "catalogue-complet-fr.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(Counter((row["Gamme"], row["Produit ou matière"]) for row in rows) == expected_csv,
            "CSV category/name coverage differs from the current index")
    return {"scope": "Named references in frozen official sources; not a stock or distinct-formulation audit",
            "category_mentions": total, "distinct_normalized_names": len(distinct_names),
            "ranges": summary, "csv_coverage": "exact match"}, source_paths


def check_timeline(index, timeline, layout_required):
    require((timeline["width"], timeline["height"], timeline["fps"]) == (1920, 1080, 30),
            "Timeline must be Full HD at 30 fps")
    products = {p["id"]: (r["slug"], p) for r in index["ranges"] for p in r["products"]}
    expected = Counter((slug, ident) for ident, (slug, _) in products.items())
    shown, chapters, scenes_by_range = Counter(), Counter(), defaultdict(list)
    offset = 0
    scenes = timeline["scenes"]
    for position, scene in enumerate(scenes):
        duration = scene["duration"]
        require(isinstance(duration, int) and duration > 0, f"Invalid scene duration at {position}")
        require((scene["index"], scene["start"], scene["end"]) == (position, offset, offset + duration),
                f"Non-contiguous scene timing at {position}")
        offset += duration
        if scene["kind"] == "chapter":
            chapters[scene["range"]] += 1
        if scene["kind"] != "products":
            continue
        ids, names = scene["product_ids"], scene["on_screen_names"]
        require(1 <= len(ids) <= 6 and len(ids) == len(names), f"Invalid product batch at {position}")
        for ident, name in zip(ids, names):
            require(ident in products, f"Unknown timeline product ID: {ident}")
            slug, product = products[ident]
            require(slug == scene["range"], f"Product in the wrong range: {name}")
            require(name == product["name"], f"Timeline name differs from source-index name: {name}")
            shown[(slug, ident)] += 1
        scenes_by_range[scene["range"]].append(scene)
    require(offset == timeline["duration"], "Timeline total duration does not match its scenes")
    require(shown == expected, "Timeline must show every product ID/name exactly once in its range")
    require(chapters == Counter({slug: 1 for slug in RANGES}), "Missing or repeated range chapter")
    for slug, product_scenes in scenes_by_range.items():
        require([s["page"] for s in product_scenes] == list(range(1, len(product_scenes) + 1)),
                f"Skipped/repeated catalogue page in {slug}")
        require(all(s["pages"] == len(product_scenes) for s in product_scenes),
                f"Wrong page total in {slug}")
    require(timeline["range_counts"] == {r["slug"]: r["count"] for r in index["ranges"]},
            "Timeline range counts differ from source index")
    for key in ("category_entries", "unique_normalized_names"):
        require(timeline[key] == index[key], f"Timeline {key} differs from source index")
    result = {"scene_count": len(scenes), "duration_seconds": offset,
              "required_product_cards": sum(shown.values()), "exact_id_and_name_coverage": "passed"}
    if not layout_required:
        return result
    checks = timeline["layout_checks"]
    require(Counter(c["id"] for c in checks) == Counter(products.keys()),
            "Rendered typography checks must cover all product IDs exactly once")
    fonts = {}
    for check in checks:
        product = products[check["id"]][1]
        require(check["name"] == product["name"], f"Wrong layout name: {check['id']}")
        require(unwrapped("".join(check["lines"])) == unwrapped(product["name"]),
                f"Letters, accents or punctuation were lost during wrapping: {product['name']}")
        size = check["font_size"]
        require(isinstance(size, int) and size >= 26, f"Product-name font below 26 px: {product['name']}")
        if size not in fonts:
            fonts[size] = ImageFont.truetype(BOLD_FONT, size)
        font = fonts[size]
        lines = check["lines"]
        require(lines and all(isinstance(line, str) and line for line in lines),
                f"Empty product-name line: {product['name']}")
        left, top, right, bottom = check["name_bounds"]
        require(0 <= left < right <= 546 and 0 <= top < bottom <= 246,
                f"Product-name region overlaps card edge/caption: {product['name']}")
        require(math.isclose(right-left, check["text_width"], abs_tol=0.01),
                f"Inconsistent product text width: {product['name']}")
        leading = round(size * 1.23)
        require(math.isclose(bottom-top, len(lines) * leading, abs_tol=0.01),
                f"Inconsistent line-height bounds: {product['name']}")
        for number, line in enumerate(lines):
            require(font.getlength(line) <= check["text_width"] + 0.01,
                    f"Product-name line exceeds its text region: {product['name']}")
            x0, y0, x1, y1 = font.getbbox(line, anchor="lt")
            require(left + 3 + x0 >= 0 and left + 3 + x1 <= 546
                    and top + number * leading + y0 >= 0
                    and top + number * leading + y1 < 246,
                    f"Actual product-name glyph bounds exceed the name area: {product['name']}")
    result["product_name_layout"] = {"checked_names": len(checks),
        "minimum_font_px": min(c["font_size"] for c in checks),
        "exact_characters_after_wrapping": "passed", "measured_glyph_and_card_bounds": "passed",
        "scope": "Required product-name cards; ancillary labels and decorative repetitions have smaller type"}
    return result


def check_source_hashes(source_paths):
    records = []
    for filename, key in [("assets/site/catalogue-image-sources.json", "images"),
                          ("assets/site/brand-client-sources.json", "assets"),
                          ("assets/site/products/product-sources.json", "products")]:
        records.extend(read_json(ROOT / filename)[key])
    images = len(records)
    for path in source_paths:
        manifest = read_json(path)
        for key in ("catalogue_documents", "source_documents"):
            for record in manifest.get(key, []):
                if record.get("sha256"):
                    raw_path = record.get("local_path", record.get("path", record.get("file")))
                    require(bool(raw_path), f"PDF hash without a local path in {path.name}")
                    if raw_path.startswith("catalog/"):
                        raw_path = "assets/site/" + raw_path
                    records.append({**record, "local_path": raw_path})
    checked = {}
    for record in records:
        path = (ROOT / record["local_path"]).resolve()
        require(path.is_relative_to(ROOT), f"Source path outside checkout: {record['local_path']}")
        require(path.is_file(), f"Missing source asset: {record['local_path']}")
        relative = str(path.relative_to(ROOT))
        if relative not in checked:
            checked[relative] = file_digest(path)
        require(checked[relative] == record["sha256"], f"Original source hash differs: {relative}")
        if record.get("bytes") is not None:
            require(path.stat().st_size == record["bytes"], f"Original source byte count differs: {relative}")
    return {"manifest_image_records_checked": images, "pdf_records_checked": len(records)-images,
            "unique_files_checked": len(checked), "sha256_matches_frozen_manifests": True,
            "files": [{"file": p, "sha256": h} for p, h in sorted(checked.items())]}


def check_video(version, duration):
    path = OUT / f"saraproc-maroc-catalogue-complet-{version}.mp4"
    require(path.is_file(), f"Missing export: {path.name}")
    print(f"Inspecting and fully decoding {path.name}", flush=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                           text=True, capture_output=True, check=True)
    data = json.loads(probe.stdout)
    videos = [s for s in data["streams"] if s["codec_type"] == "video"]
    audios = [s for s in data["streams"] if s["codec_type"] == "audio"]
    require(len(videos) == 1, f"Expected one video stream: {path.name}")
    video = videos[0]
    require(video["codec_name"] == "h264" and (video["width"], video["height"]) == (1920, 1080),
            f"Wrong video codec/dimensions: {path.name}")
    require(Fraction(video["r_frame_rate"]) == Fraction(30) and Fraction(video["avg_frame_rate"]) == Fraction(30),
            f"Video is not constant 30 fps: {path.name}")
    require(abs(float(data["format"]["duration"])-duration) < .001
            and abs(float(video["duration"])-duration) < .001, f"Wrong actual duration: {path.name}")
    require(len(audios) == (1 if version == "musique" else 0), f"Wrong audio stream count: {path.name}")
    if audios:
        audio = audios[0]
        require((audio["codec_name"], int(audio["sample_rate"]), audio["channels"]) == ("aac", 48000, 2),
                f"Musical export must contain AAC stereo 48 kHz: {path.name}")
    # A complete, error-fatal decode counts actual output frames. Passthrough
    # timestamps prevent FFmpeg from adding/dropping frames to satisfy a rate.
    decode = subprocess.run(["ffmpeg", "-xerror", "-v", "error", "-nostdin", "-nostats",
        "-stats_period", "30", "-i", str(path), "-map", "0:v:0", "-map", "0:a?",
        "-fps_mode", "passthrough", "-progress", "pipe:1", "-f", "null", "-"],
        text=True, capture_output=True, check=True)
    require(not decode.stderr.strip(), f"Decode reported errors in {path.name}: {decode.stderr[-1500:]}")
    counts = re.findall(r"^frame=(\d+)\s*$", decode.stdout, re.MULTILINE)
    require(counts and "progress=end" in decode.stdout, f"No completed frame-count decode: {path.name}")
    frames = int(counts[-1])
    require(frames == duration * 30, f"Wrong decoded frame count in {path.name}: {frames}")
    if video.get("nb_frames") not in (None, "N/A"):
        require(int(video["nb_frames"]) == frames, f"Container frame count differs from full decode: {path.name}")
    result = {"file": path.name, "duration_seconds": duration, "decoded_frames": frames,
              "dimensions": [1920, 1080], "fps": 30, "video_codec": "h264",
              "full_ffmpeg_xerror_decode": "passed", "audio": "AAC stereo 48 kHz" if audios else None,
              "bytes": path.stat().st_size, "sha256": file_digest(path)}
    print(f"Validated {path.name}: {frames} decoded frames", flush=True)
    return result


def check_archive(videos):
    path = OUT / "Saraproc-Maroc-catalogue-complet.zip"
    require(path.is_file(), f"Missing archive: {path.name}")
    expected = {v["file"]: v["sha256"] for v in videos}
    expected["catalogue-complet-fr.csv"] = file_digest(OUT / "catalogue-complet-fr.csv")
    with ZipFile(path) as archive:
        require(Counter(archive.namelist()) == Counter(expected.keys()), "ZIP must contain exactly both current MP4s and the CSV")
        for name, sha256 in expected.items():
            with archive.open(name) as stream:
                require(digest(stream) == sha256, f"ZIP contains stale/different bytes: {name}")
    return {"file": path.name, "members_match_current_files": True,
            "member_sha256": expected, "sha256": file_digest(path), "bytes": path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-only", action="store_true", help="Validate data/source assets before full exports exist")
    args = parser.parse_args()
    index = read_json(OUT / "catalogue-index.json")
    coverage, source_paths = check_data(index)
    report = {"validated_at_utc": datetime.now(timezone.utc).isoformat(), "coverage": coverage,
              "source_assets": check_source_hashes(source_paths)}
    timeline_path = OUT / ("timeline-catalogue-plan.json" if args.data_only else "timeline-catalogue.json")
    if not args.data_only or timeline_path.exists():
        timeline = read_json(timeline_path)
        report["timeline"] = check_timeline(index, timeline, layout_required=not args.data_only)
    print(f"Data passed: {coverage['category_mentions']} category mentions / "
          f"{coverage['distinct_normalized_names']} distinct normalized names; "
          f"{report['source_assets']['unique_files_checked']} original source files unchanged", flush=True)
    if args.data_only:
        print("Data-only mode: exports/layout/ZIP not certified; final validation report was not written.", flush=True)
        return
    with ThreadPoolExecutor(max_workers=2) as pool:
        report["videos"] = list(pool.map(lambda v: check_video(v, timeline["duration"]), ["musique", "sans-son"]))
    report["archive"] = check_archive(report["videos"])
    report["status"] = "passed"
    report["artifact_sha256"] = {name: file_digest(OUT / name) for name in
        ["catalogue-index.json", "timeline-catalogue.json", "catalogue-complet-fr.csv"]}
    target = OUT / "validation-catalogue.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"All checks passed; saved {target.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValidationError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
