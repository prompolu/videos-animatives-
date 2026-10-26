# Promark — référence visuelle du film

## Overview
Film vertical d’une agence marketing de Fès, situé dans une application sociale fictive.
Le site source a été rendu depuis son archive publique au commit 094d14327d5add28197eb9cdfa65f1ee08d37967.
La capture montre une identité noire/lime, une grande typographie, des projets vidéo et des appels WhatsApp.
Les choix explicites du brief définissent le film, y compris Geist plutôt que les fontes Arial/Georgia de la capture.

## Colors
- Lime #D7FF00 : accent, boutons, curseur, halo, logo.
- Ink #131419 : fond constant et raccord de boucle.
- Graphite #24252C : cartes et feuilles.
- Rule #2E3039 : séparateurs et bordures.
- Paper #F2F2F6 : texte principal.
- Lavender #DBDBE9 : reflets doux.
- Muted #8B8D96 : informations secondaires.
- Les couleurs internes des captures authentiques restent inchangées.

## Typography
- Geist variable, poids 700–800, pour affichage et interface ; approche −0.04em.
- Geist Mono variable, poids 400–600, pour petites étiquettes en capitales ; approche +0.06em.
- Titres de 76 à 116 px ; messages de 40 à 48 px ; étiquettes de 26 à 34 px.
- Les mots d’accent « remarquées. » et « Impact. » sont lime.
- Chiffres tabulaires pour les compteurs ; aucune substitution du logo par du texte.

## Elevation
Surfaces graphite aux angles arrondis, filets Rule, ombres noires et halos lime localisés.
Le téléphone est un volume CSS en perspective, avec cadre sombre et reflet lime.
Les scènes sont raccordées par poussées, zooms, feuilles montantes et flou de mouvement.
Le fond reste uni : pas de grand dégradé sombre susceptible de produire des bandes à l’encodage.

## Components
- Point carré lime : côté 97.2 px, deux pulsations ; même pose au dernier plan.
- Logo et k : géométrie vectorielle originale, extraite du négatif du SVG fourni par le site.
- Téléphone sombre : cadre, encoche, écran et reflet, animé en trois dimensions.
- Recherche : texte tapé, curseur lime, suggestions échangées avec flou.
- Résultats : quatre publications propres à Promark, dont deux captures de son vrai site.
- Profil : avatar au liseré lime, compteurs à rouleaux et bouton Suivre/Abonné.
- Feuilles : commentaires, conversation privée et partage, avec contenu français du brief.
- Notifications : cœurs et trois annonces « Nouvel abonné » empilées.
- Signature : logo à 66 % de la largeur, deux lignes Marques/remarquées., label et bouton WhatsApp.

## Do’s and Don’ts
### Do
- Conserver les courbes exactes du logo ; seul le recadrage et la couleur changent.
- Faire émerger chaque interface avec une transition visible et une hiérarchie claire.
- Garder les éléments essentiels entre x=80–1000 et y=200–1630.
- Employer les vraies captures du site, sans iframe ni requête réseau pendant le rendu.
- Traiter les compteurs et messages comme les scènes illustratives demandées par le client.
### Don’t
- Ne pas réutiliser la palette bronze, le logo ou le téléphone commercial de PROMPOLU.
- Ne pas remplacer le mot-symbole par une police, ni modifier ses courbes.
- Ne pas ajouter de musique ou une voix différente de Vivienne sans demande.
- Ne pas afficher une voix synthétique fictive comme une voix Vivienne effectivement produite.
- Ne pas laisser de saut entre le carré d’ouverture et la pose finale de boucle.
