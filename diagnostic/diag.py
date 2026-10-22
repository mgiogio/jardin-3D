# Diagnostic automatique d'un jardin à partir de l'adresse (données publiques IGN, cadastre, Géoportail de l'urbanisme).
# Usage : python3 diag.py projet-jardin.json sortie_dossier
# Sorties : diagnostic.json (chiffres) et plan.png (vue de dessus : soleil d'été heure par heure, vis-à-vis).
import sys, json, math, os, urllib.request, urllib.parse
import numpy as np
from shapely.geometry import shape, Polygon, Point, LineString, mapping
from shapely.ops import unary_union
from shapely import affinity
from PIL import Image, ImageDraw, ImageFont

P = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
lat0, lon0 = P['address']['lat'], P['address']['lon']
KX, KY = 111320 * math.cos(math.radians(lat0)), 110540
loc = lambda lon, lat: ((lon - lon0) * KX, (lat - lat0) * KY)          # mètres, x = est, y = nord
def get(url):
    with urllib.request.urlopen(url, timeout=40) as r: return json.load(r)

parcelle = Polygon([loc(*p[:2]) for p in P['parcel']['ring']])
maison = Polygon([loc(*p[:2]) for p in P['building']['ring']])
h_maison = P['building'].get('height') or 6
c = parcelle.centroid
# bâtiments autour (BD TOPO) : 60 m
dlat, dlon = 60 / KY, 60 / KX; clat, clon = lat0 + c.y / KY, lon0 + c.x / KX
url = ('https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:batiment&OUTPUTFORMAT=application/json&COUNT=400&SRSNAME=EPSG:4326'
       f'&BBOX={clat-dlat},{clon-dlon},{clat+dlat},{clon+dlon},urn:ogc:def:crs:EPSG::4326')
bats = []
for f in get(url)['features']:
    g = shape(f['geometry']); g = affinity.affine_transform(g, [KX, 0, 0, KY, -lon0 * KX, -lat0 * KY]) if False else None
    polys = f['geometry']['coordinates']
    for poly in polys:
        pg = Polygon([loc(x, y) for x, y, *_ in poly[0]])
        if pg.area < 4: continue
        bats.append({'g': pg, 'h': f['properties'].get('hauteur') or 3.5, 'etages': f['properties'].get('nombre_d_etages'), 'usage': f['properties'].get('usage_1')})
# la maison du client = bâtiment qui recouvre le plus son emprise
for b in bats: b['client'] = b['g'].intersection(maison).area > 0.5 * min(b['g'].area, maison.area)
jardin = parcelle.difference(unary_union([b['g'] for b in bats if b['client']] + [maison]).buffer(0.3))

# ---- soleil (formule NOAA simplifiée), heure solaire locale ----
def soleil(jour, heure_legale, tz=2):
    g = 2 * math.pi / 365 * (jour - 1 + (heure_legale - 12) / 24)
    decl = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = heure_legale * 60 + eqt + 4 * lon0 - 60 * tz
    ha = math.radians(tst / 4 - 180); la = math.radians(lat0)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    el = math.degrees(math.asin(max(-1, min(1, cz))))
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la))) + 180
    return el, az                     # az : 0 = nord, 90 = est
def ombres(el, az):
    if el <= 2: return None
    L = 1 / math.tan(math.radians(el)); dx, dy = -math.sin(math.radians(az)), -math.cos(math.radians(az))
    out = []
    for b in bats:
        t = affinity.translate(b['g'], dx * L * b['h'], dy * L * b['h'])
        out.append(unary_union([b['g'], t]).convex_hull if b['g'].convex_hull.area / b['g'].area < 1.3 else unary_union([b['g'], t, b['g'].union(t).convex_hull.intersection(b['g'].buffer(L * b['h'] + 1))]))
    return unary_union(out)
# grille du jardin (0,5 m)
minx, miny, maxx, maxy = jardin.bounds; pas = 0.5
pts = [(x, y) for x in np.arange(minx + pas / 2, maxx, pas) for y in np.arange(miny + pas / 2, maxy, pas) if jardin.contains(Point(x, y))]
def heures_soleil(jour, h0=8, h1=21):
    n = np.zeros(len(pts)); apm = np.zeros(len(pts))
    for hq in np.arange(h0, h1, 0.5):
        el, az = soleil(jour, hq); o = ombres(el, az)
        if o is None: continue
        s = np.array([not o.contains(Point(p)) for p in pts]) * 0.5
        n += s
        if hq >= 14: apm += s
    return n, apm
ete, ete_apm = heures_soleil(172)          # 21 juin
mi, _ = heures_soleil(265)                  # 22 septembre
# ---- vis-à-vis : étages voisins qui plongent sur le jardin ----
vav = []
for b in bats:
    if b['client'] or b['h'] < 4.5: continue
    d = b['g'].distance(jardin)
    if d > 25: continue
    # œil à l'étage : hauteur du bâtiment - 1,5 m ; personne assise à 1,2 m au point du jardin le plus proche
    pj, pb = [np.array(p.coords[0]) for p in __import__('shapely.ops', fromlist=['x']).nearest_points(jardin, b['g'])]
    oeil = b['h'] - 1.5
    limite = parcelle.exterior.distance(Point(pb)) if not parcelle.contains(Point(pb)) else 0
    # hauteur d'écran nécessaire en limite de terrain pour couper la vue vers une personne assise à 2 m dans le jardin
    D = max(d + 2, 0.5); dl = min(max(d - 0.0, 0.1), D)
    besoin = 1.2 + (oeil - 1.2) * (D - dl) / D if D > 0 else oeil
    vav.append({'distance_m': round(d, 1), 'hauteur_m': b['h'], 'oeil_m': round(oeil, 1), 'ecran_necessaire_m': round(besoin, 2),
                'direction': ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ouest', 'ouest', 'nord-ouest'][int(((math.degrees(math.atan2(pb[0] - pj[0], pb[1] - pj[1])) + 360 + 22.5) % 360) // 45)],
                'centre': list(b['g'].centroid.coords[0])})
vav.sort(key=lambda v: v['distance_m'])
# ---- urbanisme (Géoportail de l'urbanisme) ----
geom = urllib.parse.quote(json.dumps({'type': 'Point', 'coordinates': [lon0, lat0]}))
urba = {'zone': None, 'servitudes': []}
try:
    z = get(f'https://apicarto.ign.fr/api/gpu/zone-urba?geom={geom}')['features']
    if z: urba['zone'] = z[0]['properties'].get('libelong') or z[0]['properties'].get('libelle'); urba['document'] = z[0]['properties'].get('partition')
    for t in ('assiette-sup-s', 'assiette-sup-l', 'assiette-sup-p'):
        for f in get(f'https://apicarto.ign.fr/api/gpu/{t}?geom={geom}').get('features', []):
            urba['servitudes'].append({'type': f['properties'].get('suptype'), 'nom': f['properties'].get('nomsuplitt') or f['properties'].get('nomass')})
except Exception as e: urba['erreur'] = str(e)
# ---- linéaire de limites de terrain non bâties (clôture possible) ----
lim = parcelle.exterior.difference(unary_union([b['g'] for b in bats]).buffer(0.4))
diag = {'surface_parcelle_m2': round(parcelle.area), 'surface_jardin_m2': round(jardin.area), 'hauteur_maison_m': h_maison,
        'soleil_ete_h_moyen': round(float(ete.mean()), 1), 'soleil_ete_apres14h_h': round(float(ete_apm.mean()), 1),
        'part_jardin_plus_6h_ete': round(float((ete >= 6).mean()) * 100), 'soleil_equinoxe_h': round(float(mi.mean()), 1),
        'vis_a_vis': vav[:5], 'urbanisme': urba, 'lineaire_limites_libres_m': round(lim.length, 1)}
json.dump(diag, open(f'{OUT}/diagnostic.json', 'w'), ensure_ascii=False, indent=1)
# ---- plan ----
S = 22; marge = 18
bx = unary_union([parcelle] + [b['g'] for b in bats if b['g'].distance(parcelle) < 18]).bounds
W, H = int((bx[2] - bx[0] + 2 * marge / S * 0) * S + 2 * marge), int((bx[3] - bx[1]) * S + 2 * marge)
im = Image.new('RGB', (W, H), (246, 244, 238)); d = ImageDraw.Draw(im)
T = lambda x, y: (marge + (x - bx[0]) * S, H - marge - (y - bx[1]) * S)
cmap = lambda h: tuple(int(a + (b - a) * min(1, h / 12)) for a, b in zip((90, 110, 160), (250, 170, 40)))
for (x, y), h in zip(pts, ete):
    X, Y = T(x - pas / 2, y + pas / 2); d.rectangle([X, Y, X + pas * S, Y + pas * S], fill=cmap(h))
for b in bats:
    if b['g'].distance(parcelle) > 18: continue
    d.polygon([T(*p) for p in b['g'].exterior.coords], fill=(120, 120, 120) if not b['client'] else (70, 70, 70), outline=(60, 60, 60))
    X, Y = T(*b['g'].centroid.coords[0]); d.text((X - 10, Y - 6), f"{b['h']:.0f} m", fill='white')
d.line([T(*p) for p in parcelle.exterior.coords], fill=(20, 110, 60), width=3)
for v in vav[:3]:
    a = T(*v['centre']); d.ellipse([a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6], outline=(200, 30, 30), width=3)
# flèche nord
d.polygon([(W - 30, 14), (W - 38, 34), (W - 22, 34)], fill='black'); d.text((W - 34, 36), 'N', fill='black')
im.save(f'{OUT}/plan.png'); print(json.dumps(diag, ensure_ascii=False, indent=1))
