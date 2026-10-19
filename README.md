# Saraproc Maroc — catalogue animé par catégorie et sous-catégorie

La nouvelle version est dans **[`output/catalogue-hierarchique/`](output/catalogue-hierarchique/)** : **31 min 11 s**, en français, Full HD, avec musique d’ambiance originale et sans voix off. Elle suit le parcours **catégorie → sous-catégorie → produits**, avec les neuf visuels fournis par l’utilisateur. Le logo complet est affiché dans ses couleurs et proportions d’origine, sans recadrage ni retouche.

- [Télécharger la vidéo avec musique](output/catalogue-hierarchique/saraproc-maroc-categories-sous-categories-musique.mp4).
- [Télécharger le ZIP](output/catalogue-hierarchique/Saraproc-Maroc-categories-sous-categories.zip) : vidéo musicale, liste des produits par sous-catégorie, chapitres et storyboard.
- [Voir le storyboard](output/catalogue-hierarchique/storyboard.jpg) et [les chapitres](output/catalogue-hierarchique/chapitres.csv).
- [Version sans son](output/catalogue-hierarchique/saraproc-maroc-categories-sous-categories-sans-son.mp4).

Le montage présente **7 catégories et 86 sections**, dont 65 sous-catégories ou sous-niveaux du site et 21 familles supplémentaires des PDF officiels. Les 503 mentions du relevé précédent sont conservées ; leurs appartenances à plusieurs sous-catégories produisent 509 apparitions. Ces chiffres ne désignent pas un nombre de SKU vérifiés. L’annonce « Plus de 320 produits au catalogue Saraproc » est conservée.

Chaque sous-catégorie dispose d’un carton, puis de pages de six produits au maximum, lisibles pendant au moins 12 secondes. Les photographies officielles disponibles accompagnent les noms. Les matières sans photo documentée gardent une présentation typographique. Deux rubriques de parfums sont nommées sans inventer de références absentes des sources. Les bannières fournies sont montrées en entier ; la présence d’une piscine dans le visuel fourni pour les eaux ne modifie pas la sélection de produits industriels.

Les originaux et leurs empreintes sont dans [assets/user/manifest.json](assets/user/manifest.json). La hiérarchie et les preuves de rattachement sont dans [hierarchy.json](output/catalogue-hierarchique/hierarchy.json). La nouvelle musique douce, sans batterie ni échantillon tiers, est documentée dans [assets/ambient-music-notes.md](assets/ambient-music-notes.md).

| Début | Catégorie |
| --- | --- |
| 00:19 | Hygiène professionnelle et institutionnelle |
| 07:46 | Hygiène en milieu hospitalier |
| 11:17 | Hygiène professionnelle écologique |
| 11:56 | Matières premières cosmétiques |
| 22:24 | Produits chimiques pour les industries |
| 28:43 | Traitement des eaux industrielles |
| 30:07 | Lavage et entretien des véhicules |

Pour reproduire cette version depuis la racine du dépôt, avec les prérequis décrits ci-dessous :

```bash
python3 tools/prepare_hierarchy.py
python3 tools/compose_ambient_loop.py
python3 tools/render_hierarchical_video.py --stills
python3 tools/render_hierarchical_video.py
python3 tools/validate_hierarchical_video.py
```

Le [brief de cette régénération](creative/brief-hierarchique-fr.md) décrit les choix de présentation. Le rapport [validation.json](output/catalogue-hierarchique/validation.json) contrôle la couverture des noms, les neuf fichiers originaux, la lisibilité, le décodage intégral des MP4 et le contenu exact du ZIP.

**Validation réussie :** les deux MP4 ont été décodés entièrement, avec chacun 56 130 images sur 1 871 secondes. Les 509 cartes conservent les noms exacts, avec une taille minimale mesurée de 31 pixels. Les neuf JPG sont identiques aux pièces jointes et les quatre fichiers du ZIP correspondent aux exports courants.

## Version précédente : catalogue des sept gammes, 19 min 19 s

La version longue présente les noms des produits et matières des **sept gammes demandées**, d’après les pages et catalogues PDF officiels de Saraproc Maroc. Le film exporté et validé dure **19 min 19 s** en Full HD, en français, avec une version musicale et une version silencieuse, **sans voix off**. Les noms sont répartis sur des écrans de six références au maximum, pendant au moins 12 secondes par écran.

Le relevé figé compte **503 mentions réparties entre les sept gammes et 493 noms distincts après normalisation**. Certains noms figurent dans plusieurs gammes ; les libellés et variantes de codes des sources sont conservés. Ces nombres décrivent le relevé et ne constituent pas un décompte de références commerciales uniques ou de SKU vérifiés. Le message « Plus de 320 produits au catalogue Saraproc » reste une information fournie par l’utilisateur sur le catalogue de l’entreprise.

## Version longue : fichiers

Les fichiers suivants sont disponibles dans `output/catalogue/` :

- `saraproc-maroc-catalogue-complet-musique.mp4` : 1920 × 1080, 16:9, 30 images/s, H.264, instrumental original en AAC stéréo, sans voix off.
- `saraproc-maroc-catalogue-complet-sans-son.mp4` : même film sans piste audio.
- `Saraproc-Maroc-catalogue-complet.zip` : les deux MP4 et le relevé `catalogue-complet-fr.csv`.
- `catalogue-complet-fr.csv` et `catalogue-complet-fr.md` : tous les noms retenus avec leur gamme, origine et sources ; le CSV conserve aussi les sous-familles et pages PDF lorsqu’elles sont renseignées.
- `chapitres.csv` : repères des sept gammes.
- `storyboard-catalogue.jpg` : aperçu des séquences principales.
- `catalogue-index.json` : données figées utilisées pour composer le film.
- `timeline-catalogue.json` : chronologie finale des 100 séquences ; `timeline-catalogue-plan.json` conserve le plan de montage.
- [validation-catalogue.json](output/catalogue/validation-catalogue.json) : rapport de validation complète, statut `passed`.

Le scénario et les règles de présentation sont documentés dans [creative/brief-catalogue-fr.md](creative/brief-catalogue-fr.md).

## Chapitres de la version longue

Les repères ci-dessous proviennent de `output/catalogue/chapitres.csv` et de la chronologie finale.

| Début | Gamme | Mentions dans le relevé |
| --- | --- | --- |
| 00:18 | Hygiène professionnelle et institutionnelle | 117 |
| 04:23 | Hygiène en milieu hospitalier | 46 |
| 06:07 | Hygiène professionnelle écologique | 9 |
| 06:36 | Matières premières cosmétiques | 189 |
| 13:20 | Produits chimiques pour les industries | 115 |
| 17:27 | Traitement des eaux industrielles | 19 |
| 18:21 | Lavage et entretien des véhicules | 8 |

Les références clients apparaissent à 18:51, le carton salon à 19:01 et la carte finale à 19:09. La durée vérifiée est de 1 159 secondes, soit 34 770 images à 30 images/s, pour 100 séquences.

## Reproduire la version longue

Prérequis : Python 3.12, FFmpeg avec `libx264` et AAC, polices système Open Sans et Nimbus Sans. Pillow et NumPy sont consignés dans `requirements.txt`. Les manifestes, PDF et images officiels sont conservés dans `assets/site/` ; la préparation et le rendu utilisent ces fichiers locaux.

Depuis le checkout existant `/workspace/videos-animatives-` :

```bash
python3 tools/prepare_catalogue.py
python3 tools/compose_catalogue_loop.py
python3 tools/render_catalogue.py --stills
python3 tools/render_catalogue.py
python3 tools/validate_catalogue.py
```

`prepare_catalogue.py` reconstruit l’index et les listes CSV/Markdown à partir des sept manifestes. `compose_catalogue_loop.py` crée la boucle instrumentale originale. `--stills` produit les aperçus, le plan et les chapitres ; le rendu complet exporte le film, sa version musicale et l’archive ZIP. La dernière commande valide l’ensemble et écrit `output/catalogue/validation-catalogue.json`. Aucun serveur ou service de génération externe n’est nécessaire.

Pour un autre environnement, installer d’abord les dépendances :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/prepare_catalogue.py
.venv/bin/python tools/compose_catalogue_loop.py
.venv/bin/python tools/render_catalogue.py --stills
.venv/bin/python tools/render_catalogue.py
.venv/bin/python tools/validate_catalogue.py
```

Les règles de collecte et de regroupement sont dans `tools/prepare_catalogue.py`. Les pages, durées, textes et animations de la version longue sont dans `tools/render_catalogue.py`. Réutiliser le checkout existant dans les tâches cloud ; aucun worktree supplémentaire n’est nécessaire.

## Sources, identité et périmètre

Les sept manifestes `assets/site/catalog/*.json` relient les noms aux pages ou catalogues officiels de `https://www.saraprocmaroc.com/`. Les PDF conservés dans ce répertoire complètent les fiches web. Les origines « fiche officielle », « catalogue officiel » et « exemple cité » sont documentées dans l’index et les listes annexes. À l’écran, les cartes affichent la sous-famille du produit, ou « Solutions professionnelles » si elle est absente ; les trois huiles nommées comme exemples portent « Huile citée sur le site ». Le film affiche les photographies officielles disponibles ; les noms sans photographie documentée restent présentés sous forme typographique, sans image de produit inventée.

Les sept gammes couvrent l’hygiène professionnelle et institutionnelle, l’hygiène hospitalière, l’hygiène professionnelle écologique, les matières premières cosmétiques, les produits chimiques pour les industries, le traitement des eaux industrielles et le lavage/entretien des véhicules. La nutrition végétale, les fertilisants et compléments alimentaires animaux restent hors périmètre. Sept références classées uniquement pour piscine sont écartées du chapitre des eaux industrielles et consignées dans `catalogue-index.json`. L’hygiène des bâtiments d’élevage demeure incluse lorsqu’elle appartient à la gamme professionnelle du site.

Les logos officiels couleur et blanc proviennent de l’en-tête et du pied de page du site. Le bleu `#26547F`, le bleu grisé `#7D90B3` et le blanc sont relevés dans le site et le logo. Le manifeste `assets/site/brand-client-sources.json` documente aussi les sept logos affichés dans la section « Ils nous font confiance » : Centrale Danone, Chergui, Les Domaines Agricoles, SIOF, ALF AL MAGHRIB, ALF SAHEL et Valencia. Les relations commerciales sont celles présentées sur le site, sans vérification indépendante ni déduction sur les produits fournis à chaque entreprise.

Les noms de gammes et produits reprennent les sources ; ils n’ajoutent pas de certification, résultat médical ou garantie environnementale. Les bases et matières premières cosmétiques sont présentées pour ce qu’elles sont, sans être transformées en cosmétiques finis. Les URL, images et éléments de provenance sont conservés dans les manifestes.

La musique longue utilise `assets/saraproc-catalogue-loop-20s.wav`, une boucle originale de 20 secondes synthétisée pour ce projet, répétée sans interruption avec un fondu au début et à la fin du film complet. Aucun enregistrement, échantillon ou boucle tiers n’est utilisé. Sa fabrication est documentée dans `assets/catalogue-music-notes.md`. Aucune voix n’a été enregistrée.

## Vérifier la version longue

La validation complète a réussi : les deux MP4 ont été décodés intégralement, avec 34 770 images sur 1 159 secondes en 1920 × 1080 à 30 images/s. La version musicale contient une piste AAC stéréo 48 kHz ; la version silencieuse ne contient aucune piste audio. Le rapport [output/catalogue/validation-catalogue.json](output/catalogue/validation-catalogue.json) confirme aussi les 503 noms requis, leurs limites de rendu, les 131 fichiers sources officiels inchangés et la concordance du ZIP avec les deux MP4 et le CSV courants. Les noms de produits ont une taille minimale mesurée de 31 pixels dans ce rendu ; les libellés secondaires sont plus petits.

Pour reproduire ce contrôle :

```bash
python3 tools/validate_catalogue.py
```

Les commandes suivantes permettent également une inspection directe :

```bash
ffprobe -v error -count_frames -show_streams -show_format output/catalogue/saraproc-maroc-catalogue-complet-musique.mp4
ffmpeg -xerror -v error -i output/catalogue/saraproc-maroc-catalogue-complet-musique.mp4 -f null -
ffmpeg -xerror -v error -i output/catalogue/saraproc-maroc-catalogue-complet-sans-son.mp4 -f null -
```

Le script contrôle la couverture exacte des identifiants et noms dans la chronologie, les caractères après retour à la ligne, les dimensions réelles du texte dans chaque carte, les chapitres et les empreintes SHA-256 des sources et livrables.

## Version courte de 60 secondes conservée

La version courte est un film distinct, limité à une sélection **d’hygiène médicale et de bases cosmétiques**. Elle est conservée et **ne représente pas le brief élargi aux sept gammes**.

- `output/saraproc-maroc-60s-musique.mp4` et `output/saraproc-maroc-60s-sans-son.mp4` : 60 secondes, Full HD, 30 images/s, sans voix off.
- `output/Saraproc-Maroc-videos.zip` : ces deux MP4.
- `output/storyboard-saraproc.jpg`, `output/affiche-saraproc.jpg` et `output/timeline.json` : aperçu et montage du film court.
- `creative/brief-fr.md` et `creative/narration-fr.txt` : scénario et narration facultative du film court, non enregistrée.
- `assets/saraproc-original-60s.wav`, `assets/music-notes.md` et `assets/site/products/product-sources.json` : musique et sélection de photographies de cette version.

Pour reproduire et vérifier uniquement ce film court :

```bash
python3 tools/compose_music.py
python3 tools/render_video.py --stills
python3 tools/render_video.py
python3 tools/validate_outputs.py
```

Le dernier script contrôle les deux exports courts par décodage intégral, leur format, leur durée de 60 secondes et leurs 1 800 images, le ZIP et les empreintes des 17 images officielles de cette sélection. Son rapport reste `output/validation.json` ; il ne valide pas les exports longs du catalogue.
