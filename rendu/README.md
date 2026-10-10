# Rendu 3D des produits dans la photo du client

- `produits.json` : quels objets garder dans chaque modèle .glb, variantes par défaut, teintes de bois réelles.
- `scene.html` + `scene.mjs` : rendu three.js sans écran (Chromium) des produits placés dans une scène, caméra calée sur la photo, fond transparent avec ombres.
- `composer.py` : pose le rendu sur la photo, impose la teinte réelle du bois, remet devant les éléments qui doivent masquer le produit.

Les modèles (`modeles/*.glb`) et les photos clients ne sont pas publiés ici (dépôt public).

Usage : `node scene.mjs scene.json calque.png` puis `python3 composer.py photo.jpg calque.png sortie.jpg '#7a6858' masques.json`

## Passe lumière (visuel final)

`lumiere.py` enchaîne : recadrage automatique si le produit fait moins de 15 % de l'image, profondeur de la photo (Depth Anything V2, local) remplacée sur le produit par la profondeur exacte de la 3D (`scene.html` avec `depthPass`), lumière par Flux + LoRA profondeur sur ComfyUI (Replicate, `comfy/`), puis retouche du produit par le modèle entraîné Cover Green (`affine.py`, force 0,45). Réglage conseillé : denoise 0,6 à 0,66 ; au-delà l'IA modifie le jardin.

## Pans brise-soleil et brise-vue

Les deux pans se posent partout et se multiplient (règle dans `produits.json`).

- `briseVue` : liste de côtés dans le repère du modèle, avec la travée de 3 m en option. Exemple `["x-0", "z-"]` : face avant, première travée, plus tout le bout côté z-. Sur une murale, `x-` est la face avant (opposée au mur) et les bouts `z-` / `z+` vont du poteau au mur, lames recoupées à la longueur.
- `briseSoleil` : toutes les travées par défaut, ou une sélection, par exemple `[0, 2]`.
- `facadeZ` (murale) : position de la façade dans la scène. La face du mur du modèle y est collée, jamais dans le vide.
- `PORT=8777 node scene.mjs ...` permet de lancer plusieurs rendus en parallèle.
