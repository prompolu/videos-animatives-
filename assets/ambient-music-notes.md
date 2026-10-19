# Saraproc Maroc — musique d’ambiance originale

- Fichier : `saraproc-ambient-loop.wav`, exactement **40,000 secondes**, stéréo, **48 kHz**, **PCM 16 bits**, 7 680 044 octets.
- Composition et synthèse originales dans `tools/compose_ambient_loop.py`, avec Python, NumPy et la bibliothèque standard. Aucun enregistrement, échantillon, morceau ou instrument tiers téléchargé ; aucune voix.
- Nappes chaleureuses, transitions harmoniques lentes et notes aiguës espacées à attaque douce. Aucun battement de batterie ni impulsion de basse. Progression : Dmaj9 → Bm11 → Gmaj9 → Asus4/add9, une harmonie toutes les dix secondes.
- Les notes et leurs fins se poursuivent de manière circulaire à travers la jonction de la boucle. Aucun fondu global dans le fichier ; appliquer les fondus uniquement au début et à la fin de la vidéo complète.
- Génération déterministe, graine `20261019`. Les musiques des versions précédentes sont conservées.

Pour reproduire le fichier depuis la racine du dépôt :

```sh
python tools/compose_ambient_loop.py
```

Contrôles effectués sur le fichier PCM enregistré :

- **1 920 000 images audio stéréo**, soit exactement 40 secondes ; format confirmé par FFprobe.
- Crête : **−11,00 dBFS** ; niveau RMS : **−23,15 dBFS** ; aucun échantillon écrêté.
- Niveau RMS sur des fenêtres de 0,5 seconde : **−28,72 à −21,32 dBFS** ; aucune pause périodique ni fondu récurrent.
- Écart maximal entre dernier et premier échantillons : **136 unités PCM**, soit 0,004150 pleine échelle. Cet écart est inférieur aux variations ordinaires du signal (272 unités au percentile 99,9) ; les enveloppes circulaires préservent la continuité musicale.
- Décodage intégral par `ffmpeg -v error -xerror` réussi. Aucun outil d’écoute n’était disponible ; les contrôles portent sur le signal et le format.
- SHA-256 : `8832f8199388286c66036532f74a276f4ce4d8770b0a2df633c0101ebcbf0556`.

Exemple d’intégration sous une vidéo silencieuse de 300 secondes :

```sh
ffmpeg -i output/video-sans-son.mp4 \
  -stream_loop -1 -i assets/saraproc-ambient-loop.wav \
  -map 0:v:0 -map 1:a:0 -t 300 \
  -c:v copy -c:a aac -b:a 128k -ar 48000 \
  -af 'afade=t=in:st=0:d=1.5,afade=t=out:st=297:d=3' \
  -movflags +faststart output/video-ambiance.mp4
```

Adapter la durée et le départ du fondu final à la vidéo réelle.
