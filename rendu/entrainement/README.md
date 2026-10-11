# Modèles entraînés (LoRA Flux, Replicate, organisation covergreen, privés)

| Modèle | Mot déclencheur | Données | Usage |
|---|---|---|---|
| pergola-adossee-lora | CVGPRGL | réalisations + rendus 3D | retouche des pergolas murales |
| pergola-autoportante-lora | CVGPRGA | réalisations + rendus 3D | retouche des pergolas autoportantes |
| cloture-terrasse-lora (entraîné le 11/10, 20 min, 1600 pas) | CVGCLO | 44 photos de clôtures/bardages posés (réalisations www.cover.green) | retouche des clôtures et bardages vus de près |
| terrasse-lora (entraîné le 11/10, 2000 pas, légendes auto) | CVGTER | 92 photos de terrasses pin posées, sur les 191 des 73 réalisations terrasse | retouche des terrasses |

- Entraîneur : ostris/flux-dev-lora-trainer, rang 16, taux 4e-4, 1200 à 1600 pas, légendes écrites à la main.
- `build_ds.py` : sélection des photos (indices dans la liste des réalisations) et légendes. Les photos clients ne sont jamais mises dans ce dépôt public.
- Sélection : produit net et bien visible, lames horizontales Cover Green ; exclus les photos de nuit, de chantier, d'intérieur, les poteaux alu gris et les claire-voie.
- Coût : environ 1,20 à 2,50 $ par entraînement.
- Photos : toutes les pages de www.cover.green/realisations/ (4 pages, 132 réalisations) via curl. Terrasses exclues : composite gris, vues aériennes, brouillard, nuit, chantier, gros plans de détail.

Règle d'usage du modèle clôture : seulement sur une clôture vue de près (lames larges dans l'image). Sur une clôture lointaine, il sème des nœuds en taches brun-orangé qui font « bois abîmé » : on y garde la retouche générique douce (force 0,22).
