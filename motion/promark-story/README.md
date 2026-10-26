# Promark — Marques remarquées

Publicité verticale de 20 secondes, 1080 × 1920, 30 images/s. Version avec effets sonores, sans voix ni musique, selon le choix du client. Les repères de la future voix française Vivienne sont conservés dans `voice-cues.json` et `SCRIPT.md`.

## Projet éditable

Le film est une composition HyperFrames HTML avec une timeline GSAP synchrone et déterministe. `build.cjs`, `style.css` et `motion.js` produisent `index.html`. Les polices et médias sont locaux ; aucun iframe ni site distant n’est sollicité pendant le rendu.

```sh
cd motion/promark-story
npm ci --ignore-scripts
node sound-design.cjs
node build.cjs
HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium npm run check
HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium npm run render -- --output renders/promark-story-sfx.mp4 --fps 30 --quality high --workers 2
node validate-export.cjs
```

Prérequis : Node 22+, FFmpeg/ffprobe et Chromium. Adapter `HYPERFRAMES_BROWSER_PATH` à votre système. Le CLI est fixé à 0.8.206, GSAP à 3.14.2 et Playwright à 1.62.1 ; le lockfile conserve les intégrités des paquets.

Pour le Studio sur votre propre machine : `npm run dev`. Dans un environnement où le dossier d’état utilisateur n’est pas accessible, `XDG_STATE_HOME` permet de choisir un dossier d’état autorisé. Le projet peut être parcouru sans export MP4.

## Médias et identité

- Logo : courbes du SVG original du site Promark, recadrées et appliquées comme masque ; aucun mot-symbole reconstitué en police. Les versions lime et paper et le k utilisent la même géométrie originale.
- Captures : copie publique du site fournie dans le dépôt `prompolu/promark-marketing-agency-`, commit `094d14327d5add28197eb9cdfa65f1ee08d37967`. Le proxy refuse l’URL GitHub Pages ; les captures viennent du rendu local de l’archive exportée, et ne sont pas présentées comme une vérification du site en ligne actuel.
- Geist et Geist Mono : fichiers variables locaux et licences OFL dans `assets/fonts/`.
- Effets : 14 fichiers de la bibliothèque HyperFrames/Pixabay, 36 cues montées avec leurs pics repérés. Sources, crédits et liste de cues sont conservés. Aucun effet n’est synthétisé par le script.
- Interface sociale : les publications adaptées, les compteurs et les conversations illustrent le storyboard du client. Aucun message n’est envoyé à un vrai compte.

Le film finit sur la même pose du carré que son ouverture. Les effets s’éteignent avant 20 secondes pour éviter un clic à la reprise. La narration, sa transcription réelle et le ducking sous voix seront réalisés après réception de l’enregistrement ; aucun faux fichier de narration n’est livré.

## Contrôles

Les rapports conservent le résultat complet du check HyperFrames et la validation de l’export. Les instantanés sont produits par `hyperframes snapshot`, puis inspectés. Le décodage complet, le nombre d’images, la durée, la lecture dans Chromium, la loudness et le raccord premier/dernier photogramme sont vérifiés par `validate-export.cjs`.

Certaines alertes de lecture sont maintenues car les temps très courts et la tenue finale d’une seconde sont explicitement fixés par le brief. Les croisements d’écrans pendant les transitions sont intentionnels et inspectés ; les rouleaux hors des fenêtres de chiffres sont exclus comme décor de l’audit de texte, leurs chiffres visibles étant contrôlés dans les images de review.
