# Moteur du « Diagnostic jardin Cover Green » : à partir d'une photo, d'une adresse et de quelques réponses, produit
# le diagnostic (soleil, vis-à-vis, surface), le plan vu du ciel, la sélection de plantes, un visuel avec NOS produits
# (contrôlé) et les données de la page « Mon projet jardin ».
# Usage local : python3 pipeline.py dossier   (dossier contenant projet.json et photo.jpg)
import threading, os, sys, io, json, time, base64, subprocess, urllib.request, urllib.error, traceback
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()      # photos iPhone (HEIC)
except Exception:
    pass

ICI = os.path.dirname(os.path.abspath(__file__))
DIAG = os.environ.get('DIAG_DIR', os.path.join(ICI, '..', 'diagnostic'))
ASSETS = os.path.join(ICI, 'assets')
PROD = json.load(open(os.path.join(ICI, 'produits.json')))
TEXTE = os.environ.get('MODELE_TEXTE', 'gpt-5.5'); IMAGE = os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst')
CONTROLE = os.environ.get('MODELE_CONTROLE', 'claude-opus-5-5')


# coût IA de chaque diagnostic (USD par million de jetons, tarifs publics ; ajustables par la variable PRIX_IA en JSON)
PRIX = {'texte': {'in': 5.0, 'out': 30.0}, 'image': {'in_texte': 5.0, 'in_image': 8.0, 'out': 30.0}, 'controle': {'in': 4.0, 'out': 20.0}}
PRIX.update(json.loads(os.environ.get('PRIX_IA') or '{}'))
_cout = threading.local()
def compter(genre, u):
    L = getattr(_cout, 'lignes', None)
    if L is None or not u: return
    if genre == 'image':
        d = u.get('input_tokens_details') or {}; ti = d.get('text_tokens', 0); ii = d.get('image_tokens', max(0, u.get('input_tokens', 0) - ti))
        usd = (ti * PRIX['image']['in_texte'] + ii * PRIX['image']['in_image'] + u.get('output_tokens', 0) * PRIX['image']['out']) / 1e6
    else:
        P_ = PRIX[genre]; usd = (u.get('input_tokens', 0) * P_['in'] + u.get('output_tokens', 0) * P_['out']) / 1e6
    L.append({'genre': genre, 'usd': round(usd, 4), 'in': u.get('input_tokens', 0), 'out': u.get('output_tokens', 0)})


def b64(im, mx=1280):
    im = im.copy(); im.thumbnail((mx, mx)); b = io.BytesIO(); im.convert('RGB').save(b, 'JPEG', quality=86); return base64.b64encode(b.getvalue()).decode()


def gpt(consigne, images, effort='low'):
    contenu = [{'type': 'input_text', 'text': consigne}] + [{'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + b64(im)} for im in images]
    corps = {'model': TEXTE, 'input': [{'role': 'user', 'content': contenu}], 'reasoning': {'effort': effort}, 'text': {'format': {'type': 'json_object'}}}
    req = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(corps).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    for essai in range(3):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300)); compter('texte', r.get('usage')); break
        except Exception:
            if essai == 2: raise
            time.sleep(4)
    return json.loads(''.join(c.get('text', '') for o in r.get('output', []) if o.get('type') == 'message' for c in o.get('content', [])))


def claude(consigne, images):
    contenu = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': b64(im, 1024)}} for im in images]
    contenu.append({'type': 'text', 'text': consigne + "\nRéponds uniquement avec un objet JSON valide."})
    for essai in range(3):
        req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=json.dumps({'model': CONTROLE, 'max_tokens': 8000, 'messages': [{'role': 'user', 'content': contenu}]}).encode(),
                                     headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300)); compter('controle', r.get('usage'))
            t = ''.join(b.get('text', '') for b in r['content'] if b['type'] == 'text'); t = t[t.find('{'):t.rindex('}') + 1]
            return json.loads(t)
        except Exception as ex:
            print('contrôle Claude, nouvel essai :', str(ex)[:200], flush=True); time.sleep(5)
    return gpt(consigne + "\nRéponds en JSON.", images, 'medium')     # secours : contrôle par GPT


def editer(prompt, images, sortie, qualite='high'):
    bd = 'cg' + os.urandom(8).hex()
    def part(n, v, fn=None, ct=None):
        h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '') + '\r\n'
        return h.encode() + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
    def png(im, mx):
        im = im.copy(); im.thumbnail((mx, mx)); b = io.BytesIO(); im.convert('RGB').save(b, 'PNG'); return b.getvalue()
    W, H = images[0].size; size = '1024x1536' if H > W * 1.15 else ('1536x1024' if W > H * 1.15 else '1024x1024')
    body = b''.join([part('model', IMAGE), part('prompt', prompt), part('size', size), part('quality', qualite)] +
                    [part('image[]', png(im, 1536 if i == 0 else 1024), f'i{i}.png', 'image/png') for i, im in enumerate(images)]) + f'--{bd}--\r\n'.encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': f'multipart/form-data; boundary={bd}'})
    res = json.load(urllib.request.urlopen(req, timeout=500)); compter('image', res.get('usage'))
    Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS).save(sortie, quality=90)
    return res.get('usage', {})


STYLES = {'contemporain': "contemporain et épuré : lignes droites, aluminium anthracite, coussins gris clair et blanc cassé, grandes dalles claires, jardinières en acier",
          'naturel': "naturel et chaleureux : bois, lin, terre cuite, graminées et vivaces généreuses, gravier clair",
          'mediterraneen': "méditerranéen : pierre claire, gravier, oliviers, lavandes, coussins écrus et terracotta",
          'champetre': "champêtre : fleurs généreuses, bois brut, chaises en métal coloré, pelouse fleurie"}
BESOINS = {'intimite': "se sentir chez soi, à l'abri des regards", 'ombre': "profiter du jardin sans souffrir du soleil", 'recevoir': "recevoir famille et amis",
           'embellir': "embellir et mettre en valeur le jardin", 'sol': "un sol propre et agréable"}


def choisir_produits(envies, ombre_maison=False, etage=None):
    # terrasse ou balcon en étage : la terrasse bois sur plots (sans percer l'étanchéité) d'abord, jamais de clôture ;
    # une pergola seulement sur un toit-terrasse, pour de l'ombre ou pour recevoir
    if etage:
        produits = ['terrasse']
        if etage.get('toit') and ({'ombre', 'recevoir'} & set(envies)) and not (ombre_maison and 'ombre' not in envies): produits.append('pergola')
        return produits
    # produits Cover Green du visuel, dans l'ordre des envies ; la terrasse dès que le client veut un sol propre ;
    # pas de pergola brise-soleil sur une zone déjà à l'ombre l'essentiel de l'année
    produits = []
    for x in envies:
        for p in PROD['besoins'].get(x, PROD['besoins']['_defaut']):
            if p not in produits: produits.append(p)
    # sauf si le client veut justement de l'ombre : la pergola ira alors dans la partie ensoleillée du jardin
    if ombre_maison and 'pergola' in produits and 'ombre' not in envies: produits.remove('pergola')
    if not produits: produits = ['cloture']
    return produits[:3]


def run(dossier, log=print):
    t0 = time.time(); P = json.load(open(f'{dossier}/projet.json')); etat = {'statut': 'en_cours', 'etapes': {}}; _cout.lignes = []
    def maj(**k):
        etat.update(k); json.dump(etat, open(f'{dossier}/etat.json', 'w'), ensure_ascii=False)
    maj()
    # photo : orientation EXIF, taille raisonnable
    im = None
    if os.path.exists(f'{dossier}/photo_brute'):
        im = ImageOps.exif_transpose(Image.open(f'{dossier}/photo_brute')).convert('RGB'); im.thumbnail((1600, 1600)); im.save(f'{dossier}/photo.jpg', quality=90)
    # terrain : si le questionnaire n'a pas pu récupérer la parcelle et la maison, on les cherche ici
    a_ = P.get('address') or {}
    if a_.get('lat') and not (P.get('parcel') and P.get('building')):
        try:
            import terrain; T_ = terrain.terrain(a_['lat'], a_['lon'])
            for k in ('parcel', 'building', 'facades'):
                if T_.get(k) and not P.get(k): P[k] = T_[k]
            json.dump(P, open(f'{dossier}/projet.json', 'w'), ensure_ascii=False)
        except Exception as e:
            log('terrain introuvable', e)
    besoin = (P.get('project', {}).get('need') or P.get('need') or '_defaut'); style = (P.get('needs', {}).get('style') or P.get('style') or 'contemporain')
    # plusieurs envies possibles, dans l'ordre de priorité choisi par le client : la première décide, les suivantes complètent
    envies = [x for x in (P.get('project', {}).get('needs') or [besoin]) if x in BESOINS] or [besoin]
    produits = choisir_produits(envies)
    data = {'id': os.path.basename(dossier), 'cree_le': time.strftime('%Y-%m-%d'), 'ville': P.get('address', {}).get('city', ''), 'besoin': besoin, 'envies': envies, 'style': style}
    # 1. diagnostic depuis l'adresse (gratuit) ; terrasse en étage : soleil et vis-à-vis calculés à la hauteur de la terrasse
    lieu = P.get('lieu') or {}
    en_etage = lieu.get('type') == 'appartement' and int(lieu.get('etage') or 0) >= 1
    data['lieu'] = lieu if lieu else {'type': 'maison'}
    if en_etage and P.get('building'):
        try:
            subprocess.run(['python3', f'{DIAG}/etage.py', f'{dossier}/projet.json', f'{dossier}/diag'], check=True, capture_output=True, timeout=240)
            data['diag'] = json.load(open(f'{dossier}/diag/diagnostic.json'))
        except Exception as e:
            log('diagnostic étage en échec', e, getattr(e, 'stderr', b'')[-800:]); data['diag'] = None
    elif P.get('parcel') and P.get('building'):
        try:
            subprocess.run(['python3', f'{DIAG}/diag.py', f'{dossier}/projet.json', f'{dossier}/diag'], check=True, capture_output=True, timeout=240)
            data['diag'] = json.load(open(f'{dossier}/diag/diagnostic.json'))
        except Exception as e:
            log('diagnostic adresse en échec', e, getattr(e, 'stderr', b'')[-800:]); data['diag'] = None
        if data.get('diag'):
            try:
                subprocess.run(['python3', f'{DIAG}/plan.py', f'{dossier}/diag', f'{dossier}/plan.png'], check=True, capture_output=True, timeout=120, env=dict(os.environ, PLAN_AUTO='1'))
                data['plan'] = 'plan.png'
            except Exception as e:
                log('plan en échec', e, getattr(e, 'stderr', b'')[-800:])
    etat['etapes']['diagnostic'] = round(time.time() - t0); maj()
    # 2. plantes (banque, sans génération)
    # exposition de la zone de vie contre la maison (côté principal du jardin), moyenne été / mi-saison
    zm = (data.get('diag') or {}).get('zone_maison') or {}
    expo = ''
    if zm.get('soleil_ete_h') is not None:
        moy = (zm['soleil_ete_h'] + zm.get('soleil_equinoxe_h', zm['soleil_ete_h'])) / 2
        expo = 'soleil' if moy >= 7 else 'mi-ombre' if moy >= 3.5 else 'ombre'
    # contre la maison, à l'ombre l'essentiel de l'année : une pergola brise-soleil n'y aurait pas de sens
    ombre_maison = zm.get('soleil_equinoxe_h') is not None and zm['soleil_equinoxe_h'] < 4
    ETG = {'n': int(lieu.get('etage') or 1), 'toit': bool((data.get('diag') or {}).get('toit_terrasse'))} if en_etage else None
    produits = choisir_produits(envies, ombre_maison, ETG)
    if not ETG and ombre_maison and 'pergola' in choisir_produits(envies): data['pergola_retiree'] = 'ombre contre la maison'
    subprocess.run(['python3', f'{DIAG}/saisons.py', f'{dossier}/projet.json', '-', f'{dossier}/plantes'], check=True, capture_output=True, timeout=60,
                   env=dict(os.environ, SAISONS_VISUELS='0', EXPO=expo, EN_BAC='1' if ETG else ''))
    data['plantes'] = json.load(open(f'{dossier}/plantes/plantes.json'))
    # 3. lecture de la photo par l'IA : atouts, pistes, placement des produits (texte)
    d = data.get('diag') or {}
    faits = {k: d.get(k) for k in ('surface_jardin_m2', 'soleil_ete_h_moyen', 'soleil_ete_apres14h_h', 'cote_jardin')} | {'vis_a_vis_proche': (d.get('vis_a_vis') or [None])[0],
             'zone_contre_la_maison': d.get('zone_maison')}
    if ETG:
        faits['important'] = (f"C'est une terrasse ou un balcon d'appartement au {ETG['n']}e étage{' (toit-terrasse)' if ETG['toit'] else ''} : jamais de clôture ; "
                              "la terrasse bois se pose sur plots, sans percer l'étanchéité ; le garde-corps reste ; les plantes vont en grands bacs. "
                              "Le soleil donné est celui du côté le plus ensoleillé de l'immeuble.")
    elif (d.get('zone_maison') or {}).get('soleil_equinoxe_h', 99) < 4 and 'pergola' in produits:
        faits['important'] = ("La zone contre la maison est à l'ombre l'essentiel de l'année : place la pergola plus loin, dans la partie ensoleillée du jardin, "
                              "jamais collée à la façade ombragée.")
    if data.get('pergola_retiree'):
        faits['important'] = ("La zone contre la maison, celle de la photo, est à l'ombre l'essentiel de l'année : ne propose pas de pergola à cet endroit. "
                              "Valorise plutôt une terrasse fraîche et des plantes d'ombre ; une pergola aurait sa place plus loin, dans la partie ensoleillée du jardin.")
    lecture = {} if im is None else gpt(f"""Tu es paysagiste-conseil pour Cover Green (clôtures, pergolas, terrasses et bardages en bois). Voici la photo du jardin d'un particulier.
Son envie : {' ; puis '.join(BESOINS.get(x, x) for x in envies)}. Style souhaité : {style}. Données calculées depuis son adresse : {json.dumps(faits, ensure_ascii=False)}.
Produits Cover Green à intégrer (donne un placement pour chacun) : {', '.join(PROD[p]['nom'] for p in produits)}.
Réponds en JSON, en français, ton chaleureux et positif, phrases courtes, sans tiret cadratin :
{{"atouts": ["2 ou 3 atouts réels visibles sur la photo"], "pistes": ["2 ou 3 améliorations concrètes, formulées positivement"],
 "placement": {{"cloture": "où poser la clôture sur cette photo pour répondre à l'envie, en une phrase (ou null)", "pergola": "où poser la pergola sur cette photo, décollée de la façade si une fenêtre est derrière (ou null)", "terrasse": "où poser la terrasse bois sur cette photo, sur la zone de vie au sol, en une phrase (ou null)"}},
 "cloture_longueur_m": nombre estimé (entre 4 et 30), "a_garder": ["seulement les éléments fixes ou plantés à conserver (maison, arbres, arbustes, murets, escaliers, accès) : le mobilier, les tapis et la déco peuvent être remplacés"], "a_retirer": ["encombrants ou objets à faire disparaître (poubelles, bâches, vieux mobilier)"],
 "sol_actuel": "dalle_ou_terrasse" ou "pelouse" ou "terre_ou_gravier" ou "mixte" (le sol de la zone de vie visible),
 "surface_sol_m2": surface estimée de la zone où l'on vivrait dehors (entre 8 et 40),
 "mur_a_habiller": "un mur, un abri ou une façade visible, laid ou abîmé (parpaing, enduit fatigué, tôle), qui gagnerait à être habillé de bois, en quelques mots ; jamais un mur déjà joli (pierre, brique, enduit propre) ni un élément cité dans les atouts (sinon null)", "mur_surface_m2": surface estimée de ce mur (ou null),
 "photo_exploitable": true ou false (false si la photo ne montre pas un extérieur)}}""", [im])
    data['lecture'] = lecture; etat['etapes']['lecture'] = round(time.time() - t0); maj()
    # 4. visuel avec nos produits, contrôlé
    data['visuel'] = None
    if im is not None and lecture.get('photo_exploitable', True):
        refs = [Image.open(f'{ASSETS}/refs/{r}').convert('RGB') for p in produits for r in PROD[p]['refs']]
        noms = [p for p in produits if (lecture.get('placement') or {}).get(p)]
        if ETG: consigne_lieu = "C'est une terrasse d'appartement en étage : garde le garde-corps et la façade, la terrasse bois est posée sur plots par-dessus le sol existant, les plantes sont en grands bacs. "
        else: consigne_lieu = ''
        consigne = consigne_lieu + (f"La première image est la photo du jardin d'un client : garde exactement la même maison, le même cadrage, la même perspective et la même lumière. "
                    f"Les images suivantes sont des photos de vrais produits Cover Green posés chez des clients. Reproduis CES produits à l'identique (proportions, sections, espacement des lames, connecteurs, teinte), jamais un modèle générique :\n"
                    + ''.join(f"- {PROD[p]['description_visuel']} : {lecture['placement'][p]}\n" for p in noms)
                    + f"Aménage autour dans un style {STYLES.get(style, style)}, très peu d'entretien, crédible pour un particulier : remplace le mobilier, les tapis et la déco existants par un aménagement neuf dans ce style, ajoute des plantations généreuses. "
                    + (f"Pour les plantations, utilise uniquement ces plantes, choisies pour l'exposition de cette zone ({(data.get('plantes') or {}).get('expo', '')}) : "
                       + ', '.join(f"{x['nom']} ({x['latin']})" for x in (data.get('plantes') or {}).get('plantes', [])) + " ; aucune autre espèce. " if (data.get('plantes') or {}).get('plantes') else '')
                    + (f"Retire : {', '.join(lecture.get('a_retirer') or [])}. " if lecture.get('a_retirer') else '')
                    + (f"Conserve : {', '.join(lecture.get('a_garder') or [])}. " if lecture.get('a_garder') else '')
                    + "Les passages et l'accès à la maison restent libres : aucun poteau, aucune poutre ni clôture ne passe devant une fenêtre ou une porte, les poteaux se posent à côté des ouvertures. Photo réaliste de smartphone, aucun texte.")
        retour = ''
        for essai in range(3):
            editer(consigne + retour, [im] + refs, f'{dossier}/visuel.jpg')
            ctl = claude("""Contrôle qualité d'un visuel d'aménagement pour un client. Image 1 : photo d'origine. Image 2 : visuel proposé. Images suivantes : nos vrais produits (références).
Note de 0 à 10 : "ressemblance" (les produits du visuel ressemblent-ils à nos références : sections, lames, connecteurs, teinte ?), "maison" (la maison est-elle préservée : mêmes fenêtres, portes, façade ?), "credibilite" (le visuel est-il réaliste, sans objet fondu, meuble qui flotte, produit qui traverse un objet ?).
Regarde en particulier chaque fenêtre et chaque porte de la maison : si un poteau, une poutre, une clôture ou un meuble passe devant l'une d'elles ou en bloque l'accès, c'est un défaut grave.
Liste uniquement les "defauts" GRAVES (qui empêchent de montrer l'image au client : maison modifiée, fenêtre ou porte masquée par un produit, produit qui ne ressemble pas, objet fondu ou impossible, passage bloqué), en une phrase chacun ; les petites imperfections vont dans "remarques". JSON : {"ressemblance": n, "maison": n, "credibilite": n, "defauts": [...], "remarques": [...]}""",
                         [im, Image.open(f'{dossier}/visuel.jpg')] + refs[:4])
            data['controle'] = ctl
            if ctl['ressemblance'] >= 7 and ctl['maison'] >= 7 and ctl['credibilite'] >= 7 and not ctl.get('defauts'):
                data['visuel'] = 'visuel.jpg'; break
            os.replace(f'{dossier}/visuel.jpg', f'{dossier}/visuel_refuse_{essai}.jpg')
            retour = "\nCorrige ces défauts de la première tentative : " + ' ; '.join(ctl.get('defauts') or ['produits pas assez fidèles aux références'])
        etat['etapes']['visuel'] = round(time.time() - t0); maj()
    r100 = lambda n: int(round(n / 100.0) * 100)
    # 4b. estimation du reste du visuel (mobilier, plantes, bacs, sol, éclairage), hors produits Cover Green
    data['reste'] = None
    if data['visuel']:
        try:
            inv = gpt("""Voici une idée d'aménagement de jardin. Fais l'inventaire de ce qui a été AJOUTÉ par rapport à un jardin vide, SAUF la clôture et la pergola en bois (déjà chiffrées) et sauf la maison.
Compte précisément ce que tu vois. JSON : {"mobilier": [{"type": un de "canape", "fauteuil", "table_basse", "table_repas", "chaise", "bain_de_soleil", "parasol", "banc", "quantite": n}],
 "plantes": {"grands_sujets": n (arbres ou gros arbustes en sujet), "arbustes": n, "vivaces_graminees": n (touffes)}, "contenants": {"grands_bacs": n, "pots": n},
 "sol": {"refait": true ou false (sol neuf différent de la photo d'origine), "type": "dalles", "gravier", "pelouse" ou null, "m2": surface estimée}, "eclairage": n (points lumineux)}""",
                      [Image.open(f'{dossier}/visuel.jpg'), im])
            # milieu de gamme (prix moyens constatés en jardinerie et chez les enseignes de mobilier)
            T = {'canape': (700, 1000), 'fauteuil': (200, 300), 'table_basse': (150, 250), 'table_repas': (400, 650), 'chaise': (70, 110),
                 'bain_de_soleil': (200, 300), 'parasol': (150, 250), 'banc': (200, 300)}
            lignes = {}
            mob = [0, 0]
            for m in inv.get('mobilier') or []:
                t = T.get(m.get('type')); q = max(0, min(12, int(m.get('quantite') or 0)))
                if t and q: mob[0] += t[0] * q; mob[1] += t[1] * q
            if mob[1]: lignes['Mobilier de jardin'] = mob
            pl = inv.get('plantes') or {}
            g, a_, v = [max(0, min(n, int(pl.get(k) or 0))) for k, n in (('grands_sujets', 4), ('arbustes', 20), ('vivaces_graminees', 40))]
            pla = [g * 200 + a_ * 30 + v * 9, g * 300 + a_ * 45 + v * 13]
            if pla[1]: lignes['Plantes'] = pla
            co = inv.get('contenants') or {}
            gb, po = max(0, min(10, int(co.get('grands_bacs') or 0))), max(0, min(15, int(co.get('pots') or 0)))
            if gb + po: lignes['Bacs et pots'] = [gb * 150 + po * 40, gb * 220 + po * 60]
            so = inv.get('sol') or {}
            if so.get('refait') and so.get('type') in ('dalles', 'gravier', 'pelouse'):
                m2 = max(5, min(60, int(so.get('m2') or 15))); pm = {'dalles': (45, 60), 'gravier': (10, 15), 'pelouse': (8, 12)}[so['type']]
                lignes[{'dalles': 'Dallage', 'gravier': 'Gravier', 'pelouse': 'Gazon'}[so['type']] + f' (environ {m2} m²)'] = [m2 * pm[0], m2 * pm[1]]
            ec = max(0, min(12, int(inv.get('eclairage') or 0)))
            if ec: lignes['Éclairage'] = [ec * 30, ec * 45]
            if lignes:
                r50 = lambda n: max(50, int(round(n / 50.0) * 50))
                lignes = {k: [r50(v[0]), max(r50(v[1]), r50(v[0]) + 50)] for k, v in lignes.items()}
                data['reste'] = {'lignes': lignes, 'total': [sum(v[0] for v in lignes.values()), sum(v[1] for v in lignes.values())]}
        except Exception as e:
            log('estimation du reste en échec', e)
    # 5. produits et budget (fourchettes arrondies)
    props = []
    for p in produits:
        c = PROD[p]
        if p == 'terrasse':
            S = int(max(8, min(40, float(lecture.get('surface_sol_m2') or 15))))
            props.append({'cle': p, 'nom': c['nom'], 'lien': c['lien'], 'photo': c['photo'], 'detail': {'Surface': f'environ {S} m²', 'Pose': 'sur plots réglables, sans percer' if ETG else c['format']},
                          'placement': (lecture.get('placement') or {}).get(p), 'prix': [r100(S * c['prix_m2'][0]), r100(S * c['prix_m2'][1])], 'm2': S})
        elif p == 'cloture':
            L = max(4, min(30, round(float(lecture.get('cloture_longueur_m') or min(d.get('lineaire_limites_libres_m') or 10, 20)) / 2) * 2))
            props.append({'cle': p, 'nom': c['nom'], 'lien': c['lien'], 'photo': c['photo'], 'detail': {'Hauteur': c['hauteur'], 'Longueur': f'environ {L} m'},
                          'placement': (lecture.get('placement') or {}).get(p), 'prix': [r100(L * c['prix_m'][0]), r100(L * c['prix_m'][1])], 'longueur': L})
        else:
            props.append({'cle': p, 'nom': c['nom'], 'lien': c['lien'], 'photo': c['photo'], 'detail': {'Format': c['format'], 'Toiture': 'brise-soleil'},
                          'placement': (lecture.get('placement') or {}).get(p), 'prix': c['prix']})
    data['produits'] = props; data['budget'] = [sum(p['prix'][0] for p in props), sum(p['prix'][1] for p in props)]
    # 6. compléments Cover Green selon l'envie, la photo et le terrain (2 au plus)
    C = PROD.get('complements', {}); comp = []
    sol = lecture.get('sol_actuel') or ''
    if 'terrasse' in C and 'terrasse' not in produits and ('sol' in envies or sol in ('pelouse', 'terre_ou_gravier', 'mixte')):
        S = int(max(8, min(40, float(lecture.get('surface_sol_m2') or 15))))
        comp.append({'cle': 'terrasse', 'm2': S, 'prix': [r100(S * C['terrasse']['prix_m2'][0]), r100(S * C['terrasse']['prix_m2'][1])],
                     'pourquoi': f"Un sol en bois d'environ {S} m² pour installer le coin salon de plain-pied, propre en toute saison."})
    if 'bardage' in C and lecture.get('mur_a_habiller'):
        S = int(max(4, min(30, float(lecture.get('mur_surface_m2') or 10))))
        comp.append({'cle': 'bardage', 'm2': S, 'prix': [r100(S * C['bardage']['prix_m2'][0]), r100(S * C['bardage']['prix_m2'][1])],
                     'pourquoi': f"Habiller {lecture['mur_a_habiller']} (environ {S} m²) avec le même bois que le reste du projet."})
    toit = d.get('surface_toit_m2') or 0
    if 'recuperateur' in C and (d.get('surface_jardin_m2') or 0) >= 40 and toit:
        pluie = {'mediterraneen': 0.6, 'continental': 0.7, 'montagnard': 1.0}.get((data.get('plantes') or {}).get('climat'), 0.75)
        m3 = int(round(toit * pluie * 0.8))
        comp.append({'cle': 'recuperateur', 'prix': C['recuperateur']['prix'],
                     'pourquoi': f"Votre toit d'environ {toit} m² récolte près de {m3} m³ d'eau de pluie par an : de quoi arroser vos nouvelles plantations."})
    ordre = [{'sol': 'terrasse', 'embellir': 'bardage'}[x] for x in envies if x in ('sol', 'embellir')]
    comp.sort(key=lambda c: 0 if c['cle'] in ordre else 1)
    for c in comp[:2]: c.update(nom=C[c['cle']]['nom'], lien=C[c['cle']]['lien'], photo=C[c['cle']]['photo'], bouton=C[c['cle']]['bouton'])
    data['complements'] = comp[:2]
    data['duree_s'] = round(time.time() - t0)
    L = _cout.lignes; data['cout'] = {'usd': round(sum(x['usd'] for x in L), 3), 'appels': L}
    json.dump(data, open(f'{dossier}/data.json', 'w'), ensure_ascii=False, indent=1)
    maj(statut='pret')
    return data


if __name__ == '__main__':
    try:
        print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=1)[:3000])
    except Exception:
        traceback.print_exc(); sys.exit(1)
