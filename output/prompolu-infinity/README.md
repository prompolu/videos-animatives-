# PROMPOLU — Infinity, film éditorial de 15 secondes

Vidéo verticale silencieuse : 1080 × 1920, 30 images/s, exactement 450 images, H.264/yuv420p et fast start. Le nom demandé `Prompolu_S140RP_Editorial_15s.mp4` est conservé pour le fichier ; le texte visible indique « STRUGAL Infinity », seul nom vérifiable dans la page visible fournie. Le code S140RP reste non vérifié.

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
- Aucun téléphone, adresse, certification ou chiffre technique ajouté. Pas de voix, musique ni API payante externe appelée par les scripts livrés.

Le contrôle visuel se fonde sur les images représentatives et les séquences d'images autour des transitions ; il ne constitue pas un visionnage humain continu de la vidéo.

Mise à jour : logo extrait affiché sur les sept plans, version agrandie en fermeture ; site prompolu.com ajouté sur le plan final.

Extraction du logo reproductible : `python extract_logo.py` (nécessite Poppler/pdftoppm). Le PNG transparent déjà livré suffit au rendu ; aucun outil génératif n’intervient dans cette extraction.
