# Saraproc Maroc — film catalogue des sept gammes

## Objectif et format

Présenter en français toutes les mentions de produits et matières retenues dans les sept gammes demandées, à partir du site et des catalogues PDF officiels de Saraproc Maroc. Le spectateur doit pouvoir lire les noms, identifier les familles et retrouver l’offre sur `saraprocmaroc.com`.

Le film exporté et validé comprend **100 séquences sur 19 min 19 s**, en 1920 × 1080, 16:9, 30 images/s. Il est disponible avec instrumental et en version silencieuse, sans voix off. Le logo officiel, les couleurs bleu/blanc du site et les photographies officielles disponibles composent une présentation sobre. Les produits ou matières sans photographie documentée apparaissent avec leur nom complet et leur sous-famille lorsqu’elle est renseignée, sans photographie inventée.

## Relevé et signification des nombres

L’index `output/catalogue/catalogue-index.json` contient **503 mentions réparties entre les sept gammes**, correspondant à **493 noms distincts après normalisation**. Une référence peut apparaître dans plusieurs gammes ; les libellés, matières citées et variantes de codes des sources sont conservés. Ces nombres décrivent la couverture du relevé. Ils ne constituent ni un décompte vérifié de SKU, ni une preuve que tous les noms correspondent à des produits commerciaux distincts actuellement disponibles.

L’annonce « Plus de 320 produits au catalogue Saraproc » est fournie par l’utilisateur et porte sur le catalogue de l’entreprise. Elle reste séparée des statistiques de collecte. Les 503 mentions ne remplacent pas cette information par une nouvelle promesse commerciale de « 503 produits ».

Le relevé figé distingue 167 entrées issues de fiches officielles, 333 mentions issues des catalogues officiels et trois matières nommées comme exemples sur le site. Les trois types sont identifiés dans l’index et les listes annexes. À l’écran, les cartes affichent la sous-famille ou « Solutions professionnelles » si elle est absente ; les trois huiles données comme exemples sont accompagnées de « Huile citée sur le site ». Les variantes de codes et les noms issus des PDF sont conservés sans les déclarer indépendamment validés comme SKU.

## Lecture des noms

- Six cartes au maximum par écran, sur deux rangées de trois ; le dernier écran de chaque gamme peut en comporter moins.
- Au moins 12 secondes par écran de produits. Les écrans chargés en mots durent davantage : 12 à 18 secondes dans le film exporté.
- Tous les noms retenus sont présents dans `on_screen_names`, avec leurs identifiants dans la chronologie ; le total correspond aux 503 mentions réparties entre les sept gammes.
- Les noms restent lisibles et complets. La mise en page ajuste la taille et les retours à la ligne ; elle ne remplace pas les noms longs par une simple catégorie.
- Une photographie officielle accompagne le nom lorsqu’une image adaptée est documentée. Une carte sans photographie conserve une présentation typographique claire.
- La gamme et le numéro d’écran restent visibles. Les listes CSV/Markdown et leurs liens permettent une lecture détaillée hors vidéo.

## Déroulé et chapitres

Les repères proviennent de `output/catalogue/chapitres.csv` et de `output/catalogue/timeline-catalogue.json`. Les intervalles incluent le carton de chapitre de cinq secondes suivi des pages de noms.

| Intervalle | Gamme | Mentions | Écrans de noms |
| --- | --- | --- | --- |
| 00:18–04:23 | Hygiène professionnelle et institutionnelle | 117 | 20 |
| 04:23–06:07 | Hygiène en milieu hospitalier | 46 | 8 |
| 06:07–06:36 | Hygiène professionnelle écologique | 9 | 2 |
| 06:36–13:20 | Matières premières cosmétiques | 189 | 32 |
| 13:20–17:27 | Produits chimiques pour les industries | 115 | 20 |
| 17:27–18:21 | Traitement des eaux industrielles | 19 | 4 |
| 18:21–18:51 | Lavage et entretien des véhicules | 8 | 2 |

- **00:00–00:09 — Introduction :** « L’expertise au service des professionnels. » ; hygiène, cosmétique, industrie, eaux industrielles et entretien des véhicules.
- **00:09–00:18 — Vue d’ensemble :** « Plus de 320 produits au catalogue Saraproc. » et les sept gammes.
- **18:51–19:01 — Confiance :** « Ils nous font confiance. » ; « Les références présentées sur le site Saraproc Maroc. » et les sept logos provenant de cette section du site.
- **19:01–19:09 — Salon :** « Parlons de vos besoins. » ; « Retrouvons-nous au Salon international de l’hygiène. » Aucun numéro de stand ni calendrier inventé.
- **19:09–19:19 — Contact :** logo officiel blanc, « Des solutions professionnelles pour vos activités. », `saraprocmaroc.com` et « ÉCHANGEONS SUR VOS BESOINS ».

La chronologie finale est conservée dans `output/catalogue/timeline-catalogue.json`. Les chiffres et repères ci-dessus correspondent aux deux MP4 vérifiés.

## Sources et limites du périmètre

Les sept manifestes de `assets/site/catalog/` relient chaque mention aux catégories, fiches, exemples nommés ou catalogues PDF de `https://www.saraprocmaroc.com/`. Les URL et pages PDF renseignées sont reprises dans `catalogue-complet-fr.csv`. Les PDF officiels sont conservés avec les manifestes. La liste complète lisible est disponible dans `output/catalogue/catalogue-complet-fr.md` ; elle ne doit pas être remplacée par une liste abrégée de produits représentatifs.

Les sept familles sont celles du tableau, avec les intitulés de la chronologie finale. « Hygiène professionnelle écologique » est le nom de la gamme du site ; cette appellation n’ajoute pas de certification environnementale. Les matières premières et bases cosmétiques gardent leur nature de matières ou bases de formulation. Les produits industriels et de traitement des eaux restent dans leurs chapitres respectifs, sans confusion avec les gammes d’hygiène médicale.

La nutrition végétale, les fertilisants et les compléments alimentaires animaux ne sont pas inclus. Les sept références présentées uniquement pour piscine sont explicitement écartées des eaux industrielles dans `catalogue-index.json`. Les produits d’hygiène des bâtiments d’élevage classés dans la gamme professionnelle restent inclus ; leur présence ne réintroduit pas une gamme de nutrition ou de fertilisation agricole.

Le logo officiel et les sept logos de Centrale Danone, Chergui, Les Domaines Agricoles, SIOF, ALF AL MAGHRIB, ALF SAHEL et Valencia proviennent des éléments documentés dans `assets/site/brand-client-sources.json`. Les relations commerciales sont celles affichées dans la section « Ils nous font confiance » du site, sans vérification indépendante ni déduction sur les produits fournis à chaque entreprise. Aucune certification, efficacité médicale chiffrée ou autre promesse absente des sources n’est ajoutée.

## Son

Aucune voix n’a été enregistrée. Tous les noms et messages sont lisibles à l’écran. La version musicale répète `assets/saraproc-catalogue-loop-20s.wav`, instrumental original de 20 secondes synthétisé par `tools/compose_catalogue_loop.py`, avec un fondu uniquement au début et à la fin du film complet. Aucun enregistrement, boucle ou échantillon tiers n’est utilisé. Voir [assets/catalogue-music-notes.md](../assets/catalogue-music-notes.md).

## Livrables et contrôle

Les fichiers disponibles dans `output/catalogue/` comprennent deux MP4 nommés `saraproc-maroc-catalogue-complet-musique.mp4` et `saraproc-maroc-catalogue-complet-sans-son.mp4`, l’archive `Saraproc-Maroc-catalogue-complet.zip` contenant ces MP4 et le CSV, `storyboard-catalogue.jpg` et la chronologie finale. Les listes `catalogue-complet-fr.csv` et `.md`, l’index et les chapitres complètent la livraison.

La validation complète a réussi : les deux MP4 ont été décodés intégralement et comptent chacun 34 770 images sur 1 159 secondes en Full HD à 30 images/s. La version musicale contient une piste AAC stéréo 48 kHz ; la version silencieuse ne contient aucune piste audio. Les 503 noms requis sont présents et leur texte complet tient dans les limites des cartes, avec une taille minimale mesurée de 31 pixels pour les noms. Les libellés secondaires utilisent des tailles plus petites. Les 131 fichiers sources officiels vérifiés sont inchangés et le ZIP correspond aux deux MP4 et au CSV courants.

Depuis la racine du dépôt, reproduire le contrôle avec :

```bash
python3 tools/validate_catalogue.py
```

Le rapport [output/catalogue/validation-catalogue.json](../output/catalogue/validation-catalogue.json), au statut `passed`, contient la couverture des noms, les limites de rendu, les caractéristiques des MP4, les empreintes des sources et la vérification de l’archive.

Le film court de 60 secondes et son brief restent conservés comme une présentation distincte limitée à l’hygiène médicale et aux bases cosmétiques. Ils ne représentent pas le périmètre des sept gammes de cette version longue.
