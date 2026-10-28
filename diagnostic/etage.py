# Diagnostic d'une terrasse ou d'un balcon en étage (appartement) : soleil et vis-à-vis à la hauteur de la terrasse.
# Usage : python3 etage.py projet.json sortie_dossier       (projet.json : address, building, lieu = {type: appartement, etage: n})
# On ne sait pas sur quelle façade donne la terrasse : on calcule chaque côté de l'immeuble (nord, est, sud, ouest) ;
# le dernier étage est traité comme un toit-terrasse (ouvert de tous les côtés).
import sys, json, math, os, time, urllib.request
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity

P = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
lat0, lon0 = P['address']['lat'], P['address']['lon']
KX, KY = 111320 * math.cos(math.radians(lat0)), 110540
loc = lambda lon, lat: ((lon - lon0) * KX, (lat - lat0) * KY)
ETAGE = max(1, int((P.get('lieu') or {}).get('etage') or 1))
NOMS = ['nord', 'est', 'sud', 'ouest']


def get(url):
    for k in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r: return json.load(r)
        except Exception:
            if k == 2: raise
            time.sleep(2 + 3 * k)


def soleil(jour, heure_legale, tz=2):
    g = 2 * math.pi / 365 * (jour - 1 + (heure_legale - 12) / 24)
    decl = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = heure_legale * 60 + eqt + 4 * lon0 - 60 * tz
    ha = math.radians(tst / 4 - 180); la = math.radians(lat0)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    el = math.degrees(math.asin(max(-1, min(1, cz))))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la))) + 180
    return el, az


maison = Polygon([loc(*p[:2]) for p in P['building']['ring']]).buffer(0)
h_imm = float(P['building'].get('height') or 3 * (P['building'].get('floors') or 4))
etages = int(P['building'].get('floors') or max(1, round(h_imm / 3)))
haut_etage = h_imm / max(1, etages)
Z = ETAGE * haut_etage + 1.2                                # œil d'une personne assise sur la terrasse, depuis le sol
toit = ETAGE >= etages                                      # dernier étage : toit-terrasse probable

# bâtiments voisins (BD TOPO), relief compris
c = maison.centroid; dlat, dlon = 80 / KY, 80 / KX; clat, clon = lat0 + c.y / KY, lon0 + c.x / KX
url = ('https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:batiment&OUTPUTFORMAT=application/json&COUNT=500&SRSNAME=EPSG:4326'
       f'&BBOX={clat-dlat},{clon-dlon},{clat+dlat},{clon+dlon},urn:ogc:def:crs:EPSG::4326')
bats = []
for f in get(url)['features']:
    for poly in f['geometry']['coordinates']:
        pg = Polygon([loc(x, y) for x, y, *_ in poly[0]]).buffer(0)
        if pg.area < 4: continue
        pr = f['properties']; a0, a1 = pr.get('altitude_minimale_sol'), pr.get('altitude_maximale_sol')
        bats.append({'g': pg, 'h': pr.get('hauteur') or 3.5, 'sol': (a0 + a1) / 2 if a0 is not None and a1 is not None else a0})
for b in bats: b['client'] = b['g'].intersection(maison).area > 0.5 * min(b['g'].area, maison.area)
_cl = [b['sol'] for b in bats if b['client'] and b['sol'] is not None]
niv = _cl[0] if _cl else None
for b in bats:
    dz = (b['sol'] - niv) if (niv is not None and b['sol'] is not None and not b['client']) else 0.0
    b['he'] = max(0.0, b['h'] + max(-15.0, min(15.0, dz)))
autres = [b for b in bats if not b['client']]

# points d'observation : 1 m devant chaque façade, par côté
ring = list(maison.exterior.coords); aire = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))
cotes = {k: [] for k in range(4)}
for a, b in zip(ring, ring[1:]):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    if L < 2: continue
    nx, ny = (dy / L, -dx / L) if aire > 0 else (-dy / L, dx / L)               # normale extérieure
    az = (math.degrees(math.atan2(nx, ny)) + 360) % 360; k = int(((az + 45) % 360) // 90)
    for t in np.arange(0.5, L, 1.5):
        q = (a[0] + dx * t / L + nx, a[1] + dy * t / L + ny)
        if any(b['g'].contains(Point(q)) for b in autres): continue          # mur mitoyen : pas de fenêtre ni de balcon
        cotes[k].append((q, (nx, ny)))


def ombre_a(el, az):
    # ombre portée par les voisins plus hauts que la terrasse, sur le plan horizontal à la hauteur de l'œil
    if el <= 2: return None
    Lr = 1 / math.tan(math.radians(el)); sx, sy = -math.sin(math.radians(az)), -math.cos(math.radians(az))
    out = []
    for b in autres:
        hr = b['he'] - Z
        if hr <= 0.2: continue
        t = affinity.translate(b['g'], sx * Lr * hr, sy * Lr * hr)
        out.append(unary_union([b['g'], t, b['g'].union(t).convex_hull]))
    return unary_union(out) if out else Polygon()


def heures(jour, h0=8, h1=21):
    res = {k: np.zeros(len(v)) for k, v in cotes.items()}; apm = {k: np.zeros(len(v)) for k, v in cotes.items()}; prof = {k: [] for k in cotes}
    for hq in np.arange(h0, h1, 0.5):
        el, az = soleil(jour, hq); o = ombre_a(el, az)
        sx, sy = math.sin(math.radians(az)), math.cos(math.radians(az))
        for k, L in cotes.items():
            if not L: continue
            s = np.array([0.5 if (o is not None and (toit or nx * sx + ny * sy > 0.05) and not o.contains(Point(p))) else 0.0 for p, (nx, ny) in L])
            res[k] += s; prof[k].append(round(float(s.mean() * 2), 2))
            if hq >= 14: apm[k] += s
    return res, apm, prof


ete, ete_apm, prof = heures(172); mi, _, _ = heures(265)
COTES = {NOMS[k]: {'soleil_ete_h': round(float(ete[k].mean()), 1), 'soleil_ete_apres14h_h': round(float(ete_apm[k].mean()), 1), 'soleil_equinoxe_h': round(float(mi[k].mean()), 1)}
         for k in range(4) if len(cotes[k]) >= 2}
# côté retenu pour le conseil : le plus ensoleillé à mi-saison (une terrasse donne en général sur le côté dégagé)
best = max(COTES, key=lambda n: (COTES[n]['soleil_equinoxe_h'], COTES[n]['soleil_ete_h'])) if COTES else 'sud'
kb = NOMS.index(best)

# vis-à-vis : voisins à moins de 30 m dont les fenêtres sont au moins à la hauteur de la terrasse
vav = []
for b in autres:
    d = b['g'].distance(maison)
    if d > 30 or d < 2 or b['he'] < Z: continue             # un immeuble mitoyen ne voit pas la terrasse
    pb = np.array(b['g'].centroid.coords[0]); pm = np.array(maison.centroid.coords[0])
    oeil = b['he'] - 1.5 - (Z - 1.2)                         # hauteur des fenêtres voisines au-dessus de votre terrasse
    if oeil < 1: continue
    vav.append({'distance_m': round(d, 1), 'hauteur_m': round(b['h'], 1), 'denivele_m': 0.0, 'oeil_m': round(max(0.0, oeil), 1), 'au_dessus_m': round(max(0.0, oeil), 1),
                'direction': ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ouest', 'ouest', 'nord-ouest'][int(((math.degrees(math.atan2(pb[0] - pm[0], pb[1] - pm[1])) + 360 + 22.5) % 360) // 45)],
                'centre': list(pb)})
vav.sort(key=lambda v: v['distance_m'])
diag = {'mode': 'etage', 'etage': ETAGE, 'etages_immeuble': etages, 'toit_terrasse': toit, 'hauteur_terrasse_m': round(Z - 1.2, 1),
        'soleil_ete_h_moyen': COTES.get(best, {}).get('soleil_ete_h'), 'soleil_ete_apres14h_h': COTES.get(best, {}).get('soleil_ete_apres14h_h'),
        'soleil_equinoxe_h': COTES.get(best, {}).get('soleil_equinoxe_h'), 'soleil_ete_profil_8h_21h': prof.get(kb),
        'cote_jardin': best, 'zone_maison': dict(COTES.get(best, {}), cote=best), 'cotes_maison': COTES, 'vis_a_vis': vav[:5]}
json.dump(diag, open(f'{OUT}/diagnostic.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in diag.items() if k != 'soleil_ete_profil_8h_21h'}, ensure_ascii=False))
