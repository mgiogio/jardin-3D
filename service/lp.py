# Page d'entrée du « Diagnostic jardin » : un visuel, un encadré avec un seul bouton pour commencer, trois cartes de réassurance.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin] au-dessus du questionnaire, qui reste caché
# jusqu'au clic sur « Je commence ». Styles préfixés .cglp. On ne dévoile pas ici le contenu du diagnostic (plantes, produits).
import html

e = lambda s: html.escape(str(s or ''))

CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);max-width:1080px;margin:0 auto;padding:32px 16px 8px}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp .entree{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(30,33,31,.08),0 8px 30px rgba(30,33,31,.06)}
.cglp .visuel{position:relative;min-height:420px;background:var(--gris) center/cover no-repeat}
.cglp .bulle{position:absolute;display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:10px 14px;font-size:14px;font-weight:500;
box-shadow:0 6px 18px rgba(0,0,0,.18);max-width:78%}
.cglp .bulle svg{flex:none;width:20px;height:20px}
.cglp .bulle.b1{left:18px;top:22px}.cglp .bulle.b2{right:18px;top:42%}.cglp .bulle.b3{left:18px;bottom:22px;background:var(--vert);color:#fff}
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
.cglp form .cta{width:100%;min-width:0;margin-top:2px}
.cglp .geo{appearance:none;background:none;border:0;padding:4px 0;font:500 14px var(--f);color:var(--vert);text-decoration:underline;cursor:pointer;justify-self:center}
.cglp .msg{margin:0;font-size:14px;color:#C62828;min-height:0}.cglp .msg:empty{display:none}
.cglp .reprise{font-size:14px;color:var(--txt);text-decoration:underline}
.cglp .atouts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
.cglp .atouts div{background:#fff;border-radius:14px;padding:22px 20px;text-align:center;box-shadow:0 1px 3px rgba(30,33,31,.06)}
.cglp .atouts i{display:inline-grid;place-items:center;width:44px;height:44px;border-radius:10px;background:var(--brume);color:var(--vert);margin-bottom:10px}
.cglp .atouts i svg{width:24px;height:24px}
.cglp .atouts b{display:block;font-size:17px;margin-bottom:4px}.cglp .atouts p{margin:0;color:var(--muted);font-size:14px}
@media (max-width:820px){.cglp{padding-top:16px}.cglp .entree{grid-template-columns:1fr}.cglp .visuel{min-height:260px}
.cglp .boite{margin:14px;padding:26px 18px}.cglp h1{font-size:28px}.cglp .cta{width:100%;min-width:0;padding:0 14px;font-size:16px;white-space:nowrap}.cglp .atouts{grid-template-columns:1fr}
.cglp .bulle{font-size:13px;padding:8px 11px}.cglp .bulle.b2{top:auto;bottom:64px}}
</style>'''

SOLEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#EB5A00" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
OEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#1E211F" stroke-width="2" stroke-linecap="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>'
FEUILLE_V = '<svg viewBox="0 0 24 24" fill="none" stroke="#049E00" stroke-width="2" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7z"/></svg>'
FEUILLE = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15M5 19l7-7"/></svg>'
ICO = {'plante': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7zM7 21h10"/></svg>',
       'soleil': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
       'cadeau': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13M12 7c-2-4-6-3-5 0M12 7c2-4 6-3 5 0"/></svg>',
       'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg>',
       'plan': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 9h18M5 9l2-4h10l2 4M6 9v11M18 9v11M3 20h18"/></svg>'}


JS = r'''<script>(function(){var F=document.getElementById("cglp-form");if(!F)return;var I=document.getElementById("cglp-a"),L=document.getElementById("cglp-sug"),M=document.getElementById("cglp-msg"),G=document.getElementById("cglp-geo"),Q=F.getAttribute("data-q"),res=[],tm,ct,CLE="cg_diag_v1";
function h(s){return String(s||"").replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function ev(n,p){try{window.dataLayer=window.dataLayer||[];var o={event:n};for(var k in p)o[k]=p[k];dataLayer.push(o)}catch(e){}}
function va(f){var p=f.properties||{},c=f.geometry.coordinates;return{label:p.label,name:p.name||p.label,city:p.city,postcode:p.postcode||"",citycode:p.citycode,lat:c[1],lon:c[0],score:p.score,type:p.type}}
function cherche(q,sig){var u=["https://data.geopf.fr/geocodage/search?q="+encodeURIComponent(q)+"&limit=5&index=address&autocomplete=1","https://api-adresse.data.gouv.fr/search/?q="+encodeURIComponent(q)+"&limit=5&autocomplete=1"];
function t(i){if(i>=u.length)return Promise.reject(new Error("x"));return fetch(u[i],{signal:sig}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){return(d.features||[]).map(va)}).catch(function(e){if(e&&e.name==="AbortError")throw e;return t(i+1)})}return t(0)}
function aff(l){res=l;if(!l.length){L.hidden=true;return}L.innerHTML=l.map(function(a,i){return'<li role="option"><button type="button" data-i="'+i+'">'+h(a.name)+" <small>"+h(a.postcode+" "+a.city)+"</small></button></li>"}).join("");L.hidden=false}
function suivi(){var q=new URLSearchParams(location.search),s={};["utm_source","utm_medium","utm_campaign","utm_content","utm_term","gclid","fbclid","msclkid"].forEach(function(k){if(q.get(k))s[k]=q.get(k).slice(0,120)});s.referrer=(document.referrer||"").slice(0,200);s.page=(location.origin+location.pathname).slice(0,200);return s}
function partir(a){var S={v:1,cree:Date.now(),etape:"terrain",temps:{},infos:{},suivi:suivi(),adresse:{label:a.label,city:a.city,postcode:a.postcode,citycode:a.citycode,lat:a.lat,lon:a.lon,score:a.score}};
try{localStorage.setItem(CLE,JSON.stringify(S))}catch(e){}ev("cgp_q_adresse",{etape:"accueil",reponse:a.type||""});
var qs=location.search.replace(/^\?/,"");if(Q)location.href=Q+(qs?(Q.indexOf("?")<0?"?":"&")+qs:"");else location.reload()}
I.addEventListener("input",function(){clearTimeout(tm);M.textContent="";var v=I.value.trim();if(v.length<4){L.hidden=true;return}tm=setTimeout(function(){if(ct)ct.abort();ct=window.AbortController?new AbortController():null;cherche(v,ct&&ct.signal).then(aff).catch(function(e){if(!e||e.name!=="AbortError")M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})},220)});
I.addEventListener("focus",function(){ev("cgp_q_etape",{etape:"accueil_adresse"})},{once:true});
L.addEventListener("click",function(e){var b=e.target.closest("button[data-i]");if(b)partir(res[+b.getAttribute("data-i")])});
F.addEventListener("submit",function(e){e.preventDefault();if(res[0])return partir(res[0]);var v=I.value.trim();if(v.length<4){M.textContent="Indiquez l'adresse de votre jardin.";I.focus();return}cherche(v).then(function(l){if(l[0])partir(l[0]);else M.textContent="Adresse introuvable, vérifiez-la ou choisissez-la dans la liste."}).catch(function(){M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})});
if("geolocation" in navigator){G.hidden=false;G.addEventListener("click",function(){G.textContent="Localisation en cours…";navigator.geolocation.getCurrentPosition(function(p){var la=p.coords.latitude,lo=p.coords.longitude;fetch("https://data.geopf.fr/geocodage/reverse?lat="+la+"&lon="+lo+"&limit=1&index=address").then(function(r){return r.json()}).then(function(d){var f=(d.features||[])[0];if(!f)throw 0;var a=va(f);a.lat=la;a.lon=lo;ev("cgp_q_geoloc",{});partir(a)}).catch(function(){M.textContent="Adresse introuvable, tapez-la simplement.";G.textContent="Je suis dans mon jardin : me localiser"})},function(){M.textContent="Position indisponible, tapez simplement votre adresse.";G.textContent="Je suis dans mon jardin : me localiser"},{enableHighAccuracy:true,timeout:10000,maximumAge:60000})})}
try{var s=JSON.parse(localStorage.getItem(CLE)||"null");if(s&&!s.id&&s.adresse){var r=document.getElementById("cglp-reprise");if(r&&Q)r.hidden=false}}catch(e){}
ev("cgp_q_vue",{etape:"accueil"})})()</script>'''


def rendre(base='', questionnaire=''):
    fond = f'{base}/assets/refs/pergola_ensemble.jpg'
    return CSS + f'''<div class="cglp" id="cglp-accueil">
<div class="entree">
<div class="visuel" style="background-image:url('{e(fond)}')" role="img" aria-label="Une pergola Cover Green posée chez un client">
<span class="bulle b1">{SOLEIL}Le soleil heure par heure</span>
<span class="bulle b2">{FEUILLE_V}Quoi planter, et quand</span>
<span class="bulle b3">{FEUILLE}Le potentiel de votre jardin</span></div>
<div class="boite">
<h1>Le diagnostic gratuit de votre <span class="v">jardin</span><span class="o">.</span></h1>
<p>Quoi planter et quand, où créer de l'ombre et de l'intimité, et votre jardin imaginé avec nos produits. Tout commence par son adresse.</p>
<form id="cglp-form" data-q="{e(questionnaire)}" novalidate autocomplete="off">
<label for="cglp-a">Où se trouve votre jardin ?</label>
<div class="champ"><input id="cglp-a" type="text" autocomplete="street-address" placeholder="Ex. 12 rue des Lilas, Nantes" aria-autocomplete="list" aria-controls="cglp-sug"><ul class="sug" id="cglp-sug" role="listbox" hidden></ul></div>
<p class="msg" id="cglp-msg" role="status"></p>
<button type="submit" class="cta">Voir le potentiel de mon jardin</button>
<button type="button" class="geo" id="cglp-geo" hidden>Je suis dans mon jardin : me localiser</button>
</form>
<span class="petit"><b>Gratuit</b> · résultat par email en 3 minutes · votre adresse sert uniquement au calcul</span>
<a class="reprise" id="cglp-reprise" href="{e(questionnaire) or '#'}" hidden>Reprendre mon diagnostic en cours</a>
</div></div>
<div class="atouts">
<div><i>{ICO['plante']}</i><b>Quoi planter, et quand</b><p>Des plantes choisies pour votre région, votre soleil et votre temps, avec le bon mois pour les planter.</p></div>
<div><i>{ICO['soleil']}</i><b>Le potentiel de votre jardin</b><p>Le soleil heure par heure, les vis-à-vis, les coins à valoriser : ce que votre jardin peut devenir.</p></div>
<div><i>{ICO['plan']}</i><b>Votre jardin imaginé</b><p>À partir de votre photo, nos produits posés chez vous, au bon endroit, avec un budget clair.</p></div>
</div></div>''' + JS
