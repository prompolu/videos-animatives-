# Promark — story ad de 20 secondes

Format : 1080 × 1920, 30 fps, 600 images. Style : DESIGN.md et brief client.
Audio livré : effets sonores, sans musique ni narration, selon le choix explicite du client.
La narration reste documentée dans SCRIPT.md pour une intégration ultérieure.
Les captures viennent du site exporté dans son dépôt public ; l’accès direct GitHub Pages est bloqué ici.

## Audit et affectation des assets
| Asset | Type | Affectation | Rôle |
| --- | --- | --- | --- |
| assets/brand/logo-lime.svg | Courbes originales recadrées/recolorées | Profil, publications, fin | Mot-symbole exact |
| assets/brand/logo-paper.svg | Même géométrie | Moments de marque | Séparation chromatique lime/paper |
| assets/brand/k-lime.svg, k-paper.svg | Recadrage du vrai k | 1.2–2.2 s | Transition de marque |
| capture/website/screenshots/mobile-home.png | Capture locale du vrai site | Téléphone, résultat 1 | Hero original |
| capture/website/screenshots/mobile-services.png | Section services du site | Résultat 2 | Services réels |
| capture/website/screenshots/mobile-home-full.png | Page d’accueil complète | Publication déroulante | Hero → services |
| capture/website/screenshots/mobile-services-page.png | Page services | Aperçu de contenu | Second écran de contenu |
| capture/website/assets/media/prompolu-motion-1280.webp | Projet présent sur le site | Résultat réalisations | Illustration du portfolio Promark |
| assets/fonts/Geist-variable.ttf | Police locale OFL | Toutes les interfaces | 700/800 |
| assets/fonts/GeistMono-variable.ttf | Police locale OFL | Labels | 400/600 |
| assets/sfx/*.mp3 | Bibliothèque HyperFrames/Pixabay | Cues du brief | Sources et crédits conservés |
| Autres médias du portfolio capturé | Archives de référence | Non assignés | Éviter de détourner l’attention des quatre posts demandés |

## 01 — Le signal, 0.0–1.2
Un carré lime de 9 % de la largeur apparaît déjà au premier photogramme, dans un monde noir.
Deux pulsations traversent son halo. Le son monte sans musique.
Techniques : échelle seekable, ombre locale, rythme en deux cycles. Fond/halo/carré sont trois niveaux.
Transition : le carré se résout rapidement en véritable k ; pas de remplacement typographique.
Son : hum/riser obtenu par découpe des sons existants de la bibliothèque.

## 02 — La marque devient passage, 1.2–2.2
Le vrai k lime et sa réplique paper se séparent légèrement, avec une inclinaison en profondeur.
La caméra plonge dans l’espace négatif du signe ; le flou donne le raccord vers le téléphone.
Techniques : SVG authentique, split chromatique, zoom et rotation en perspective.
Son : whoosh à 1.2 ; le téléphone prend le relais pendant la transition.

## 03 — L’interface entre en scène, 2.2–3.6
Un téléphone noir incliné flotte dans un halo lime ; son écran montre une entrée Promark.
Cadre, écran, reflet et indicateur inférieur dessinent la profondeur.
Le push-in remplit progressivement le cadre avec l’écran et raccorde la recherche.
Techniques : 3D CSS, pan léger de capture, changement d’échelle avec flou.

## 04 — Être trouvé, 3.6–6.0
La recherche tape « agence marketing digital fès », avec curseur lime.
Trois propositions changent pendant le mouvement de la saisie. L’interface reste nette sur son fond graphite.
Techniques : écriture déterministe par caractères, curseur seekable, déplacement et flou des suggestions.
Son : touches de 3.7 à 5.2. Le champ monte et se raccorde aux résultats.

## 05 — Quatre preuves de marque, 6.0–7.4
Une grille 2×2 présente le hero du vrai site, les services, une publication Stratégie/Création/Impact et les réalisations.
Les cartes entrent sur des axes différents, puis un ripple lime désigne la première.
Techniques : captures locales en cadres, perspective légère, stagger et ripple.
Son : tap à 6.8. La première carte devient le post plein écran.

## 06 — Du post au site, 7.4–9.0
La page capturée défile du hero aux services dans une publication @promark.
La légende et le bouton « Voir nos réalisations → » restent attachés au cadre social.
Techniques : défilement de capture, interface en couches, pression du bouton et poussée 3D de transition.
Texte : « @promark — Découvrez nos réalisations sur notre site ✳ Lien en bio · #marketingdigital #fès ».

## 07 — Suivre, 9.0–10.8
Le profil prend la place du post : avatar lime, @promark et compteurs 48 / 2 512 / 31 k.
Les rouleaux des chiffres s’arrêtent l’un après l’autre ; Suivre devient Abonné ✓ après le tap.
Techniques : avatar en anneau, odomètres sans accumulation d’état, bouton à deux états.
Son : ticks de 9.2 à 10 ; tap à 10.2. Une feuille glisse sur le profil pour les commentaires.

## 08 — Réactions, 10.8–12.0
Une feuille graphite affiche successivement les trois commentaires exacts du brief.
Le profil précédent n’est pas évacué avant que cette feuille le recouvre.
Techniques : sheet reveal, avatars géométriques, décalage des lignes.
Son : pops à 11.0, 11.3 et 11.6.

## 09 — La demande, 12.0–14.2
La conversation privée montre la demande de vidéo pour une boutique, la réponse lime et le rendez-vous jeudi à 10 h.
Les bulles arrivent en trois accents ; leur taille s’adapte au français, sans texte coincé dans des hauteurs fixes.
Techniques : bulles flex, alternance gauche/droite, pression discrète du champ de message.
Son : blips à 12.2, 12.9, 13.6. La conversation glisse sous les notifications.

## 10 — L’élan social, 14.2–15.8
Des cœurs lime parcourent des trajectoires déterministes et trois notifications « Nouvel abonné » s’empilent.
Techniques : trajectoires définies, perspective des cartes, stagger ; pas de hasard pendant le rendu.
Son : pings entre 14.3 et 15.4. Le panneau de partage recouvre la pile.

## 11 — Partager, 15.8–17.4
Une feuille de partage, des contacts abstraits et le bouton Envoyer occupent le cadre.
Le tap se conclut par une pastille paper « Envoyé ✓ ».
Techniques : sheet, déplacement de chips, morphing de bouton ; trois niveaux lisibles.
Son : swoosh et chime à 16.9.

## 12 — Le signe plus, 17.4–18.6
Deux traînées lime et paper enveloppent un bouton +.
Les traits se dessinent, tournent et convergent ; le plongeon révèle la signature.
Techniques : dash SVG, rotation sur timeline, zoom flouté. Sons : whooshes à 17.4 et 17.9.

## 13 — La signature et le raccord, 18.6–20.0
Mot-symbole lime centré à 66 % de largeur, Marques paper / remarquées. lime, label agence de Fès et bouton WhatsApp.
Les éléments terminent leur arrivée à 18.6, tiennent une seconde, puis disparaissent vers le carré d’origine.
La pose est entièrement raccordée à 19.9 pour que le dernier photogramme retrouve le premier.
Techniques : marque exacte, split chromatique retenu, masque de texte et fondu final demandé.
Son : bass impact à 18.6, shimmer à 19.0, fin audio adoucie avant 20.0.

## Architecture
index.html : composition racine et timeline GSAP synchrone de 20 secondes.
assets/ : logo et k, polices, bibliothèque sonore et mix prêt à l’emploi.
capture/website/ : captures, médias et textes du site source.
sound-design.cjs : assemblage des cues depuis les sons fournis par la bibliothèque, sans synthèse.
SCRIPT.md et voice-cues.json : narration future et repères demandés, sans faux transcript.
renders/ et snapshots/ : exports et images de contrôle produits par HyperFrames.
