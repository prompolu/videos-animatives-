# Saraproc Maroc — film d’animation corporate

## Intention

Présenter Saraproc Maroc comme un fournisseur de produits d’hygiène pour les professionnels, en mettant particulièrement en avant l’hygiène médicale et l’hygiène cosmétique, et un interlocuteur de confiance pour les entreprises au Maroc. Le film doit rester clair et lisible sans le son, pour une diffusion sur un stand au Salon international de l’hygiène, sur le site web et en présentation d’entreprise.

- Durée : environ 60 secondes.
- Format principal : 16:9, Full HD, 1 920 × 1 080 pixels.
- Langue : français.
- Style : animation graphique sobre, typographie large, illustrations de produits génériques, mouvements fluides.
- Direction visuelle provisoire : bleu nuit, turquoise et blanc cassé. Ce choix ne constitue pas une charte officielle.
- Une idée principale par scène. Les textes à l’écran portent le message même sans narration.

## Texte à l’écran et déroulé réalisé

Les séquences et repères ci-dessous correspondent à `SCENES` et aux textes du moteur de rendu `tools/render_video.py`. Les sauts de ligne du film sont regroupés ici pour faciliter la lecture.

| Temps | Séquence | Texte principal et complément à l’écran | Traitement visuel |
| --- | --- | --- | --- |
| 00–07 s | L’hygiène inspire la confiance | **L’hygiène inspire la confiance.** · Des produits pour les professionnels du médical et de la cosmétique. | Fond bleu nuit, bandeau « L’HYGIÈNE PROFESSIONNELLE » et produits génériques. |
| 07–15 s | Des produits pour les professionnels | **Des produits d’hygiène pour les professionnels.** · Deux univers. Une même attention à l’hygiène. | Fond clair, bandeau « SARAPROC MAROC », flacons-pompes et contenants illustrés. |
| 15–24 s | Hygiène médicale | **L’hygiène médicale.** · Des produits pour les besoins des professionnels du secteur médical. | Bandeau « UNIVERS MÉDICAL » et mise en avant de flacons-pompes génériques. Aucune promesse d’efficacité médicale ni marquage de certification. |
| 24–33 s | Hygiène cosmétique | **L’hygiène cosmétique.** · Des produits pour les besoins des professionnels de la cosmétique. | Bandeau « UNIVERS COSMÉTIQUE », flacons-pompes et pots cosmétiques génériques. |
| 33–43 s | La confiance des entreprises | **La confiance des grandes entreprises au Maroc.** · Saraproc Maroc, aux côtés des professionnels. | Fond bleu nuit, bandeau « UNE RELATION DE CONFIANCE » et réseau graphique, sans logo client ni marque tierce. |
| 43–51 s | Rencontrons-nous au salon | **Parlons de vos besoins.** · Retrouvons-nous au Salon international de l’hygiène. | Fond clair, bandeau « À VOTRE RENCONTRE » et produits illustrés, sans date ni numéro de stand inventé. |
| 51–60 s | Saraproc Maroc · Contact | **SARAPROC MAROC** · L’hygiène médicale et cosmétique au service des professionnels. · **saraprocmaroc.com** · ÉCHANGEONS SUR VOS BESOINS | Carte finale sur fond bleu nuit, adresse du site dans une pastille claire et animation discrète. |

## Narration facultative

Le texte intégral est fourni dans `narration-fr.txt` pour une éventuelle production vocale ultérieure. Aucune voix n’a été enregistrée et aucune voix off n’est incluse dans les exports. Le film est livré en version avec musique instrumentale et en version silencieuse. Les informations essentielles restent à l’écran.

La version musicale utilise l’instrumental original de 60 secondes `assets/saraproc-original-60s.wav`, composé pour ce projet avec `tools/compose_music.py`. Les nappes, notes pincées, basses et percussions douces sont synthétisées mathématiquement ; aucun enregistrement, boucle ou échantillon tiers n’est utilisé. La provenance, les caractéristiques audio et la procédure de reproduction sont documentées dans [assets/music-notes.md](../assets/music-notes.md).

## Éléments de marque et vérifications avant diffusion externe

- Le nom « Saraproc Maroc », la vente de produits d’hygiène, les catégories « hygiène médicale » et « hygiène cosmétique » et la présence au salon proviennent du brief utilisateur.
- Exclure entièrement les produits et substances chimiques agricoles, les pesticides, les engrais et toute illustration évoquant ces produits. Le périmètre demandé est exclusivement celui des produits d’hygiène, en particulier médicale et cosmétique.
- L’adresse `https://www.saraprocmaroc.com/` a été fournie par l’utilisateur. Son contenu n’a pas pu être récupéré : la requête a été bloquée par le proxy réseau avec une réponse HTTP 403. Aucune information de catalogue, aucun logo et aucune référence client n’en ont été déduits.
- La référence à la confiance de grandes entreprises au Maroc reprend l’affirmation fournie par l’utilisateur. Confirmer les références commerciales qui la justifient avant diffusion ; n’ajouter aucun nom ou logo client sans autorisation et sans validation des éléments fournis.
- Le nom est composé en typographie dans la version provisoire. Aucun logo officiel n’a été fourni.
- Les flacons-pompes d’hygiène médicale, flacons et pots cosmétiques illustrés sont génériques et sans marque : ils ne représentent pas une gamme, un conditionnement ou une performance attestés du catalogue Saraproc Maroc.
- Ne pas ajouter de certification, chiffre, promesse de désinfection, allégation sanitaire, origine de fabrication ou liste de clients non fournis.
- Remplacer la palette provisoire, les illustrations et la carte finale par les éléments officiels si disponibles : logo, catalogue, coordonnées, site web et éventuel numéro de stand.
- Le carton salon peut devenir « Découvrez nos produits d’hygiène » pour une variante pérenne destinée au site web après l’événement.

## Contrôle de livraison

Vérifier une durée de 60 secondes, le format 16:9, la lisibilité des accents, l’absence de texte tronqué, les marges de sécurité, la continuité des transitions et une carte finale stable. Contrôler la compréhension du message lors d’une lecture sans son. Toute présence d’une voix ou d’une musique doit être explicitement indiquée dans la livraison.
