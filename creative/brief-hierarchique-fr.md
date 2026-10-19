# Saraproc Maroc — régénération par sous-catégorie

## Demande

Régénérer le film en français en mentionnant les catégories et leurs sous-catégories, puis les produits correspondants. Utiliser les neuf photos jointes et conserver le logo complet sans modification. Ajouter une musique ambiante. Maintenir le message « Plus de 320 produits au catalogue Saraproc », les références clients du site et le rendez-vous au Salon international de l’hygiène.

## Montage

Le plan comprend 216 séquences sur 1 871 secondes, soit 31 min 11 s : introduction avec le visuel Laboratoires Saraproc, vue d’ensemble, sept gammes, 86 cartons de sous-catégorie ou de famille, 118 pages de produits, références clients, salon et contact. Les fondus et l’apparition douce des titres et cartes accompagnent la lecture. Les photos de chapitre sont affichées entières et fixes pour préserver leurs compositions et leurs logos intégrés.

Le parcours est catégorie → sous-catégorie → produits. Les sous-niveaux sont indiqués par leur chemin. Les références classées à la fois dans un parent et dans son enfant ne sont pas répétées pour cette seule raison ; celles qui appartiennent à deux branches indépendantes sont montrées dans chacune. Le fichier `output/catalogue-hierarchique/hierarchy.json` conserve les preuves de chaque rattachement, y compris les familles supplémentaires issues des PDF.

Les 503 mentions de l’index précédent, soit 493 noms normalisés distincts, sont conservées. Le classement par sous-catégorie donne 509 apparitions, et non 509 produits distincts. Les 65 nœuds du site compris dans le périmètre et 21 familles PDF forment les 86 sections. Les deux rubriques de parfums sans produit individuel nommé sont présentées sans inventer de référence. Chaque page contient six noms au maximum pendant au moins 12 secondes. Les photos officielles disponibles sont utilisées ; aucune photographie de conditionnement n’est fabriquée pour les noms sans image documentée.

## Identité et visuels fournis

Les neuf JPG de `assets/user/` sont des copies identiques aux pièces jointes. Le manifeste documente leur taille et SHA-256. Le logo complet comprend « Import - Export / Fabricant & Négociant ». Il est proportionnellement ajusté sur son fond blanc, sans recadrage, déformation, recoloration ou redessin. Les huit autres images fournissent l’introduction et les sept bannières de gamme ; leurs logos intégrés restent visibles.

Le visuel fourni pour les eaux contient une piscine ; il est conservé entier. Les sept références uniquement destinées aux piscines demeurent exclues de la liste des eaux industrielles, comme dans le film précédent. La nutrition végétale, les fertilisants et les compléments alimentaires animaux restent hors périmètre. Les produits d’hygiène des bâtiments d’élevage et de traite classés dans l’hygiène professionnelle restent inclus.

Les sept logos de clients proviennent toujours de la rubrique « Ils nous font confiance » de saraprocmaroc.com et de ses fichiers documentés dans `assets/site/brand-client-sources.json`. Ils ne sont pas remplacés par des logos redessinés.

## Son et livrables

La musique est une composition originale d’ambiance de 40 secondes, prolongée par boucle continue sous le film complet, avec fondu au début et à la fin. Elle comporte des nappes douces et des notes espacées, sans batterie ni échantillon tiers. Il n’y a pas de voix off. Le fichier et sa provenance sont décrits dans `assets/ambient-music-notes.md`.

Les livrables sont dans `output/catalogue-hierarchique/` : MP4 musical et silencieux, ZIP avec le MP4 musical, CSV des produits par sous-catégorie, chapitres et storyboard. Les deux anciens films restent conservés dans leurs dossiers respectifs. Le validateur vérifie les noms et appartenances, les caractères et dimensions des cartes, les originaux joints, le signal audio, le décodage intégral des deux MP4 et les empreintes de chaque membre du ZIP.
