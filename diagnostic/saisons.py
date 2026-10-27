# Plantes par saison : sélection automatique dans la banque végétale (climat, exposition, style, entretien),
# calendrier mois par mois et visuels (photo par plante, cour du client à chaque saison).
# Usage : python3 saisons.py projet.json visuel_ambiance.jpg sortie_dossier [refs produits...]
import sys, os, re, json, io, base64, urllib.request, concurrent.futures as cf
from PIL import Image
ICI = os.path.dirname(os.path.abspath(__file__))
KB = json.load(open(os.path.join(ICI, '..', 'rendu', 'paysage', 'palettes_vegetales.json')))
P = json.load(open(sys.argv[1])); AMB = sys.argv[2]; OUT = sys.argv[3]; REFS = sys.argv[4:]; os.makedirs(OUT, exist_ok=True)
MOIS = {'janv': 1, 'févr': 2, 'fevr': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'août': 8, 'aout': 8, 'sept': 9, 'oct': 10, 'nov': 11, 'déc': 12, 'dec': 12}
def mois(txt):
    t = (txt or '').lower(); f = [(m.start(), v) for k, v in MOIS.items() for m in re.finditer(k, t)]
    f = [v for _, v in sorted(f)]
    if not f: return []
    if '-' in t and len(f) >= 2: a, b = f[0], f[1]; return list(range(a, b + 1)) if a <= b else list(range(a, 13)) + list(range(1, b + 1))
    return f
def climat(dep):
    for c, deps in KB['climats'].items():
        if c != '_doc' and str(dep).zfill(2) in deps: return c
    return 'oceanique_degrade'
dep = P['address']['postcode'][:2]; clim = climat(dep)
style = P.get('needs', {}).get('style', 'contemporain'); upkeep = P.get('needs', {}).get('upkeep', 'peu')
# exposition : calculée par le diagnostic (soleil de la zone de vie contre la maison) ; à défaut, d'après les façades
expo = os.environ.get('EXPO') or ('soleil' if any(f['facing'] == 'sud' for f in P.get('facades', [])) else 'mi-ombre')
# styles du questionnaire -> styles de la banque végétale
STYLES_KB = {'naturel': ['champetre', 'contemporain'], 'contemporain': ['contemporain', 'ville'], 'champetre': ['champetre', 'cottage'], 'mediterraneen': ['mediterraneen']}
SAISONS = {'printemps': (3, 4, 5), 'ete': (6, 7, 8), 'automne': (9, 10, 11), 'hiver': (12, 1, 2)}
def profil(p):
    fl = mois(p['floraison']); h = p['hiver'].lower(); s = set()
    for k, ms in SAISONS.items():
        if set(fl) & set(ms): s.add(k)
    if any(w in h for w in ('automne', 'orange', 'rouge', 'doré', 'marcescent')): s.add('automne')
    if any(w in h for w in ('persistant', 'marcescent', 'écorce', 'rouge en hiver', 'blond')): s.add('hiver')
    if 'feuillage' in h or 'persistant' in h: s.add('ete')
    return fl, s
SK = STYLES_KB.get(style, [style])
def filtre(expos, avec_style=True):
    return [p for p in KB['plantes'] if clim in p['climats'] and set(expos) & set(p['expo']) and (not avec_style or set(SK) & set(p['styles']))]
# du plus précis au plus large : jamais de liste vide (style, puis exposition voisine)
VOIS = {'soleil': ['soleil', 'mi-ombre'], 'mi-ombre': ['mi-ombre', 'soleil', 'ombre'], 'ombre': ['ombre', 'mi-ombre']}
cands = filtre([expo])
if len(cands) < 8: cands = filtre([expo], False)
if len(cands) < 8: cands = filtre(VOIS.get(expo, [expo]), False)
if upkeep == 'peu': cands = [p for p in cands if not re.search(r'taille 2|taille$', p['entretien'])]
quota = {'focal': 1, 'structure': 2, 'vivace': 1, 'graminee': 1, 'grimpante': 1}
choix, couvert = [], {}
for _ in range(sum(quota.values())):
    best = None
    for p in cands:
        if p in choix or quota.get(p['role'], 0) <= sum(1 for c in choix if c['role'] == p['role']): continue
        fl, s = profil(p)
        sc = sum(1 / (1 + couvert.get(k, 0)) for k in s) + 0.1 * len(fl)
        if best is None or sc > best[0]: best = (sc, p, s)
    if not best: break
    choix.append(best[1]); [couvert.__setitem__(k, couvert.get(k, 0) + 1) for k in best[2]]
# mois de plantation : en automne pour les plantes rustiques (meilleure reprise), au printemps pour les plantes frileuses et les graminées
FRILEUSES = ('Olea', 'Lagerstroemia', 'Trachycarpus', 'Cistus', 'Phlomis', 'Rosmarinus', 'Teucrium', 'Perovskia', 'Lavandula', 'Ceanothus', 'Gaura',
             'Erigeron', 'Agapanthus', 'Euphorbia characias', 'Stipa', 'Pennisetum', 'Miscanthus', 'Muhlenbergia', 'Festuca', 'Trachelospermum',
             'Fargesia', 'Abelia', 'Arbutus', 'Pittosporum', 'Calamagrostis', 'Hakonechloa', 'Carex', 'Ophiopogon')
def plantation(p):
    if p['latin'].startswith('Iris germanica'): return [7, 8, 9]
    fri = p['latin'].startswith(FRILEUSES)
    if clim == 'mediterraneen': return [3, 4, 10, 11]
    if clim in ('continental', 'montagnard'): return [5, 6] if fri else [4, 5, 9, 10]
    return [4, 5] if fri else [3, 4, 10, 11]
plantes = []
for p in choix:
    fl, s = profil(p)
    plantes.append({'latin': p['latin'], 'nom': p['nom'], 'role': p['role'], 'hauteur_m': p['hauteur_m'], 'floraison': p['floraison'],
                    'hiver': p['hiver'], 'entretien': p['entretien'], 'mois_fleurs': fl, 'mois_plantation': plantation(p), 'saisons': sorted(s), 'couleur': p.get('couleur', '')})
json.dump({'climat': clim, 'expo': expo, 'style': style, 'plantes': plantes}, open(f'{OUT}/plantes.json', 'w'), ensure_ascii=False, indent=1)
print(clim, expo, style, [p['nom'] for p in plantes])

# ---- photos des plantes : banque générée une fois (banque_plantes.py) ----
BANQUE = os.environ.get('BANQUE_PLANTES', '')
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:50]
for p in plantes: p['photo'] = f"{slug(p['latin'])}.jpg"
if os.environ.get('SAISONS_VISUELS', '1') == '0':
    json.dump({'climat': clim, 'expo': expo, 'style': style, 'plantes': plantes}, open(f'{OUT}/plantes.json', 'w'), ensure_ascii=False, indent=1)
    sys.exit(0)
# ---- visuels ----
KEY = os.environ['OPENAI_API_KEY']; MODEL = os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst')
def post(url, body, ct):
    r = urllib.request.Request(url, data=body, headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': ct})
    return json.load(urllib.request.urlopen(r, timeout=500))
def generer(prompt, out, size='1024x1024'):
    res = post('https://api.openai.com/v1/images/generations', json.dumps({'model': MODEL, 'prompt': prompt, 'size': size, 'quality': 'medium'}).encode(), 'application/json')
    Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').save(out, quality=88); return out
def editer(prompt, imgs, out):
    bd = 'xx' + os.urandom(8).hex()
    def part(n, v, fn=None, ct=None):
        h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '') + '\r\n'
        return h.encode() + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
    def png(p, mx):
        im = Image.open(p).convert('RGB'); im.thumbnail((mx, mx)); b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
    W, H = Image.open(imgs[0]).size; size = '1024x1536' if H > W else '1536x1024'
    body = b''.join([part('model', MODEL), part('prompt', prompt), part('size', size), part('quality', 'high')] +
                    [part('image[]', png(p, 1536 if i == 0 else 1024), f'i{i}.png', 'image/png') for i, p in enumerate(imgs)]) + f'--{bd}--\r\n'.encode()
    res = post('https://api.openai.com/v1/images/edits', body, f'multipart/form-data; boundary={bd}')
    Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS).save(out, quality=90); return out
NOMS = {'printemps': 'au printemps (fin avril)', 'ete': 'en été (début juillet)', 'automne': "à l'automne (fin octobre)", 'hiver': 'en hiver (janvier)'}
def phare(p):
    for k in ('printemps', 'ete', 'automne', 'hiver'):
        if k in p['saisons'] and (p['mois_fleurs'] and set(p['mois_fleurs']) & set(SAISONS[k])): return k
    return 'automne' if 'automne' in p['saisons'] else 'ete'
jobs = []
with cf.ThreadPoolExecutor(6) as ex:
    for i, p in enumerate(plantes):
        s = phare(p); p['saison_photo'] = s
        jobs.append(ex.submit(generer, f"Photo réaliste, prise au smartphone, d'un(e) {p['nom']} ({p['latin']}) {NOMS[s]}, planté(e) dans un jardin contemporain en France, "
                              f"jardinière en acier anthracite ou massif paillé de gravier, lumière naturelle douce, cadrage serré sur la plante, aucune personne, aucun texte.", f'{OUT}/plante_{i}.jpg'))
    desc = {k: ', '.join(f"{p['nom']}" + (' en fleurs' if set(p['mois_fleurs']) & set(SAISONS[k]) else '') for p in plantes if k in p['saisons']) for k in SAISONS}
    for k in SAISONS:
        jobs.append(ex.submit(editer, f"La première image est un projet d'aménagement. Garde exactement la même maison, le même cadrage, la même perspective, les mêmes produits en bois (pergola, clôture) et le même mobilier, "
                              f"identiques à la première image (les images suivantes montrent les vrais produits). Montre la même scène {NOMS[k]} : lumière, ciel et végétation de cette saison. "
                              f"Plantes visibles dans les jardinières et massifs : {desc[k]}. Les plantes caduques sont sans fleurs ni feuilles hors saison, les persistants restent verts. "
                              f"{'Lumière froide et basse, un peu de givre sur les graminées. ' if k == 'hiver' else ''}Photo réaliste de smartphone, aucun texte.", [AMB] + REFS, f'{OUT}/saison_{k}.jpg'))
    for j in jobs: print('ok', j.result())
json.dump({'climat': clim, 'expo': expo, 'style': style, 'plantes': plantes}, open(f'{OUT}/plantes.json', 'w'), ensure_ascii=False, indent=1)
