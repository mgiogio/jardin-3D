# Page d'entrée du « Diagnostic jardin » : un beau jardin imaginé par l'outil, avec ce qu'on livre (soleil, plantes, budget) en cartes, l'encadré avec la question de l'adresse, quatre cartes.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin] au-dessus du questionnaire, qui reste caché
# jusqu'au clic sur « Je commence ». Styles préfixés .cglp. On ne dévoile pas ici le contenu du diagnostic (plantes, produits).
import html

e = lambda s: html.escape(str(s or ''))
# visuels : le jardin imaginé par l'outil pour un vrai projet et les photos de la banque de plantes ; dans la médiathèque WordPress (pas dans ce dépôt public)
IMG = 'https://cover.green/wp-content/uploads/diagnostic/'
# vitrine : un vrai diagnostic lancé dans l'outil (photo libre de droits Pexels, adresse de démonstration dans l'Hérault)
PLANTES = [('abelia-x-grandiflora', 'Abélia'), ('viburnum-tinus', 'Laurier-tin'), ('clematis-armandii', 'Clématite')]
PLANTES_EN_PLUS = ('geranium-macrorrhizum', 3)           # photo floutée sous le « ? », nombre de plantes non montrées
MOIS_PLANTATION = [3, 4, 10, 11]
SOLEIL = {'heures': 11, 'profil': [0.47, 0.56, 0.65, 0.73, 0.78, 0.81, 0.84, 0.87, 0.89, 0.91, 0.92, 0.94, 0.94, 0.95, 0.96, 0.95, 0.93, 0.91, 0.89, 0.86, 0.84, 0.84, 0.84, 0.84, 0.85, 0.86]}
BUDGET = [('Terrasse bois, 32 m²', '1 900 à 2 600 €'), ('Pergola 3 x 3 m', '1 100 à 1 400 €'), ('Clôture, 22 m', '2 500 à 3 100 €')]


def couleur_soleil(f):
    # même dégradé que la page projet : ombre (bleu-gris) -> soleil doux (jaune) -> plein soleil (orange)
    f = max(0.0, min(1.0, float(f))); pts = [(0, (150, 172, 196)), (0.5, (255, 222, 140)), (1, (232, 116, 42))]
    (a, ca), (b, cb) = (pts[0], pts[1]) if f <= 0.5 else (pts[1], pts[2]); t = (f - a) / (b - a)
    return '#%02x%02x%02x' % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))

CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);max-width:1080px;margin:0 auto;padding:32px 16px 8px}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp .entree{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(30,33,31,.08),0 8px 30px rgba(30,33,31,.06)}
.cglp .apercu{position:relative;min-height:560px;background:#DDE3DF;overflow:hidden}
.cglp .apercu .photo{position:absolute;inset:0;overflow:hidden}.cglp .apercu .photo img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:42% 60%;display:block}
.cglp .apercu .photo img.ap{opacity:0;animation:cglp-fondu 11s ease-in-out 1.2s infinite}
@keyframes cglp-fondu{0%,12%{opacity:0}24%,88%{opacity:1}100%{opacity:0}}
@keyframes cglp-fondu-inv{0%,12%{opacity:1}24%,88%{opacity:0}100%{opacity:1}}
.cglp .apercu .tag{position:absolute;z-index:2;right:18px;bottom:18px;padding:6px 11px;border-radius:7px;background:rgba(30,33,31,.72);color:#fff;font-size:13px;font-weight:600}
.cglp .apercu .t-av{animation:cglp-fondu-inv 11s ease-in-out 1.2s infinite}.cglp .apercu .t-ap{opacity:0;background:var(--vert);animation:cglp-fondu 11s ease-in-out 1.2s infinite}
@media (prefers-reduced-motion:reduce){.cglp .apercu .photo img.ap,.cglp .apercu .t-ap{animation:none;opacity:1}.cglp .apercu .t-av{display:none}}
.cglp .apercu .v-pla .plus i{position:relative;display:block;width:50px;height:50px;margin:0 auto 5px;border-radius:50%;overflow:hidden;box-shadow:0 0 0 2px #fff,0 0 0 3px var(--brume)}
.cglp .apercu .v-pla .plus img{width:100%;height:100%;margin:0;box-shadow:none;filter:blur(3px) saturate(.85);transform:scale(1.2)}
.cglp .apercu .v-pla .plus i:after{content:"?";position:absolute;inset:0;display:grid;place-items:center;background:rgba(4,158,0,.42);color:#fff;font-size:26px;font-weight:800}
.cglp .apercu .photo:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.12),rgba(0,0,0,0) 30%,rgba(0,0,0,0) 65%,rgba(0,0,0,.25));pointer-events:none}
.cglp .apercu .vu{position:absolute;z-index:2;background:rgba(255,255,255,.96);border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,.08),0 12px 30px rgba(0,0,0,.2);padding:11px 13px 12px;text-align:left;color:var(--txt);font-size:13px;line-height:1.35}
.cglp .apercu .vu small{display:block;font-size:11.5px;color:var(--muted);margin-bottom:3px}
.cglp .apercu .v-sol{top:18px;left:18px;width:182px}
.cglp .apercu .v-sol strong{display:block;font-size:23px;line-height:1.1;font-weight:800}.cglp .apercu .v-sol strong span{font-size:13px;font-weight:600;color:var(--muted)}
.cglp .apercu .sol{display:flex;gap:1px;height:10px;margin-top:8px;border-radius:3px;overflow:hidden}.cglp .apercu .sol i{flex:1}
.cglp .apercu .heures{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:4px}
.cglp .apercu .v-bud{top:18px;right:18px;width:232px}.cglp .apercu .v-bud span{white-space:nowrap}
.cglp .apercu .v-bud div{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:5px 0;border-top:1px solid var(--ligne);font-size:12.5px}.cglp .apercu .v-bud div:first-of-type{border-top:0;padding-top:1px}
.cglp .apercu .v-bud b{font-weight:700;color:var(--orange);white-space:nowrap}
.cglp .apercu .v-pla{left:18px;bottom:18px;width:286px}.cglp .apercu .long{display:inline}
.cglp .apercu .v-pla ul{list-style:none;margin:4px 0 0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.cglp .apercu .v-pla li{text-align:center;font-size:11.5px;line-height:1.25}
.cglp .apercu .v-pla img{display:block;width:50px;height:50px;margin:0 auto 5px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 2px #fff,0 0 0 3px var(--brume)}
.cglp .apercu .v-pla p{margin:8px 0 0;padding-top:7px;border-top:1px solid var(--ligne);font-size:12.5px;color:var(--txt);font-weight:700}
.cglp .boite{margin:20px;border:2px dashed #9AA29E;border-radius:12px;padding:36px 28px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:14px}
.cglp h1{font:800 34px/1.12 var(--f);margin:0;letter-spacing:-.01em;color:var(--txt)}
.cglp h1 .v{color:var(--vert)}.cglp h1 .o{color:var(--orange)}
.cglp .boite p{margin:0;color:var(--muted);font-size:16px;max-width:380px}
.cglp .cta{appearance:none;display:inline-flex;align-items:center;justify-content:center;height:56px;padding:0 32px;border-radius:8px;border:1px solid var(--orange);
background:var(--orange);color:#fff;font:600 17px/1 var(--f);cursor:pointer;margin-top:6px;min-width:260px}
.cglp .cta:hover{background:var(--orange-survol);border-color:var(--orange-survol)}
.cglp .cta:focus-visible{outline:3px solid var(--vert);outline-offset:2px}
.cglp .petit{font-size:14px;color:var(--muted)}.cglp .petit b{color:var(--txt)}
.cglp form{width:100%;max-width:420px;display:grid;gap:10px;text-align:left;margin-top:4px}
.cglp form label{font-weight:700;font-size:15px}
.cglp .champ{position:relative}
.cglp .champ input{width:100%;height:56px;border:1px solid #9AA29E;border-radius:8px;padding:0 16px 0 44px;font:400 17px var(--f);color:var(--txt);background:#fff no-repeat 14px center/20px url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23049E00' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M12 21s7-6.3 7-11.5A7 7 0 0 0 5 9.5C5 14.7 12 21 12 21z'/%3E%3Ccircle cx='12' cy='9.5' r='2.5'/%3E%3C/svg%3E")}
.cglp .champ input:focus{outline:none;border-color:var(--vert);box-shadow:0 0 0 3px rgba(4,158,0,.18)}
.cglp .sug{position:absolute;left:0;right:0;top:60px;z-index:20;list-style:none;margin:0;padding:0;background:#fff;border:1px solid var(--ligne);border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,.12);overflow:hidden}
.cglp .sug button{appearance:none;display:block;width:100%;text-align:left;background:#fff;border:0;border-top:1px solid var(--ligne);padding:13px 16px;font:400 15px var(--f);color:var(--txt);cursor:pointer}
.cglp .sug li:first-child button{border-top:0}.cglp .sug button:hover,.cglp .sug button:focus{background:var(--brume);outline:none}.cglp .sug small{color:var(--muted)}
.cglp form .cta{width:100%;min-width:0;margin-top:2px;gap:10px}
.cglp form.ok .champ input{border-color:var(--vert);background-color:#F6FBF4}
.cglp form.encours .cta{opacity:.92;cursor:progress}
.cglp .rond{width:18px;height:18px;border-radius:50%;border:2.5px solid rgba(255,255,255,.45);border-top-color:#fff;animation:cglp-t .8s linear infinite;flex:none}
@keyframes cglp-t{to{transform:rotate(360deg)}}
.cglp .geo{appearance:none;background:none;border:0;padding:4px 0;font:500 14px var(--f);color:var(--vert);text-decoration:underline;cursor:pointer;justify-self:center}
.cglp .msg{margin:0;font-size:14px;color:#C62828;min-height:0}.cglp .msg:empty{display:none}
.cglp .reprise{font-size:14px;color:var(--txt);text-decoration:underline}
.cglp .atouts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}
.cglp .atouts div{background:#fff;border-radius:14px;padding:22px 20px;text-align:center;box-shadow:0 1px 3px rgba(30,33,31,.06)}
.cglp .atouts i{display:inline-grid;place-items:center;width:44px;height:44px;border-radius:10px;background:var(--brume);color:var(--vert);margin-bottom:10px}
.cglp .atouts i svg{width:24px;height:24px}
.cglp .atouts b{display:block;font-size:17px;margin-bottom:4px}.cglp .atouts p{margin:0;color:var(--muted);font-size:14px}
@media (max-width:980px){.cglp .atouts{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:820px){.cglp{padding-top:16px}.cglp .entree{grid-template-columns:1fr}.cglp .boite{order:-1;margin:14px;padding:26px 18px}
.cglp .apercu{min-height:0;margin:0 14px 14px;background:none;overflow:visible;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cglp .apercu .photo{position:relative;grid-column:1/-1;aspect-ratio:3/2;border-radius:12px}
.cglp .apercu .vu{position:static;width:auto;box-shadow:none;border:1px solid var(--ligne);background:#fff;padding:10px 11px}
.cglp .apercu .v-pla{grid-column:1/-1}.cglp .apercu .long{display:none}
.cglp .apercu .v-bud span{white-space:normal}.cglp .apercu .v-bud div{flex-direction:column;align-items:flex-start;gap:0;padding:4px 0}
.cglp .apercu .tag{right:10px;bottom:10px;font-size:12px}
.cglp h1{font-size:28px}.cglp .cta{width:100%;min-width:0;padding:0 14px;font-size:16px;white-space:nowrap}}
@media (max-width:520px){.cglp .atouts{grid-template-columns:1fr}}
</style>'''

ICO = {'plante': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7zM7 21h10"/></svg>',
       'soleil': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
       'cadeau': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13M12 7c-2-4-6-3-5 0M12 7c2-4 6-3 5 0"/></svg>',
       'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg>',
       'euro': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M17 6.5A7 7 0 1 0 17 17.5M4 10h9M4 14h9"/></svg>',
       'plan': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 9h18M5 9l2-4h10l2 4M6 9v11M18 9v11M3 20h18"/></svg>'}


JS = r'''<script>(function(){var F=document.getElementById("cglp-form");if(!F)return;var I=document.getElementById("cglp-a"),L=document.getElementById("cglp-sug"),M=document.getElementById("cglp-msg"),G=document.getElementById("cglp-geo"),Q=F.getAttribute("data-q"),A=F.getAttribute("data-api"),B=F.querySelector(".cta"),res=[],tm,ct,sel=null,tp=null,CLE="cg_diag_v1";
function h(s){return String(s||"").replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function ev(n,p){try{window.dataLayer=window.dataLayer||[];var o={event:n};for(var k in p)o[k]=p[k];dataLayer.push(o)}catch(e){}}
function va(f){var p=f.properties||{},c=f.geometry.coordinates;return{label:p.label,name:p.name||p.label,city:p.city,postcode:p.postcode||"",citycode:p.citycode,lat:c[1],lon:c[0],score:p.score,type:p.type}}
function cherche(q,sig){var u=["https://data.geopf.fr/geocodage/search?q="+encodeURIComponent(q)+"&limit=5&index=address&autocomplete=1","https://api-adresse.data.gouv.fr/search/?q="+encodeURIComponent(q)+"&limit=5&autocomplete=1"];
function t(i){if(i>=u.length)return Promise.reject(new Error("x"));return fetch(u[i],{signal:sig}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){return(d.features||[]).map(va)}).catch(function(e){if(e&&e.name==="AbortError")throw e;return t(i+1)})}return t(0)}
function aff(l){res=l;if(!l.length){L.hidden=true;return}L.innerHTML=l.map(function(a,i){return'<li role="option"><button type="button" data-i="'+i+'">'+h(a.name)+" <small>"+h(a.postcode+" "+a.city)+"</small></button></li>"}).join("");L.hidden=false}
function suivi(){var q=new URLSearchParams(location.search),s={};["utm_source","utm_medium","utm_campaign","utm_content","utm_term","gclid","fbclid","msclkid"].forEach(function(k){if(q.get(k))s[k]=q.get(k).slice(0,120)});s.referrer=(document.referrer||"").slice(0,200);s.page=(location.origin+location.pathname).slice(0,200);return s}
function terrain(a){if(!A)return Promise.resolve(null);return fetch(A+"/api/terrain?lat="+a.lat+"&lon="+a.lon).then(function(r){return r.ok?r.json():null}).catch(function(){return null})}
function choisir(a){sel=a;I.value=a.label;L.hidden=true;F.classList.add("ok");tp=terrain(a);ev("cgp_q_adresse_choisie",{etape:"accueil"});try{B.focus({preventScroll:true})}catch(e){}}
function go(a){if(F.classList.contains("encours"))return;F.classList.add("encours");B.disabled=true;B.innerHTML='<span class="rond"></span>Nous cherchons votre terrain…';
var t=(sel===a&&tp)?tp:terrain(a);Promise.race([t,new Promise(function(r){setTimeout(function(){r(null)},9000)})]).then(function(x){partir(a,x)})}
function partir(a,t){var S={v:1,cree:Date.now(),etape:"terrain",temps:{},infos:{},suivi:suivi(),adresse:{label:a.label,city:a.city,postcode:a.postcode,citycode:a.citycode,lat:a.lat,lon:a.lon,score:a.score}};if(t)S.terrain=t;
try{localStorage.setItem(CLE,JSON.stringify(S))}catch(e){}ev("cgp_q_adresse",{etape:"accueil",reponse:a.type||""});
var u=new URLSearchParams(location.search),k=new URLSearchParams();u.forEach(function(v,n){if(/^(utm_|gclid$|fbclid$|msclkid$)/.test(n))k.append(n,v)});var qs=k.toString();if(Q)location.href=Q+(qs?(Q.indexOf("?")<0?"?":"&")+qs:"");else location.reload()}
I.addEventListener("input",function(){clearTimeout(tm);M.textContent="";sel=null;tp=null;F.classList.remove("ok");var v=I.value.trim();if(v.length<4){L.hidden=true;return}tm=setTimeout(function(){if(ct)ct.abort();ct=window.AbortController?new AbortController():null;cherche(v,ct&&ct.signal).then(aff).catch(function(e){if(!e||e.name!=="AbortError")M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})},220)});
I.addEventListener("focus",function(){ev("cgp_q_etape",{etape:"accueil_adresse"})},{once:true});
L.addEventListener("click",function(e){var b=e.target.closest("button[data-i]");if(b)choisir(res[+b.getAttribute("data-i")])});
F.addEventListener("submit",function(e){e.preventDefault();if(sel)return go(sel);if(res[0])return go(res[0]);var v=I.value.trim();if(v.length<4){M.textContent="Indiquez l'adresse de votre jardin.";I.focus();return}cherche(v).then(function(l){if(l[0])go(l[0]);else M.textContent="Adresse introuvable, vérifiez-la ou choisissez-la dans la liste."}).catch(function(){M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})});
if("geolocation" in navigator&&window.matchMedia&&matchMedia("(pointer:coarse)").matches){G.hidden=false;G.addEventListener("click",function(){G.textContent="Localisation en cours…";navigator.geolocation.getCurrentPosition(function(p){var la=p.coords.latitude,lo=p.coords.longitude;fetch("https://data.geopf.fr/geocodage/reverse?lat="+la+"&lon="+lo+"&limit=1&index=address").then(function(r){return r.json()}).then(function(d){var f=(d.features||[])[0];if(!f)throw 0;var a=va(f);a.lat=la;a.lon=lo;ev("cgp_q_geoloc",{});go(a)}).catch(function(){M.textContent="Adresse introuvable, tapez-la simplement.";G.textContent="Je suis dans mon jardin : me localiser"})},function(){M.textContent="Position indisponible, tapez simplement votre adresse.";G.textContent="Je suis dans mon jardin : me localiser"},{enableHighAccuracy:true,timeout:10000,maximumAge:60000})})}
try{var s=JSON.parse(localStorage.getItem(CLE)||"null");if(s&&!s.id&&s.adresse){var r=document.getElementById("cglp-reprise");if(r&&Q)r.hidden=false}}catch(e){}
if(A&&Q)try{fetch(A+"/q/q.js",{mode:"no-cors"}).catch(function(){})}catch(e){}
ev("cgp_q_vue",{etape:"accueil"})})()</script>'''


# « À planter dès maintenant » si le mois en cours est un bon mois, sinon le prochain bon mois
JSMOIS = r'''<script>(function(){var b=document.getElementById("cglp-planter");if(!b)return;var L=b.getAttribute("data-mois").split(",").map(Number),m=new Date().getMonth()+1,N=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"];
if(L.indexOf(m)>=0)return;for(var i=1;i<=12;i++){var k=(m+i-1)%12+1;if(L.indexOf(k)>=0){b.textContent="À planter dès "+N[k-1];return}}})()</script>'''


def rendre(base='', questionnaire='', api=''):
    return CSS + f'''<div class="cglp" id="cglp-accueil">
<div class="entree">
<div class="apercu">
<div class="photo"><img class="av" src="{IMG}jardin-avant.webp" width="1200" height="800" alt="Le jardin avant : une pelouse et une terrasse couverte derrière la maison" decoding="async">
<img class="ap" src="{IMG}jardin-apres.webp" width="1200" height="800" alt="Le même jardin imaginé par notre outil : terrasse bois, pergola, clôture et massifs fleuris" decoding="async">
<span class="tag t-av">Avant</span><span class="tag t-ap">Après, imaginé par notre outil</span></div>
<div class="vu v-sol"><small>Votre soleil<span class="long">, heure par heure</span></small><strong>{SOLEIL['heures']} h <span>le 21 juin</span></strong><div class="sol">{''.join(f'<i style="background:{couleur_soleil(f)}"></i>' for f in SOLEIL['profil'])}</div><div class="heures"><span>8 h</span><span>14 h</span><span>21 h</span></div></div>
<div class="vu v-bud"><small>Votre budget<span class="long">, idée par idée</span></small>{''.join(f'<div><span>{e(n)}</span><b>{e(x)}</b></div>' for n, x in BUDGET)}</div>
<div class="vu v-pla"><small>Vos plantes<span class="long">, choisies pour votre soleil</span></small><ul>{''.join(f'<li><img src="{IMG}plante-{k}.webp" width="64" height="64" alt="" loading="lazy">{e(n)}</li>' for k, n in PLANTES)}<li class="plus"><i><img src="{IMG}plante-{PLANTES_EN_PLUS[0]}.webp" width="64" height="64" alt="" loading="lazy"></i>Et {PLANTES_EN_PLUS[1]} autres</li></ul><p><b id="cglp-planter" data-mois="{','.join(map(str, MOIS_PLANTATION))}">À planter dès maintenant</b></p></div>
</div>
<div class="boite">
<h1>Le diagnostic gratuit de votre <span class="v">jardin</span><span class="o">.</span></h1>
<p>Quoi planter et quand, où créer de l'ombre et de l'intimité, et ce que coûte chaque idée. Il suffit de son adresse.</p>
<form id="cglp-form" data-q="{e(questionnaire)}" data-api="{e(api)}" novalidate autocomplete="off">
<label for="cglp-a">Où se trouve votre jardin ?</label>
<div class="champ"><input id="cglp-a" type="text" autocomplete="street-address" placeholder="Ex. 12 rue des Lilas, Nantes" aria-autocomplete="list" aria-controls="cglp-sug"><ul class="sug" id="cglp-sug" role="listbox" hidden></ul></div>
<p class="msg" id="cglp-msg" role="status"></p>
<button type="submit" class="cta">Voir le potentiel de mon jardin</button>
<button type="button" class="geo" id="cglp-geo" hidden>Je suis dans mon jardin : me localiser</button>
</form>
<span class="petit"><b>Gratuit</b> : plan, plantes et budget par email en 3 minutes. Votre adresse sert uniquement au calcul.</span>
<a class="reprise" id="cglp-reprise" href="{e(questionnaire) or '#'}" hidden>Reprendre mon diagnostic en cours</a>
</div></div>
<div class="atouts">
<div><i>{ICO['plante']}</i><b>Quoi planter, et quand</b><p>Des plantes choisies pour votre région, votre soleil et votre temps, avec le bon mois pour les planter.</p></div>
<div><i>{ICO['soleil']}</i><b>Le potentiel de votre jardin</b><p>Le soleil heure par heure, les vis-à-vis, les coins à valoriser : ce que votre jardin peut devenir.</p></div>
<div><i>{ICO['plan']}</i><b>Votre jardin imaginé</b><p>À partir de votre photo, nos produits posés chez vous, au bon endroit.</p></div>
<div><i>{ICO['euro']}</i><b>Le budget, chiffré</b><p>Ce que coûte chaque idée, de la plus simple à la plus ambitieuse, pour avancer à votre rythme.</p></div>
</div></div>''' + JS + JSMOIS
