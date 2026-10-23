# Service « Diagnostic jardin Cover Green » (Cloud Run).
#   POST /api/diagnostic   formulaire : projet (JSON du questionnaire), photo (fichier), prenom, email  -> {id, page}
#   GET  /api/diagnostic/{id}          état et données
#   GET  /projet/{id}                  page personnelle « Mon projet jardin »
#   GET  /fichiers/{id}/{nom}          images du projet ; /assets/... images communes (plantes, réalisations)
import os, json, secrets, threading, html, time
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pipeline

DATA = os.environ.get('DATA_DIR', '/data')            # sur Cloud Run : bucket Cloud Storage monté ici
ORIGINES = os.environ.get('ORIGINES', 'https://www.cover.green,https://dhxx19tchw-staging.onrocket.site,https://mgiogio.github.io').split(',')
app = FastAPI(title='Diagnostic jardin Cover Green')
app.add_middleware(CORSMiddleware, allow_origins=ORIGINES, allow_methods=['GET', 'POST'], allow_headers=['*'])
ICI = os.path.dirname(os.path.abspath(__file__))
GABARIT = open(os.path.join(ICI, 'page.html'), encoding='utf-8').read()


def lancer(dossier):
    try:
        pipeline.run(dossier)
    except Exception as e:
        json.dump({'statut': 'erreur', 'erreur': str(e)[:500]}, open(f'{dossier}/etat.json', 'w'))


@app.post('/api/diagnostic')
async def creer(projet: str = Form(...), photo: UploadFile = File(...), prenom: str = Form(''), email: str = Form('')):
    if photo.content_type and not photo.content_type.startswith('image/'): raise HTTPException(400, 'La photo doit être une image.')
    contenu = await photo.read()
    if len(contenu) > 20_000_000: raise HTTPException(400, 'Photo trop lourde (20 Mo maximum).')
    try: P = json.loads(projet)
    except Exception: raise HTTPException(400, 'Questionnaire illisible.')
    pid = time.strftime('%y%m') + '-' + secrets.token_urlsafe(9)      # lien personnel non devinable
    d = os.path.join(DATA, pid); os.makedirs(d)
    P['contact'] = dict(P.get('contact') or {}, firstName=prenom or (P.get('contact') or {}).get('firstName', ''), email=email or (P.get('contact') or {}).get('email', ''))
    json.dump(P, open(f'{d}/projet.json', 'w'), ensure_ascii=False); open(f'{d}/photo_brute', 'wb').write(contenu)
    threading.Thread(target=lancer, args=(d,), daemon=True).start()
    return {'id': pid, 'page': f'/projet/{pid}'}


def dossier(pid):
    d = os.path.join(DATA, os.path.basename(pid))
    if not os.path.isdir(d): raise HTTPException(404, 'Projet introuvable.')
    return d


@app.get('/api/diagnostic/{pid}')
def lire(pid: str):
    d = dossier(pid); etat = json.load(open(f'{d}/etat.json')) if os.path.exists(f'{d}/etat.json') else {'statut': 'en_attente'}
    if etat.get('statut') == 'pret': etat['data'] = json.load(open(f'{d}/data.json'))
    return JSONResponse(etat)


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


def rendre(pid, d):
    D = json.load(open(f'{d}/data.json')); g = D.get('diag') or {}; L = D.get('lecture') or {}
    v = (g.get('vis_a_vis') or [None])[0]
    faits = ''
    if g:
        faits += f'''<div class="fact"><span class="k">Soleil le 21 juin</span><span class="val">{str(g["soleil_ete_h_moyen"]).replace(".", ",")} h <small>par jour</small></span>
          <div class="sunbar">{''.join(f'<i class="on" style="opacity:{0.35 + 0.65 * f:.2f}"></i>' if f > 0.05 else '<i></i>' for k, f in enumerate(g.get("soleil_ete_profil_8h_21h") or []))}</div>
          <div class="hours"><span>8 h</span><span>14 h</span><span>21 h</span></div><p>Dont {str(g["soleil_ete_apres14h_h"]).replace(".", ",")} h après 14 h, au moment le plus chaud.</p></div>'''
        if v and v['hauteur_m'] >= 5:
            faits += f'''<div class="fact"><span class="k">Vis-à-vis</span><span class="val">{v["hauteur_m"]:.0f} m <small>de haut, à {str(v["distance_m"]).replace(".", ",")} m</small></span>
          <p>Une maison voisine côté {e(v["direction"])} a vue depuis son étage sur votre jardin.</p></div>'''
        faits += f'''<div class="fact"><span class="k">Votre terrain</span><span class="val">{g["surface_parcelle_m2"]} m² <small>dont {g["surface_jardin_m2"]} de jardin</small></span>
          <p>{g["part_jardin_plus_6h_ete"]} % du jardin a plus de 6 h de soleil en été.</p></div>'''
    atouts = ''.join(f'<li>{e(a)}</li>' for a in L.get('atouts') or []); pistes = ''.join(f'<li>{e(a)}</li>' for a in L.get('pistes') or [])
    visuel = (f'''<div class="cmp" id="cmp" style="--p:50%"><img src="/fichiers/{pid}/visuel.jpg" alt="Idée d'aménagement avec nos produits"><img class="av" src="/fichiers/{pid}/photo.jpg" alt="Votre photo">
          <span class="bar"></span><span class="tag l">Avant</span><span class="tag r">Idée Cover Green</span><input id="cmp-range" type="range" min="0" max="100" value="50" aria-label="Comparer avant et après"></div>
          <p class="note">Idée d'aménagement non contractuelle, réalisée avec nos produits.</p>''' if D.get('visuel') else
              '<div class="refs">' + ''.join(f'<img src="/assets/refs/{p["photo"]}" alt="{e(p["nom"])} Cover Green">' for p in D['produits']) + '</div><p class="note">Des réalisations Cover Green proches de votre projet.</p>')
    pl = (D.get('plantes') or {}).get('plantes') or []
    cartes = ''.join(f'''<article class="pcard"><img src="/assets/plantes/{e(p["photo"])}" alt="{e(p["nom"])}" loading="lazy"><div class="pc"><span class="role">{ROLE.get(p["role"], p["role"])}</span><h4>{e(p["nom"])}</h4><i>{e(p["latin"])}</i>
        <div class="badges">{''.join(f'<span class="badge">{LAB[s]}</span>' for s in ("printemps", "ete", "automne", "hiver") if s in p["saisons"])}</div>
        <dl><div><dt>Fleurs</dt><dd>{e(p["floraison"] or "feuillage décoratif")}</dd></div><div><dt>Hiver</dt><dd>{e(p["hiver"])}</dd></div><div><dt>Entretien</dt><dd>{e(p["entretien"])}</dd></div></dl></div></article>''' for p in pl)
    M = 'JFMAMJJASOND'
    cal = ''.join(f'<tr><th scope="row">{e(p["nom"])}</th>' + ''.join(f'<td class="{"fl" if m + 1 in p["mois_fleurs"] else ("fo" if ("persistant" in p["hiver"] or "marcescent" in p["hiver"] or 4 <= m + 1 <= 10) else "")}"></td>' for m in range(12)) + '</tr>' for p in pl)
    VERBE = {'cloture': 'Configurer ma clôture', 'pergola': 'Configurer ma pergola'}
    prods = ''.join(f'''<div class="prod"><img src="/assets/refs/{p["photo"]}" alt=""><div><h3>{e(p["nom"])}</h3><p class="why">{e(p.get("placement"))}</p>
        <dl class="spec">{''.join(f'<div><dt>{e(k)}</dt><dd>{e(x)}</dd></div>' for k, x in p["detail"].items())}</dl></div>
        <div class="est"><small>Estimation</small><b>{eur(p["prix"][0])} à {eur(p["prix"][1])}</b><a class="cta reduit{"" if i == 0 else " sec"}" href="{p["lien"]}" target="_blank" rel="noopener">{VERBE.get(p.get("cle"), "Configurer")}</a></div></div>''' for i, p in enumerate(D['produits']))
    planbloc = (f'''<div class="planrow"><div class="carte plan"><img src="/fichiers/{pid}/plan.png" alt="Votre parcelle vue du ciel"></div><div><h3>Votre parcelle vue du ciel</h3>
      <ul class="legend"><li><span class="sw" style="background:linear-gradient(90deg,#96acc4,#ffde8c,#e8742a)"></span>Heures de soleil le 21 juin, de l'ombre au plein soleil</li><li><span class="sw" style="background:#344239"></span>Votre maison</li><li><span class="sw" style="background:#d6dad2;border:1px solid #b0b6ac"></span>Maisons voisines, avec leur hauteur</li><li><span class="sw" style="background:#c43428;border-radius:50%"></span>Voisin qui a vue sur votre jardin</li></ul></div></div>''' if D.get('plan') else '')
    rep = {'ID': e(pid), 'VILLE': e(D.get('ville')), 'DATE': e(D.get('cree_le')), 'VISUEL': visuel, 'FAITS': faits, 'ATOUTS': atouts, 'PISTES': pistes,
           'PLANBLOC': planbloc, 'CARTES': cartes,
           'CAL': cal, 'MOIS': ''.join(f'<th scope="col">{m}</th>' for m in M), 'PRODUITS': prods, 'BUDGET': f'{eur(D["budget"][0])} à {eur(D["budget"][1])}'}
    out = GABARIT
    for k, x in rep.items(): out = out.replace('{{' + k + '}}', x)
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
    return HTMLResponse(h[h.index('<!--DEBUT-->'):h.index('<!--FIN-->')].replace('src="/', f'src="{base}/'))


@app.get('/sante')
def sante():
    return {'ok': True}
