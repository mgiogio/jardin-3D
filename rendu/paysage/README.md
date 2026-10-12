# Aménagement paysager « expert »

Méthode (validée sur Tours, octobre 2026) :
1. **Diagnostic de paysagiste** sur la photo : climat (région), exposition, ce qui tue l'effet waouh (sol, transitions, façades nues, absence de point focal).
2. **Concept** : une intention en une phrase, un point focal, des strates (structure persistante au fond, floraison au milieu, lisière basse et répétée devant), une palette végétale adaptée au climat et à l'exposition, le traitement du sol.
3. **Génération par zones** avec `gpt-image-2.5-sunburst` (variable `IMG_MODEL` de `amenage.py`) : une passe globale (`p_tout.txt`), puis des passes ciblées (`p_p2.txt`, `p_p4.txt`). `LIBRE_POLY` autorise la végétation à passer devant un produit (arbre en pot devant l'angle de la terrasse), puis `feuillage_devant.py` ne garde que le feuillage et remet le produit exact.
4. **Finition** (`finition.py`) : ombre de contact sous la terrasse et les potées, lumière des zones IA raccordée à la photo.
5. **Double relecture indépendante** : architecte paysagiste (cohérence climat, exposition, saisons, entretien) et retoucheur (montage). Corriger, relire, puis seulement montrer.

Ce qui n'a pas marché : gpt-image-1 (massifs maigres), nettoyage des dalles par traitement d'image (taches), Kontext / Nano Banana pour garder le calepinage (géométrie faussée près des bordures). Une passe qui « affine » trop fait perdre les contrastes (or et pourpre) qui font l'effet waouh : ne garder une passe que si la relecture la juge meilleure.
