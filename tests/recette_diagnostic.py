# Recette automatique du diagnostic (sans IA) : terrain -> diag -> exposition -> plantes -> produits, sur des adresses de toute la France
import sys, os, json, subprocess, urllib.request, urllib.parse, itertools, concurrent.futures as cf
R = '/home/claude/jardin-3d'; sys.path.insert(0, R + '/service'); os.chdir(R + '/service')
import terrain, pipeline
KB = json.load(open(R + '/rendu/paysage/palettes_vegetales.json')); BANQUE = {p['latin']: p for p in KB['plantes']}
ICI = os.environ.get('RECETTE_DIR', '/tmp/recette_diagnostic')
ADR = ['46 avenue du Maréchal de Lattre de Tassigny 94350 Villiers-sur-Marne', '15 rue des Rossignols 34830 Clapiers', '8 allée des Chênes 44300 Nantes',
       '22 rue Victor Hugo 59650 Villeneuve-d\'Ascq', '5 rue des Vosges 67400 Illkirch-Graffenstaden', '14 chemin des Vignes 69130 Écully',
       '30 avenue de la Libération 33700 Mérignac', '10 rue de Kerzu 29200 Brest', '7 avenue des Pins 06100 Nice', '3 route de Thônes 74940 Annecy',
       '12 rue des Écoles 31700 Blagnac', '9 rue du Stade 63800 Cournon-d\'Auvergne', '4 impasse des Lilas 13090 Aix-en-Provence', '18 rue de la Gare 38500 Voiron']
def geo(q):
    u = 'https://data.geopf.fr/geocodage/search?' + urllib.parse.urlencode({'q': q, 'limit': 1, 'index': 'address'})
    f = json.load(urllib.request.urlopen(u, timeout=20))['features'][0]; p = f['properties']; c = f['geometry']['coordinates']
    return {'label': p['label'], 'city': p['city'], 'postcode': p['postcode'], 'lat': c[1], 'lon': c[0]}
def un(q):
    try:
        a = geo(q); T = terrain.terrain(a['lat'], a['lon'])
        d = os.path.join(ICI, 'cas', a['postcode'] + '_' + a['city'].replace(' ', '_')); os.makedirs(d, exist_ok=True)
        P = {'address': a, 'parcel': T.get('parcel'), 'building': T.get('building'), 'facades': T.get('facades') or [], 'needs': {'style': 'naturel', 'upkeep': 'peu'}}
        json.dump(P, open(d + '/projet.json', 'w'), ensure_ascii=False)
        subprocess.run(['python3', R + '/diagnostic/diag.py', d + '/projet.json', d + '/diag'], check=True, capture_output=True, timeout=300)
        return d, json.load(open(d + '/diag/diagnostic.json'))
    except Exception as e:
        return q, {'erreur': str(e)[:200]}
res = list(cf.ThreadPoolExecutor(5).map(un, ADR))
pb = []; lignes = []
for d, g in res:
    if 'erreur' in g: pb.append(f'TERRAIN/DIAG {d}: {g["erreur"]}'); continue
    zm = g.get('zone_maison') or {}
    moy = (zm['soleil_ete_h'] + zm['soleil_equinoxe_h']) / 2 if zm else None
    expo = 'soleil' if moy and moy >= 7 else 'mi-ombre' if moy and moy >= 3.5 else 'ombre'
    ombre = zm.get('soleil_equinoxe_h', 99) < 4
    P = json.load(open(d + '/projet.json'))
    for st, up in itertools.product(['contemporain', 'naturel', 'mediterraneen', 'champetre'], ['peu', 'moyen', 'jardinier']):
        P['needs'] = {'style': st, 'upkeep': up}; json.dump(P, open(d + '/p.json', 'w'), ensure_ascii=False)
        r = subprocess.run(['python3', R + '/diagnostic/saisons.py', d + '/p.json', '-', d + '/pl'], capture_output=True, text=True, timeout=60, env=dict(os.environ, SAISONS_VISUELS='0', EXPO=expo))
        if r.returncode: pb.append(f'PLANTES {d} {st}/{up}: plantage {r.stderr[-200:]}'); continue
        J = json.load(open(d + '/pl/plantes.json')); pl = J['plantes']
        if len(pl) < 5: pb.append(f'PLANTES {d} {st}/{up}: seulement {len(pl)} plantes')
        for p in pl:
            b = BANQUE[p['latin']]
            if J['climat'] not in b['climats']: pb.append(f'CLIMAT {d} {p["latin"]} pas pour {J["climat"]}')
            if expo not in b['expo'] and not (set(b['expo']) & set({'ombre': ['mi-ombre'], 'soleil': ['mi-ombre'], 'mi-ombre': ['soleil', 'ombre']}[expo])): pb.append(f'EXPO {d} {p["latin"]} {b["expo"]} pour {expo}')
            if not p.get('mois_plantation'): pb.append(f'PLANTATION {d} {p["latin"]} sans mois')
            if not os.path.exists(f'{R}/service/assets/plantes/{p.get("photo") or ""}') and not p.get('photo'): pass
        roles = [p['role'] for p in pl]
        if len(set(roles)) < 3: pb.append(f'DIVERSITE {d} {st}/{up}: rôles {roles}')
    for env in [['sol'], ['recevoir', 'sol'], ['intimite'], ['ombre'], ['ombre', 'sol'], ['embellir', 'intimite', 'sol', 'recevoir']]:
        pr = pipeline.choisir_produits(env, ombre)
        if 'sol' in env and 'terrasse' not in pr: pb.append(f'PRODUITS {d} {env}: pas de terrasse {pr}')
        if 'intimite' in env and 'cloture' not in pr: pb.append(f'PRODUITS {d} {env}: pas de clôture {pr}')
        if ombre and 'pergola' in pr and 'ombre' not in env: pb.append(f'PRODUITS {d} {env}: pergola à l\'ombre {pr}')
        if not pr: pb.append(f'PRODUITS {d} {env}: aucun produit')
    lignes.append(f'{os.path.basename(d):32} côté {g.get("cote_jardin"):6} zone été {zm.get("soleil_ete_h")} h, mi-saison {zm.get("soleil_equinoxe_h")} h -> {expo}{" (ombre: pas de pergola)" if ombre else ""} | jardin {g["surface_jardin_m2"]} m²')
print('\n'.join(lignes)); print('\nPROBLEMES', len(pb)); print('\n'.join(sorted(set(pb))[:80]))
