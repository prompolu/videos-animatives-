# PROMPOLU — Infinity, film éditorial de 15 secondes

Versions verticale sonorisée et silencieuse : 1080 × 1920, 30 images/s, exactement 450 images, H.264/yuv420p et fast start. Le nom demandé `Prompolu_S140RP_Editorial_15s.mp4` est conservé pour le fichier ; le texte visible indique « STRUGAL Infinity », seul nom vérifiable dans la page visible fournie. Le code S140RP reste non vérifié.

## Reproduction

Prérequis : Python 3.12, FFmpeg avec libx264, polices DejaVu incluses dans assets/fonts avec leur licence. Sur Debian : paquet ffmpeg. Blender n'est pas nécessaire : composition 2,5D via Pillow.

Depuis le dossier du projet, utiliser le checkout existant sans créer de worktree :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python render.py --stills
.venv/bin/python render.py --preview
.venv/bin/python render.py
.venv/bin/python validate.py
```

Les chemins d'assets sont relatifs au script. `timeline.json` contient les phrases principales éditables, le minutage central et les couleurs. `render.py` contient les dimensions, typographies, éclairages graphiques, mouvements et la phrase de signature finale. Le produit remplaçable est `assets/product.png` ; les trois cartes sont générées localement par `architecture()` dans le script.

## Sources et limites

- Brief : texte fourni par l'utilisateur, conservé dans BRIEF.txt. L'utilisateur a ensuite demandé de continuer sans l'enregistrement de référence. Aucun enregistrement n'a donc été examiné ni reproduit exactement.
- Produit : adaptation/détourage assisté par génération d'image de la page STRUGAL Infinity visible dans la conversation. **La géométrie et les détails fins sont approximatifs, non certifiés conformes à un plan technique.** Ce visuel n'est pas une extraction pixel pour pixel de la photographie. Le PDF original de plus de 32 MiB n'a pas pu être transféré. Pour une publicité technique définitive, remplacer ce PNG par un détourage non génératif de la photographie officielle haute résolution. Le rendu est reproductible depuis le PNG livré ; sa génération ne nécessite pas d'être répétée.
- Architecture : trois illustrations conceptuelles originales, créées localement, identifiées comme telles à l'écran. Ce ne sont pas des photographies ni des réalisations PROMPOLU.
- Aucun modèle 3D du mécanisme, rotation, mouvement de coulissement ou valeur de performance n'est inventé. Le produit est une image plate animée en translation/échelle.
- Marque : logo PROMPOLU ALUMINIUM extrait sans génération du PDF fourni (assets/brand-source.pdf, page 1), palette fournie #15171A / #F1F0EC / #8C6A45. Fès et activité repris du brief.
- Aucun téléphone, adresse, certification ou chiffre technique ajouté. Aucune voix ni API payante externe appelée par les scripts livrés. Musique originale synthétisée localement.

Le contrôle visuel se fonde sur les images représentatives et les séquences d'images autour des transitions ; il ne constitue pas un visionnage humain continu de la vidéo.

Mise à jour : logo extrait affiché sur les sept plans, version agrandie en fermeture ; site prompolu.com ajouté sur le plan final.

Extraction du logo reproductible : `python extract_logo.py` (nécessite Poppler/pdftoppm). Le PNG transparent déjà livré suffit au rendu ; aucun outil génératif n’intervient dans cette extraction.

Transitions révisées : six raccords distincts de 24 images (0,8 s), accélération quintique à vitesse et accélération nulles aux extrémités. Fond et logo restent ancrés. Types et durée modifiables dans timeline.json ; fonctions dans render.py. Zoom de détail, glissement horizontal, passage vertical, révélation latérale à bord doux, révélation radiale et recul vers le logo. Aucun changement de durée : 450 images.

Les textes ont des pistes indépendantes : sortie douce, intervalle bref, puis entrée de la phrase suivante. Ils ne sont ni découpés par les masques de transition ni superposés en fondu.

## Version sonorisée

`output/Prompolu_Infinity_15s_avec_son.mp4` ajoute une musique instrumentale originale, composée et synthétisée localement : nappes douces, notes de clavier synthétiques, basse discrète, souffle aux six raccords et accord de fermeture. Aucun sample ou enregistrement tiers, aucune voix. La version silencieuse précédente est conservée.

Reproduction : après `python render.py`, lancer `python add_sound.py`. Les WAV et la vidéo sonorisée sont régénérés avec une graine fixe. Master visé à −18 LUFS / plafond −2 dBTP ; les mesures du fichier AAC livré sont enregistrées dans output/audio-validation.json. Le flux vidéo H.264 est copié sans réencodage et son empreinte est comparée à celle de la version silencieuse. Le script contrôle les 450 images, la durée, le décodage complet, les deux canaux et la fréquence audio de 48 kHz. Le contrôle audio est technique ; aucune écoute humaine n'est revendiquée.

## Variante sonore naturelle / premium

Fichier : `output/Prompolu_Infinity_15s_son_premium.mp4`. La composition originale est jouée avec un piano acoustique échantillonné, des accords espacés, une vélocité douce, des attaques légèrement décalées, une réverbération de petite pièce et un équilibre plus chaud. Les pulsations de basse et les notes synthétiques de la première version sont retirées. Trois textures d’air très discrètes remplacent les six souffles identiques. Pas de voix off.

Reproduction : `python premium_sound.py`, après le rendu vidéo. Dépendance supplémentaire : bibliothèque système FluidSynth (`libfluidsynth3` sur Debian). Aucun serveur audio ni outil payant requis. Banque TimGM6mb incluse dans assets/audio, attribuée à Tim Brechbill / David Bolton ; notice de provenance et licence GPL-2 incluses dans ce dossier. Cette version utilise des échantillons d’instrument sous licence ; ce n’est pas un enregistrement d’un pianiste en studio. La partition éditable et les notes MIDI sont consignées dans premium-score.json. Les mesures du fichier final figurent dans output/premium-audio-validation.json. Le contrôle est technique ; aucune écoute humaine n’est revendiquée.

## Variante sans piano

`output/Prompolu_Infinity_15s_sans_piano.mp4` : ambiance d’air chaude et discrète, six mouvements sonores doux adaptés aux transitions, petites réflexions diffuses et fondus d’entrée/sortie. Aucun piano, clavier, instrument tonal, mélodie, rythme de batterie ni voix. Sons originaux synthétisés localement, sans échantillon tiers dans cette variante.

Reproduction : `python no_piano_sound.py`. Nécessite seulement les dépendances Python du projet et FFmpeg. Niveau visé à −23 LUFS et plafond −3 dBTP pour une présence discrète. Le script vérifie le décodage audio/vidéo, les 450 images, les 15 secondes, les canaux stéréo et la conservation exacte du flux vidéo ; rapport dans output/no-piano-audio-validation.json. Aucune écoute humaine n’est revendiquée.
