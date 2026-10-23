# Terrain du client à partir d'un point (adresse) : parcelle cadastrale, maison (BD TOPO) et façades.
# Données publiques IGN (licence ouverte Etalab 2.0). Utilisé par le questionnaire (aperçu « c'est bien chez vous ? »)
# et par le service si le questionnaire n'a pas pu les récupérer.
import json, math, urllib.request, urllib.parse
from shapely.geometry import Polygon, Point

UA = {'User-Agent': 'CoverGreen-Diagnostic/1.0'}
BOUSSOLE = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ouest', 'ouest', 'nord-ouest']


def _get(url, t=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
        return json.load(r)


def _anneaux(geom):
    c = geom['coordinates']
    return [p[0] for p in c] if geom['type'] == 'MultiPolygon' else [c[0]]


def parcelle(lat, lon):
    g = urllib.parse.quote(json.dumps({'type': 'Point', 'coordinates': [lon, lat]}))
    F = _get(f'https://apicarto.ign.fr/api/cadastre/parcelle?geom={g}').get('features') or []
    if not F: return None
    f = F[0]; p = f.get('properties') or {}
    ring = max(_anneaux(f['geometry']), key=len)
    return {'ring': [[round(x, 8), round(y, 8)] for x, y, *_ in ring], 'area': p.get('contenance'),
            'ref': ' '.join(str(x) for x in (p.get('code_insee'), p.get('section'), p.get('numero')) if x)}


def batiments(lat, lon, r=45):
    dlat, dlon = r / 110540, r / (111320 * math.cos(math.radians(lat)))
    url = ('https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3:batiment&OUTPUTFORMAT=application/json'
           f'&COUNT=200&SRSNAME=EPSG:4326&BBOX={lat - dlat},{lon - dlon},{lat + dlat},{lon + dlon},urn:ogc:def:crs:EPSG::4326')
    out = []
    for f in _get(url).get('features') or []:
        p = f.get('properties') or {}
        for ring in _anneaux(f['geometry']):
            out.append({'ring': [[round(x, 8), round(y, 8), *([round(z[0], 1)] if z else [])] for x, y, *z in ring],
                        'height': p.get('hauteur'), 'floors': p.get('nombre_d_etages'), 'usage': p.get('usage_1')})
    return out


def facades(ring, lat0):
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110540
    pts = [(x * kx, y * ky) for x, y, *_ in ring]
    aire = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:]))      # > 0 : sens trigonométrique
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        if L < 1.2: continue
        nx, ny = (dy, -dx) if aire > 0 else (-dy, dx)                      # normale extérieure
        az = (math.degrees(math.atan2(nx, ny)) + 360) % 360
        out.append({'index': i, 'length': round(L, 2), 'azimuth': round(az), 'facing': BOUSSOLE[int((az + 22.5) % 360 // 45)],
                    'a': list(ring[i][:2]), 'b': list(ring[i + 1][:2])})
    return out


def terrain(lat, lon):
    """Parcelle + maison + façades + quelques chiffres pour l'aperçu. Lève une exception si rien n'est trouvé."""
    par = parcelle(lat, lon)
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540
    loc = lambda r: Polygon([((x - lon) * kx, (y - lat) * ky) for x, y, *_ in r])
    bats = batiments(lat, lon)
    maison = None
    if par:
        P = loc(par['ring']).buffer(0)
        cands = [(loc(b['ring']).buffer(0).intersection(P).area, b) for b in bats if len(b['ring']) > 3]
        cands = [c for c in cands if c[0] > 15]
        # la maison : le plus gros bâtiment de la parcelle, en privilégiant le résidentiel (un abri ou un garage passe après)
        if cands: maison = max(cands, key=lambda c: c[0] * (1.0 if (c[1].get('usage') or 'Résidentiel') == 'Résidentiel' else 0.3))[1]
    if not maison and bats:
        maison = min(bats, key=lambda b: loc(b['ring']).distance(Point(0, 0)))
        if loc(maison['ring']).distance(Point(0, 0)) > 25: maison = None
    if not par and not maison: raise ValueError('terrain introuvable')
    out = {'parcel': par, 'building': None, 'facades': [], 'apercu': {}}
    if maison:
        out['building'] = {'ring': maison['ring'], 'height': maison.get('height') or 6, 'floors': maison.get('floors')}
        out['facades'] = facades(maison['ring'], lat)
    if par:
        Pp = loc(par['ring']).buffer(0); M = loc(maison['ring']).buffer(0) if maison else None
        j = Pp.difference(M) if M is not None else Pp
        a = {'parcelle_m2': round(Pp.area), 'jardin_m2': round(j.area)}
        if M is not None and j.area > 5:
            c, m = j.centroid, M.centroid
            az = (math.degrees(math.atan2(c.x - m.x, c.y - m.y)) + 360) % 360
            a['jardin_cote'] = BOUSSOLE[int((az + 22.5) % 360 // 45)]          # où se trouve l'essentiel du jardin par rapport à la maison
        out['apercu'] = a
    return out


if __name__ == '__main__':
    import sys
    r = terrain(float(sys.argv[1]), float(sys.argv[2]))
    print(json.dumps({k: (v if k == 'apercu' else bool(v)) for k, v in r.items()}, ensure_ascii=False), r['building'] and r['building']['height'])
