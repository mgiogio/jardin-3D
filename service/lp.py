# Page d'entrée du « Diagnostic jardin » : un avant / après réel (photo d'un jardin et visuel produit par l'outil), l'encadré avec la question de l'adresse, quatre cartes.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin] au-dessus du questionnaire, qui reste caché
# jusqu'au clic sur « Je commence ». Styles préfixés .cglp. On ne dévoile pas ici le contenu du diagnostic (plantes, produits).
import html

e = lambda s: html.escape(str(s or ''))
# avant / après : un vrai projet passé dans l'outil ; images dans la médiathèque WordPress (pas dans ce dépôt public)
AVANT = 'https://cover.green/wp-content/uploads/diagnostic/jardin-avant.webp'
APRES = 'https://cover.green/wp-content/uploads/diagnostic/jardin-apres.webp'

CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);max-width:1080px;margin:0 auto;padding:32px 16px 8px}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp .entree{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(30,33,31,.08),0 8px 30px rgba(30,33,31,.06)}
.cglp .apercu{position:relative;min-height:520px;background:#DDE3DF;overflow:hidden;touch-action:pan-y;cursor:ew-resize;user-select:none;-webkit-user-select:none}
.cglp .apercu img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 55%;display:block;pointer-events:none}
.cglp .apercu .avant{clip-path:inset(0 calc(100% - var(--p)) 0 0)}
.cglp .apercu .trait{position:absolute;top:0;bottom:0;left:var(--p);width:2px;margin-left:-1px;background:#fff;box-shadow:0 0 8px rgba(0,0,0,.35);pointer-events:none}
.cglp .apercu .trait:after{content:"";position:absolute;top:50%;left:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:#fff no-repeat center/24px url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E211F' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 6l-6 6 6 6M15 6l6 6-6 6'/%3E%3C/svg%3E");box-shadow:0 2px 10px rgba(0,0,0,.3)}
.cglp .apercu .tag{position:absolute;top:16px;padding:5px 10px;border-radius:6px;background:rgba(30,33,31,.62);color:#fff;font-size:13px;font-weight:600;pointer-events:none;transition:opacity .2s}
.cglp .apercu .t-av{left:16px}.cglp .apercu .t-ap{right:16px;background:var(--vert)}
.cglp .apercu .bas{position:absolute;left:0;bottom:0;max-width:64%;padding:40px 18px 16px;color:#fff;text-align:left;pointer-events:none;font-size:15px;line-height:1.3;font-weight:700;text-shadow:0 1px 4px rgba(0,0,0,.6)}
.cglp .apercu:before{content:"";position:absolute;left:0;right:0;bottom:0;height:120px;background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.5));pointer-events:none;z-index:1}
.cglp .apercu .bas,.cglp .apercu .trait,.cglp .apercu .tag{z-index:2}.cglp .apercu .pt{z-index:3}.cglp .apercu .fiche{z-index:4}
.cglp .apercu .pt{position:absolute;width:34px;height:34px;margin:-17px 0 0 -17px;border:0;padding:0;border-radius:50%;background:rgba(255,255,255,.3);cursor:pointer;opacity:0;transform:scale(.3);transition:opacity .35s,transform .35s}
.cglp .apercu .pt:before{content:"";position:absolute;inset:9px;border-radius:50%;background:#fff;box-shadow:0 1px 5px rgba(0,0,0,.4);transition:background .2s}
.cglp .apercu .pt:after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid #fff;animation:cglp-pouls 2s ease-out infinite}
@keyframes cglp-pouls{0%{transform:scale(.5);opacity:.9}100%{transform:scale(1.5);opacity:0}}
.cglp .apercu.points .pt{opacity:1;transform:none}.cglp .apercu .pt.cache{opacity:0;pointer-events:none}
.cglp .apercu .pt.on:before{background:var(--orange)}.cglp .apercu .pt:focus-visible{outline:3px solid var(--vert);outline-offset:2px}
.cglp .apercu .fiche{position:absolute;width:256px;background:#fff;border-radius:10px;padding:12px 14px 13px;box-shadow:0 10px 28px rgba(0,0,0,.28);font-size:13.5px;line-height:1.4;color:var(--muted);text-align:left;opacity:0;transform:translateY(6px);transition:opacity .25s,transform .25s;pointer-events:none;cursor:default}
.cglp .apercu .fiche.on{opacity:1;transform:none}
.cglp .apercu .fiche b{display:block;font-size:15px;line-height:1.3;color:var(--txt);margin-bottom:8px}
.cglp .apercu .fiche p{margin:8px 0 0}
.cglp .apercu .fiche .prix{margin-top:8px;color:var(--txt);font-weight:600}.cglp .apercu .fiche .prix strong{color:var(--orange)}
.cglp .apercu .sol{display:flex;gap:1px;height:10px}.cglp .apercu .sol i{flex:1;border-radius:1px}
.cglp .apercu .heures{display:flex;justify-content:space-between;font-size:11px;margin-top:3px}
.cglp .apercu .mois{display:grid;grid-template-columns:repeat(12,1fr);gap:2px}
.cglp .apercu .mois i{font-style:normal;font-size:10.5px;line-height:18px;text-align:center;border-radius:3px;background:var(--vert);color:#fff}
.cglp .apercu input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.cglp .apercu:focus-within .trait:after{outline:3px solid var(--vert);outline-offset:2px}
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
.cglp .apercu{min-height:0;aspect-ratio:4/5;margin:0 14px 14px;border-radius:12px}.cglp .apercu .bas{font-size:14px;max-width:70%}
.cglp .apercu .fiche{width:min(232px,66%);font-size:12.5px;padding:10px 12px 11px}.cglp .apercu .fiche b{font-size:14px}
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


# avant / après : premier balayage automatique quand l'image apparaît, puis 3 points qui expliquent le projet (soleil, vis-à-vis, plantes)
# avec les vrais chiffres de ce diagnostic ; glisser (souris ou doigt) ou clavier pour comparer
JSBA = r'''<script>(function(){var B=document.getElementById("cglp-ba");if(!B)return;var R=B.querySelector("input"),P=[].slice.call(B.querySelectorAll(".pt")),F=[].slice.call(B.querySelectorAll(".fiche")),TA=B.querySelector(".t-av"),TP=B.querySelector(".t-ap"),p=82,touche=false,vu=false,act=-1,tc=null;
function ev(n,o){try{window.dataLayer=window.dataLayer||[];var x={event:n};for(var k in o)x[k]=o[k];dataLayer.push(x)}catch(e){}}
function pose(v){p=Math.max(0,Math.min(100,v));B.style.setProperty("--p",p+"%");R.value=Math.round(p);TA.style.opacity=p<14?0:1;TP.style.opacity=p>86?0:1;
P.forEach(function(d,i){var c=(+d.getAttribute("data-xc")||0)<p+3;d.classList.toggle("cache",c);if(c&&act===i)montre(-1)})}
function place(){var cw=B.clientWidth,ch=B.clientHeight,iw=+B.getAttribute("data-l"),ih=+B.getAttribute("data-h"),s=Math.max(cw/iw,ch/ih),dw=iw*s,dh=ih*s,ox=(cw-dw)/2,oy=(ch-dh)*(+B.getAttribute("data-oy"))/100;
P.forEach(function(d,i){var X=ox+d.getAttribute("data-x")/100*dw,Y=oy+d.getAttribute("data-y")/100*dh;d.style.left=X+"px";d.style.top=Y+"px";d.setAttribute("data-xc",X/cw*100);
var f=F[i],fw=f.offsetWidth,fh=f.offsetHeight;if(X>cw*.55){f.style.left="";f.style.right=Math.max(8,cw-X+24)+"px"}else{f.style.right="";f.style.left=Math.min(cw-fw-8,X+24)+"px"}
f.style.top=Math.max(12,Math.min(ch-fh-12,Y-fh/2))+"px"});pose(p)}
function montre(i){act=i;P.forEach(function(d,k){d.classList.toggle("on",k===i)});F.forEach(function(f,k){f.classList.toggle("on",k===i)})}
function stopCycle(){if(tc){clearInterval(tc);tc=null}}
function stop(){stopCycle();if(!touche){touche=true;ev("cgp_lp_avant_apres",{})}}
var bouge=false;B.addEventListener("pointerdown",function(e){if(e.target.closest(".pt,.fiche"))return;bouge=true;stop();montre(-1);pose(x(e))});
function x(e){var r=B.getBoundingClientRect();return(e.clientX-r.left)/r.width*100}
addEventListener("pointermove",function(e){if(bouge)pose(x(e))});addEventListener("pointerup",function(){bouge=false});addEventListener("pointercancel",function(){bouge=false});
R.addEventListener("input",function(){stop();pose(+R.value)});
P.forEach(function(d,i){d.addEventListener("click",function(){stopCycle();montre(act===i?-1:i);ev("cgp_lp_point",{point:i+1})})});
function points(){B.classList.add("points");place();if(touche)return;var i=0;montre(0);tc=setInterval(function(){i=(i+1)%P.length;montre(i)},4200)}
function anime(){if(touche||vu)return;vu=true;if(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches){pose(4);B.classList.add("points");place();montre(0);return}
var t0=null,K=[[0,82],[700,82],[2200,4]];function f(t){if(touche)return;if(!t0)t0=t;var d=t-t0,i=1;while(i<K.length-1&&d>K[i][0])i++;var a=K[i-1],b=K[i],u=Math.max(0,Math.min(1,(d-a[0])/(b[0]-a[0])));u=u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;pose(a[1]+(b[1]-a[1])*u);if(d<K[K.length-1][0])requestAnimationFrame(f);else setTimeout(points,250)}requestAnimationFrame(f)}
addEventListener("resize",place);place();
var im=B.querySelector(".apres");function go(){if("IntersectionObserver" in window){var o=new IntersectionObserver(function(z){if(z[0].isIntersecting){o.disconnect();anime()}},{threshold:.5});o.observe(B)}else anime()}
if(im.complete)go();else im.addEventListener("load",go)})()</script>'''


def rendre(base='', questionnaire='', api=''):
    return CSS + f'''<div class="cglp" id="cglp-accueil">
<div class="entree">
<div class="apercu" id="cglp-ba" style="--p:82%" data-l="720" data-h="960" data-oy="55">
<img class="apres" src="{e(APRES)}" width="720" height="960" alt="Le même jardin imaginé avec une pergola, une clôture, du gravier et des plantes" decoding="async">
<img class="avant" src="{e(AVANT)}" width="720" height="960" alt="Le jardin avant : de la terre nue devant la maison" decoding="async">
<span class="trait"></span><span class="tag t-av">Avant</span><span class="tag t-ap">Après</span>
<input type="range" min="0" max="100" value="82" aria-label="Comparer le jardin avant et après">
<div class="bas">Un vrai jardin, imaginé par notre outil à partir d'une photo.</div>
<button type="button" class="pt" data-x="45" data-y="34" aria-label="Pourquoi une pergola"></button>
<button type="button" class="pt" data-x="18" data-y="50" aria-label="Pourquoi une clôture"></button>
<button type="button" class="pt" data-x="81" data-y="80" aria-label="Pourquoi ces plantes"></button>
<div class="fiche" role="note"><b>11 h de soleil le 21 juin</b><div class="sol"><i style="background:#ef9447"></i><i style="background:#ed8b40"></i><i style="background:#ed893e"></i><i style="background:#ec873c"></i><i style="background:#ed893e"></i><i style="background:#ed8b40"></i><i style="background:#ee8d42"></i><i style="background:#ee8d42"></i><i style="background:#ee9043"></i><i style="background:#ed8b40"></i><i style="background:#ed893e"></i><i style="background:#ec873c"></i><i style="background:#ec873c"></i><i style="background:#ec853a"></i><i style="background:#ed893e"></i><i style="background:#ee8d42"></i><i style="background:#ee9043"></i><i style="background:#ee9245"></i><i style="background:#ef9447"></i><i style="background:#ef9447"></i><i style="background:#ef9649"></i><i style="background:#f09a4d"></i><i style="background:#f2a355"></i><i style="background:#f5af61"></i><i style="background:#f8bc6d"></i><i style="background:#fccf7e"></i></div><div class="heures"><span>8 h</span><span>21 h</span></div><p>Dont 6 h après 14 h : la pergola garde la table à l'ombre.</p><div class="prix">Pergola 3 x 3 m : <strong>1 100 à 1 400 €</strong></div></div>
<div class="fiche" role="note"><b>Un voisin voit le jardin depuis 5 m de haut</b><p>Côté ouest : la clôture occultante de 1,80 m coupe la vue.</p><div class="prix">Clôture, 12 m : <strong>1 400 à 1 700 €</strong></div></div>
<div class="fiche" role="note"><b>6 plantes choisies pour ce soleil</b><div class="mois"><i>J</i><i>F</i><i>M</i><i>A</i><i>M</i><i>J</i><i>J</i><i>A</i><i>S</i><i>O</i><i>N</i><i>D</i></div><p>Quelque chose en fleur chaque mois, pour un entretien minimal.</p><div class="prix">Toutes à planter en avril</div></div>
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
</div></div>''' + JS + JSBA
