// Accès aux données IGN / cadastre et calculs géométriques (mètres, orientations).
import { ENDPOINTS } from './config.js';

// ---------- Géocodage ----------

function toAddress(f) {
  const p = f.properties || {};
  const [lon, lat] = f.geometry.coordinates;
  return { label: p.label, city: p.city, postcode: p.postcode, citycode: p.citycode, lat, lon, score: p.score };
}

export async function geocode(query, { signal } = {}) {
  const q = encodeURIComponent(query.trim());
  if (q.length < 3) return [];
  const urls = [
    `${ENDPOINTS.geocode}?q=${q}&limit=5&index=address&autocomplete=1`,
    `${ENDPOINTS.geocodeFallback}?q=${q}&limit=5&autocomplete=1`,
  ];
  for (const url of urls) {
    try {
      const r = await fetch(url, { signal });
      if (!r.ok) continue;
      const data = await r.json();
      if (data && Array.isArray(data.features)) return data.features.map(toAddress);
    } catch (e) {
      if (e.name === 'AbortError') throw e;
    }
  }
  throw new Error('geocode_unavailable');
}

export async function reverseGeocode(lat, lon) {
  const urls = [
    `${ENDPOINTS.geocode.replace('/search', '/reverse')}?lat=${lat}&lon=${lon}&limit=1&index=address`,
    `${ENDPOINTS.geocodeFallback.replace('/search/', '/reverse/')}?lat=${lat}&lon=${lon}&limit=1`,
  ];
  for (const url of urls) {
    try {
      const r = await fetch(url);
      if (!r.ok) continue;
      const data = await r.json();
      const f = data?.features?.[0];
      if (f) return toAddress(f);
    } catch (e) { /* service suivant */ }
  }
  return null;
}

// ---------- Projection locale (mètres) ----------
// Équirectangulaire autour d'un point de référence : largement suffisant à l'échelle d'un jardin.

export function makeProjection(lat0, lon0) {
  const kx = 111320 * Math.cos((lat0 * Math.PI) / 180);
  const ky = 110574;
  return {
    toXY: ([lon, lat]) => [(lon - lon0) * kx, (lat - lat0) * ky],
    toLonLat: ([x, y]) => [lon0 + x / kx, lat0 + y / ky],
  };
}

// France métropolitaine : latitudes 41-51, longitudes -5 à 10. Les plages ne se recouvrent
// pas, ce qui permet de corriger un ordre d'axes inversé renvoyé par un service.
function fixOrder(c) {
  return c[0] > 30 && c[1] < 15 ? [c[1], c[0]] : c;
}

function normalizeRing(ring) {
  return ring.map(fixOrder);
}

function outerRings(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Polygon') return [normalizeRing(geometry.coordinates[0])];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.map((p) => normalizeRing(p[0]));
  return [];
}

export function pointInRing([x, y], ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function ringCentroid(ring) {
  let sx = 0, sy = 0;
  const n = ring.length - 1;
  for (let i = 0; i < n; i++) { sx += ring[i][0]; sy += ring[i][1]; }
  return [sx / n, sy / n];
}

export function ringAreaM2(ring) {
  const [lon0, lat0] = ringCentroid(ring);
  const P = makeProjection(lat0, lon0);
  const pts = ring.map(P.toXY);
  let a = 0;
  for (let i = 0; i < pts.length - 1; i++) a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1];
  return Math.abs(a) / 2;
}

// ---------- Bâtiments BD TOPO ----------

async function wfsBuildings(lat, lon, radiusM, latFirst) {
  const dLat = radiusM / 110574;
  const dLon = radiusM / (111320 * Math.cos((lat * Math.PI) / 180));
  const bbox = latFirst
    ? `${lat - dLat},${lon - dLon},${lat + dLat},${lon + dLon},urn:ogc:def:crs:EPSG::4326`
    : `${lon - dLon},${lat - dLat},${lon + dLon},${lat + dLat},EPSG:4326`;
  const params = new URLSearchParams({
    SERVICE: 'WFS', VERSION: '2.0.0', REQUEST: 'GetFeature',
    TYPENAMES: ENDPOINTS.buildingLayer, OUTPUTFORMAT: 'application/json',
    SRSNAME: 'EPSG:4326', COUNT: '60', BBOX: bbox,
  });
  const r = await fetch(`${ENDPOINTS.wfs}?${params}`);
  if (!r.ok) throw new Error(`wfs_${r.status}`);
  const data = await r.json();
  return data.features || [];
}

// Renvoie les bâtiments autour du point, chacun avec son anneau extérieur en [lon, lat].
export async function fetchBuildings(lat, lon, radiusM = 60) {
  let feats = [];
  try { feats = await wfsBuildings(lat, lon, radiusM, true); } catch (e) { feats = []; }
  if (!feats.length) feats = await wfsBuildings(lat, lon, radiusM, false);
  const out = [];
  feats.forEach((f, i) => {
    outerRings(f.geometry).forEach((ring, k) => {
      const p = f.properties || {};
      out.push({
        id: `${f.id || i}-${k}`,
        ring,
        height: typeof p.hauteur === 'number' ? p.hauteur : null,
        floors: p.nombre_d_etages ?? null,
        usage: p.usage_1 || null,
      });
    });
  });
  return out;
}

// ---------- Parcelle cadastrale ----------

export async function fetchParcel(lat, lon) {
  const geom = encodeURIComponent(JSON.stringify({ type: 'Point', coordinates: [lon, lat] }));
  const r = await fetch(`${ENDPOINTS.parcel}?geom=${geom}`);
  if (!r.ok) throw new Error(`parcel_${r.status}`);
  const data = await r.json();
  const f = (data.features || [])[0];
  if (!f) return null;
  const rings = outerRings(f.geometry);
  const p = f.properties || {};
  return {
    ring: rings[0],
    area: p.contenance || (rings[0] ? Math.round(ringAreaM2(rings[0])) : null),
    ref: [p.code_insee, p.section, p.numero].filter(Boolean).join(' '),
  };
}

// ---------- Façades ----------

const COMPASS = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ouest', 'ouest', 'nord-ouest'];
export function compassLabel(deg) {
  return COMPASS[Math.round((((deg % 360) + 360) % 360) / 45) % 8];
}

// Découpe l'emprise en façades : arêtes consécutives presque alignées fusionnées,
// très petits décrochés ignorés. Chaque façade a sa longueur et l'orientation de sa
// normale extérieure (azimut depuis le nord, sens horaire).
export function facadesOf(ring, { mergeAngle = 12, minLength = 1.2 } = {}) {
  const [lon0, lat0] = ringCentroid(ring);
  const P = makeProjection(lat0, lon0);
  let pts = ring.map(P.toXY);
  if (pts.length > 1) {
    const [a, b] = [pts[0], pts[pts.length - 1]];
    if (a[0] !== b[0] || a[1] !== b[1]) pts.push(a);
  }
  let area2 = 0;
  for (let i = 0; i < pts.length - 1; i++) area2 += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1];
  const ccw = area2 > 0;

  const edges = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[i + 1];
    const len = Math.hypot(x2 - x1, y2 - y1);
    if (len < 0.05) continue;
    edges.push({ a: [x1, y1], b: [x2, y2], dir: Math.atan2(y2 - y1, x2 - x1) });
  }
  // Fusion des arêtes presque colinéaires
  const merged = [];
  for (const e of edges) {
    const last = merged[merged.length - 1];
    if (last) {
      let d = Math.abs(e.dir - last.dir);
      if (d > Math.PI) d = 2 * Math.PI - d;
      if ((d * 180) / Math.PI < mergeAngle) {
        last.b = e.b;
        last.dir = Math.atan2(last.b[1] - last.a[1], last.b[0] - last.a[0]);
        continue;
      }
    }
    merged.push({ ...e });
  }
  if (merged.length > 2) {
    const f = merged[0], l = merged[merged.length - 1];
    let d = Math.abs(f.dir - l.dir);
    if (d > Math.PI) d = 2 * Math.PI - d;
    if ((d * 180) / Math.PI < mergeAngle) {
      f.a = l.a;
      f.dir = Math.atan2(f.b[1] - f.a[1], f.b[0] - f.a[0]);
      merged.pop();
    }
  }

  return merged
    .map((e, i) => {
      const dx = e.b[0] - e.a[0], dy = e.b[1] - e.a[1];
      const length = Math.hypot(dx, dy);
      // Normale extérieure : à droite de l'arête si l'anneau tourne dans le sens trigonométrique
      const nx = ccw ? dy : -dy, ny = ccw ? -dx : dx;
      const azimuth = ((Math.atan2(nx, ny) * 180) / Math.PI + 360) % 360;
      return {
        index: i,
        length,
        azimuth,
        facing: compassLabel(azimuth),
        a: P.toLonLat(e.a),
        b: P.toLonLat(e.b),
        mid: P.toLonLat([(e.a[0] + e.b[0]) / 2, (e.a[1] + e.b[1]) / 2]),
      };
    })
    .filter((f) => f.length >= minLength);
}

// ---------- Cône de vue ----------

export function bearingDeg(from, to) {
  const P = makeProjection(from[1], from[0]);
  const [x, y] = P.toXY(to);
  return ((Math.atan2(x, y) * 180) / Math.PI + 360) % 360;
}

export function distanceM(a, b) {
  const P = makeProjection(a[1], a[0]);
  const [x, y] = P.toXY(b);
  return Math.hypot(x, y);
}

// Secteur angulaire en [lon, lat] pour l'affichage du cône.
export function conePolygon(origin, bearing, fov = 70, radius = 25) {
  const P = makeProjection(origin[1], origin[0]);
  const pts = [origin];
  for (let k = 0; k <= 16; k++) {
    const t = ((bearing - fov / 2 + (fov * k) / 16) * Math.PI) / 180;
    pts.push(P.toLonLat([Math.sin(t) * radius, Math.cos(t) * radius]));
  }
  pts.push(origin);
  return pts;
}

// Façades vues depuis la position de prise de vue : milieu dans le champ, et façade
// tournée vers le photographe. Triées de la plus visible à la moins visible.
export function visibleFacades(facades, origin, bearing, fov = 70, maxDist = 60) {
  return facades
    .map((f) => {
      const b = bearingDeg(origin, f.mid);
      let off = Math.abs(b - bearing);
      if (off > 180) off = 360 - off;
      const dist = distanceM(origin, f.mid);
      // La façade regarde vers le photographe si sa normale pointe à l'opposé du regard
      let facingOff = Math.abs(((f.azimuth + 180) % 360) - b);
      if (facingOff > 180) facingOff = 360 - facingOff;
      return { ...f, off, dist, facingOff };
    })
    .filter((f) => f.off <= fov / 2 + 5 && f.dist <= maxDist && f.facingOff < 80)
    .sort((x, y) => x.off - y.off || y.length - x.length);
}

// ---------- Placement : rectangle orienté à partir d'un côté et d'une profondeur ----------

export function rectFromSide(a, b, depth, side = 1) {
  const P = makeProjection(a[1], a[0]);
  const A = P.toXY(a), B = P.toXY(b);
  const dx = B[0] - A[0], dy = B[1] - A[1];
  const L = Math.hypot(dx, dy) || 1;
  const nx = (-dy / L) * depth * side, ny = (dx / L) * depth * side;
  const C = [B[0] + nx, B[1] + ny], D = [A[0] + nx, A[1] + ny];
  return { ring: [A, B, C, D, A].map(P.toLonLat), width: L, depth };
}

export function polylineLength(points) {
  let L = 0;
  for (let i = 1; i < points.length; i++) L += distanceM(points[i - 1], points[i]);
  return L;
}

// Projette un point sur la façade la plus proche si elle est à moins de `tol` mètres.
export function snapToFacades(point, facades, tol = 2) {
  let best = null;
  for (const f of facades) {
    const P = makeProjection(point[1], point[0]);
    const A = P.toXY(f.a), B = P.toXY(f.b);
    const dx = B[0] - A[0], dy = B[1] - A[1];
    const L2 = dx * dx + dy * dy || 1;
    let t = (-A[0] * dx - A[1] * dy) / L2;
    t = Math.max(0, Math.min(1, t));
    const S = [A[0] + t * dx, A[1] + t * dy];
    const d = Math.hypot(S[0], S[1]);
    if (d <= tol && (!best || d < best.d)) best = { d, point: P.toLonLat(S), facade: f };
  }
  return best;
}
