# Moteur du « Diagnostic jardin Cover Green » : à partir d'une photo, d'une adresse et de quelques réponses, produit
# le diagnostic (soleil, vis-à-vis, surface), le plan vu du ciel, la sélection de plantes, un visuel avec NOS produits
# (contrôlé) et les données de la page « Mon projet jardin ».
# Usage local : python3 pipeline.py dossier   (dossier contenant projet.json et photo.jpg)
import os, sys, io, json, time, base64, subprocess, urllib.request, urllib.error, traceback
from PIL import Image, ImageOps

ICI = os.path.dirname(os.path.abspath(__file__))
DIAG = os.environ.get('DIAG_DIR', os.path.join(ICI, '..', 'diagnostic'))
ASSETS = os.path.join(ICI, 'assets')
PROD = json.load(open(os.path.join(ICI, 'produits.json')))
TEXTE = os.environ.get('MODELE_TEXTE', 'gpt-5.5'); IMAGE = os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst')
CONTROLE = os.environ.get('MODELE_CONTROLE', 'claude-opus-5-5')


def b64(im, mx=1280):
    im = im.copy(); im.thumbnail((mx, mx)); b = io.BytesIO(); im.convert('RGB').save(b, 'JPEG', quality=86); return base64.b64encode(b.getvalue()).decode()


def gpt(consigne, images, effort='low'):
    contenu = [{'type': 'input_text', 'text': consigne}] + [{'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + b64(im)} for im in images]
    corps = {'model': TEXTE, 'input': [{'role': 'user', 'content': contenu}], 'reasoning': {'effort': effort}, 'text': {'format': {'type': 'json_object'}}}
    req = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(corps).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    for essai in range(3):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300)); break
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
            r = json.load(urllib.request.urlopen(req, timeout=300))
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
    res = json.load(urllib.request.urlopen(req, timeout=500))
    Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS).save(sortie, quality=90)
    return res.get('usage', {})


STYLES = {'contemporain': "contemporain et épuré : lignes droites, aluminium anthracite, coussins gris clair et blanc cassé, grandes dalles claires, jardinières en acier",
          'naturel': "naturel et chaleureux : bois, lin, terre cuite, graminées et vivaces généreuses, gravier clair",
          'mediterraneen': "méditerranéen : pierre claire, gravier, oliviers, lavandes, coussins écrus et terracotta",
          'champetre': "champêtre : fleurs généreuses, bois brut, chaises en métal coloré, pelouse fleurie"}
BESOINS = {'intimite': "se sentir chez soi, à l'abri des regards", 'ombre': "profiter du jardin sans souffrir du soleil", 'recevoir': "recevoir famille et amis",
           'embellir': "embellir et mettre en valeur le jardin", 'sol': "un sol propre et agréable"}


def run(dossier, log=print):
    t0 = time.time(); P = json.load(open(f'{dossier}/projet.json')); etat = {'statut': 'en_cours', 'etapes': {}}
    def maj(**k):
        etat.update(k); json.dump(etat, open(f'{dossier}/etat.json', 'w'), ensure_ascii=False)
    maj()
    # photo : orientation EXIF, taille raisonnable
    im = ImageOps.exif_transpose(Image.open(f'{dossier}/photo_brute')).convert('RGB'); im.thumbnail((1600, 1600)); im.save(f'{dossier}/photo.jpg', quality=90)
    besoin = (P.get('project', {}).get('need') or P.get('need') or '_defaut'); style = (P.get('needs', {}).get('style') or P.get('style') or 'contemporain')
    produits = PROD['besoins'].get(besoin, PROD['besoins']['_defaut'])
    data = {'id': os.path.basename(dossier), 'cree_le': time.strftime('%Y-%m-%d'), 'ville': P.get('address', {}).get('city', ''), 'besoin': besoin, 'style': style}
    # 1. diagnostic depuis l'adresse (gratuit)
    if P.get('parcel') and P.get('building'):
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
    subprocess.run(['python3', f'{DIAG}/saisons.py', f'{dossier}/projet.json', '-', f'{dossier}/plantes'], check=True, capture_output=True, timeout=60, env=dict(os.environ, SAISONS_VISUELS='0'))
    data['plantes'] = json.load(open(f'{dossier}/plantes/plantes.json'))
    # 3. lecture de la photo par l'IA : atouts, pistes, placement des produits (texte)
    d = data.get('diag') or {}
    faits = {k: d.get(k) for k in ('surface_jardin_m2', 'soleil_ete_h_moyen', 'soleil_ete_apres14h_h')} | {'vis_a_vis_proche': (d.get('vis_a_vis') or [None])[0]}
    lecture = gpt(f"""Tu es paysagiste-conseil pour Cover Green (clôtures, pergolas, bardages en bois). Voici la photo du jardin d'un particulier.
Son envie : {BESOINS.get(besoin, besoin)}. Style souhaité : {style}. Données calculées depuis son adresse : {json.dumps(faits, ensure_ascii=False)}.
Produits Cover Green à intégrer : {', '.join(PROD[p]['nom'] for p in produits)}.
Réponds en JSON, en français, ton chaleureux et positif, phrases courtes, sans tiret cadratin :
{{"atouts": ["2 ou 3 atouts réels visibles sur la photo"], "pistes": ["2 ou 3 améliorations concrètes, formulées positivement"],
 "placement": {{"cloture": "où poser la clôture sur cette photo pour répondre à l'envie, en une phrase (ou null)", "pergola": "où poser la pergola sur cette photo, décollée de la façade si une fenêtre est derrière (ou null)"}},
 "cloture_longueur_m": nombre estimé (entre 4 et 30), "a_garder": ["seulement les éléments fixes ou plantés à conserver (maison, arbres, arbustes, murets, escaliers, accès) : le mobilier, les tapis et la déco peuvent être remplacés"], "a_retirer": ["encombrants ou objets à faire disparaître (poubelles, bâches, vieux mobilier)"],
 "photo_exploitable": true ou false (false si la photo ne montre pas un extérieur)}}""", [im])
    data['lecture'] = lecture; etat['etapes']['lecture'] = round(time.time() - t0); maj()
    # 4. visuel avec nos produits, contrôlé
    data['visuel'] = None
    if lecture.get('photo_exploitable', True):
        refs = [Image.open(f'{ASSETS}/refs/{r}').convert('RGB') for p in produits for r in PROD[p]['refs']]
        noms = [p for p in produits if (lecture.get('placement') or {}).get(p)]
        consigne = (f"La première image est la photo du jardin d'un client : garde exactement la même maison, le même cadrage, la même perspective et la même lumière. "
                    f"Les images suivantes sont des photos de vrais produits Cover Green posés chez des clients. Reproduis CES produits à l'identique (proportions, sections, espacement des lames, connecteurs, teinte), jamais un modèle générique :\n"
                    + ''.join(f"- {PROD[p]['description_visuel']} : {lecture['placement'][p]}\n" for p in noms)
                    + f"Aménage autour dans un style {STYLES.get(style, style)}, très peu d'entretien, crédible pour un particulier : remplace le mobilier, les tapis et la déco existants par un aménagement neuf dans ce style, ajoute des plantations généreuses. "
                    + (f"Retire : {', '.join(lecture.get('a_retirer') or [])}. " if lecture.get('a_retirer') else '')
                    + (f"Conserve : {', '.join(lecture.get('a_garder') or [])}. " if lecture.get('a_garder') else '')
                    + "Les passages et l'accès à la maison restent libres, aucune fenêtre n'est masquée. Photo réaliste de smartphone, aucun texte.")
        retour = ''
        for essai in range(2):
            editer(consigne + retour, [im] + refs, f'{dossier}/visuel.jpg')
            ctl = claude("""Contrôle qualité d'un visuel d'aménagement pour un client. Image 1 : photo d'origine. Image 2 : visuel proposé. Images suivantes : nos vrais produits (références).
Note de 0 à 10 : "ressemblance" (les produits du visuel ressemblent-ils à nos références : sections, lames, connecteurs, teinte ?), "maison" (la maison est-elle préservée : mêmes fenêtres, portes, façade ?), "credibilite" (le visuel est-il réaliste, sans objet fondu, meuble qui flotte, produit qui traverse un objet ?).
Liste uniquement les "defauts" GRAVES (qui empêchent de montrer l'image au client : maison modifiée, produit qui ne ressemble pas, objet fondu ou impossible, passage bloqué), en une phrase chacun ; les petites imperfections vont dans "remarques". JSON : {"ressemblance": n, "maison": n, "credibilite": n, "defauts": [...], "remarques": [...]}""",
                         [im, Image.open(f'{dossier}/visuel.jpg')] + refs[:4])
            data['controle'] = ctl
            if ctl['ressemblance'] >= 7 and ctl['maison'] >= 7 and ctl['credibilite'] >= 7 and not ctl.get('defauts'):
                data['visuel'] = 'visuel.jpg'; break
            os.replace(f'{dossier}/visuel.jpg', f'{dossier}/visuel_refuse_{essai}.jpg')
            retour = "\nCorrige ces défauts de la première tentative : " + ' ; '.join(ctl.get('defauts') or ['produits pas assez fidèles aux références'])
        etat['etapes']['visuel'] = round(time.time() - t0); maj()
    # 5. produits et budget (fourchettes arrondies)
    r100 = lambda n: int(round(n / 100.0) * 100)
    props = []
    for p in produits:
        c = PROD[p]
        if p == 'cloture':
            L = max(4, min(30, round(float(lecture.get('cloture_longueur_m') or 10) / 2) * 2))
            props.append({'cle': p, 'nom': c['nom'], 'lien': c['lien'], 'photo': c['photo'], 'detail': {'Hauteur': c['hauteur'], 'Longueur': f'environ {L} m'},
                          'placement': (lecture.get('placement') or {}).get(p), 'prix': [r100(L * c['prix_m'][0]), r100(L * c['prix_m'][1])], 'longueur': L})
        else:
            props.append({'cle': p, 'nom': c['nom'], 'lien': c['lien'], 'photo': c['photo'], 'detail': {'Format': c['format'], 'Toiture': 'brise-soleil'},
                          'placement': (lecture.get('placement') or {}).get(p), 'prix': c['prix']})
    data['produits'] = props; data['budget'] = [sum(p['prix'][0] for p in props), sum(p['prix'][1] for p in props)]
    data['duree_s'] = round(time.time() - t0)
    json.dump(data, open(f'{dossier}/data.json', 'w'), ensure_ascii=False, indent=1)
    maj(statut='pret')
    return data


if __name__ == '__main__':
    try:
        print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=1)[:3000])
    except Exception:
        traceback.print_exc(); sys.exit(1)
