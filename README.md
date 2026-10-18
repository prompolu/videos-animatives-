# Saraproc Maroc — animation de présentation

Première version d’un film de 60 secondes en français pour une présentation d’entreprise et une diffusion au Salon international de l’hygiène. Le périmètre est exclusivement l’hygiène, avec une mise en avant de l’hygiène médicale et cosmétique.

## Livrables

- `output/saraproc-maroc-60s-musique.mp4` : Full HD 1920 × 1080, 16:9, 30 images/s, H.264, musique instrumentale originale en AAC stéréo. **Sans voix off.**
- `output/saraproc-maroc-60s-sans-son.mp4` : même film, sans piste audio, pour un écran de salon. Le fondu final rejoint le début afin de permettre la lecture en boucle.
- `output/storyboard-saraproc.jpg` : vue d’ensemble des sept séquences.
- `output/affiche-saraproc.jpg` : image de présentation.
- `creative/brief-fr.md` : scénario, textes et notes de production.
- `creative/narration-fr.txt` : proposition de narration facultative, non enregistrée.
- `output/timeline.json` : durée, format et repères des séquences.
- `assets/saraproc-original-60s.wav` et `assets/music-notes.md` : musique et provenance.

Les messages principaux sont intégrés à l’image : la vidéo se comprend sans le son. Les deux fichiers MP4 sont optimisés pour une lecture progressive avec `faststart`.

## Reproduire et modifier

Prérequis : Python 3.12, FFmpeg avec `libx264` et AAC, polices système Open Sans et Nimbus Sans. Pillow et NumPy sont déjà disponibles dans l’environnement utilisé pour ce rendu ; leurs versions sont consignées dans `requirements.txt`.

Depuis le checkout existant `/workspace/videos-animatives-` :

```bash
python3 tools/compose_music.py
python3 tools/render_video.py --stills
python3 tools/render_video.py
```

Le premier script synthétise la musique sans échantillon externe. Le second produit les images de contrôle. Le troisième exporte la vidéo silencieuse, puis y associe la musique lorsque le WAV est présent. Aucun serveur n’est nécessaire.

Pour un autre environnement, installer les dépendances dans un environnement virtuel avant ces commandes :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/compose_music.py
.venv/bin/python tools/render_video.py
```

Les textes, couleurs, dessins et temps d’apparition sont modifiables dans `tools/render_video.py`. Les fonctions du fichier dessinent les contenants et animent les éléments ; aucun service externe de génération n’est nécessaire. Réutiliser le checkout existant dans les tâches cloud ; aucun worktree supplémentaire n’est nécessaire.

## État de l’identité et des informations

L’identité bleu nuit/turquoise, le nom composé en typographie et les contenants dessinés sont provisoires. Ils ne constituent ni le logo officiel, ni une reproduction du catalogue. Le site `https://www.saraprocmaroc.com/` a été fourni par le client, mais sa consultation est bloquée par le proxy réseau dans l’environnement actuel. Les deux domaines correspondants ont été ajoutés au brouillon de configuration réseau ; cette sauvegarde ne les rend pas accessibles dans le processus actuel.

La phrase sur la confiance des grandes entreprises au Maroc reprend le brief utilisateur. Aucun nom ni logo client, certification, résultat médical ou référence commerciale n’a été inventé. Les références commerciales et les éléments officiels de marque sont à confirmer pour la version de diffusion. Aucun produit agricole n’est représenté.

Pour une version destinée au site après le salon, adapter le carton de rencontre dans la sixième séquence, puis relancer le rendu.

## Vérification des exports

Les deux fichiers doivent annoncer exactement 60 secondes et 1 800 images en 1920 × 1080 à 30 images/s. La version musicale contient une piste AAC stéréo 48 kHz ; la version silencieuse ne contient pas de piste audio.

```bash
ffprobe -v error -count_frames -show_streams -show_format output/saraproc-maroc-60s-musique.mp4
ffmpeg -v error -i output/saraproc-maroc-60s-musique.mp4 -f null -
ffmpeg -v error -i output/saraproc-maroc-60s-sans-son.mp4 -f null -
```

Le rapport du contrôle courant est enregistré dans `output/validation.json`.
