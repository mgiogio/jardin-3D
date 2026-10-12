# Mobilier 3D (libre de droits)

Le mobilier n'est plus généré par l'IA : ce sont des modèles 3D posés dans la scène, comme les produits. Ils ne débordent jamais de la terrasse, ne touchent pas les poteaux et ont des ombres justes.

Source : Poly Haven (polyhaven.com), licence CC0 (domaine public, usage commercial libre, sans attribution obligatoire). Fichiers convertis en .glb dans `modeles/` (non versionnés, comme les produits) :

- `M_outdoor_table_chair_set_01.glb` : table bistrot et deux chaises bois/métal
- `M_potted_plant_01.glb` : arbuste en pot terre cuite
- `M_planter_pot_clay.glb` : pot terre cuite seul

Téléchargement : API `https://api.polyhaven.com/files/<id>` (gltf 1k) puis `npx @gltf-transform/cli copy x.gltf x.glb`.
Pose : `meubles_poser.py` (couleurs du modèle accordées à la photo). Les produits Cover Green passent par `poser.py` (teinte des réalisations), le mobilier non.
