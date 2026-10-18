# Saraproc Maroc — animation de présentation

Film de 60 secondes en français pour une présentation d’entreprise et une diffusion au Salon international de l’hygiène. Cette version intègre le logo officiel, des photographies du catalogue et les sept logos de la section « Ils nous font confiance » du site Saraproc Maroc. Elle annonce « Plus de 320 produits au catalogue Saraproc », puis présente une sélection en hygiène médicale et en bases cosmétiques. Aucun produit chimique agricole n’est présenté.

## Livrables

- `output/saraproc-maroc-60s-musique.mp4` : Full HD 1920 × 1080, 16:9, 30 images/s, H.264, musique instrumentale originale en AAC stéréo. **Sans voix off.**
- `output/saraproc-maroc-60s-sans-son.mp4` : même film, sans piste audio, pour un écran de salon. Le fondu final rejoint le début afin de permettre la lecture en boucle.
- `output/Saraproc-Maroc-videos.zip` : archive des deux MP4 courants, recréée à chaque rendu complet.
- `output/storyboard-saraproc.jpg` : vue d’ensemble des sept séquences.
- `output/affiche-saraproc.jpg` : image de présentation.
- `creative/brief-fr.md` : scénario, textes, sources et notes de production.
- `creative/narration-fr.txt` : proposition de narration facultative, non enregistrée.
- `output/timeline.json` : durée, format et repères des séquences.
- `assets/saraproc-original-60s.wav` et `assets/music-notes.md` : musique et provenance.
- `assets/site/brand-client-sources.json` : provenance du logo officiel et des sept logos de références affichées sur le site.
- `assets/site/products/product-sources.json` : photographies officielles sélectionnées, catégories, liens et empreintes de contrôle.

Les messages principaux sont intégrés à l’image : la vidéo se comprend sans le son. Les deux fichiers MP4 sont optimisés pour une lecture progressive avec `faststart`.

## Reproduire et modifier

Prérequis : Python 3.12, FFmpeg avec `libx264` et AAC, polices système Open Sans et Nimbus Sans. Pillow et NumPy sont déjà disponibles dans l’environnement utilisé pour ce rendu ; leurs versions sont consignées dans `requirements.txt`.

Depuis le checkout existant `/workspace/videos-animatives-` :

```bash
python3 tools/compose_music.py
python3 tools/render_video.py --stills
python3 tools/render_video.py
python3 tools/validate_outputs.py
```

Le premier script synthétise la musique sans échantillon externe. Le second produit les images de contrôle. Le troisième exporte la vidéo silencieuse, puis y associe la musique lorsque le WAV est présent et recrée l’archive ZIP. La dernière commande valide les exports, l’archive et l’intégrité des images officielles. Les éléments visuels officiels téléchargés sont conservés dans `assets/site/` ; le rendu utilise ces fichiers locaux et ne nécessite pas de serveur.

Pour un autre environnement, installer les dépendances dans un environnement virtuel avant ces commandes :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/compose_music.py
.venv/bin/python tools/render_video.py
.venv/bin/python tools/validate_outputs.py
```

Les textes, couleurs, mises en page, placements des logos et photographies et temps d’apparition sont modifiables dans `tools/render_video.py`. Le script anime les éléments et compose les images à partir des fichiers locaux ; aucun service externe de génération n’est nécessaire. Réutiliser le checkout existant dans les tâches cloud ; aucun worktree supplémentaire n’est nécessaire.

## Identité, catalogue et références

Les logos couleur et blanc proviennent respectivement de l’en-tête et du pied de page de `https://www.saraprocmaroc.com/`. Les couleurs principales relevées sur le site et dans le logo sont le bleu `#26547F`, le bleu grisé `#7D90B3` et le blanc. Les photographies représentent des produits réellement présentés sur les pages sources consignées dans les manifestes.

Les 17 fichiers sources officiels restent inchangés. Le cadrage dans le film retire l’excès de fond vide autour de certaines photographies et du logo ALF AL MAGHRIB, tout en conservant les emballages complets, les étiquettes et les proportions.

Le chiffre « Plus de 320 produits » est fourni par l’utilisateur et porte sur le catalogue Saraproc dans son ensemble. Il ne décrit pas le nombre de références d’hygiène médicale ou cosmétique. Les photographies retenues concernent l’hygiène en milieu médical et des **bases de formulation cosmétique** pour savon, shampooing et crème ; ces bases ne sont pas présentées comme des cosmétiques finis destinés à la vente au détail.

Les sept logos de Centrale Danone, Chergui, Les Domaines Agricoles, SIOF, ALF AL MAGHRIB, ALF SAHEL et Valencia proviennent de la section « Ils nous font confiance » du site officiel. Leur présence et leur contexte sont documentés dans le manifeste. Les relations commerciales sont celles annoncées sur ce site, sans vérification indépendante ni déduction sur les produits fournis à chaque entreprise. Aucun produit agricole n’est représenté et aucune certification ou performance médicale n’est ajoutée.

Les pages et images officielles ont été récupérées avec vérification TLS ; les manifestes conservent leurs URL et empreintes SHA-256. La musique instrumentale est synthétisée pour ce projet, sans enregistrement, boucle ou échantillon tiers ; sa provenance est documentée dans `assets/music-notes.md`. Aucune voix n’a été enregistrée.

Pour une version destinée au site après le salon, adapter le carton de rencontre dans la sixième séquence, puis relancer le rendu.

## Vérification des exports

Les deux fichiers doivent annoncer exactement 60 secondes et 1 800 images en 1920 × 1080 à 30 images/s. La version musicale contient une piste AAC stéréo 48 kHz ; la version silencieuse ne contient pas de piste audio.

```bash
python3 tools/validate_outputs.py
```

Ce contrôle décode intégralement les deux vidéos, vérifie leurs caractéristiques, confirme que l’archive ZIP contient les MP4 courants et compare les 17 images officielles aux empreintes SHA-256 des manifestes.

Les commandes FFmpeg suivantes permettent aussi une inspection directe :

```bash
ffprobe -v error -count_frames -show_streams -show_format output/saraproc-maroc-60s-musique.mp4
ffmpeg -v error -i output/saraproc-maroc-60s-musique.mp4 -f null -
ffmpeg -v error -i output/saraproc-maroc-60s-sans-son.mp4 -f null -
```

Le rapport du contrôle courant est enregistré dans `output/validation.json`.
