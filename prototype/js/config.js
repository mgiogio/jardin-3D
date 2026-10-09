// Configuration du prototype "Mon jardin aménagé" - Cover Green
// Toutes les données publiques utilisées viennent de la Géoplateforme IGN
// (licence ouverte Etalab 2.0) et de l'API Carto cadastre.

export const ENDPOINTS = {
  // Géocodage d'adresse (BAN via Géoplateforme), avec secours sur l'ancienne API Adresse
  geocode: 'https://data.geopf.fr/geocodage/search',
  geocodeFallback: 'https://api-adresse.data.gouv.fr/search/',
  // Tuiles orthophoto et parcellaire (WMTS)
  wmts: 'https://data.geopf.fr/wmts',
  // Emprises de bâtiments BD TOPO (WFS)
  wfs: 'https://data.geopf.fr/wfs/ows',
  buildingLayer: 'BDTOPO_V3:batiment',
  // Parcelle cadastrale contenant un point
  parcel: 'https://apicarto.ign.fr/api/cadastre/parcelle',
  // API de l'outil (phase suivante) : réception du projet, rendu, email
  projectApi: null,
};

// Catalogue utilisé par le questionnaire. Source cible : WooCommerce (produits actifs).
// mode : "zone" = surface posée au sol (on trace un côté puis on règle la profondeur)
//        "ligne" = linéaire (on clique les points successifs)
export const PRODUCTS = [
  { id: 'pergola-adossee', label: 'Pergola adossée', hint: 'Fixée contre la façade', mode: 'zone', snapFacade: true, defaultDepth: 3 },
  { id: 'pergola-autoportante', label: 'Pergola autoportante', hint: 'Posée librement dans le jardin', mode: 'zone', snapFacade: false, defaultDepth: 3 },
  { id: 'terrasse', label: 'Terrasse bois', hint: 'Sol en lames de bois', mode: 'zone', snapFacade: false, defaultDepth: 3 },
  { id: 'cloture', label: 'Clôture bois', hint: 'Occultante ou claire-voie', mode: 'ligne' },
  { id: 'bardage', label: 'Bardage bois', hint: 'Habiller un mur ou une façade', mode: 'ligne' },
  { id: 'portillon', label: 'Portillon bois', hint: 'Entrée assortie à la clôture', mode: 'ligne' },
  { id: 'abri', label: 'Abri de jardin', hint: 'Rangement', mode: 'zone', snapFacade: false, defaultDepth: 2 },
  { id: 'studio', label: 'Studio de jardin', hint: 'Bureau, chambre, pièce en plus', mode: 'zone', snapFacade: false, defaultDepth: 4 },
];

// Phase de test : pas de demande d'email, le parcours se termine sur un récapitulatif.
export const CAPTURE_EMAIL = false;

export const COLORS = {
  orange: '#EB5A00',
  green: '#049E00',
  ink: '#1E211F',
  mist: '#EAF7E5',
};
