# Paysagiste automatique : photo du jardin (produits Cover Green déjà posés) + ville -> concept, aménagement, relecture, planche.
#
#   python3 paysagiste.py <dossier_travail> <image.jpg> <calque_produits.png> <pieds_clotures.png[,..]|-> <terrasse.png|-> \
#           --ville "Tours" --dep 37 [--style ville] [--tours 2]
#
# Étapes :
#   1. concept   : GPT-5.5 (vision) joue l'architecte paysagiste : diagnostic, concept, point focal, strates, palette tirée
#                  de palettes_vegetales.json (filtrée par climat), traitement du sol, zones à aménager (polygones).
#   2. génération: une passe globale gpt-image-2.5 masquée (amenage.py), produits recollés à l'identique.
#   3. relecture : GPT-5.5 note l'effet waouh, la crédibilité paysagère et le montage, et propose des corrections par zone.
#                  Une correction n'est gardée que si la relecture suivante la juge meilleure (sinon on revient en arrière).
#   4. planche   : avant / après, concept, palette, entretien.
# Clés : OPENAI_API_KEY dans l'environnement. Rien n'est écrit hors du dossier de travail.
import sys, os, json, base64, io, subprocess, argparse, urllib.request, time
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
RENDU = os.path.dirname(ICI)
KB = json.load(open(os.path.join(ICI, 'palettes_vegetales.json')))
MODELE_TEXTE = os.environ.get('MODELE_TEXTE', 'gpt-5.5')
MODELE_IMAGE = os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst')
GRILLE = 1000   # les polygones s'échangent en coordonnées d'une image ramenée à 1000 px de large


def climat_de(dep):
    for c, deps in KB['climats'].items():
        if c != '_doc' and str(dep).zfill(2) in deps:
            return c
    return 'oceanique_degrade'


def b64(im, fmt='JPEG'):
    b = io.BytesIO(); im.save(b, fmt, quality=88); return base64.b64encode(b.getvalue()).decode()


def gpt(consigne, images, effort='medium'):
    """Appel Responses API, réponse JSON."""
    contenu = [{'type': 'input_text', 'text': consigne}] + [
        {'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + b64(im)} for im in images]
    corps = {'model': MODELE_TEXTE, 'input': [{'role': 'user', 'content': contenu}],
             'reasoning': {'effort': effort}, 'text': {'format': {'type': 'json_object'}}}
    req = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(corps).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    for essai in range(3):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=600)); break
        except Exception as e:
            if essai == 2: raise
            time.sleep(5)
    txt = ''.join(c.get('text', '') for o in r.get('output', []) if o.get('type') == 'message' for c in o.get('content', []))
    return json.loads(txt)


def vue_grille(img, calque=None):
    """Image ramenée à GRILLE px de large, produits cernés en magenta, grille légendée tous les 100 px."""
    k = GRILLE / img.width; v = img.resize((GRILLE, round(img.height * k))).convert('RGB')
    d = ImageDraw.Draw(v)
    if calque is not None:
        a = calque.resize(v.size).getchannel('A').point(lambda x: 255 if x > 120 else 0)
        bord = a.filter(__import__('PIL.ImageFilter', fromlist=['x']).FIND_EDGES)
        v.paste((255, 0, 255), mask=bord)
    for x in range(0, v.width, 100):
        d.line([(x, 0), (x, v.height)], fill=(255, 255, 0), width=1); d.text((x + 3, 3), str(x), fill=(255, 255, 0))
    for y in range(0, v.height, 100):
        d.line([(0, y), (v.width, y)], fill=(255, 255, 0), width=1); d.text((3, y + 3), str(y), fill=(255, 255, 0))
    return v, k


def palette_candidates(clim):
    return [p for p in KB['plantes'] if clim in p['climats']]


METHODE = """Tu es architecte paysagiste DPLG en France, 20 ans de projets de jardins de particuliers, reconnu pour des projets
spectaculaires mais réalistes. Méthode : 1) diagnostic (ce qui tue l'effet waouh : sol, transitions, façades nues, absence de
point focal, vides), 2) une intention en une phrase, 3) UN point focal, 4) des strates : structure persistante au fond,
floraison au milieu, lisière basse répétée devant, 5) répétition de 2 ou 3 végétaux pour le rythme, 6) cohérence climat,
exposition et saisons (pas de plante de soleil à l'ombre, floraisons visibles en même temps sur l'image), 7) intérêt en
hiver (persistants), 8) entretien raisonnable, 9) traitement du sol et des transitions (bordures, paillage).
Les produits Cover Green (pergola, terrasse, clôtures, cernés en magenta) sont intouchables : on aménage autour."""


def concept(img, calque, ville, dep, style, sortie):
    clim = climat_de(dep)
    v, k = vue_grille(img, calque)
    cand = [{x: p[x] for x in ('latin', 'nom', 'role', 'expo', 'styles', 'floraison', 'hiver', 'hauteur_m')} for p in palette_candidates(clim)]
    consigne = METHODE + f"""

Jardin d'un client à {ville} (département {dep}, climat {clim}). Style souhaité : {style or 'à choisir selon la maison et le lieu'}.
L'image est ramenée à {v.width} x {v.height} px, avec une grille jaune légendée tous les 100 px pour lire les coordonnées.
Plantes autorisées (choisis UNIQUEMENT dans cette liste, selon l'exposition que tu observes) :
{json.dumps(cand, ensure_ascii=False)}

Réponds en JSON, en français, avec exactement ces clés :
{{"exposition": "soleil|mi-ombre|ombre (dominante observée)",
 "style": "...",
 "diagnostic": ["4 constats concrets"],
 "titre": "titre court du concept",
 "intention": "une phrase",
 "point_focal": "plante + emplacement",
 "sol": {{"action": "garder|nettoyer|remplacer|pelouse", "description": "..."}},
 "zones": [{{"nom": "...", "polygone": [[x,y],...], "consigne": "description précise de ce qu'on voit dans cette zone une fois aménagée : végétaux (noms latins), strates, paillage, bordures, hauteurs, densité"}}],
 "palette": [{{"latin": "...", "nom": "...", "role_projet": "...", "periode": "..."}}],
 "eclairage": "...",
 "entretien": "une phrase"}}
Règles des zones : 2 à 5 zones, polygones en coordonnées de la grille, sur le sol ou les murs à aménager, jamais sur les
produits cernés en magenta, jamais sur la maison (sauf grimpante sur un mur nu), ni sur le ciel. Assez grandes pour être
généreuses, mais crédibles pour un jardin de particulier. Pas de construction (ni mur, ni abri, ni clôture en plus)."""
    c = gpt(consigne, [v], 'high')
    for z in c['zones']:
        z['polygone_px'] = [[round(x / k), round(y / k)] for x, y in z['polygone']]
    c.update(ville=ville, departement=str(dep), climat=clim)
    json.dump(c, open(sortie, 'w'), ensure_ascii=False, indent=1)
    return c


def consigne_image(c, zones):
    lignes = [f"Retouche d'une vraie photo de jardin de particulier à {c['ville']}, prise au téléphone. Garder exactement le même "
              "cadrage, la même perspective, la même lumière et le même grain. Hors des zones à modifier rien ne change : "
              "la maison, la pergola, la terrasse, les clôtures, le mobilier, le ciel et les voisins restent identiques.",
              f"Projet d'un architecte paysagiste : {c['intention']} Exposition {c['exposition']}.",
              "Dans les zones à modifier uniquement :"]
    for i, z in enumerate(zones, 1):
        lignes.append(f"{i}. {z['nom']} : {z['consigne']}")
    if c['sol']['action'] != 'garder':
        lignes.append(f"Sol : {c['sol']['description']}")
    lignes.append("Plantes installées depuis deux ou trois ans, sol couvert, bordures nettes. Photo naturelle et crédible, "
                  "pas un rendu 3D. Pas de personnage, pas de construction ajoutée.")
    return '\n'.join(lignes)


def generer(base, zones, c, args, sortie, tag):
    zj = os.path.join(args.dossier, f'zones_{tag}.json'); json.dump([z['polygone_px'] for z in zones], open(zj, 'w'))
    cj = os.path.join(args.dossier, f'consigne_{tag}.txt'); open(cj, 'w').write(consigne_image(c, zones))
    vide = os.path.join(args.dossier, '_vide.png')
    if not os.path.exists(vide): Image.new('RGBA', Image.open(base).size, (0, 0, 0, 0)).save(vide)
    env = dict(os.environ, IMG_MODEL=MODELE_IMAGE, FONDU_ZONE='6', MOBILIER_SEPARE='1', HAUT_MOBILIER='0')
    if args.garder: env['GARDER'] = args.garder
    cmd = ['python3', os.path.join(RENDU, 'amenage.py'), base, zj, '1', cj, sortie, args.calque,
           args.pieds if args.pieds != '-' else vide, args.terrasse if args.terrasse != '-' else vide, '0.0']
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-1500:])


RUBRIQUE = """Tu relis un visuel de démonstration commerciale : photo réelle d'un jardin, transformée par un projet paysager autour
de produits bois Cover Green (pergola, terrasse, clôtures : ne pas les juger). Tu es à la fois architecte paysagiste exigeant
et retoucheur qui traque les montages. Première image : photo avant. Deuxième : visuel aménagé, avec grille jaune
légendée tous les 100 px. Concept visé : {concept}
Réponds en JSON : {{"waouh": note sur 10, "credibilite_paysagere": note sur 10, "montage": note sur 10 (10 = aucun défaut visible),
"livrable": true|false, "defauts": ["défaut précis avec position"],
"corrections": [{{"nom": "...", "polygone": [[x,y],...], "consigne": "ce qu'on doit voir dans cette zone après correction"}}]}}
Au plus 3 corrections, chacune sur une zone précise du jardin (jamais sur les produits ni la maison), uniquement pour des
défauts réels et importants : plante inadaptée à l'exposition ou au climat, floraisons incohérentes, massif maigre, plante
coupée net, flou ou halo, objet absurde, raccord visible. Une correction ne doit pas affadir le projet : garder les contrastes
et la générosité qui font l'effet waouh. Livrable = waouh >= 7, credibilite >= 7 et montage >= 7."""


def relire(avant, apres_path, calque, c):
    av = Image.open(avant).convert('RGB'); ap = Image.open(apres_path).convert('RGB')
    v, k = vue_grille(ap)
    resume = f"{c['titre']} : {c['intention']} Point focal : {c['point_focal']}. Exposition {c['exposition']}, climat {c['climat']}."
    r = gpt(RUBRIQUE.format(concept=resume), [av.resize(v.size), v], 'high')
    for z in r.get('corrections', []):
        z['polygone_px'] = [[round(x / k), round(y / k)] for x, y in z['polygone']]
    return r


def score(r):
    return r['waouh'] + r['credibilite_paysagere'] + r['montage']


def planche(avant, apres, c, sortie):
    F = '/usr/share/fonts/truetype/dejavu/DejaVuSans'
    f = lambda s, b=False: ImageFont.truetype(F + ('-Bold' if b else '') + '.ttf', s)
    av, ap = Image.open(avant).convert('RGB'), Image.open(apres).convert('RGB')
    w = 900; h = round(ap.height * w / ap.width); W = 2 * w + 60
    o = Image.new('RGB', (W, h + 1400), (247, 245, 240)); d = ImageDraw.Draw(o); G = (30, 60, 40)
    d.text((20, 18), f"{c['titre']}  -  {c['ville']}", fill=G, font=f(38, True))
    o.paste(av.resize((w, h)), (20, 80)); o.paste(ap.resize((w, h)), (w + 40, 80))
    d.text((30, 90), 'AVANT', fill='white', font=f(30, True)); d.text((w + 50, 90), 'APRÈS', fill='white', font=f(30, True))
    y = h + 110
    def bloc(titre, lignes):
        nonlocal y
        d.text((20, y), titre, fill=G, font=f(30, True)); y += 45
        for t in lignes:
            d.text((30, y), '- ' + t, fill=(40, 40, 40), font=f(22)); y += 34
        y += 18
    bloc('Le concept', [c['intention'], 'Point focal : ' + c['point_focal'], 'Sol : ' + c['sol']['description']])
    d.text((20, y), f"Palette végétale (climat {c['climat'].replace('_', ' ')}, {c['exposition']})", fill=G, font=f(30, True)); y += 48
    for p in c['palette'][:10]:
        d.text((30, y), p['latin'], fill=(20, 20, 20), font=f(21, True)); d.text((560, y), p['role_projet'][:70], fill=(50, 50, 50), font=f(21))
        d.text((1450, y), p.get('periode', '')[:30], fill=(90, 90, 90), font=f(21)); y += 33
    y += 15
    bloc('Éclairage et entretien', [c['eclairage'], c['entretien']])
    o.crop((0, 0, W, y + 20)).save(sortie, quality=90)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dossier'); ap.add_argument('image'); ap.add_argument('calque'); ap.add_argument('pieds'); ap.add_argument('terrasse')
    ap.add_argument('--avant', help='photo d\'origine du client (pour la planche et la relecture)')
    ap.add_argument('--ville', required=True); ap.add_argument('--dep', required=True); ap.add_argument('--style', default='')
    ap.add_argument('--garder', default=''); ap.add_argument('--tours', type=int, default=2)
    a = ap.parse_args(); os.makedirs(a.dossier, exist_ok=True)
    avant = a.avant or a.image
    img = Image.open(a.image).convert('RGB'); cal = Image.open(a.calque).convert('RGBA')
    journal = []
    cp = os.path.join(a.dossier, 'concept.json')
    c = json.load(open(cp)) if os.path.exists(cp) else concept(img, cal, a.ville, a.dep, a.style, cp)
    print('concept :', c['titre'], '|', c['exposition'], '|', len(c['zones']), 'zones', flush=True)
    cur = os.path.join(a.dossier, 'v0.jpg')
    if not os.path.exists(cur): generer(a.image, c['zones'], c, a, cur, 'v0')
    r = relire(avant, cur, cal, c); journal.append({'version': 'v0', **r})
    print('v0 :', r['waouh'], r['credibilite_paysagere'], r['montage'], 'livrable' if r['livrable'] else '', flush=True)
    for t in range(1, a.tours + 1):
        if r['livrable'] or not r.get('corrections'): break
        nv = os.path.join(a.dossier, f'v{t}.jpg')
        generer(cur, r['corrections'], c, a, nv, f'v{t}')
        r2 = relire(avant, nv, cal, c); journal.append({'version': f'v{t}', **r2})
        print(f'v{t} :', r2['waouh'], r2['credibilite_paysagere'], r2['montage'], 'livrable' if r2['livrable'] else '', flush=True)
        if score(r2) > score(r) or (r2['livrable'] and not r['livrable']):
            cur, r = nv, r2
        else:
            print(f'v{t} rejetée (pas mieux que la précédente)', flush=True)
    final = os.path.join(a.dossier, 'final.jpg'); Image.open(cur).save(final, quality=94)
    planche(avant, final, c, os.path.join(a.dossier, 'planche.jpg'))
    json.dump(journal, open(os.path.join(a.dossier, 'relectures.json'), 'w'), ensure_ascii=False, indent=1)
    print('fini', final, '| retenue :', os.path.basename(cur), '| livrable :', r['livrable'])


if __name__ == '__main__':
    main()
