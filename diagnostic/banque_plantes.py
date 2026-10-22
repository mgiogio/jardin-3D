# Banque de photos des plantes (générée une seule fois) : une photo par plante, dans sa saison la plus belle.
# Usage : OPENAI_API_KEY=... python3 banque_plantes.py dossier_sortie
import sys, os, re, json, io, base64, urllib.request, concurrent.futures as cf
from PIL import Image
ICI = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
KB = json.load(open(os.path.join(ICI, '..', 'rendu', 'paysage', 'palettes_vegetales.json')))
MOIS = {'janv': 1, 'févr': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'août': 8, 'sept': 9, 'oct': 10, 'nov': 11, 'déc': 12}
SAI = {3: 'au printemps', 4: 'au printemps', 5: 'au printemps', 6: 'en été', 7: 'en été', 8: 'en été', 9: "à l'automne", 10: "à l'automne", 11: "à l'automne", 12: 'en hiver', 1: 'en hiver', 2: 'en hiver'}
def saison(p):
    t = (p['floraison'] or '').lower()
    for k, v in MOIS.items():
        if k in t: return SAI[v] + ', en fleurs'
    h = p['hiver'].lower()
    if any(w in h for w in ('automne', 'orange', 'rouge')): return "à l'automne, feuillage coloré"
    return 'en été, en plein feuillage'
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:50]
def gen(p):
    f = f"{OUT}/{slug(p['latin'])}.jpg"
    if os.path.exists(f): return f
    prompt = (f"Photo réaliste prise au smartphone d'un(e) {p['nom']} ({p['latin']}) {saison(p)}, de taille adulte jeune (environ {p['hauteur_m']} m), "
              "planté(e) dans un jardin de particulier en France, lumière naturelle douce, cadrage serré sur la plante, arrière-plan flou, aucune personne, aucun texte.")
    body = json.dumps({'model': os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst'), 'prompt': prompt, 'size': '1024x1024', 'quality': 'medium'}).encode()
    r = urllib.request.Request('https://api.openai.com/v1/images/generations', data=body, headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(r, timeout=400))
    im = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((640, 640), Image.LANCZOS)
    im.save(f, quality=84); return f
with cf.ThreadPoolExecutor(6) as ex:
    for p, f in zip(KB['plantes'], ex.map(lambda p: (lambda: gen(p))() if True else None, KB['plantes'])):
        print('ok', f, flush=True)
json.dump({slug(p['latin']): f"{slug(p['latin'])}.jpg" for p in KB['plantes']}, open(f'{OUT}/index.json', 'w'), indent=1)
