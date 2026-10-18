# Saraproc Maroc — film d’animation corporate

## Intention

Présenter Saraproc Maroc comme un fournisseur de produits pour les professionnels. Le film annonce la largeur du catalogue Saraproc, puis se concentre sur l’hygiène médicale et les bases cosmétiques. Il doit rester clair et lisible sans le son pour le Salon international de l’hygiène, le site web et les présentations d’entreprise.

- Durée : 60 secondes.
- Format principal : 16:9, Full HD, 1 920 × 1 080 pixels, 30 images/s.
- Langue : français.
- Style : animation graphique sobre, typographie large, photographies de produits et logos provenant du site officiel.
- Identité : logo Saraproc officiel en couleur ou en blanc selon le fond ; couleurs relevées dans le site et le logo, notamment bleu `#26547F`, bleu grisé `#7D90B3` et blanc.
- Une idée principale par scène. Les textes à l’écran portent le message même sans narration.

## Texte à l’écran et déroulé de la version avec éléments officiels

Les repères restent ceux du film de 60 secondes. Le titre « Plus de 320 produits » porte sur le catalogue Saraproc dans son ensemble ; le film ne présente qu’une sélection médicale et cosmétique.

| Temps | Séquence | Texte principal et complément | Traitement visuel |
| --- | --- | --- | --- |
| 00–07 s | Présentation | **L’hygiène inspire la confiance.** · Des produits pour les professionnels du médical et de la cosmétique. | Logo Saraproc officiel et photographies de la sélection, composition épurée. |
| 07–15 s | Catalogue | **Plus de 320 produits au catalogue Saraproc.** · Focus : hygiène médicale et cosmétique. | Texte réparti sur quatre lignes : « Plus de », « 320 », « produits », « au catalogue Saraproc. ». Chiffre très lisible, logo officiel et photographies. Ne pas présenter le chiffre comme celui des seuls produits d’hygiène. |
| 15–24 s | Hygiène médicale | **L’hygiène médicale.** · Des produits pour les mains, les surfaces et les instruments. | Photographies officielles de produits classés « Hygiène en milieu médical » sur le site. Aucune performance médicale ou certification ajoutée. |
| 24–33 s | Bases cosmétiques | **L’univers cosmétique.** · Des bases pour savon, shampooing et crème. | Photographies officielles des bases BIOMA pour savon, shampooing et crème. Les présenter comme des bases de formulation, pas comme des cosmétiques finis destinés à la vente au détail. |
| 33–43 s | Références affichées sur le site | **Ils nous font confiance.** · Saraproc Maroc, aux côtés des professionnels. | Écran consacré aux sept logos de la section correspondante du site officiel, avec des dimensions permettant de les reconnaître. |
| 43–51 s | Rencontre au salon | **Parlons de vos besoins.** · Retrouvons-nous au Salon international de l’hygiène. | Logo officiel et produits sélectionnés, sans date ni numéro de stand inventé. |
| 51–60 s | Saraproc Maroc · Contact | L’hygiène médicale et cosmétique au service des professionnels. · **saraprocmaroc.com** · ÉCHANGEONS SUR VOS BESOINS | Logo officiel Saraproc blanc avec son aigle et carte finale stable, adresse du site très lisible. |

## Narration facultative et musique

Le texte intégral est fourni dans `narration-fr.txt` pour une éventuelle production vocale ultérieure. Aucune voix n’a été enregistrée et aucune voix off n’est incluse dans les exports. Le film est livré en version avec musique instrumentale et en version silencieuse. Les informations essentielles restent à l’écran.

La version musicale utilise l’instrumental original de 60 secondes `assets/saraproc-original-60s.wav`, composé pour ce projet avec `tools/compose_music.py`. Les nappes, notes pincées, basses et percussions douces sont synthétisées mathématiquement ; aucun enregistrement, boucle ou échantillon tiers n’est utilisé. La provenance, les caractéristiques audio et la procédure de reproduction sont documentées dans [assets/music-notes.md](../assets/music-notes.md).

## Sources et périmètre de la présentation

- **Catalogue :** « Plus de 320 produits » est une information fournie par l’utilisateur pour le catalogue Saraproc. Elle ne constitue pas un décompte indépendant et ne s’applique pas exclusivement à l’hygiène médicale ou cosmétique.
- **Site officiel :** `https://www.saraprocmaroc.com/`, fourni par l’utilisateur, a désormais pu être consulté. Les logos et photographies utilisés sont téléchargés depuis ce site avec vérification TLS. Les manifestes conservent les pages sources, URL des images, chemins locaux, dimensions et empreintes SHA-256.
- **Identité et références :** [assets/site/brand-client-sources.json](../assets/site/brand-client-sources.json) documente le logo couleur de l’en-tête, le logo blanc du pied de page et les sept logos affichés dans la section « Ils nous font confiance » : Centrale Danone, Chergui, Les Domaines Agricoles, SIOF, ALF AL MAGHRIB, ALF SAHEL et Valencia. Ces relations commerciales sont celles présentées par Saraproc sur son site ; elles n’ont pas été vérifiées indépendamment. Ne pas déduire quels produits ont été fournis à chacune de ces entreprises.
- **Produits :** [assets/site/products/product-sources.json](../assets/site/products/product-sources.json) documente cinq références classées en hygiène médicale et trois bases cosmétiques. Les pages et catégories du site étayent la sélection. Le film présente une sélection de ces photographies, sans prétendre montrer tout le catalogue.
- **Cadrage :** les 17 fichiers sources officiels sont conservés sans modification. Les fenêtres de cadrage du film retirent seulement l’excès de fond vide autour de certaines photographies et du logo ALF AL MAGHRIB, en conservant les emballages, les étiquettes et les proportions.
- **Bases cosmétiques :** BIOMA luxury soap (MELT & POUR), BIOMA luxury HAIR CARE Free sulfate et BIOMA luxury EC 90 (Full care/ make cream) sont respectivement présentées comme bases de savon, de shampooing et de crème, conformément aux fiches sources. Ne pas les transformer visuellement ou verbalement en produits de beauté finis.
- **Exclusion demandée :** aucun produit chimique agricole, pesticide ou engrais n’est présenté. Le secteur d’activité de certains clients affichés ne décrit pas les produits vendus dans cette sélection.
- **Allégations :** n’ajouter aucun chiffre de performance, résultat médical, certification, origine de fabrication ou détail commercial non fourni. Le nom des produits sur leurs photographies ne justifie pas d’ajouter de nouvelles promesses à l’écran.
- **Salon :** la présence au Salon international de l’hygiène provient du brief utilisateur. Aucun numéro de stand ni calendrier n’a été fourni.

Le carton salon peut devenir « Découvrez notre sélection » pour une variante pérenne destinée au site web après l’événement.

## Contrôle de livraison

Vérifier une durée de 60 secondes, le format 16:9, la lisibilité des accents et des logos, l’absence de texte tronqué, les marges de sécurité, la continuité des transitions et une carte finale stable. Contrôler la compréhension lors d’une lecture sans son. Vérifier que le chiffre 320 n’est jamais associé à un décompte exclusif de produits d’hygiène et que les bases cosmétiques sont identifiées comme telles. Toute présence d’une voix ou d’une musique doit être explicitement indiquée dans la livraison.

Depuis la racine du dépôt, `python3 tools/validate_outputs.py` contrôle les deux exports par décodage intégral, leur durée de 60 secondes et leurs 1 800 images, la concordance de l’archive `output/Saraproc-Maroc-videos.zip` avec les MP4 courants et les empreintes SHA-256 des 17 fichiers sources officiels. Le rapport est enregistré dans `output/validation.json`.
