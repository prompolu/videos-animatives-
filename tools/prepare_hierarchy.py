#!/usr/bin/env python3
"""Arrange the audited catalogue into its website/PDF category hierarchy.

Original index IDs and display names are never changed. A reference may appear
in several independently sourced branches; ancestor memberships implied by a
more specific membership are represented by the breadcrumb, without a repeat.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "output/catalogue/catalogue-index.json"
OUT = ROOT / "output/catalogue-hierarchique/hierarchy.json"
SITE = "https://www.saraprocmaroc.com"
MEDICAL_OLD = "/categories/hygiene-en-milieu-medicale"
MEDICAL_NEW = "/categories/hygiene-en-milieu-medical-et-hospitalier"


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    return re.sub(r"[^\w]+", " ", "".join(c for c in value if not unicodedata.combining(c))).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_url(url):
    return str(url).replace(MEDICAL_OLD, MEDICAL_NEW).rstrip("/")


DISPLAY_NAMES = {
    "HYGIENE DES BATIMENTS D'ELEVAGE": "Hygiène des bâtiments d’élevage",
    "HYGIENE ET PROPHYLAXIE DE TRAITE": "Hygiène et prophylaxie de traite",
    "HYGIENE DES CUISINES PROFESSIONNELLES": "Hygiène des cuisines professionnelles",
    "HYGIENE ET ENTRETIEN DU TEXTILE ET LINGE PROFESSIONNEL": "Hygiène et entretien du textile et du linge professionnel",
    "L'HYGIENE EN INDUSTRIE DE TRANSFORMATION AGRO-ALIMENTAIRE": "Hygiène en industrie de transformation agroalimentaire",
    "HYGIENE ET TRAITEMENT DES SOLS ET SURFACES": "Hygiène et traitement des sols et surfaces",
    "BIOSECURITE INTERNE DES SURFACES ET DES EQUIPEMENTS": "Biosécurité interne des surfaces et des équipements",
    "BIOSECURITE INTERNE, HYGIENE DU PERSONNEL": "Biosécurité interne : hygiène du personnel",
    "BIOSECURITE INTERNE, EAU D'ABREUVAGE": "Biosécurité interne : eau d’abreuvage",
    "HYGIENE DES SURFACES ET DES INSTALLATIONS DE TRAITE": "Hygiène des surfaces et des installations de traite",
    "HYGIENE DE LA MAMELLE": "Hygiène de la mamelle",
    "HYGIENE DES MAINS ET DES LAVETTES": "Hygiène des mains et des lavettes",
    "HYGIENE DE L'EAU D'ABREUVAGE": "Hygiène de l’eau d’abreuvage",
    "HYGIENE DES SOLS, SURFACES ET EQUIPEMENTS": "Hygiène des sols, surfaces et équipements",
    "LAVAGE ET RINÇAGE DE LA VAISSELLE": "Lavage et rinçage de la vaisselle",
    "PRODUITS D'ENTRETIEN ET ADDITIFS POUR MACHINE LAVE VAISSELLE": "Entretien et additifs pour machine lave-vaisselle",
    "PRODUITS POUR LE TRAITEMENT ASSAINISSANT DES VEGETAUX": "Traitement assainissant des végétaux",
    "HYGIENE DU PERSONNEL": "Hygiène du personnel",
    "LAVAGE DU LINGE": "Lavage du linge",
    "BLANCHIMENT ET DECONTAMINATION DU LINGE": "Blanchiment et décontamination du linge",
    "HYGIENE DES SOLS, SURFACES ET MATERIEL": "Hygiène des sols, surfaces et matériel",
    "HYGIENE DU PERSONNEL – HYGIENE DES MAINS": "Hygiène du personnel et des mains",
    "TRAITEMENT DES FRUITS ET LEGUMES EN STATIONS D'EMBALLAGE": "Traitement des fruits et légumes en stations d’emballage",
    "DESINFECTION PAR VOIE AERIENNE (aerosolisation)": "Désinfection par voie aérienne (aérosolisation)",
    "HYGIENE DES MAINS": "Hygiène des mains",
    "TRAITEMENT DES INSTRUMENTS MEDICO-CHIRURGICAUX": "Traitement des instruments médico-chirurgicaux",
    "TRAITEMENT DES ENDOSCOPES": "Traitement des endoscopes",
    "GEL DE TRANSMISSION ULTRASONIQUE": "Gel de transmission ultrasonique",
    "HYGIENE DES SOLS, SURFACES ET MATERIEL MEDICAL": "Hygiène des sols, surfaces et matériel médical",
    "HYGIENE DES GENERATEURS D’HEMODIALYSE ET DE LA BOUCLE D'EAU": "Hygiène des générateurs d’hémodialyse et de la boucle d’eau",
    "TRAITEMENT EXTERNE": "Traitement externe",
    "TRAITEMENT INTERNE": "Traitement interne",
    "HYGIENE DU PERSONNEL SOIGNANT": "Hygiène du personnel soignant",
    "HYGIENE DE L’ENVIRONNEMENT DE LA SALLE DE DIALYSE": "Hygiène de l’environnement de la salle de dialyse",
    "LES BASES COSMETIQUES NEUTRES ET NATURELLES": "Bases cosmétiques neutres et naturelles",
    "LES HUILES VEGETALES GRADE COSMETIQUE": "Huiles végétales de grade cosmétique",
    "LES HUILES MINERALES GRADE COSMETIQUE": "Huiles minérales de grade cosmétique",
    "LES HUILES DE SILICONE GRADE COSMETIQUE": "Huiles de silicone de grade cosmétique",
    "BASE DE SAVON GLYCERINE MELT and POUR": "Base de savon glycériné Melt and Pour",
    "TENSIO-ACTIFS POUR LA COSMETIQUE": "Tensioactifs pour la cosmétique",
    "LES ALCOOLS GRAS POUR LA COSMETIQUE": "Alcools gras pour la cosmétique",
    "CIRES NATURELLES POUR FORMULATIONS COSMETIQUES": "Cires naturelles pour formulations cosmétiques",
    "ÉMULSIFIANTS, CO-EMULSIFIANTS ET BASES AUTO-EMULSIFIANTES": "Émulsifiants, coémulsifiants et bases autoémulsifiantes",
    "Les vitamines en cosmétique": "Vitamines en cosmétique",
    "Sols, Surfaces et Équipements Professionnels": "Sols, surfaces et équipements professionnels",
    "Hygiène Écologique du Linge": "Hygiène écologique du linge",
    "LES ACIDES": "Acides",
    "LES SOLVANTS": "Solvants",
    "LES BASES": "Bases",
    "LES ESTERS D’ACIDE GRAS": "Esters d’acides gras",
    "LES ALCOOLS": "Alcools",
    "LES ALCOOLS GRAS": "Alcools gras",
    "LES TENSIO-ACTIFS": "Tensioactifs",
    "Les solvants oxygénés": "Solvants oxygénés",
    "Les solvants halogénés": "Solvants halogénés",
    "Les hydrocarbures aliphatiques ": "Hydrocarbures aliphatiques",
    "Les tensio-actifs anioniques": "Tensioactifs anioniques",
    "Les tensio-actifs non ioniques": "Tensioactifs non ioniques",
    "Les tensio-actifs amphotères": "Tensioactifs amphotères",
    "Les tensio-actifs cationiques": "Tensioactifs cationiques",
}


class Tree:
    def __init__(self, source_range):
        self.source_range = source_range
        self.nodes = []
        self.by_url = {}
        self.by_label = {}

    def add(self, name, url, parent_url=None, kind="website_subcategory", source_url=None, **extra):
        if url in self.by_url:
            raise ValueError(f"Duplicate hierarchy URL: {url}")
        node = {
            "id": hashlib.sha256((self.source_range["slug"] + "/" + url).encode()).hexdigest()[:16],
            "name": name,
            "display_name": DISPLAY_NAMES.get(name, name),
            "source_url": source_url or url,
            "current_url": canonical_url(url) if kind == "website_subcategory" else None,
            "parent_source_url": parent_url,
            "node_kind": kind,
            "products": [],
            "children": [],
            **extra,
        }
        self.nodes.append(node)
        self.by_url[url] = node
        key = normalized(name)
        if key in self.by_label:
            raise ValueError(f"Ambiguous hierarchy label: {name}")
        self.by_label[key] = node
        return node

    def alias(self, label, target):
        self.by_label[normalized(label)] = self.by_label[normalized(target)]

    def connect(self):
        roots = []
        for node in self.nodes:
            parent = self.by_url.get(node["parent_source_url"])
            node["parent_id"] = parent["id"] if parent else None
            if parent:
                parent["children"].append(node)
            else:
                roots.append(node)
        sections = []

        def visit(node, path):
            node["depth"] = len(path)
            node["path"] = path + [node["display_name"]]
            sections.append(node)
            for child in node["children"]:
                visit(child, node["path"])
        for node in roots:
            visit(node, [])
        return roots, sections


def make_tree(source_range, manifest):
    tree = Tree(source_range)
    slug = source_range["slug"]
    root_url = manifest["root_url"]
    for entry in manifest.get("subcategories", []):
        url = entry["url"]
        tree.add(entry["name"], url,
                 entry.get("parent_url") or url.rsplit("/", 1)[0])
    if slug == "hygiene-en-milieu-medicale":
        internal = next(x["name"] for x in tree.nodes if x["source_url"].endswith("/traitement-interne"))
        tree.alias("Hémodialyse — traitement interne et boucles d’eau", internal)
        url = SITE + "/catalogues/12/download#produits-speciaux"
        tree.add("Produits spéciaux", url, root_url, "catalogue_pdf_family",
                 source_url=SITE + "/catalogues/12/download#page=18", source_pdf_pages=[18, 19])
    elif slug == "matiere-premiere-cosmetique":
        aliases = {
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
        for alias, target in aliases.items():
            tree.alias(alias, target)
        surfactant_parent = tree.by_label[normalized("TENSIO-ACTIFS POUR LA COSMETIQUE")]["source_url"]
        for name in ["Tensioactifs naturels", "Tensioactifs synthétiques"]:
            tree.add(name, SITE + "/catalogues/13/download#" + normalized(name).replace(" ", "-"),
                     surfactant_parent, "catalogue_pdf_family",
                     source_url=SITE + "/catalogues/13/download#page=3", source_pdf_pages=[3])
        tree.add("Savons de toilette", SITE + "/catalogues/13/download#savons-de-toilette", root_url,
                 "catalogue_pdf_family", source_url=SITE + "/catalogues/13/download#page=2", source_pdf_pages=[2])
    elif slug == "produits-chimiques-industriels":
        listing_url = root_url + "/liste-des-produits-chimique-industriels-par-categorie"
        assert listing_url in manifest["visited_pages"]
        listing = tree.add("Liste des produits chimiques industriels par catégorie", listing_url, root_url)
        document = SITE + "/product/liste-des-produits-chimiques-pour-les-industriels/download/fiche_technique"
        families = [
            ("LES ACIDES", [], 2),
            ("LES SOLVANTS", ["Les solvants oxygénés", "Les solvants halogénés", "Les hydrocarbures aliphatiques "], 3),
            ("LES BASES", [], 2),
            ("LES ESTERS D’ACIDE GRAS", [], 2),
            ("LES ALCOOLS", ["Monoalcools", "Dialcools", "Polyalcools"], 4),
            ("LES ALCOOLS GRAS", [], 4),
            ("LES TENSIO-ACTIFS", ["Les tensio-actifs anioniques", "Les tensio-actifs non ioniques", "Les tensio-actifs amphotères", "Les tensio-actifs cationiques"], 4),
        ]
        for family, children, page in families:
            family_url = document + "#" + normalized(family).replace(" ", "-")
            tree.add(family, family_url, listing["source_url"], "catalogue_pdf_family",
                     source_url=document + f"#page={page}", source_pdf_pages=[page])
            for child in children:
                tree.add(child, document + "#" + normalized(child).replace(" ", "-"), family_url,
                         "catalogue_pdf_family", source_url=document + f"#page={page}", source_pdf_pages=[page])
    elif slug in {"traitement-des-eaux", "produits-de-lavage-et-dentretien-des-vehicules"}:
        for record in manifest["products"]:
            if record.get("include_in_video") is False:
                continue
            for label in record["subcategories"]:
                url = record["source_page"]
                if url not in tree.by_url:
                    assert url in manifest["visited_pages"]
                    tree.add(label, url, root_url)
    return tree


def raw_records(manifest):
    for key in ["products", "supplementary_products", "named_materials"]:
        records = manifest.get(key, [])
        if isinstance(records, dict):
            records = records.get("items", records.get("materials", []))
        for number, raw in enumerate(records):
            record = {"name": raw} if isinstance(raw, str) else raw
            if record.get("include_in_video") is not False:
                yield key, number, record


def product_for_record(record, products_by_name):
    name = record.get("name", record.get("product_name", ""))
    if normalized(name) in products_by_name:
        return products_by_name[normalized(name)]
    aliases = record.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    matches = {products_by_name[normalized(a)]["id"]: products_by_name[normalized(a)]
               for a in aliases if normalized(a) in products_by_name}
    if len(matches) != 1:
        raise ValueError(f"Cannot unambiguously map raw record: {name}, {list(matches)}")
    return next(iter(matches.values()))


def gather_memberships(source_range, manifest, tree):
    products_by_name = {normalized(p["name"]): p for p in source_range["products"]}
    memberships = {p["id"]: {} for p in source_range["products"]}
    mapped_records = 0
    for key, number, record in raw_records(manifest):
        product = product_for_record(record, products_by_name)
        labels = record.get("subcategories", record.get("subcategory", []))
        if isinstance(labels, str):
            labels = [labels]
        for label in labels:
            label_data = label if isinstance(label, dict) else {"name": str(label)}
            node = tree.by_url.get(label_data.get("url")) or tree.by_label.get(normalized(label_data["name"]))
            if not node:
                raise ValueError(f"Unmapped membership in {source_range['slug']}: {label_data}")
            memberships[product["id"]].setdefault(node["id"], []).append({
                "method": "source_subcategory_label",
                "source_record": f"{source_range['source_manifest']}#{key}/{number}",
                "source_record_name": record["name"],
                "source_subcategory_name": label_data["name"],
                "source_subcategory_url": label_data.get("url"),
                "source_page": record.get("source_page", record.get("source_url", "")),
                "source_pdf_page": record.get("pdf_page", record.get("page")),
            })
        if not labels and key == "named_materials" and source_range["theme"] == "cosmetic":
            assert record["source_page"].endswith("/les-huiles-vegetales-aux-vertus-cosmetiques")
            node = tree.by_label[normalized("LES HUILES VEGETALES GRADE COSMETIQUE")]
            memberships[product["id"]].setdefault(node["id"], []).append({
                "method": "official_grouped_product_context",
                "source_record": f"{source_range['source_manifest']}#{key}/{number}",
                "source_record_name": record["name"],
                "source_page": record["source_page"],
                "note": "Named example explicitly appears in the official vegetable-oil grouped product page; not an independently listed SKU.",
            })
        mapped_records += 1
    # Both names explicitly identify the website's otherwise empty Melt-and-Pour
    # subcategory. Keep their original Bases membership, and disclose this extra
    # presentation grouping instead of claiming that its empty listing has SKUs.
    if source_range["theme"] == "cosmetic":
        node = tree.by_label[normalized("BASE DE SAVON GLYCERINE MELT and POUR")]
        for name in ["BIOMA luxury soap (MELT & POUR)", "Base de savon neutre glycérinée « Melt and Pour »"]:
            product = products_by_name[normalized(name)]
            memberships[product["id"]].setdefault(node["id"], []).append({
                "method": "explicit_product_name",
                "source_record_name": product["name"],
                "source_page": product["sources"][0],
                "note": "Presentation grouping supported by the explicit Melt & Pour product name; website subcategory listing itself is empty.",
            })
    return memberships, mapped_records


def build_hierarchy():
    index = json.loads(INDEX.read_text())
    output = {
        "schema_version": 1,
        "source_site": index["source_site"],
        "source_index": str(INDEX.relative_to(ROOT)),
        "source_index_sha256": digest(INDEX),
        "product_count_claim": index["product_count_claim"],
        "scope_note": index["scope_note"],
        "grouping_note": "Les sous-catégories du site sont conservées. Les rubriques supplémentaires des PDF officiels sont identifiées séparément. Une référence peut apparaître dans plusieurs branches lorsque ses sources l’y classent explicitement. Une appartenance à un parent est portée par le chemin si une appartenance plus précise est présente.",
        "ranges": [],
        "excluded": deepcopy(index["excluded"]),
    }
    source_manifest_hashes = {}
    all_occurrences = []
    for source_range in index["ranges"]:
        manifest_path = ROOT / source_range["source_manifest"]
        manifest = json.loads(manifest_path.read_text())
        source_manifest_hashes[source_range["source_manifest"]] = digest(manifest_path)
        tree = make_tree(source_range, manifest)
        children, sections = tree.connect()
        nodes_by_id = {node["id"]: node for node in sections}
        memberships, mapped_records = gather_memberships(source_range, manifest, tree)
        suppressed = []
        products_by_id = {p["id"]: p for p in source_range["products"]}
        for product_id, original_memberships in memberships.items():
            if not original_memberships:
                raise ValueError(f"Unassigned reference {source_range['slug']}: {products_by_id[product_id]['name']}")
            selected = set(original_memberships)
            for node_id in original_memberships:
                parent_id = nodes_by_id[node_id]["parent_id"]
                while parent_id:
                    if parent_id in selected:
                        selected.remove(parent_id)
                        suppressed.append({"product_id": product_id, "ancestor_node_id": parent_id,
                                           "represented_by_descendant_node_id": node_id,
                                           "source_membership_evidence": original_memberships[parent_id]})
                    parent_id = nodes_by_id[parent_id]["parent_id"]
            for node_id in selected:
                product = deepcopy(products_by_id[product_id])
                product["membership_audit"] = {
                    "source_index_product_id": product_id,
                    "source_index_subcategories": products_by_id[product_id]["subcategories"],
                    "assigned_node_id": node_id,
                    "evidence": original_memberships[node_id],
                }
                nodes_by_id[node_id]["products"].append(product)
        for node in sections:
            node["products"].sort(key=lambda p: normalized(p["name"]))
            node["product_count"] = len(node["products"])
            node["subtree_product_count"] = sum(len(child["products"]) for child in sections
                                                 if child["path"][:len(node["path"])] == node["path"])
            node["empty_leaf"] = not node["children"] and not node["products"]
            if node["empty_leaf"]:
                node["coverage_note"] = "Sous-catégorie présente sur le site ; aucune référence individuelle nommée trouvée dans les sources collectées."
        occurrences = [p["id"] for node in sections for p in node["products"]]
        expected = set(products_by_id)
        assert set(occurrences) == expected
        website_urls = {e["url"] for e in manifest.get("subcategories", [])}
        actual_website_urls = {n["source_url"] for n in sections if n["node_kind"] == "website_subcategory"}
        assert website_urls <= actual_website_urls
        raw_expected_count = sum(1 for _ in raw_records(manifest))
        assert raw_expected_count == mapped_records
        range_data = {key: source_range[key] for key in ["slug", "title", "theme", "root_url", "source_manifest"]}
        range_data["current_root_url"] = canonical_url(source_range["root_url"])
        range_data["count"] = source_range["count"]
        range_data["children"] = children
        # Flat sections repeat node metadata, with child IDs rather than another
        # nested copy. Renderers can iterate this deterministic pre-order directly.
        range_data["sections"] = [{**{k: deepcopy(v) for k, v in node.items() if k != "children"},
                                   "children": [c["id"] for c in node["children"]]} for node in sections]
        range_data["audit"] = {
            "source_index_count": source_range["count"],
            "source_record_count_in_scope": mapped_records,
            "covered_source_index_ids": sorted(expected),
            "product_membership_occurrences": len(occurrences),
            "repeated_occurrences_across_independent_branches": len(occurrences) - len(expected),
            "website_subcategory_count": len(actual_website_urls),
            "pdf_only_family_count": sum(n["node_kind"] == "catalogue_pdf_family" for n in sections),
            "section_count": len(sections),
            "nonempty_product_sections": sum(bool(n["products"]) for n in sections),
            "empty_leaf_sections": [{"id": n["id"], "name": n["display_name"], "source_url": n["source_url"]}
                                    for n in sections if n["empty_leaf"]],
            "suppressed_ancestor_memberships": suppressed,
        }
        output["ranges"].append(range_data)
        all_occurrences += occurrences
    output["audit"] = {
        "source_manifest_sha256": source_manifest_hashes,
        "source_index_category_entries": index["category_entries"],
        "source_index_unique_normalized_names": index["unique_normalized_names"],
        "covered_source_index_ids": len(set(all_occurrences)),
        "product_membership_occurrences": len(all_occurrences),
        "section_count": sum(r["audit"]["section_count"] for r in output["ranges"]),
        "website_subcategory_count": sum(r["audit"]["website_subcategory_count"] for r in output["ranges"]),
        "pdf_only_family_count": sum(r["audit"]["pdf_only_family_count"] for r in output["ranges"]),
        "excluded_reference_count": len(index["excluded"]),
        "checks": ["All 503 original category reference IDs covered", "All original names preserved byte-for-byte",
                   "Every in-scope source record reconciled", "Every collected website node represented",
                   "Original source manifests and index preserved"],
    }
    assert len(set(all_occurrences)) == index["category_entries"] == 503
    assert len(index["excluded"]) == 7
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    for data in output["ranges"]:
        a = data["audit"]
        print(f"{data['slug']}: {a['section_count']} sections, {a['source_index_count']} refs, {a['product_membership_occurrences']} appearances")
    print(f"Total: {output['audit']['section_count']} sections / {len(all_occurrences)} product appearances / {len(set(all_occurrences))} source reference IDs")
    return output


if __name__ == "__main__":
    build_hierarchy()
