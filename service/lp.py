# Contenu de la page « Diagnostic jardin » sous le questionnaire : ce que l'on reçoit, les plantes par région et saison, comment ça marche, FAQ.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin]. Styles préfixés .cglp.
import json, os, re, unicodedata, html

ICI = os.path.dirname(os.path.abspath(__file__))
KB = json.load(open(os.path.join(ICI, '..', 'rendu', 'paysage', 'palettes_vegetales.json'), encoding='utf-8'))
PHOTOS = set(os.listdir(os.path.join(ICI, 'assets', 'plantes')))
e = lambda s: html.escape(str(s or ''))

MOIS = {'janv': 1, 'févr': 2, 'fév': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'août': 8, 'sept': 9, 'oct': 10, 'nov': 11, 'déc': 12}
REGIONS = [('mediterraneen', 'Méditerranée'), ('oceanique', 'Façade atlantique'), ('oceanique_degrade', 'Nord, Centre et Île-de-France'),
           ('continental', 'Est'), ('montagnard', 'Montagne')]
SAISONS = [('printemps', 'Printemps', (3, 4, 5)), ('ete', 'Été', (6, 7, 8)), ('automne', 'Automne', (9, 10, 11)), ('hiver', 'Hiver', (12, 1, 2))]
ROLE = {'focal': 'Arbuste vedette', 'structure': 'Persistant', 'vivace': 'Vivace fleurie', 'graminee': 'Graminée', 'grimpante': 'Grimpante',
        'fleuri': 'Arbuste fleuri', 'couvre_sol': 'Couvre-sol'}
FRILEUSES = ('Olea', 'Lagerstroemia', 'Trachycarpus', 'Cistus', 'Phlomis', 'Rosmarinus', 'Teucrium', 'Perovskia', 'Lavandula', 'Ceanothus', 'Gaura',
             'Erigeron', 'Agapanthus', 'Euphorbia characias', 'Stipa', 'Pennisetum', 'Miscanthus', 'Muhlenbergia', 'Festuca', 'Trachelospermum',
             'Fargesia', 'Abelia', 'Arbutus', 'Pittosporum', 'Calamagrostis', 'Hakonechloa', 'Carex', 'Ophiopogon')


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def mois(txt):
    t = (txt or '').lower(); f = [v for _, v in sorted((m.start(), v) for k, v in MOIS.items() for m in re.finditer(k, t))]
    if not f: return []
    if '-' in t and len(f) >= 2:
        a, b = f[0], f[1]; return list(range(a, b + 1)) if a <= b else list(range(a, 13)) + list(range(1, b + 1))
    return f


def saisons(p):
    fl = mois(p['floraison']); h = p['hiver'].lower(); s = set()
    for k, _, ms in SAISONS:
        if set(fl) & set(ms): s.add(k)
    if any(w in h for w in ('automne', 'orange', 'rouge', 'doré', 'marcescent')): s.add('automne')
    if any(w in h for w in ('persistant', 'marcescent', 'écorce', 'rouge en hiver', 'blond')): s.add('hiver')
    if 'feuillage' in h or 'persistant' in h: s.add('ete')
    return fl, s


def plantation(p, clim):
    if p['latin'].startswith('Iris germanica'): return [7, 8, 9]
    fri = p['latin'].startswith(FRILEUSES)
    if clim == 'mediterraneen': return [3, 4, 10, 11]
    if clim in ('continental', 'montagnard'): return [5, 6] if fri else [4, 5, 9, 10]
    return [4, 5] if fri else [3, 4, 10, 11]


def selection():
    """Pour chaque région et chaque saison, 8 plantes au plus, en variant les rôles (vedette, persistant, vivace, graminée...)."""
    out = {}
    for clim, _ in REGIONS:
        out[clim] = {}
        for k, _, ms in SAISONS:
            c = []
            for p in KB['plantes']:
                if clim not in p['climats'] or f"{slug(p['latin'])}.jpg" not in PHOTOS: continue
                fl, s = saisons(p)
                if k not in s: continue
                fleurit = bool(set(fl) & set(ms))
                c.append((0 if fleurit else 1, p, fl))
            c.sort(key=lambda x: x[0]); pris, roles = [], {}
            for _, p, fl in c:                                   # au plus 3 plantes du même rôle
                if roles.get(p['role'], 0) >= 3: continue
                roles[p['role']] = roles.get(p['role'], 0) + 1; pris.append((p, fl))
                if len(pris) == 8: break
            out[clim][k] = [{'n': p['nom'], 'l': p['latin'], 'r': ROLE.get(p['role'], ''), 'f': p['floraison'], 'h': p['hiver'], 'e': p['entretien'],
                             'm': plantation(p, clim), 'ph': f"{slug(p['latin'])}.jpg"} for p, fl in pris]
    return out


CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);background:#fff}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp section{max-width:1120px;margin:0 auto;padding:56px 16px}
.cglp section+section{border-top:1px solid var(--ligne)}
.cglp h2{font:800 30px/1.15 var(--f);margin:0 0 10px;letter-spacing:-.01em;color:var(--txt)}
.cglp .sous{color:var(--muted);margin:0 0 28px;max-width:720px;font-size:17px}
.cglp .grille{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.cglp .carte{border:1px solid var(--ligne);border-radius:12px;padding:22px;background:#fff}
.cglp .carte h3{font:700 19px/1.3 var(--f);margin:16px 0 6px}
.cglp .carte p{margin:0;color:var(--muted);font-size:15px}
.cglp .illu{height:150px;border-radius:10px;background:var(--gris);display:flex;align-items:center;justify-content:center;padding:16px;overflow:hidden}
.cglp .sunbar{display:flex;gap:3px;width:100%}.cglp .sunbar i{flex:1;height:44px;border-radius:4px;display:block}
.cglp .heures{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:6px;width:100%}
.cglp .sol{width:100%}
.cglp .av{display:grid;grid-template-columns:1fr 30px 1fr;gap:6px;width:100%;height:100%;align-items:stretch}
.cglp .av span{border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;text-align:center;padding:6px}
.cglp .av .a{border:2px dashed var(--vert);background:var(--brume)}.cglp .av .b{background:#fff;border:1px solid var(--ligne);color:var(--muted)}
.cglp .av .fl{color:var(--vert);font-size:22px;font-weight:400}
.cglp .budget{width:100%;display:grid;gap:8px}.cglp .budget div{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--muted)}
.cglp .budget b{display:block;height:12px;border-radius:6px;background:var(--vert)}.cglp .budget div:nth-child(2) b{background:#7FBF6A}.cglp .budget div:nth-child(3) b{background:#BFE3B0}
.cglp .puces{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.cglp .puce{appearance:none;border:1px solid var(--ligne);background:#fff;border-radius:999px;height:44px;padding:0 16px;font:500 15px var(--f);color:var(--txt);cursor:pointer}
.cglp .puce:hover{border-color:var(--vert)}.cglp .puce[aria-pressed=true]{background:var(--vert);border-color:var(--vert);color:#fff}
.cglp .puces.saisons .puce[aria-pressed=true]{background:var(--brume);color:var(--txt);border-color:var(--vert);box-shadow:inset 0 0 0 1px var(--vert)}
.cglp .lbl{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:18px 0 8px}
.cglp .plantes{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:18px}
.cglp .plante{border:1px solid var(--ligne);border-radius:12px;overflow:hidden;background:#fff;display:flex;flex-direction:column}
.cglp .plante img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:var(--gris)}
.cglp .plante>div{padding:12px 14px 14px;display:flex;flex-direction:column;gap:4px;flex:1}
.cglp .plante b{font-size:16px;line-height:1.25}.cglp .plante i{font-size:13px;color:var(--muted)}
.cglp .plante .r{font-size:12px;font-weight:700;color:var(--vert);text-transform:uppercase;letter-spacing:.03em}
.cglp .plante .t{font-size:13px;color:var(--muted)}
.cglp .cal{display:grid;grid-template-columns:repeat(12,1fr);gap:2px;margin-top:auto;padding-top:8px}
.cglp .cal span{font-size:11px;text-align:center;color:var(--muted);border-radius:4px;padding:3px 0;background:var(--gris)}
.cglp .cal span.p{background:var(--txt);color:#fff;font-weight:700}
.cglp .leg{font-size:13px;color:var(--muted);margin-top:12px}.cglp .leg em{display:inline-block;width:14px;height:14px;border-radius:3px;background:var(--txt);vertical-align:-2px;margin-right:6px}
.cglp .cta{appearance:none;display:inline-flex;align-items:center;justify-content:center;height:56px;padding:0 28px;border-radius:8px;border:1px solid var(--orange);
background:var(--orange);color:#fff;font:600 17px/1 var(--f);text-decoration:none;cursor:pointer;margin-top:26px}
.cglp .cta:hover{background:var(--orange-survol);border-color:var(--orange-survol);color:#fff}
.cglp .etapes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;counter-reset:e}
.cglp .etapes div{counter-increment:e;background:var(--brume);border-radius:12px;padding:22px}
.cglp .etapes div:before{content:counter(e);display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:var(--vert);color:#fff;font-weight:800;margin-bottom:12px}
.cglp .etapes b{display:block;font-size:18px;margin-bottom:4px}.cglp .etapes p{margin:0;color:var(--muted);font-size:15px}
.cglp details{border-bottom:1px solid var(--ligne);padding:18px 0}.cglp details:first-of-type{border-top:1px solid var(--ligne)}
.cglp summary{cursor:pointer;font-weight:700;font-size:17px;list-style:none;display:flex;justify-content:space-between;gap:16px}
.cglp summary::-webkit-details-marker{display:none}.cglp summary:after{content:"+";font-size:24px;line-height:1;color:var(--vert)}
.cglp details[open] summary:after{content:"−"}.cglp details p{margin:10px 0 0;color:var(--muted);max-width:760px}
.cglp .fin{text-align:center;background:var(--brume);border-radius:16px;padding:40px 20px;margin:0 16px 56px;max-width:1088px}
@media (min-width:1120px){.cglp .fin{margin:0 auto 56px}}
@media (max-width:900px){.cglp .plantes{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:760px){.cglp section{padding:40px 16px}.cglp h2{font-size:26px}.cglp .grille,.cglp .etapes{grid-template-columns:1fr}.cglp .cta{width:100%}
.cglp .puces{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin-right:-16px;padding-right:16px}.cglp .puces::-webkit-scrollbar{display:none}.cglp .puce{flex:none}}
</style>'''

SOL = [0.05, 0.1, 0.35, 0.7, 0.95, 1, 1, 1, 1, 0.9, 0.75, 0.5, 0.3, 0.2, 0.1, 0.05, 0.4, 0.75, 0.85, 0.6, 0.3, 0.1, 0.05, 0, 0, 0]


def couleur(f):
    stops = [(0, (150, 172, 196)), (0.35, (196, 210, 200)), (0.6, (255, 222, 140)), (0.8, (247, 170, 60)), (1, (232, 116, 42))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if f <= b: t = (f - a) / (b - a); return '#%02x%02x%02x' % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
    return '#e8742a'


def rendre(base=''):
    sel = selection()
    sunbar = ''.join(f'<i style="background:{couleur(f)}"></i>' for f in SOL)
    plan = ('<svg class="sol" viewBox="0 0 300 120" aria-hidden="true"><defs><linearGradient id="cglpg" x1="0" x2="1"><stop offset="0" stop-color="#c4d2c8"/>'
            '<stop offset=".5" stop-color="#ffde8c"/><stop offset="1" stop-color="#e8742a"/></linearGradient></defs>'
            '<rect x="10" y="8" width="210" height="104" rx="4" fill="#eef0e9"/><path d="M60 22h150v80H60z" fill="url(#cglpg)" opacity=".85"/>'
            '<rect x="22" y="40" width="42" height="46" rx="2" fill="#344239"/><path d="M60 22h150v80H60z" fill="none" stroke="#1f5a3d" stroke-width="3"/>'
            '<rect x="236" y="14" width="52" height="40" rx="2" fill="#d6dad2" stroke="#b0b6ac"/><path d="M236 34 L150 60" stroke="#c43428" stroke-width="2.5" stroke-dasharray="6 5"/>'
            '<circle cx="236" cy="34" r="5" fill="#c43428"/><text x="262" y="80" font-size="11" text-anchor="middle" fill="#5B625E" font-family="Roboto,Arial">6 m</text></svg>')
    carte = lambda illu, t, p: f'<div class="carte"><div class="illu">{illu}</div><h3>{t}</h3><p>{p}</p></div>'
    recu = ''.join([
        carte(f'<div style="width:100%"><div class="sunbar">{sunbar}</div><div class="heures"><span>8 h</span><span>14 h</span><span>21 h</span></div></div>',
              'Le soleil de votre jardin, heure par heure', "Calculé à partir de votre adresse et des maisons autour : où et quand le soleil tape, où l'ombre tombe, en été comme à la mi-saison."),
        carte(plan, 'Les vis-à-vis et le plan vu du ciel', "Les étages voisins qui voient votre jardin, leur hauteur de vue, et votre terrain dessiné avec son soleil."),
        carte('<div class="av"><span class="a">Votre photo</span><span class="fl">→</span><span class="b">Votre jardin avec nos produits</span></div>',
              'Votre jardin imaginé avec nos produits', "À partir d'une simple photo, nos clôtures et pergolas posées chez vous, au bon endroit, dans le style que vous aimez."),
        carte('<div class="budget"><div><b style="width:42%"></b>Vos produits Cover Green</div><div><b style="width:60%"></b>Avec les compléments utiles</div>'
              '<div><b style="width:88%"></b>Votre jardin comme sur le visuel</div></div>',
              'Un budget clair, poste par poste', "Nos produits, les compléments utiles, puis le mobilier, les plantes et le sol du visuel : vous savez où vous allez."),
    ])
    regions = ''.join(f'<button type="button" class="puce" data-r="{k}" aria-pressed="{str(k == "oceanique_degrade").lower()}">{n}</button>' for k, n in REGIONS)
    sais = ''.join(f'<button type="button" class="puce" data-s="{k}" aria-pressed="{str(k == "printemps").lower()}">{n}</button>' for k, n, _ in SAISONS)
    faq = [("C'est vraiment gratuit ?", "Oui, entièrement, et sans engagement. Nous le faisons parce qu'un projet bien préparé est un projet réussi, et que beaucoup de nos clients commencent par là."),
           ("Combien de temps ça prend ?", "Une minute pour répondre aux questions. Votre page projet arrive ensuite par email, en 2 à 3 minutes."),
           ("Faut-il une photo de mon jardin ?", "C'est elle qui permet de vous montrer votre jardin avec nos produits. Sans photo sous la main, vous recevez déjà le soleil, les vis-à-vis et les plantes, et vous ajoutez la photo plus tard depuis votre page."),
           ("Comment calculez-vous le soleil et les vis-à-vis ?", "À partir de votre adresse, avec les données publiques de l'IGN : la forme de votre terrain, les maisons autour, leur hauteur et le relief. Le soleil est calculé heure par heure."),
           ("Que faites-vous de mes données ?", "Elles servent uniquement à préparer votre diagnostic et à vous l'envoyer. Elles ne sont jamais revendues."),
           ("Je ne suis pas sûr de mon projet, ça sert quand même ?", "C'est justement le meilleur moment : le diagnostic vous aide à savoir quoi faire, où et dans quel ordre, avant d'acheter quoi que ce soit.")]
    return (CSS + f'''<div class="cglp" data-base="{e(base)}">
<section id="cglp-recu"><h2>Ce que vous recevez</h2><p class="sous">Une page projet rien qu'à vous, à garder et à partager, construite à partir de votre adresse, de vos réponses et de votre photo.</p>
<div class="grille">{recu}</div></section>
<section id="cglp-plantes"><h2>Les plantes faites pour votre jardin</h2>
<p class="sous">Choisies selon votre région, votre soleil et le temps que vous voulez y passer, avec le bon mois pour les planter. Voici un aperçu : votre diagnostic les sélectionne pour votre jardin.</p>
<p class="lbl">Votre région</p><div class="puces" role="group" aria-label="Région">{regions}</div>
<p class="lbl">La saison</p><div class="puces saisons" role="group" aria-label="Saison">{sais}</div>
<div class="plantes" id="cglp-liste" aria-live="polite"></div>
<p class="leg"><em></em>Le bon mois pour planter dans cette région</p>
<button type="button" class="cta" data-go="1">Recevoir la sélection pour mon jardin</button></section>
<section id="cglp-comment"><h2>Comment ça marche</h2><p class="sous">Trois étapes, et rien à installer.</p>
<div class="etapes"><div><b>Répondez à quelques questions</b><p>Votre envie, votre adresse, votre style : une minute, un toucher par réponse.</p></div>
<div><b>Ajoutez une photo de votre jardin</b><p>Prise depuis la maison ou la terrasse. Pas sous la main ? Vous l'ajouterez plus tard.</p></div>
<div><b>Recevez votre page projet</b><p>Soleil, vis-à-vis, plantes, votre jardin avec nos produits et le budget, par email en 3 minutes.</p></div></div></section>
<section id="cglp-faq"><h2>Vos questions</h2>{''.join(f"<details><summary>{e(q)}</summary><p>{e(r)}</p></details>" for q, r in faq)}</section>
<div class="fin"><h2>Prêt à voir votre jardin autrement ?</h2><p class="sous" style="margin:0 auto">Gratuit, sans engagement, en une minute.</p>
<button type="button" class="cta" data-go="1">Commencer mon diagnostic</button></div>
<script>(function(){{var D={json.dumps(sel, ensure_ascii=False)},R=document.currentScript.parentNode,B=R.getAttribute("data-base")||"",reg="oceanique_degrade",sai="printemps",M="JFMAMJJASOND";
function h(s){{return String(s||"").replace(/[&<>"]/g,function(c){{return{{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function aff(){{var L=(D[reg]||{{}})[sai]||[];R.querySelector("#cglp-liste").innerHTML=L.map(function(p){{var cal="";for(var i=0;i<12;i++)cal+='<span class="'+(p.m.indexOf(i+1)>=0?"p":"")+'">'+M[i]+"</span>";
return '<article class="plante"><img loading="lazy" src="'+B+'/assets/plantes/'+p.ph+'" alt="'+h(p.n)+'"><div><span class="r">'+h(p.r)+'</span><b>'+h(p.n)+'</b><i>'+h(p.l)+'</i>'
+(p.f?'<span class="t">En fleurs : '+h(p.f)+'</span>':'<span class="t">'+h(p.h)+'</span>')+'<div class="cal" aria-label="Mois de plantation">'+cal+"</div></div></article>"}}).join("")}}
R.addEventListener("click",function(e){{var b=e.target.closest("button");if(!b)return;
if(b.dataset.r){{reg=b.dataset.r;[].forEach.call(R.querySelectorAll("[data-r]"),function(x){{x.setAttribute("aria-pressed",x===b)}});aff();try{{dataLayer.push({{event:"cgp_lp_region",onglet:reg}})}}catch(x){{}}}}
if(b.dataset.s){{sai=b.dataset.s;[].forEach.call(R.querySelectorAll("[data-s]"),function(x){{x.setAttribute("aria-pressed",x===b)}});aff();try{{dataLayer.push({{event:"cgp_lp_saison",onglet:sai}})}}catch(x){{}}}}
if(b.dataset.go){{var q=document.getElementById("cg-diag")||document.body;window.scrollTo({{top:Math.max(0,q.getBoundingClientRect().top+window.scrollY-120),behavior:"smooth"}});try{{dataLayer.push({{event:"cgp_lp_cta",onglet:b.closest("section")?b.closest("section").id:"fin"}})}}catch(x){{}}}}}});
aff()}})()</script></div>''')
