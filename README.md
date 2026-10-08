# Mon jardin aménagé - Cover Green

Outil de génération de leads : le client renseigne son adresse, ses photos et son projet ;
il reçoit un visuel de son jardin aménagé avec les produits Cover Green et un compte rendu de conseils.

## Contenu

- `prototype/` : questionnaire autonome (HTML + JS modules, sans build). Sera intégré dans un plugin WordPress via un shortcode.
  - `js/geo.js` : géocodage, bâtiments BD TOPO, parcelle cadastrale, calcul des façades (longueur, orientation), cône de vue, placement.
  - `js/map.js` : carte Leaflet sur orthophoto IGN.
  - `js/app.js` : étapes du parcours et données envoyées.
- `tests/` : tests de géométrie (`node tests/geo.test.mjs`).

## Lancer en local

```
cd prototype && python3 -m http.server 8080
```
puis ouvrir http://localhost:8080.

## Données publiques utilisées

Géoplateforme IGN (géocodage, WMTS orthophoto et parcellaire, WFS BDTOPO_V3:batiment) et API Carto cadastre, licence ouverte Etalab 2.0.

## Étapes suivantes

1. API de réception des projets (photos + JSON), stockage, file de rendu.
2. Rendu 3D des produits (Blender) et habillage IA.
3. Email résultat, page résultat avec retour client, envoi HubSpot / Brevo.
4. Plugin WordPress.
