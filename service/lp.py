# Page d'entrée du « Diagnostic jardin » : un aperçu d'exemple du diagnostic (plan, soleil, budget), l'encadré avec la question de l'adresse, quatre cartes.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin] au-dessus du questionnaire, qui reste caché
# jusqu'au clic sur « Je commence ». Styles préfixés .cglp. On ne dévoile pas ici le contenu du diagnostic (plantes, produits).
import html

e = lambda s: html.escape(str(s or ''))

CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);max-width:1080px;margin:0 auto;padding:32px 16px 8px}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp .entree{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(30,33,31,.08),0 8px 30px rgba(30,33,31,.06)}
.cglp .apercu{position:relative;min-height:440px;background:linear-gradient(160deg,#EAF7E5 0%,#F7FBF5 60%,#FFF4EC 100%);padding:28px 30px 40px 26px;display:flex;align-items:center;justify-content:center}
.cglp .rapport{position:relative;width:100%;max-width:400px;background:#fff;border-radius:14px;box-shadow:0 2px 6px rgba(30,33,31,.06),0 18px 40px rgba(30,33,31,.10);padding:16px 16px 18px}
.cglp .rapport .tete{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--muted);margin-bottom:10px}
.cglp .rapport .tete b{font-size:14px;color:var(--txt)}
.cglp .rapport .tete em{font-style:normal;background:var(--gris);border-radius:20px;padding:2px 9px}
.cglp .rapport svg.plan{display:block;width:100%;height:auto;border-radius:10px}
.cglp .lignes{display:grid;gap:8px;margin-top:12px;padding-right:0}
.cglp .lig{display:flex;align-items:center;gap:10px;font-size:13.5px;line-height:1.3;text-align:left}
.cglp .lig i{flex:none;display:grid;place-items:center;width:28px;height:28px;border-radius:8px;background:var(--brume)}
.cglp .lig i svg{width:17px;height:17px}
.cglp .lig .flou{display:inline-block;height:11px;border-radius:6px;background:#BFE2B3;filter:blur(2.5px);vertical-align:middle;margin-left:5px}
.cglp .budget{margin:14px -26px -30px 26px;background:var(--txt);color:#fff;border-radius:12px;padding:12px 16px 10px;box-shadow:0 12px 28px rgba(0,0,0,.22);text-align:left}
.cglp .budget small{display:block;font-size:11.5px;opacity:.75;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
.cglp .budget ul{list-style:none;margin:0;padding:0}
.cglp .budget li{display:flex;justify-content:space-between;gap:12px;font-size:13.5px;padding:5px 0;border-top:1px solid rgba(255,255,255,.14)}
.cglp .budget li:first-child{border-top:0}.cglp .budget li b{font-weight:700;white-space:nowrap}
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
.cglp .atouts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}
.cglp .atouts div{background:#fff;border-radius:14px;padding:22px 20px;text-align:center;box-shadow:0 1px 3px rgba(30,33,31,.06)}
.cglp .atouts i{display:inline-grid;place-items:center;width:44px;height:44px;border-radius:10px;background:var(--brume);color:var(--vert);margin-bottom:10px}
.cglp .atouts i svg{width:24px;height:24px}
.cglp .atouts b{display:block;font-size:17px;margin-bottom:4px}.cglp .atouts p{margin:0;color:var(--muted);font-size:14px}
@media (max-width:980px){.cglp .atouts{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:820px){.cglp{padding-top:16px}.cglp .entree{grid-template-columns:1fr}.cglp .boite{order:-1;margin:14px;padding:26px 18px}
.cglp .apercu{min-height:0;padding:8px 22px 48px 16px;background:linear-gradient(180deg,#fff 0%,#EAF7E5 30%,#F7FBF5 100%)}.cglp .budget{margin:14px -14px -26px 10px}
.cglp h1{font-size:28px}.cglp .cta{width:100%;min-width:0;padding:0 14px;font-size:16px;white-space:nowrap}}
@media (max-width:520px){.cglp .atouts{grid-template-columns:1fr}}
</style>'''

SOLEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#EB5A00" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
OEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#1E211F" stroke-width="2" stroke-linecap="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>'
FEUILLE_V = '<svg viewBox="0 0 24 24" fill="none" stroke="#049E00" stroke-width="2" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7z"/></svg>'
FEUILLE = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15M5 19l7-7"/></svg>'
ICO = {'plante': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7zM7 21h10"/></svg>',
       'soleil': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
       'cadeau': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13M12 7c-2-4-6-3-5 0M12 7c2-4 6-3 5 0"/></svg>',
       'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg>',
       'euro': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M17 6.5A7 7 0 1 0 17 17.5M4 10h9M4 14h9"/></svg>',
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
var u=new URLSearchParams(location.search),k=new URLSearchParams();u.forEach(function(v,n){if(/^(utm_|gclid$|fbclid$|msclkid$)/.test(n))k.append(n,v)});var qs=k.toString();if(Q)location.href=Q+(qs?(Q.indexOf("?")<0?"?":"&")+qs:"");else location.reload()}
I.addEventListener("input",function(){clearTimeout(tm);M.textContent="";var v=I.value.trim();if(v.length<4){L.hidden=true;return}tm=setTimeout(function(){if(ct)ct.abort();ct=window.AbortController?new AbortController():null;cherche(v,ct&&ct.signal).then(aff).catch(function(e){if(!e||e.name!=="AbortError")M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})},220)});
I.addEventListener("focus",function(){ev("cgp_q_etape",{etape:"accueil_adresse"})},{once:true});
L.addEventListener("click",function(e){var b=e.target.closest("button[data-i]");if(b)partir(res[+b.getAttribute("data-i")])});
F.addEventListener("submit",function(e){e.preventDefault();if(res[0])return partir(res[0]);var v=I.value.trim();if(v.length<4){M.textContent="Indiquez l'adresse de votre jardin.";I.focus();return}cherche(v).then(function(l){if(l[0])partir(l[0]);else M.textContent="Adresse introuvable, vérifiez-la ou choisissez-la dans la liste."}).catch(function(){M.textContent="La recherche d'adresse ne répond pas, réessayez dans un instant."})});
if("geolocation" in navigator){G.hidden=false;G.addEventListener("click",function(){G.textContent="Localisation en cours…";navigator.geolocation.getCurrentPosition(function(p){var la=p.coords.latitude,lo=p.coords.longitude;fetch("https://data.geopf.fr/geocodage/reverse?lat="+la+"&lon="+lo+"&limit=1&index=address").then(function(r){return r.json()}).then(function(d){var f=(d.features||[])[0];if(!f)throw 0;var a=va(f);a.lat=la;a.lon=lo;ev("cgp_q_geoloc",{});partir(a)}).catch(function(){M.textContent="Adresse introuvable, tapez-la simplement.";G.textContent="Je suis dans mon jardin : me localiser"})},function(){M.textContent="Position indisponible, tapez simplement votre adresse.";G.textContent="Je suis dans mon jardin : me localiser"},{enableHighAccuracy:true,timeout:10000,maximumAge:60000})})}
try{var s=JSON.parse(localStorage.getItem(CLE)||"null");if(s&&!s.id&&s.adresse){var r=document.getElementById("cglp-reprise");if(r&&Q)r.hidden=false}}catch(e){}
ev("cgp_q_vue",{etape:"accueil"})})()</script>'''


def rendre(base='', questionnaire=''):
    return CSS + f'''<div class="cglp" id="cglp-accueil">
<div class="entree">
<div class="apercu">
<div class="rapport" aria-label="Exemple de diagnostic">
<div class="tete"><b>Votre diagnostic</b><em>Exemple</em></div>
<svg class="plan" viewBox="0 0 368 190" role="img" aria-label="Plan d'exemple : le soleil, l'ombre, le vis-à-vis et les emplacements proposés">
<defs><linearGradient id="cglp-sol" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFE3B3"/><stop offset=".55" stop-color="#FFF6E2"/><stop offset="1" stop-color="#E4EEF6"/></linearGradient>
<pattern id="cglp-h" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="#C9D8E4"/><line x1="0" y1="0" x2="0" y2="7" stroke="#B3C5D4" stroke-width="3"/></pattern></defs>
<rect width="368" height="190" fill="#DDEFD5"/>
<rect x="10" y="10" width="348" height="170" rx="6" fill="url(#cglp-sol)" opacity=".55"/>
<rect x="10" y="10" width="348" height="170" rx="6" fill="none" stroke="#049E00" stroke-width="2"/>
<rect x="18" y="18" width="118" height="68" rx="3" fill="#D9DCDA" stroke="#B5BAB7"/><text x="77" y="56" font-size="11" text-anchor="middle" fill="#5B625E" font-family="Roboto,Arial">Maison</text>
<rect x="250" y="120" width="100" height="52" fill="url(#cglp-h)" opacity=".8"/><text x="300" y="150" font-size="10" text-anchor="middle" fill="#3D5466" font-family="Roboto,Arial">Ombre à 17 h</text>
<line x1="356" y1="14" x2="356" y2="176" stroke="#EB5A00" stroke-width="5" stroke-linecap="round"/>
<g font-family="Roboto,Arial" font-size="10" fill="#C84800"><rect x="292" y="20" width="58" height="18" rx="9" fill="#fff"/><text x="321" y="33" text-anchor="middle">Vis-à-vis</text></g>
<rect x="150" y="26" width="84" height="62" rx="2" fill="none" stroke="#EB5A00" stroke-width="2" stroke-dasharray="5 4"/>
<g stroke="#EB5A00" stroke-width="1.4" opacity=".7"><line x1="160" y1="26" x2="160" y2="88"/><line x1="172" y1="26" x2="172" y2="88"/><line x1="184" y1="26" x2="184" y2="88"/><line x1="196" y1="26" x2="196" y2="88"/><line x1="208" y1="26" x2="208" y2="88"/><line x1="220" y1="26" x2="220" y2="88"/></g>
<g font-family="Roboto,Arial" font-size="10"><rect x="160" y="94" width="64" height="18" rx="9" fill="#EB5A00"/><text x="192" y="107" text-anchor="middle" fill="#fff">Pergola</text></g>
<g fill="#049E00"><circle cx="40" cy="150" r="9" opacity=".85"/><circle cx="64" cy="160" r="7" opacity=".7"/><circle cx="88" cy="148" r="10" opacity=".8"/><circle cx="114" cy="160" r="6" opacity=".7"/><circle cx="330" cy="70" r="8" opacity=".75"/><circle cx="330" cy="98" r="7" opacity=".65"/></g>
<g font-family="Roboto,Arial" font-size="10" fill="#1E211F"><rect x="26" y="112" width="88" height="18" rx="9" fill="#fff"/><text x="70" y="125" text-anchor="middle">Plein soleil</text></g>
</svg>
<div class="lignes">
<div class="lig"><i>{SOLEIL}</i><span>Soleil : 7 h par jour en été, ombre dès 17 h sur la terrasse</span></div>
<div class="lig"><i>{FEUILLE_V}</i><span>À planter en mars :<span class="flou" style="width:58px"></span><span class="flou" style="width:44px"></span><span class="flou" style="width:52px"></span></span></div>
<div class="lig"><i>{OEIL}</i><span>Vis-à-vis à 4,5 m : 12 m de clôture occultante</span></div>
</div>
<div class="budget"><small>Budget, idée par idée</small><ul><li><span>Massif de vivaces</span><b>150 à 250 €</b></li><li><span>Pergola</span><b>1 100 à 1 400 €</b></li><li><span>Clôture, 12 m</span><b>1 400 à 1 700 €</b></li></ul></div>
</div></div>
<div class="boite">
<h1>Le diagnostic gratuit de votre <span class="v">jardin</span><span class="o">.</span></h1>
<p>Quoi planter et quand, où créer de l'ombre et de l'intimité, et combien ça coûte, idée par idée. Tout commence par son adresse.</p>
<form id="cglp-form" data-q="{e(questionnaire)}" novalidate autocomplete="off">
<label for="cglp-a">Où se trouve votre jardin ?</label>
<div class="champ"><input id="cglp-a" type="text" autocomplete="street-address" placeholder="Ex. 12 rue des Lilas, Nantes" aria-autocomplete="list" aria-controls="cglp-sug"><ul class="sug" id="cglp-sug" role="listbox" hidden></ul></div>
<p class="msg" id="cglp-msg" role="status"></p>
<button type="submit" class="cta">Voir le potentiel de mon jardin</button>
<button type="button" class="geo" id="cglp-geo" hidden>Je suis dans mon jardin : me localiser</button>
</form>
<span class="petit"><b>Gratuit</b> · plan, plantes et budget par email en 3 minutes · votre adresse sert uniquement au calcul</span>
<a class="reprise" id="cglp-reprise" href="{e(questionnaire) or '#'}" hidden>Reprendre mon diagnostic en cours</a>
</div></div>
<div class="atouts">
<div><i>{ICO['plante']}</i><b>Quoi planter, et quand</b><p>Des plantes choisies pour votre région, votre soleil et votre temps, avec le bon mois pour les planter.</p></div>
<div><i>{ICO['soleil']}</i><b>Le potentiel de votre jardin</b><p>Le soleil heure par heure, les vis-à-vis, les coins à valoriser : ce que votre jardin peut devenir.</p></div>
<div><i>{ICO['plan']}</i><b>Votre jardin imaginé</b><p>À partir de votre photo, nos produits posés chez vous, au bon endroit.</p></div>
<div><i>{ICO['euro']}</i><b>Le budget, chiffré</b><p>Ce que coûte chaque idée, de la plus simple à la plus ambitieuse, pour avancer à votre rythme.</p></div>
</div></div>''' + JS
