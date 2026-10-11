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

## Calage de la perspective (photos au grand-angle)

Les photos de téléphone sont souvent prises au grand-angle (0,5x, environ 87° de champ vertical) et la façade est rarement de face. `calage.py` mesure les lignes de fuite de la façade (toiture, fenêtres, portes) et en déduit le champ, l'inclinaison, le roulis et l'orientation de la façade :

    python3 calage.py photo.jpg x0,y0,x1,y1 1.5 coin_bas_x,coin_bas_y

- `cam` va tel quel dans la scène, `rotY_murale` sur la pergola murale, `coin_bas` donne la position au sol du coin de façade.
- Option de scène `facade: {p, n}` : la face du mur du modèle est posée sur ce plan, quelle que soit son orientation.
- Option `ombreFacade: {p, n, w, h, opacity}` : plan invisible qui reçoit les ombres des lames et des poteaux sur le mur de la maison.
- `relight.py` : ne garde de la passe lumière IA que la lumière (basses fréquences), appliquée à la photo fidèle. La maison et les produits ne sont pas redessinés.

## Bois naturel (fin de l'effet 3D)

- `scene.html` : chaque lame reçoit son propre morceau de texture (décalage, sens) et une teinte légèrement différente. Les nœuds ne se répètent plus d'une lame à l'autre ni d'un échantillon répété à l'autre. Actif par défaut (`varBois: false` pour couper).
- `affine.py` avec `none` à la place du LoRA : passe de réalisme générique (Flux dev, force 0,3) sur une clôture ou une terrasse, zone par zone, au rapport d'image de la zone. La géométrie de la 3D reste en place.

## Teinte fidèle aux réalisations

- `teinte_ref.json` : couleur du bois mesurée (espace Lab, moyenne et écart entre lames) sur des clôtures Cover Green posées, en deux lumières (soleil, couvert).
- `teinte.py` : ramène le bois de chaque produit à ces mesures. Les connecteurs et le métal ne sont pas touchés, et chaque produit garde la lumière de la photo.

    python3 teinte.py image.jpg sortie.jpg teinte_ref.json soleil pergola.png,cloture_g.png,cloture_d.png 0.5

## Aménagement paysager (effet waouh)

Deux passes gpt-image-1 masquées, produits toujours exacts :

1. `amenage.py` : massifs plantés au pied des clôtures, pelouse, allée en pas japonais. L'IA peut passer devant le bas des clôtures (bande `part_pied`), mais on n'y garde que ce qu'elle a ajouté. Avec `MOBILIER_SEPARE=1`, la terrasse et le volume au-dessus sont protégés.
2. `mobilier.py` : table, chaises et pots sur la terrasse, sur un cadrage serré. Limité à l'espace entre les poteaux de la pergola, pour qu'aucun panneau ou poteau inventé n'apparaisse à côté.

    MOBILIER_SEPARE=1 python3 amenage.py image.jpg zone.json echelle consigne.txt sortie.jpg produits.png cloture_g.png,cloture_d.png terrasse.png 0.3
    python3 mobilier.py sortie.jpg terrasse.png pergola_terrasse.png consigne_mobilier.txt final.jpg 120
