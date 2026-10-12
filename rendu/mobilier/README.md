# Mobilier 3D (libre de droits)

Le mobilier n'est plus généré par l'IA : ce sont des modèles 3D posés dans la scène, comme les produits. Ils ne débordent jamais de la terrasse, ne touchent pas les poteaux et ont des ombres justes.

Source : Poly Haven (polyhaven.com), licence CC0 (domaine public, usage commercial libre, sans attribution obligatoire). Fichiers convertis en .glb dans `modeles/` (non versionnés, comme les produits) :

- `M_outdoor_table_chair_set_01.glb` : table bistrot et deux chaises bois/métal
- `M_potted_plant_01.glb` : arbuste en pot terre cuite
- `M_planter_pot_clay.glb` : pot terre cuite seul

Téléchargement : API `https://api.polyhaven.com/files/<id>` (gltf 1k) puis `npx @gltf-transform/cli copy x.gltf x.glb`.
Pose : `meubles_poser.py` (couleurs du modèle accordées à la photo). Les produits Cover Green passent par `poser.py` (teinte des réalisations), le mobilier non.

## Palettes d'ambiance

`palettes.json` : chaque ambiance = une liste de meubles en coordonnées locales de la pergola (gabarit), avec la taille minimale de pergola. `palette_scene.py scene.json <ambiance> ...` remplace le mobilier de la scène par celui de l'ambiance.

- bistrot : table bistrot et 2 chaises, arbustes en pot terre cuite, lanterne
- campagne : table de ferme patinée, 4 chaises, panier en osier, lanterne bois
- nature : table de pique-nique brute, jardinière bois, lanterne bois (pergola 3x4 conseillée)

Manque : une ambiance contemporaine (salon bas, teck, corde, coussins) : rien d'adapté en CC0, il faudra un pack payant libre de droits ou les fichiers d'une marque.

## Banque Cover Green (v2, octobre 2026)
Le mobilier CC0 vintage est remplacé par une banque générée pour nous (aucun droit tiers) :
1. `banque/gen.py` : visuel produit de chaque meuble (gpt-image-1, fond blanc, design original), liste dans `banque/items.json` avec les dimensions réelles.
2. `banque/to3d.py` : image vers GLB texturé (Trellis sur Replicate).
3. `banque/norm.mjs` : mise à l'échelle réelle, sortie `models/B_<nom>.glb`. `banque/recolor.mjs` décline une couleur (chaises métal corail, bleu, jaune, sauge).
4. `palettes.json` : bistrot coloré, lounge teck et corde, repas entre amis.
5. `fin_tours_pal.sh` (STOP_D=1) puis `compose_v8.py` : meubles posés après les retouches produits, abords d'un visuel validé conservés, ombres portées et ombres d'appui.
Les modèles générés et les photos clients ne sont pas versionnés.
