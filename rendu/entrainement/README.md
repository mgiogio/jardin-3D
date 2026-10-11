# Modèles entraînés (LoRA Flux, Replicate, organisation covergreen, privés)

| Modèle | Mot déclencheur | Données | Usage |
|---|---|---|---|
| pergola-adossee-lora | CVGPRGL | réalisations + rendus 3D | retouche des pergolas murales |
| pergola-autoportante-lora | CVGPRGA | réalisations + rendus 3D | retouche des pergolas autoportantes |
| cloture-terrasse-lora (entraîné le 11/10, 20 min, 1600 pas) | CVGCLO, CVGTER | 44 photos de clôtures/bardages posés + 5 terrasses (réalisations www.cover.green) | retouche des clôtures, bardages et terrasses |

- Entraîneur : ostris/flux-dev-lora-trainer, rang 16, taux 4e-4, 1200 à 1600 pas, légendes écrites à la main.
- `build_ds.py` : sélection des photos (indices dans la liste des réalisations) et légendes. Les photos clients ne sont jamais mises dans ce dépôt public.
- Sélection : produit net et bien visible, lames horizontales Cover Green ; exclus les photos de nuit, de chantier, d'intérieur, les poteaux alu gris et les claire-voie.
- Coût : environ 1,20 à 2 $ par entraînement. Pour progresser : plus de photos de terrasses posées (5 seulement aujourd'hui).

Règle d'usage du modèle clôture : seulement sur une clôture vue de près (lames larges dans l'image). Sur une clôture lointaine, il sème des nœuds en taches brun-orangé qui font « bois abîmé » : on y garde la retouche générique douce (force 0,22).
