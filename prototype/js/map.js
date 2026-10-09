// Carte Leaflet : orthophoto IGN, parcelle, bâtiments, façades, cônes de vue, placements.
/* global L */
import { ENDPOINTS, COLORS } from './config.js';
import { conePolygon, bearingDeg, rectFromSide, snapToFacades, polylineLength, pointInRing, makeProjection } from './geo.js';

const ll = ([lon, lat]) => [lat, lon];
// Petit personnage vu de face, dans une pastille orange : « vous étiez ici ».
const PERSON_SVG = '<svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="#EB5A00" stroke="#fff" stroke-width="3"/><circle cx="20" cy="13" r="4.2" fill="#fff"/><path d="M13.5 30v-6.5a6.5 6.5 0 0 1 13 0V30z" fill="#fff"/></svg>';
const fmt = (m) => `${m.toFixed(1).replace('.', ',')} m`;

function wmtsLayer(layer, style, format, opts = {}) {
  const url = `${ENDPOINTS.wmts}?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layer}` +
    `&STYLE=${encodeURIComponent(style)}&TILEMATRIXSET=PM&FORMAT=${format}` +
    '&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}';
  return L.tileLayer(url, { maxZoom: 21, attribution: '© IGN Géoplateforme', ...opts });
}

export class GardenMap {
  constructor(el) {
    this.map = L.map(el, { zoomControl: true, attributionControl: true, tap: true, scrollWheelZoom: false }).setView([46.6, 2.4], 6);
    wmtsLayer('ORTHOIMAGERY.ORTHOPHOTOS', 'normal', 'image/jpeg', { maxNativeZoom: 19 }).addTo(this.map);
    this.cadastre = wmtsLayer('CADASTRALPARCELS.PARCELLAIRE_EXPRESS', 'PCI vecteur', 'image/png', { maxNativeZoom: 19, opacity: 0.7 });
    this.groups = {
      parcel: L.layerGroup().addTo(this.map),
      buildings: L.layerGroup().addTo(this.map),
      facades: L.layerGroup().addTo(this.map),
      cones: L.layerGroup().addTo(this.map),
      placements: L.layerGroup().addTo(this.map),
      draft: L.layerGroup().addTo(this.map),
      address: L.layerGroup().addTo(this.map),
    };
    this.clickHandler = null;
    this.map.on('click', (e) => this.clickHandler && this.clickHandler([e.latlng.lng, e.latlng.lat]));
  }

  // La carte est dans un écran caché au départ : il faut recalculer sa taille à l'affichage.
  attach(container) {
    container.appendChild(this.map.getContainer());
    this.map.invalidateSize();
    setTimeout(() => this.map.invalidateSize(), 50);
  }

  // Chaque étape redessine ce dont elle a besoin : on repart d'une carte propre.
  reset() { Object.values(this.groups).forEach((g) => g.clearLayers()); }

  onClick(fn) { this.clickHandler = fn; }
  setCursor(c) { this.map.getContainer().style.cursor = c || ''; }
  showCadastre(on) { on ? this.cadastre.addTo(this.map) : this.map.removeLayer(this.cadastre); }

  focus(lat, lon, zoom = 19) { this.map.invalidateSize(); this.map.setView([lat, lon], zoom); }

  showAddress(lat, lon) {
    this.groups.address.clearLayers();
    L.circleMarker([lat, lon], { radius: 6, color: '#fff', weight: 2, fillColor: COLORS.orange, fillOpacity: 1 })
      .addTo(this.groups.address);
  }

  showParcel(parcel) {
    this.groups.parcel.clearLayers();
    if (!parcel?.ring) return;
    L.polygon(parcel.ring.map(ll), { color: '#fff', weight: 2, dashArray: '6 6', fillOpacity: 0.05, interactive: false })
      .addTo(this.groups.parcel);
  }

  showBuildings(buildings, selectedId, onSelect) {
    this.groups.buildings.clearLayers();
    buildings.forEach((b) => {
      const sel = b.id === selectedId;
      const poly = L.polygon(b.ring.map(ll), {
        color: sel ? COLORS.orange : '#ffffff',
        weight: sel ? 3 : 1.5,
        fillColor: sel ? COLORS.orange : '#ffffff',
        fillOpacity: sel ? 0.25 : 0.12,
      }).addTo(this.groups.buildings);
      if (onSelect) poly.on('click', (e) => { L.DomEvent.stopPropagation(e); onSelect(b); });
    });
  }

  showFacades(facades, highlight = [], onlyHighlight = false) {
    this.groups.facades.clearLayers();
    facades.forEach((f) => {
      const hot = highlight.includes(f.index);
      if (onlyHighlight && !hot) return;
      L.polyline([ll(f.a), ll(f.b)], { color: hot ? COLORS.orange : '#fff', weight: hot ? 6 : 3, interactive: false })
        .addTo(this.groups.facades);
    });
  }

  // Cadre la carte sur la maison (et le point de prise de vue s'il est connu). Appelé une seule fois par étape.
  fitTo(ring, maxZoom = 20, extra = null) {
    this.map.invalidateSize();
    if (!ring?.length) return;
    const pts = ring.map(ll);
    if (extra) pts.push(ll(extra));
    this.map.fitBounds(L.latLngBounds(pts).pad(extra ? 0.35 : 1.2), { maxZoom, animate: false });
    requestAnimationFrame(() => this.map.invalidateSize());
  }

  // Point de vue : la miniature de la photo à l'endroit de la prise de vue, et le cône si la direction est connue.
  setViewpoint(origin, bearing, thumbUrl) {
    this.groups.draft.clearLayers();
    if (bearing != null) {
      L.polygon(conePolygon(origin, bearing, 60, 18).map(ll), {
        color: COLORS.orange, weight: 2, fillColor: COLORS.orange, fillOpacity: 0.3, interactive: false,
      }).addTo(this.groups.draft);
    }
    L.marker(ll(origin), {
      interactive: false, zIndexOffset: 1000,
      icon: L.divIcon({ className: 'person-pin', iconSize: [40, 40], iconAnchor: [20, 20], html: PERSON_SVG }),
    }).addTo(this.groups.draft);
  }

  showCones(photos, activeIndex = -1) {
    this.groups.cones.clearLayers();
    photos.forEach((p, i) => {
      if (!p.view?.origin || p.view.bearing == null) return;
      const active = i === activeIndex;
      L.polygon(conePolygon(p.view.origin, p.view.bearing).map(ll), {
        color: active ? COLORS.orange : '#fff', weight: 2,
        fillColor: active ? COLORS.orange : '#fff', fillOpacity: active ? 0.25 : 0.1, interactive: false,
      }).addTo(this.groups.cones);
      L.marker(ll(p.view.origin), {
        interactive: false,
        icon: L.divIcon({ className: 'cone-pin', html: String(i + 1), iconSize: [26, 26] }),
      }).addTo(this.groups.cones);
    });
  }

  // Cône modifiable au doigt : on déplace l'œil pour changer la position, la pointe pour
  // changer la direction. onChange(origin, bearing) est appelé à chaque relâchement.
  editCone(origin, bearing, onChange, thumbUrl) {
    this.groups.draft.clearLayers();
    const reach = 16;
    const tipOf = (o, b) => {
      const P = makeProjection(o[1], o[0]);
      const t = (b * Math.PI) / 180;
      return P.toLonLat([Math.sin(t) * reach, Math.cos(t) * reach]);
    };
    let o = origin, b = bearing;
    const cone = L.polygon(conePolygon(o, b, 70, reach).map(ll), {
      color: COLORS.orange, weight: 2, fillColor: COLORS.orange, fillOpacity: 0.25, interactive: false,
    }).addTo(this.groups.draft);
    const eye = L.marker(ll(o), {
      draggable: true, autoPan: true, zIndexOffset: 1000,
      icon: L.divIcon({
        className: 'eye-handle', iconSize: [44, 44], iconAnchor: [22, 22],
        html: thumbUrl ? `<img src="${thumbUrl}" alt="">` : '<span></span>',
      }),
      title: 'Faites glisser pour indiquer où vous étiez',
    }).addTo(this.groups.draft);
    const tip = L.marker(ll(tipOf(o, b)), {
      draggable: true, autoPan: true, zIndexOffset: 1001,
      icon: L.divIcon({ className: 'tip-handle', iconSize: [32, 32], iconAnchor: [16, 16], html: '<span></span>' }),
      title: 'Faites glisser pour indiquer la direction',
    }).addTo(this.groups.draft);
    const redraw = () => cone.setLatLngs(conePolygon(o, b, 70, reach).map(ll));
    eye.on('drag', (e) => {
      o = [e.latlng.lng, e.latlng.lat];
      tip.setLatLng(ll(tipOf(o, b)));
      redraw();
    });
    tip.on('drag', (e) => {
      b = bearingDeg(o, [e.latlng.lng, e.latlng.lat]);
      redraw();
    });
    // La pointe revient à distance fixe une fois lâchée, pour rester facile à attraper.
    tip.on('dragend', () => { tip.setLatLng(ll(tipOf(o, b))); onChange(o, b); });
    eye.on('dragend', () => onChange(o, b));
    onChange(o, b);
  }

  // Cône en cours de placement : position fixée, direction suit le pointeur.
  previewCone(origin, target) {
    this.groups.draft.clearLayers();
    L.circleMarker(ll(origin), { radius: 7, color: '#fff', weight: 2, fillColor: COLORS.orange, fillOpacity: 1 })
      .addTo(this.groups.draft);
    if (target) {
      L.polygon(conePolygon(origin, bearingDeg(origin, target)).map(ll), {
        color: COLORS.orange, weight: 2, fillOpacity: 0.2, interactive: false, dashArray: '4 4',
      }).addTo(this.groups.draft);
    }
  }

  onMove(fn) {
    if (this._moveFn) this.map.off('mousemove', this._moveFn);
    this._moveFn = fn ? (e) => fn([e.latlng.lng, e.latlng.lat]) : null;
    if (this._moveFn) this.map.on('mousemove', this._moveFn);
  }

  clearDraft() { this.groups.draft.clearLayers(); }

  showPlacements(placements, labels) {
    this.groups.placements.clearLayers();
    placements.forEach((p) => {
      const style = { color: COLORS.orange, weight: 3, fillColor: COLORS.orange, fillOpacity: 0.3, interactive: false };
      if (p.ring) L.polygon(p.ring.map(ll), style).addTo(this.groups.placements);
      if (p.line) L.polyline(p.line.map(ll), { ...style, weight: 5 }).addTo(this.groups.placements);
      const anchor = p.ring ? p.ring[0] : p.line?.[0];
      if (anchor) {
        L.marker(ll(anchor), {
          interactive: false,
          icon: L.divIcon({ className: 'placement-label', html: `<span>${labels[p.productId] || p.productId}</span>`, iconSize: null }),
        }).addTo(this.groups.placements);
      }
    });
  }

  draftLine(points, cursor) {
    this.groups.draft.clearLayers();
    const pts = cursor ? [...points, cursor] : points;
    pts.forEach((pt, i) => {
      if (i < points.length) {
        L.circleMarker(ll(pt), { radius: 5, color: '#fff', weight: 2, fillColor: COLORS.orange, fillOpacity: 1, interactive: false })
          .addTo(this.groups.draft);
      }
    });
    if (pts.length > 1) {
      L.polyline(pts.map(ll), { color: COLORS.orange, weight: 4, dashArray: '6 6', interactive: false }).addTo(this.groups.draft);
      L.marker(ll(pts[pts.length - 1]), {
        interactive: false,
        icon: L.divIcon({ className: 'facade-label is-hot', html: `<span>${fmt(polylineLength(pts))}</span>`, iconSize: null }),
      }).addTo(this.groups.draft);
    }
  }

  draftRect(a, b, depth, side) {
    this.groups.draft.clearLayers();
    const r = rectFromSide(a, b, depth, side);
    L.polygon(r.ring.map(ll), { color: COLORS.orange, weight: 3, dashArray: '6 6', fillOpacity: 0.25, interactive: false })
      .addTo(this.groups.draft);
    L.marker(ll(r.ring[1]), {
      interactive: false,
      icon: L.divIcon({ className: 'facade-label is-hot', html: `<span>${fmt(r.width)} × ${fmt(depth)}</span>`, iconSize: null }),
    }).addTo(this.groups.draft);
    return r;
  }
}

// Côté du rectangle : on le pose hors du bâtiment quand il est accolé à une façade.
export function outwardSide(a, b, buildingRing) {
  if (!buildingRing) return 1;
  const probe = rectFromSide(a, b, 1, 1).ring;
  const cx = (probe[0][0] + probe[1][0] + probe[2][0] + probe[3][0]) / 4;
  const cy = (probe[0][1] + probe[1][1] + probe[2][1] + probe[3][1]) / 4;
  return pointInRing([cx, cy], buildingRing) ? -1 : 1;
}

export { snapToFacades };
