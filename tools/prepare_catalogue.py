#!/usr/bin/env python3
"""Build the seven-range video index and a complete, source-linked product list."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "assets/site/catalog"
OUT = ROOT / "output/catalogue"
RANGES = [
    ("hygiene-professionnelle-et-institutionnelle", "Hygiène professionnelle et institutionnelle", "professional"),
    ("hygiene-en-milieu-medicale", "Hygiène en milieu hospitalier", "medical"),
    ("hygiene-professionnelle-ecologique", "Hygiène professionnelle écologique", "ecological"),
    ("matiere-premiere-cosmetique", "Matières premières cosmétiques", "cosmetic"),
    ("produits-chimiques-industriels", "Produits chimiques pour les industries", "industry"),
    ("traitement-des-eaux", "Traitement des eaux industrielles", "water"),
    ("produits-de-lavage-et-dentretien-des-vehicules", "Lavage et entretien des véhicules", "vehicles"),
]


def normalized(text):
    text = unicodedata.normalize("NFKD", str(text)).casefold()
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", " ", text).strip()


def source_of(p):
    for key in ["source_page", "source_url", "source_pdf_url", "source_pdf", "url", "source_product_page"]:
        if p.get(key):
            return str(p[key])
    return ""


def load_image_lookup():
    manifest = ROOT / "assets/site/catalogue-image-sources.json"
    result = {}
    if manifest.exists():
        for image in json.loads(manifest.read_text()).get("images", []):
            result[image["image_url"]] = image["local_path"]
    for path in [ROOT/"assets/site/products/product-sources.json",
                 ROOT/"assets/site/ranges/cosmetic/sources.json"]:
        if path.exists():
            m = json.loads(path.read_text())
            for image in m.get("products", m.get("assets", [])):
                result[image["original_asset_url"]] = image["local_path"]
    for path in (ROOT/"assets/site/ranges").glob("*/manifest.json"):
        m = json.loads(path.read_text())
        for image in m if isinstance(m, list) else m.get("assets", []):
            result[image["image_url"]] = image.get("local_path") or "assets/site/"+image["file"]
    return result


def make_index():
    image_lookup = load_image_lookup()
    index = {"source_site": "https://www.saraprocmaroc.com/", "ranges": [], "excluded": [],
             "product_count_claim": "Plus de 320 produits au catalogue Saraproc — information fournie par l’utilisateur",
             "scope_note": "Références des sept gammes demandées, d’après les pages et catalogues officiels. "
                           "Hors nutrition végétale, fertilisants, compléments alimentaires animaux et produits uniquement piscine."}
    for slug, title, theme in RANGES:
        path = CAT / (slug+".json")
        m = json.loads(path.read_text())
        unique, alias_map = {}, {}
        for key in ["products", "supplementary_products", "named_materials"]:
            records = m.get(key, [])
            if isinstance(records, dict):
                records = records.get("items", records.get("materials", []))
            for raw in records:
                p = {"name": raw} if isinstance(raw, str) else dict(raw)
                name = str(p.get("name", p.get("product_name", ""))).strip()
                if not name:
                    raise ValueError(f"Missing name in {slug}/{key}: {p}")
                if p.get("include_in_video") is False:
                    index["excluded"].append({"category": title, "name": name,
                                               "reason": p.get("exclusion_reason", p.get("scope_note", "hors périmètre demandé")),
                                               "source": source_of(p)})
                    continue
                norm = normalized(name)
                norm = alias_map.get(norm, norm)
                aliases = p.get("aliases", [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                existing = next((normalized(a) for a in aliases if normalized(a) in unique), None)
                if existing:
                    norm = existing
                sources = [s for s in [source_of(p), p.get("url")] if s]
                if norm in unique:
                    unique[norm]["sources"] = sorted(set(unique[norm]["sources"]+sources))
                    continue
                subcats = p.get("subcategories", p.get("subcategory", []))
                if isinstance(subcats, str):
                    subcats = [subcats]
                subcats = [x.get("name", "") if isinstance(x, dict) else str(x) for x in subcats]
                image_url = p.get("image_url")
                local = image_lookup.get(image_url)
                if p.get("image_status") == "generic_placeholder_not_product_photo":
                    local = None
                item = {"id": hashlib.sha256((slug+"/"+norm).encode()).hexdigest()[:16],
                        "name": name, "subcategories": subcats, "url": p.get("url", ""),
                        "sources": sorted(set(sources)), "image_url": image_url, "local_image": local,
                        "source_kind": "exemple cité" if key == "named_materials" else
                            ("catalogue officiel" if key == "supplementary_products" or "pdf" in p.get("entry_type", "") else "fiche officielle"),
                        "source_page_number": p.get("pdf_page", p.get("page")),
                        "note": p.get("note", p.get("scope_note", ""))}
                unique[norm] = item
                for alias in aliases:
                    alias_map[normalized(alias)] = norm
        products = sorted(unique.values(), key=lambda p: normalized(" ".join(p["subcategories"])+" "+p["name"]))
        index["ranges"].append({"slug": slug, "title": title, "theme": theme,
                                "source_manifest": str(path.relative_to(ROOT)), "root_url": m["root_url"],
                                "products": products, "count": len(products)})
    index["category_entries"] = sum(r["count"] for r in index["ranges"])
    index["unique_normalized_names"] = len({normalized(p["name"]) for r in index["ranges"] for p in r["products"]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"catalogue-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2)+"\n")
    with (OUT/"catalogue-complet-fr.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Gamme", "Sous-famille", "Produit ou matière", "Origine", "Page PDF", "Sources"])
        for r in index["ranges"]:
            for p in r["products"]:
                writer.writerow([r["title"], " · ".join(p["subcategories"]), p["name"], p["source_kind"],
                                 p["source_page_number"] or "", " | ".join(p["sources"])])
    md = ["# Saraproc Maroc — catalogue des sept gammes", "", index["scope_note"], "",
          f"{index['category_entries']} mentions par gamme ; {index['unique_normalized_names']} noms distincts après normalisation.", ""]
    for r in index["ranges"]:
        md.extend([f"## {r['title']} — {r['count']} mentions", ""])
        for p in r["products"]:
            source = p["sources"][0] if p["sources"] else r["root_url"]
            md.append(f"- [{p['name']}]({source}) — {p['source_kind']}")
        md.append("")
    (OUT/"catalogue-complet-fr.md").write_text("\n".join(md).rstrip()+"\n")
    for r in index["ranges"]:
        print(f"{r['count']:3d}  {r['title']}")
    print(f"Total: {index['category_entries']} mentions / {index['unique_normalized_names']} noms distincts")
    return index


if __name__ == "__main__":
    make_index()
