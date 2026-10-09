# Rendu 3D des produits dans la photo du client

- `produits.json` : quels objets garder dans chaque modèle .glb, variantes par défaut, teintes de bois réelles.
- `scene.html` + `scene.mjs` : rendu three.js sans écran (Chromium) des produits placés dans une scène, caméra calée sur la photo, fond transparent avec ombres.
- `composer.py` : pose le rendu sur la photo, impose la teinte réelle du bois, remet devant les éléments qui doivent masquer le produit.

Les modèles (`modeles/*.glb`) et les photos clients ne sont pas publiés ici (dépôt public).

Usage : `node scene.mjs scene.json calque.png` puis `python3 composer.py photo.jpg calque.png sortie.jpg '#7a6858' masques.json`
