# Service « Diagnostic jardin Cover Green » (Cloud Run).
#   POST /api/diagnostic   formulaire : projet (JSON du questionnaire), photo (fichier), prenom, email  -> {id, page}
#   GET  /api/diagnostic/{id}          état et données
#   GET  /projet/{id}                  page personnelle « Mon projet jardin »
#   GET  /fichiers/{id}/{nom}          images du projet ; /assets/... images communes (plantes, réalisations)
import os, json, secrets, threading, html, time, collections
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import pipeline, envoi

DATA = os.environ.get('DATA_DIR', '/data')            # sur Cloud Run : bucket Cloud Storage monté ici
ORIGINES = os.environ.get('ORIGINES', 'https://www.cover.green,https://cover.green,https://dhxx19tchw-staging.onrocket.site,https://mgiogio.github.io').split(',')
app = FastAPI(title='Diagnostic jardin Cover Green')
app.add_middleware(CORSMiddleware, allow_origins=ORIGINES, allow_methods=['GET', 'POST'], allow_headers=['*'])
ICI = os.path.dirname(os.path.abspath(__file__))
GABARIT = open(os.path.join(ICI, 'page.html'), encoding='utf-8').read()


def lancer(dossier):
    try:
        pipeline.run(dossier)
    except Exception as e:
        json.dump({'statut': 'erreur', 'erreur': str(e)[:500]}, open(f'{dossier}/etat.json', 'w'))
        return
    try: envoi.envoyer(dossier, os.path.basename(dossier))     # « votre diagnostic est prêt » (une seule fois)
    except Exception: pass


# garde-fou contre les abus (chaque diagnostic coûte de l'IA) : par adresse IP et par jour, sur chaque instance
LIM_IP, LIM_JOUR = int(os.environ.get('LIMITE_IP_HEURE', '5')), int(os.environ.get('LIMITE_JOUR', '400'))
_vus = collections.defaultdict(list); _jour = {'d': '', 'n': 0}; _verrou = threading.Lock()


def limiter(request):
    # Cloud Run ajoute la vraie adresse en dernier : on ignore ce que le navigateur aurait pu écrire avant
    ip = (request.headers.get('x-forwarded-for') or (request.client.host if request.client else '')).split(',')[-1].strip()
    t = time.time(); j = time.strftime('%Y-%m-%d')
    with _verrou:
        if _jour['d'] != j: _jour.update(d=j, n=0)
        _vus[ip] = [x for x in _vus[ip] if t - x < 3600]
        if len(_vus[ip]) >= LIM_IP: raise HTTPException(429, 'Vous avez déjà lancé plusieurs diagnostics. Réessayez dans une heure.')
        if _jour['n'] >= LIM_JOUR: raise HTTPException(429, 'Le service est très demandé aujourd\'hui. Réessayez demain.')
        _vus[ip].append(t); _jour['n'] += 1


async def lire_photo(photo):
    if photo is None: return None
    if photo.content_type and not (photo.content_type.startswith('image/') or photo.content_type == 'application/octet-stream'): raise HTTPException(400, 'La photo doit être une image.')
    contenu = await photo.read()
    if len(contenu) > 20_000_000: raise HTTPException(400, 'Photo trop lourde (20 Mo maximum).')
    return contenu or None


@app.post('/api/diagnostic')
async def creer(request: Request, projet: str = Form(...), photo: UploadFile | None = File(None), prenom: str = Form(''), email: str = Form('')):
    limiter(request)
    contenu = await lire_photo(photo)
    try: P = json.loads(projet)
    except Exception: raise HTTPException(400, 'Questionnaire illisible.')
    pid = time.strftime('%y%m') + '-' + secrets.token_urlsafe(9)      # lien personnel non devinable
    d = os.path.join(DATA, pid); os.makedirs(d)
    pp = str(P.get('page_projet') or '')
    if not any(pp.startswith(o + '/') for o in ORIGINES): P.pop('page_projet', None)   # lien de la page projet du site, pour l'email
    P['contact'] = dict(P.get('contact') or {}, firstName=prenom or (P.get('contact') or {}).get('firstName', ''), email=email or (P.get('contact') or {}).get('email', ''))
    json.dump(P, open(f'{d}/projet.json', 'w'), ensure_ascii=False)
    if contenu: open(f'{d}/photo_brute', 'wb').write(contenu)
    threading.Thread(target=lancer, args=(d,), daemon=True).start()
    return {'id': pid, 'page': f'/projet/{pid}'}


@app.post('/api/photo/{pid}')
async def ajouter_photo(pid: str, request: Request, photo: UploadFile = File(...)):
    # le client n'avait pas de photo sous la main : il l'ajoute depuis sa page, on refait le visuel
    d = dossier(pid); limiter(request)
    contenu = await lire_photo(photo)
    if not contenu: raise HTTPException(400, 'Photo manquante.')
    open(f'{d}/photo_brute', 'wb').write(contenu)
    json.dump({'statut': 'en_cours', 'etapes': {}}, open(f'{d}/etat.json', 'w'))
    threading.Thread(target=lancer, args=(d,), daemon=True).start()
    return {'ok': True}


# réponses facultatives données pendant la préparation du diagnostic (connaissance client), une par une
INFOS = {'etat': {'neuf', 'creer', 'rafraichir', 'touches'}, 'delai': {'saison', '3mois', 'annee', 'plus', 'reve'},
         'bricolage': {'adore', 'debrouille', 'aide', 'faire'}, 'budget': {'moins1', '1a3', '3a6', 'plus6', 'moins3', '6a12', 'plus12', 'nsp'},
         'pose': {'moi', 'proche', 'poseur', 'nsp'}, 'frein': {'commencer', 'budget', 'montage', 'choix', 'temps', 'rien'},
         'statut': {'proprietaire', 'locataire', 'achat'}, 'source': {'google', 'social', 'pinterest', 'bouche', 'client', 'autre'}}


@app.post('/api/infos/{pid}')
async def infos(pid: str, request: Request):
    d = dossier(pid)
    try: A = await request.json()
    except Exception: raise HTTPException(400, 'Réponse illisible.')
    f = f'{d}/infos.json'; I = json.load(open(f)) if os.path.exists(f) else {}
    for k, v in (A or {}).items():
        if k in INFOS and v in INFOS[k]: I[k] = v
        elif k == 'telephone' and isinstance(v, str):
            t = ''.join(c for c in v if c.isdigit() or c == '+')[:16]
            if len(t) >= 9: I['telephone'] = t
        elif k == 'rappel' and v in ('matin', 'midi', 'soir', 'indifferent'): I['rappel'] = v
        elif k == 'reve' and isinstance(v, str): I['reve'] = v.strip()[:600]
        elif k == 'prenom' and isinstance(v, str) and v.strip():
            # prénom donné après l'envoi : il sert à l'email et au rappel
            I['prenom'] = v.strip()[:60]
            P = json.load(open(f'{d}/projet.json')); P.setdefault('contact', {})['firstName'] = I['prenom']
            json.dump(P, open(f'{d}/projet.json', 'w'), ensure_ascii=False)
    I['maj'] = time.strftime('%Y-%m-%d %H:%M'); json.dump(I, open(f, 'w'), ensure_ascii=False, indent=1)
    return {'ok': True}


_vus_t = collections.defaultdict(list)


@app.get('/api/terrain')
def api_terrain(lat: float, lon: float, request: Request):
    # aperçu « c'est bien chez vous ? » : parcelle, maison, surfaces (données publiques IGN)
    if not (41 < lat < 51.5 and -5.5 < lon < 10): raise HTTPException(400, 'Adresse hors de France métropolitaine.')
    ip = (request.headers.get('x-forwarded-for') or '').split(',')[-1].strip(); t = time.time()
    with _verrou:
        _vus_t[ip] = [x for x in _vus_t[ip] if t - x < 3600]
        if len(_vus_t[ip]) >= 60: raise HTTPException(429, 'Trop de recherches, réessayez dans un moment.')
        _vus_t[ip].append(t)
    import terrain
    try: return terrain.terrain(lat, lon)
    except Exception: raise HTTPException(404, 'Terrain introuvable.')


@app.get('/q/{nom}')
def questionnaire_fichier(nom: str):
    f = os.path.join(ICI, 'questionnaire', os.path.basename(nom))
    if not os.path.isfile(f): raise HTTPException(404)
    return FileResponse(f, headers={'Cache-Control': 'public, max-age=300', 'Access-Control-Allow-Origin': '*'})


@app.get('/lp', response_class=HTMLResponse)
def page_lp(request: Request):
    # contenu sous le questionnaire (ce que l'on reçoit, plantes, FAQ), inséré par le shortcode du site
    import lp
    base = str(request.base_url).rstrip('/').replace('http://', 'https://') if request.url.hostname not in ('127.0.0.1', 'localhost') else ''
    return HTMLResponse(lp.rendre(base), headers={'Cache-Control': 'public, max-age=600'})


@app.get('/questionnaire', response_class=HTMLResponse)
def questionnaire_page():
    # page de test autonome ; sur le site, le questionnaire est intégré par le shortcode [cg_diagnostic_jardin]
    return HTMLResponse('''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Diagnostic jardin</title><link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;800&display=swap" rel="stylesheet">
<body style="margin:0;background:#fff"><div style="background:#F4F6F7">''' + __import__('lp').rendre('') + '''</div><div id="cg-diag" data-api="" data-projet="/projet/"></div><script src="/q/q.js"></script></body></html>''')


def dossier(pid):
    d = os.path.join(DATA, os.path.basename(pid))
    if not os.path.isdir(d): raise HTTPException(404, 'Projet introuvable.')
    return d


@app.post('/api/avis/{pid}')
async def avis(pid: str, request: Request):
    d = dossier(pid)
    try: A = await request.json()
    except Exception: raise HTTPException(400, 'Avis illisible.')
    note = A.get('note') if A.get('note') in ('haut', 'bas') else None
    if not note: raise HTTPException(400, 'Note manquante.')
    MOTIFS = {'visuel', 'produits', 'budget', 'plantes', 'soleil', 'autre'}
    ligne = {'le': time.strftime('%Y-%m-%d %H:%M'), 'note': note, 'motifs': [m for m in (A.get('motifs') or []) if m in MOTIFS][:6], 'texte': str(A.get('texte') or '')[:1500]}
    f = f'{d}/avis.json'; L = json.load(open(f)) if os.path.exists(f) else []
    L.append(ligne); json.dump(L, open(f, 'w'), ensure_ascii=False, indent=1)
    return {'ok': True}


@app.get('/api/diagnostic/{pid}')
def lire(pid: str):
    d = dossier(pid); etat = json.load(open(f'{d}/etat.json')) if os.path.exists(f'{d}/etat.json') else {'statut': 'en_attente'}
    if etat.get('statut') == 'pret': etat['data'] = json.load(open(f'{d}/data.json'))
    etat['email'] = envoi.etat(d)
    return JSONResponse(etat)


@app.post('/api/renvoyer/{pid}')
async def renvoyer(pid: str, request: Request):
    # « Pas reçu ? » : renvoi de l'email, éventuellement à une adresse corrigée
    d = dossier(pid)
    try: A = await request.json()
    except Exception: A = {}
    P = json.load(open(f'{d}/projet.json')); C = P.setdefault('contact', {})
    m = str((A or {}).get('email') or '').strip()[:120]
    if m:
        if not envoi.EMAIL_OK.match(m): raise HTTPException(400, 'Cette adresse email ne semble pas valide.')
        C['email'] = m; json.dump(P, open(f'{d}/projet.json', 'w'), ensure_ascii=False)
    if len(envoi.lire(d)['envois']) >= envoi.MAX_ENVOIS: raise HTTPException(429, 'Nous avons déjà envoyé plusieurs emails. Écrivez-nous à contact@cover.green.')
    ok = envoi.envoyer(d, pid, force=True)
    if not ok: raise HTTPException(503, "L'envoi n'a pas marché, réessayez dans un instant.")
    return {'ok': True, 'email': C['email']}


@app.post('/api/vu/{pid}')
def vu(pid: str, src: str = ''):
    # ouverture de la page projet depuis l'email : adresse confirmée
    d = dossier(pid)
    if src == 'email':
        M = envoi.lire(d); M['clics'].append(time.strftime('%Y-%m-%d %H:%M')); M['clics'] = M['clics'][-20:]; envoi.ecrire(d, M)
    return {'ok': True}


@app.get('/fichiers/{pid}/{nom}')
def fichier(pid: str, nom: str):
    if nom not in ('photo.jpg', 'visuel.jpg', 'plan.png'): raise HTTPException(404)
    f = os.path.join(dossier(pid), nom)
    if not os.path.exists(f): raise HTTPException(404)
    return FileResponse(f, headers={'Cache-Control': 'public, max-age=86400'})


@app.get('/assets/{genre}/{nom}')
def asset(genre: str, nom: str):
    if genre not in ('plantes', 'refs'): raise HTTPException(404)
    f = os.path.join(ICI, 'assets', genre, os.path.basename(nom))
    if not os.path.exists(f): raise HTTPException(404)
    return FileResponse(f, headers={'Cache-Control': 'public, max-age=604800'})


e = lambda s: html.escape(str(s or ''))
eur = lambda n: f'{n:,}'.replace(',', ' ') + ' €'
LAB = {'printemps': 'Printemps', 'ete': 'Été', 'automne': 'Automne', 'hiver': 'Hiver'}
ROLE = {'focal': 'Arbuste vedette', 'structure': 'Persistant de structure', 'vivace': 'Vivace fleurie', 'graminee': 'Graminée', 'grimpante': 'Grimpante', 'fleuri': 'Arbuste fleuri', 'couvre_sol': 'Couvre-sol'}


def soleil(f):
    # même dégradé que le plan vu du ciel : ombre (bleu-gris) -> soleil doux (jaune) -> plein soleil (orange)
    f = max(0.0, min(1.0, float(f))); pts = [(0, (150, 172, 196)), (0.5, (255, 222, 140)), (1, (232, 116, 42))]
    (a, ca), (b, cb) = (pts[0], pts[1]) if f <= 0.5 else (pts[1], pts[2]); t = (f - a) / (b - a)
    return '#%02x%02x%02x' % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


# projet lancé sans photo : le client l'ajoute ici et reçoit son idée d'aménagement quelques minutes plus tard
AJOUT_PHOTO = '''<style>.cgp .demo{display:grid;grid-template-columns:minmax(0,1fr) 44px minmax(0,1fr);align-items:stretch;gap:6px}
.cgp .demo .case{position:relative;aspect-ratio:3/4;border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:16px;text-align:center;box-sizing:border-box}
.cgp .demo .case .tag{position:absolute;left:8px;top:8px;background:#fff;border-radius:6px;padding:4px 9px;font-size:13px;font-weight:700}
.cgp .demo .avant{white-space:normal;min-width:0;height:auto;border:2px dashed #049E00;background:#EAF7E5;cursor:pointer;font:inherit;color:#1E211F;width:100%}
.cgp .demo .avant:hover{background:#DDF1D4}.cgp .demo .avant svg{width:44px;height:44px;color:#049E00}
.cgp .demo .avant b{font-size:17px}.cgp .demo .avant small{color:#5B625E;font-size:14px;line-height:1.35}
.cgp .demo .apres{background:#F4F6F7;border:1px solid #E1E5E3;color:#5B625E}.cgp .demo .apres svg{width:44px;height:44px;color:#9AA29E}
.cgp .demo .apres span.t{font-size:15px;line-height:1.4}
.cgp .demo .fl{display:grid;place-items:center;color:#049E00}.cgp .demo .fl svg{width:36px;height:36px}
.cgp .bloc li.sansbul{display:block;padding-left:24px}.cgp .bloc li.sansbul::before{display:none}
.cgp #cgp-ajout-msg:empty{display:none}
@media (min-width:761px){.cgp .visu:has(#cgp-ajout-bloc){align-items:stretch}.cgp .visu:has(#cgp-ajout-bloc)>div{display:flex;flex-direction:column}
.cgp .visu:has(#cgp-ajout-bloc) .demo{flex:1}.cgp .visu:has(#cgp-ajout-bloc) .demo .case{aspect-ratio:auto;height:100%;min-height:360px}}
@media (max-width:600px){.cgp .demo{grid-template-columns:minmax(0,1fr) 26px minmax(0,1fr)}.cgp .demo .fl svg{width:24px;height:24px}.cgp .demo .case{padding:10px}.cgp .demo .avant b{font-size:15px}.cgp .demo .avant small,.cgp .demo .apres span.t{font-size:13px}}</style>
<div class="demo" id="cgp-ajout-bloc">
<button type="button" class="case avant" onclick="document.getElementById('cgp-ajout').click()"><span class="tag">Avant</span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>
<b>Envoyer la photo de mon jardin</b><small>Prise depuis la maison ou la terrasse, de jour. Sur ordinateur, glissez-la ici.</small></button>
<span class="fl" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></svg></span>
<div class="case apres"><span class="tag">Après</span>
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9h18M5 9l2-4h10l2 4M6 9v11M18 9v11M9 9v3M12 9v3M15 9v3M3 20h18"/></svg>
<span class="t">Votre jardin aménagé avec nos produits apparaîtra ici, 3 minutes après votre photo</span></div></div>
<input type="file" accept="image/*" id="cgp-ajout" hidden><p id="cgp-ajout-msg" class="note" role="status" style="margin:10px 0 0"></p>
<script>(function(){var i=document.getElementById("cgp-ajout"),m=document.getElementById("cgp-ajout-msg"),z=document.querySelector("#cgp-ajout-bloc .avant");if(z){["dragenter","dragover"].forEach(function(t){z.addEventListener(t,function(e){e.preventDefault();z.style.background="#DDF1D4"})});z.addEventListener("dragleave",function(){z.style.background=""});z.addEventListener("drop",function(e){e.preventDefault();var f=e.dataTransfer&&e.dataTransfer.files[0];if(f&&f.type.indexOf("image")===0)envoyer(f);else m.textContent="Déposez une photo (JPG ou PNG)."})}i.onchange=function(){var f=i.files[0];if(f)envoyer(f)};function envoyer(f){m.textContent="Envoi de la photo…";
var r=document.querySelector(".cgp[data-api]"),api=r?r.getAttribute("data-api"):"",fd=new FormData();fd.append("photo",f);
try{var a=document.querySelector("#cgp-ajout-bloc .avant"),u=URL.createObjectURL(f);a.style.background="center/cover url("+u+")";a.style.borderStyle="solid";[].forEach.call(a.querySelectorAll("svg,b,small"),function(x){x.style.visibility="hidden"})}catch(e){}
fetch(api+"/api/photo/PID",{method:"POST",body:fd}).then(function(x){if(!x.ok)throw 0;m.textContent="C'est parti : votre jardin aménagé arrive dans 3 minutes, cette page se mettra à jour.";var t=document.querySelector("#cgp-ajout-bloc .apres .t");if(t)t.textContent="En préparation…";try{dataLayer.push({event:"cgp_ajout_photo",projet_jardin:"PID"})}catch(e){}setTimeout(function(){location.reload()},150000)}).catch(function(){m.textContent="L'envoi n'a pas marché, réessayez."})}})()</script>'''


def rendre(pid, d):
    D = json.load(open(f'{d}/data.json')); g = D.get('diag') or {}; L = D.get('lecture') or {}
    v = (g.get('vis_a_vis') or [None])[0]
    faits = ''
    if g:
        faits += f'''<div class="fact"><span class="k">Soleil le 21 juin</span><span class="val">{str(g["soleil_ete_h_moyen"]).replace(".", ",")} h <small>par jour</small></span>
          <div class="sunbar">{''.join(f'<i style="background:{soleil(f)}"></i>' for f in (g.get("soleil_ete_profil_8h_21h") or []))}</div>
          <div class="hours"><span>8 h</span><span>14 h</span><span>21 h</span></div><div class="sunleg"><span>ombre</span><i></i><span>plein soleil</span></div><p>Dont {str(g["soleil_ete_apres14h_h"]).replace(".", ",")} h après 14 h, au moment le plus chaud.</p></div>'''
        # l'œil est mesuré depuis le niveau de votre jardin (relief compris) : une maison en contrebas n'est plus comptée
        if v and v.get('oeil_m', 0) >= 3 and ('denivele_m' in v or v['hauteur_m'] >= 5):
            dist = 'en limite de terrain' if v['distance_m'] < 1 else f'à {str(v["distance_m"]).replace(".", ",")} m'
            dz = v.get('denivele_m') or 0
            relief = ' Elle est construite plus haut que votre terrain, ce qui renforce la vue.' if dz >= 1 else ''
            faits += f'''<div class="fact"><span class="k">Vis-à-vis</span><span class="val">{v["oeil_m"]:.0f} m <small>de hauteur de vue, {dist}</small></span>
          <p>Depuis son étage, une maison voisine côté {e(v["direction"])} voit votre jardin d'environ {v["oeil_m"]:.0f} m de haut.{relief}</p></div>'''
        faits += f'''<div class="fact"><span class="k">Votre terrain</span><span class="val">{g["surface_parcelle_m2"]} m² <small>dont {g["surface_jardin_m2"]} de jardin</small></span>
          <p>{g["part_jardin_plus_6h_ete"]} % du jardin a plus de 6 h de soleil en été.</p></div>'''
    atouts = ''.join(f'<li>{e(a)}</li>' for a in L.get('atouts') or []); pistes = ''.join(f'<li>{e(a)}</li>' for a in L.get('pistes') or [])
    visuel = (f'''<div class="cmp" id="cmp" style="--p:50%"><img src="/fichiers/{pid}/visuel.jpg" alt="Idée d'aménagement avec nos produits"><img class="av" src="/fichiers/{pid}/photo.jpg" alt="Votre photo">
          <span class="bar"></span><span class="tag l">Avant</span><span class="tag r">Idée Cover Green</span><input id="cmp-range" type="range" min="0" max="100" value="50" aria-label="Comparer avant et après"></div>
          <p class="note">Idée d'aménagement non contractuelle, réalisée avec nos produits.</p>''' if D.get('visuel') else
              (AJOUT_PHOTO.replace('PID', e(pid)) if not os.path.exists(f'{d}/photo.jpg') else
               '<div class="refs">' + ''.join(f'<img src="/assets/refs/{p["photo"]}" alt="{e(p["nom"])} Cover Green">' for p in D['produits']) + '</div><p class="note">Des réalisations Cover Green proches de votre projet.</p>'))
    if not os.path.exists(f'{d}/photo.jpg'):
        # atouts et pistes viennent de la lecture de la photo : sans photo, on le dit et on renvoie vers l'envoi
        lien = '<li class="sansbul"><a href="#cgp-ajout-bloc" onclick="document.getElementById(\'cgp-ajout\').click();return false" style="color:#049E00;font-weight:700">Envoyer ma photo</a></li>'
        atouts = atouts or '<li>Avec une photo de votre jardin, nous repérons ses atouts : ce qu\'il faut garder et mettre en valeur.</li>' + lien
        pistes = pistes or '<li>Avec une photo, nous vous donnons des pistes concrètes pour votre jardin, avec nos produits au bon endroit.</li>' + lien
    pl = (D.get('plantes') or {}).get('plantes') or []
    M = 'JFMAMJJASOND'
    NOMS_MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
    def periodes(ms):   # [3, 4, 10, 11] -> « mars-avr. ou oct.-nov. »
        ms = sorted(ms); g = []
        for m in ms:
            if g and m == g[-1][-1] + 1: g[-1].append(m)
            else: g.append([m])
        return ' ou '.join(NOMS_MOIS[a[0] - 1] + ('-' + NOMS_MOIS[a[-1] - 1] if len(a) > 1 else '') for a in g)
    def case(p, m):
        c = 'fl' if m in p['mois_fleurs'] else ('fo' if ('persistant' in p['hiver'] or 'marcescent' in p['hiver'] or 4 <= m <= 10) else '')
        pl = '<span class="pl" aria-label="à planter">●</span>' if m in (p.get('mois_plantation') or []) else ''
        return f'<td class="{c}">{pl}</td>'
    cal = ''.join(f'<tr><th scope="row">{e(p["nom"])}</th>' + ''.join(case(p, m + 1) for m in range(12)) + '</tr>' for p in pl)
    cartes = ''.join(f'''<article class="pcard"><img src="/assets/plantes/{e(p["photo"])}" alt="{e(p["nom"])}" loading="lazy"><div class="pc"><span class="role">{ROLE.get(p["role"], p["role"])}</span><h4>{e(p["nom"])}</h4><i>{e(p["latin"])}</i>
        <div class="badges">{''.join(f'<span class="badge">{LAB[s]}</span>' for s in ("printemps", "ete", "automne", "hiver") if s in p["saisons"])}</div>
        <dl><div><dt>Fleurs</dt><dd>{e(p["floraison"] or "feuillage décoratif")}</dd></div><div><dt>Plantation</dt><dd>{periodes(p.get("mois_plantation") or [])}</dd></div><div><dt>Hiver</dt><dd>{e(p["hiver"])}</dd></div><div><dt>Entretien</dt><dd>{e(p["entretien"])}</dd></div></dl></div></article>''' for p in pl)
    VERBE = {'cloture': 'Configurer ma clôture', 'pergola': 'Configurer ma pergola'}
    prods = ''.join(f'''<div class="prod"><img src="/assets/refs/{p["photo"]}" alt=""><div><h3>{e(p["nom"])}</h3><p class="why">{e(p.get("placement"))}</p>
        <dl class="spec">{''.join(f'<div><dt>{e(k)}</dt><dd>{e(x)}</dd></div>' for k, x in p["detail"].items())}</dl></div>
        <div class="est"><small>Estimation</small><b>{eur(p["prix"][0])} à {eur(p["prix"][1])}</b><a class="cta reduit{"" if i == 0 else " sec"}" data-ev="cgp_configurer" data-produit="{p.get("cle", "")}" href="{p["lien"]}" target="_blank" rel="noopener">{VERBE.get(p.get("cle"), "Configurer")}</a></div></div>''' for i, p in enumerate(D['produits']))
    comp = D.get('complements') or []
    compl = ('<h3 class="h-compl">Pour compléter votre projet</h3><div class="compl">' + ''.join(f'''<div class="carte cpl"><img src="/assets/refs/{c["photo"]}" alt="" loading="lazy"><div class="cplt"><h4>{e(c["nom"])}</h4><p>{e(c["pourquoi"])}</p>
        <div class="cplp"><b>{eur(c["prix"][0])} à {eur(c["prix"][1])}</b><a class="cta gris reduit" data-ev="cgp_complement" data-produit="{c["cle"]}" href="{c["lien"]}" target="_blank" rel="noopener">{e(c["bouton"])}</a></div></div></div>''' for c in comp) + '</div>') if comp else ''
    b0, b1 = D['budget']
    budget = f'''<div class="r big"><span>Vos produits Cover Green</span><span>{eur(b0)} à {eur(b1)}</span></div>'''
    if comp:
        c0, c1 = b0 + sum(c['prix'][0] for c in comp), b1 + sum(c['prix'][1] for c in comp)
        budget += f'''<div class="r"><span>Avec les compléments</span><span><b>{eur(c0)} à {eur(c1)}</b></span></div>'''
    budget += '''<div class="r"><span>Livraison</span><span>offerte dès 2 000 €</span></div><div class="r"><span>Paiement</span><span>en 1x à 4x sans frais</span></div>
      <p class="note" style="margin:4px 0 0">Prix exact dans chaque configurateur, selon vos choix.</p>'''
    R = D.get('reste')
    if R:
        t0, t1 = R['total']; p0, p1 = (c0, c1) if comp else (b0, b1)
        budget += ('<div class="reste"><div class="r big2"><span>Le reste du visuel</span><span>' + f'{eur(t0)} à {eur(t1)}</span></div>'
                   + ''.join(f'<div class="r"><span>{e(k)}</span><span>{eur(v[0])} à {eur(v[1])}</span></div>' for k, v in R['lignes'].items())
                   + f'<div class="r big2 tout"><span>Votre jardin comme sur le visuel</span><span>{eur(p0 + t0)} à {eur(p1 + t1)}</span></div>'
                   + '<p class="note" style="margin:4px 0 0">Mobilier, plantes et finitions : estimation indicative aux prix moyens des jardineries et enseignes de mobilier, à choisir où vous voulez.</p></div>')
    else:
        budget += '<p class="note" style="margin:0">Le mobilier, les plantes et le sol du visuel sont là pour l\'ambiance : ils ne sont pas compris.</p>'
    budget += '<p class="confiance"><b>★ 4,6/5</b> sur Trustpilot, plus de 300 avis · plus de 3 000 clients équipés en kit</p>'
    planbloc = (f'''<div class="planrow"><div class="carte plan"><img src="/fichiers/{pid}/plan.png" alt="Votre parcelle vue du ciel"></div><div><h3>Votre parcelle vue du ciel</h3>
      <ul class="legend"><li><span class="sw" style="background:linear-gradient(90deg,#96acc4,#ffde8c,#e8742a)"></span>Heures de soleil le 21 juin, de l'ombre au plein soleil</li><li><span class="sw" style="background:#344239"></span>Votre maison</li><li><span class="sw" style="background:#d6dad2;border:1px solid #b0b6ac"></span>Maisons voisines, avec leur hauteur</li><li><span class="sw" style="background:#c43428;border-radius:50%"></span>Voisin qui a vue sur votre jardin</li></ul></div></div>''' if D.get('plan') else '')
    rep = {'ID': e(pid), 'VILLE': e(D.get('ville')), 'DATE': e(D.get('cree_le')), 'VISUEL': visuel, 'FAITS': faits, 'ATOUTS': atouts, 'PISTES': pistes,
           'PLANBLOC': planbloc, 'CARTES': cartes,
           'CAL': cal, 'MOIS': ''.join(f'<th scope="col">{m}</th>' for m in M), 'PRODUITS': prods, 'COMPLEMENTS': compl, 'BUDGET': budget}
    out = GABARIT
    for k, x in rep.items(): out = out.replace('{{' + k + '}}', x)
    if not os.path.exists(f'{d}/photo.jpg'):
        out = out.replace('à partir de votre adresse et de votre photo', 'à partir de votre adresse').replace('<h2>Votre jardin, demain</h2>', '<h2>Votre jardin imaginé avec nos produits</h2>')
    return out


ATTENTE = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="8">
<title>Votre projet se prépare</title><body style="font:16px/1.5 Roboto,system-ui,sans-serif;background:#f5f6f2;color:#1d2a22;display:grid;place-items:center;min-height:90vh;margin:0;padding:0 16px">
<div style="max-width:440px;text-align:center"><h1 style="font:700 26px 'Roboto Slab',Georgia,serif">Votre projet jardin se prépare</h1>
<p>Nous calculons le soleil de votre jardin et préparons votre idée d'aménagement avec nos produits. Cela prend environ deux minutes, cette page se met à jour toute seule.</p></div></body>'''


@app.get('/projet/{pid}', response_class=HTMLResponse)
def page(pid: str):
    d = dossier(pid); etat = json.load(open(f'{d}/etat.json')) if os.path.exists(f'{d}/etat.json') else {}
    if etat.get('statut') != 'pret':
        if etat.get('statut') == 'erreur': return HTMLResponse(ATTENTE.replace('se prépare', 'arrive bientôt').replace('<meta http-equiv="refresh" content="8">', ''), status_code=200)
        return HTMLResponse(ATTENTE)
    return HTMLResponse(rendre(pid, d))


@app.get('/fragment/{pid}', response_class=HTMLResponse)
def fragment(pid: str, request: Request):
    # contenu seul (styles + page), à insérer dans une page du site entre l'en-tête et le pied de page
    d = dossier(pid); etat = json.load(open(f'{d}/etat.json')) if os.path.exists(f'{d}/etat.json') else {}
    if etat.get('statut') != 'pret': return HTMLResponse('', status_code=202)
    h = rendre(pid, d); base = str(request.base_url).rstrip('/').replace('http://', 'https://')
    return HTMLResponse(h[h.index('<!--DEBUT-->'):h.index('<!--FIN-->')].replace('src="/', f'src="{base}/').replace('data-api=""', f'data-api="{base}"'))


CLE_ADMIN = os.environ.get('CLE_ADMIN', '')
INFO_LAB = {'saison': 'Cette saison', '3mois': 'Dans les 3 mois', 'annee': "Dans l'année", 'reve': 'Se renseigne', 'moins3': 'Moins de 3 000 €', '3a6': '3 000 à 6 000 €',
            '6a12': '6 000 à 12 000 €', 'plus12': 'Plus de 12 000 €', 'nsp': 'Ne sait pas', 'moi': 'Lui-même', 'proche': 'Avec un proche', 'poseur': 'Cherche un poseur',
            'montage': 'Le montage', 'choix': 'Choisir les produits', 'temps': 'Le temps', 'rien': 'Rien', 'budget': 'Le budget', 'proprietaire': 'Propriétaire',
            'locataire': 'Locataire', 'achat': 'Achat en cours', 'google': 'Google', 'social': 'Instagram ou Facebook', 'pinterest': 'Pinterest', 'bouche': 'Bouche-à-oreille',
            'client': 'Déjà client', 'autre': 'Autre', 'neuf': 'Maison neuve', 'creer': 'Jardin à créer', 'rafraichir': 'À rafraîchir', 'touches': 'Quelques touches',
            'plus': 'Plus tard', 'adore': 'Adore bricoler', 'debrouille': 'Se débrouille', 'aide': 'Avec un coup de main', 'faire': 'Préfère faire faire',
            'commencer': 'Par où commencer', 'moins1': 'Moins de 1 000 €', '1a3': '1 000 à 3 000 €', 'plus6': 'Plus de 6 000 €'}
QLAB = {'etat': 'Jardin', 'delai': 'Délai', 'bricolage': 'Bricolage', 'budget': 'Enveloppe', 'pose': 'Montage', 'frein': 'Frein', 'statut': 'Statut', 'canal': 'Canal'}
MOTIF_LAB = {'visuel': 'Le visuel', 'produits': 'Les produits proposés', 'budget': 'Le budget', 'plantes': 'Les plantes', 'soleil': 'Le soleil et le terrain', 'autre': 'Autre chose'}


@app.get('/admin/avis', response_class=HTMLResponse)
def admin_avis(cle: str = ''):
    # récapitulatif des diagnostics et des avis clients (accès par clé privée)
    if not CLE_ADMIN or not secrets.compare_digest(cle, CLE_ADMIN): raise HTTPException(404)
    reponses = collections.defaultdict(collections.Counter)
    lignes, n, prets, visuels, haut, bas, motifs_b, motifs_h, durees = [], 0, 0, 0, 0, 0, collections.Counter(), collections.Counter(), []
    for pid in sorted(os.listdir(DATA), reverse=True):
        d = os.path.join(DATA, pid)
        if not os.path.isfile(f'{d}/projet.json'): continue
        n += 1
        D = json.load(open(f'{d}/data.json')) if os.path.exists(f'{d}/data.json') else {}
        if D: prets += 1; visuels += bool(D.get('visuel')); durees.append(D.get('duree_s') or 0)
        A = json.load(open(f'{d}/avis.json')) if os.path.exists(f'{d}/avis.json') else []
        dernier = A[-1] if A else None
        if dernier:
            haut += dernier['note'] == 'haut'; bas += dernier['note'] == 'bas'
            for x in A:
                for m in x.get('motifs') or []: (motifs_h if x['note'] == 'haut' else motifs_b)[m] += 1
        textes = ' / '.join(e(x['texte']) for x in A if x.get('texte'))
        I = json.load(open(f'{d}/infos.json')) if os.path.exists(f'{d}/infos.json') else {}
        Pj = json.load(open(f'{d}/projet.json')); sv = Pj.get('suivi') or {}
        src = sv.get('utm_source') or ('google ads' if sv.get('gclid') else '') or ('meta' if sv.get('fbclid') else '') or INFO_LAB.get(I.get('source'), '')
        for k in INFOS: 
            if I.get(k): reponses[k][I[k]] += 1
        if src: reponses['canal'][src] += 1
        lignes.append(f'''<tr><td>{e(D.get('cree_le', pid[:4]))}</td><td><a href="/projet/{e(pid)}" target="_blank">{e(pid)}</a></td><td>{e(D.get('ville'))}</td>
          <td>{'oui' if D.get('visuel') else ('non' if D else 'en cours')}</td><td>{eur(D['budget'][0]) + ' à ' + eur(D['budget'][1]) if D.get('budget') else ''}</td>
          <td class="n">{'👍' if dernier and dernier['note'] == 'haut' else ('👎' if dernier else '')}</td>
          <td>{', '.join(MOTIF_LAB.get(m, m) for x in A for m in (x.get('motifs') or []))}</td><td>{textes}</td>
          <td>{e(INFO_LAB.get(I.get('etat'), ''))} {e(INFO_LAB.get(I.get('delai'), ''))}</td><td>{e(INFO_LAB.get(I.get('budget'), ''))}</td><td>{e(INFO_LAB.get(I.get('bricolage') or I.get('pose'), ''))}</td><td>{e(INFO_LAB.get(I.get('frein'), ''))}</td>
          <td>{e(INFO_LAB.get(I.get('statut'), ''))}</td><td>{e(src)}</td><td>{'oui' if Pj.get('photos') or os.path.exists(f'{d}/photo.jpg') else 'non'}</td><td>{e(I.get('telephone', ''))} {e(I.get('rappel', ''))}</td><td>{('cliqué' if envoi.etat(d)['clic'] else ('envoyé' if envoi.etat(d)['envoye'] else ''))}</td></tr>''')
    pc = lambda a, b: f'{round(100 * a / b)} %' if b else '-'
    mot = lambda C: ''.join(f'<li>{MOTIF_LAB.get(k, k)} : <b>{v}</b></li>' for k, v in C.most_common()) or '<li>aucun</li>'
    return HTMLResponse(f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Avis diagnostic jardin</title>
<style>body{{font:15px/1.5 Roboto,Arial,sans-serif;color:#1E211F;margin:0;padding:24px 16px;background:#fff}}h1{{font-weight:800;margin:0 0 16px}}.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:20px}}
.k div{{background:#F4F6F7;border-radius:8px;padding:14px}}.k b{{display:block;font-size:26px;font-weight:800}}.m{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}}.m div{{background:#EAF7E5;border-radius:8px;padding:14px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #E1E5E3;vertical-align:top}}th{{background:#F4F6F7}}a{{color:#049E00}}.w{{overflow-x:auto}}</style>
<h1>Diagnostic jardin : avis clients</h1>
<div class="k"><div><b>{n}</b>diagnostics lancés</div><div><b>{pc(visuels, prets)}</b>avec un visuel validé</div><div><b>{round(sum(durees) / len(durees)) if durees else '-'} s</b>temps moyen</div>
<div><b>{haut} 👍 / {bas} 👎</b>avis donnés ({pc(haut + bas, prets)} des diagnostics)</div><div><b>{pc(haut, haut + bas)}</b>de satisfaits</div></div>
<div class="m"><div><h3>Ce qui a plu</h3><ul>{mot(motifs_h)}</ul></div><div><h3>Ce qui n'a pas plu</h3><ul>{mot(motifs_b)}</ul></div></div>
<div class="m">{''.join(f'<div><h3>{QLAB[k]}</h3><ul>' + ''.join(f'<li>{e(INFO_LAB.get(a, a))} : <b>{v}</b></li>' for a, v in reponses[k].most_common()) + '</ul></div>' for k in QLAB if reponses[k])}</div>
<div class="w"><table><tr><th>Date</th><th>Projet</th><th>Ville</th><th>Visuel</th><th>Budget Cover Green</th><th>Avis</th><th>Motifs</th><th>Commentaire</th><th>Jardin, délai</th><th>Enveloppe</th><th>Bricolage</th><th>Frein</th><th>Statut</th><th>Canal</th><th>Photo</th><th>Rappel</th><th>Email</th></tr>{''.join(lignes)}</table></div>''')


@app.get('/')
def accueil():
    # l'adresse technique du service ne sert à rien seule : on renvoie vers le site
    return RedirectResponse('https://www.cover.green/', status_code=302)


@app.get('/sante')
def sante():
    return {'ok': True}
