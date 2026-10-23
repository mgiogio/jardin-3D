/* Questionnaire « Diagnostic jardin » Cover Green.
   S'affiche dans <div id="cg-diag" data-api="https://..." data-projet="/mon-projet-jardin/?projet="></div>.
   Principes : une question par écran, un toucher suffit, l'effort (photo, email) vient quand l'envie est là,
   les questions de connaissance client sont posées après l'envoi, pendant la préparation du diagnostic. */
(function () {
  'use strict';
  var R = document.getElementById('cg-diag');
  if (!R || R.dataset.pret) return;
  R.dataset.pret = '1';
  var API = (R.dataset.api || '').replace(/\/$/, '');
  var PROJET = R.dataset.projet || '/projet/';
  var CLE = 'cg_diag_v1';
  var VERT = '#049E00';

  /* ---------- styles ---------- */
  var css = '\
.cgq{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--orange-pale:#FDEBE0;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;\
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.5 var(--f);color:var(--txt);max-width:640px;margin:0 auto;padding:0 16px 40px;box-sizing:border-box}\
.cgq *,.cgq *:before,.cgq *:after{box-sizing:border-box}\
.cgq button,.cgq input{font-family:var(--f)}\
.cgq .haut{position:sticky;top:var(--cgq-haut,0px);z-index:5;background:#fff;padding:12px 0 10px;display:flex;align-items:center;gap:12px}\
.cgq .ret{appearance:none;background:none;border:0;padding:8px 4px;margin:0;font:500 15px var(--f);color:var(--txt);cursor:pointer;min-width:64px;text-align:left}\
.cgq .ret[hidden]{visibility:hidden;display:block}\
.cgq .barre{flex:1;height:6px;border-radius:3px;background:var(--gris);overflow:hidden}\
.cgq .barre i{display:block;height:100%;background:var(--vert);border-radius:3px;transition:width .5s ease}\
.cgq .reste{font-size:13px;color:var(--muted);min-width:72px;text-align:right;white-space:nowrap}\
.cgq .ecran{animation:cgqIn .28s ease both;padding-top:8px}\
@keyframes cgqIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}\
.cgq h2{font:800 26px/1.2 var(--f);margin:8px 0 8px;letter-spacing:-.01em;color:var(--txt)}\
.cgq .sous{color:var(--muted);margin:0 0 20px;font-size:16px}\
.cgq .cartes{display:grid;gap:10px}\
.cgq .c{appearance:none;display:flex;align-items:center;gap:14px;width:100%;min-height:68px;padding:12px 16px;background:#fff;border:1px solid var(--ligne);border-radius:12px;\
text-align:left;cursor:pointer;color:var(--txt);transition:border-color .15s,background-color .15s,transform .1s;font:inherit}\
@media (hover:hover){.cgq .c:hover{border-color:var(--vert)}}\
.cgq .c:active{transform:scale(.99)}\
.cgq .c:focus-visible{outline:3px solid var(--vert);outline-offset:2px}\
.cgq .c.on{border-color:var(--vert);background:var(--brume);box-shadow:inset 0 0 0 1px var(--vert)}\
.cgq .c .ic{flex:none;width:44px;height:44px;border-radius:10px;background:var(--brume);display:grid;place-items:center;color:var(--vert)}\
.cgq .c .ic svg{width:26px;height:26px}\
.cgq .c b{display:block;font-weight:700;font-size:17px;line-height:1.25}\
.cgq .c small{display:block;color:var(--muted);font-size:14px;line-height:1.35;margin-top:2px}\
.cgq .pal{flex:none;display:grid;grid-template-columns:1fr 1fr;width:44px;height:44px;border-radius:10px;overflow:hidden}\
.cgq .pal i{display:block}\
.cgq .cartes.mini{grid-template-columns:1fr 1fr}\
.cgq .c .rang{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--vert);color:#fff;font:800 16px/1 var(--f)}\
.cgq .multi .c.on .ic{background:#fff}\
.cgq .cartes.mini .c{min-height:56px;justify-content:center;text-align:center;padding:10px 12px}\
.cgq .cartes.mini .c b{font-size:16px;font-weight:500}\
.cgq .cta{appearance:none;display:flex;align-items:center;justify-content:center;width:100%;height:56px;padding:0 24px;border-radius:8px;border:1px solid var(--orange);\
font:600 17px/1 var(--f);cursor:pointer;background:var(--orange);color:#fff;text-decoration:none;transition:background-color .15s,border-color .15s}\
.cgq .cta:hover{background:var(--orange-survol);border-color:var(--orange-survol);color:#fff}\
.cgq .cta:focus-visible{outline:3px solid var(--vert);outline-offset:2px}\
.cgq .cta[disabled]{opacity:.45;cursor:not-allowed}\
.cgq .cta.sec{background:#fff;color:var(--txt);border-color:var(--txt)}\
.cgq .cta.sec:hover{background:var(--gris)}\
.cgq .lien{appearance:none;background:none;border:0;padding:12px 0;margin:4px auto 0;display:block;font:500 15px var(--f);color:var(--muted);text-decoration:underline;cursor:pointer}\
.cgq .pile{display:grid;gap:10px;margin-top:20px}\
.cgq label.ch{display:block;font-weight:500;font-size:15px;margin:14px 0 6px}\
.cgq input.t{width:100%;height:56px;border:1px solid #9AA29E;border-radius:8px;padding:0 16px;font:400 17px var(--f);color:var(--txt);background:#fff;-webkit-appearance:none}\
.cgq input.t:focus{outline:none;border-color:var(--vert);box-shadow:0 0 0 3px rgba(4,158,0,.18)}\
.cgq input.t.err{border-color:#C62828}\
.cgq .msg{font-size:14px;color:#C62828;margin:6px 0 0;min-height:0}\
.cgq .msg.ok{color:var(--txt)}\
.cgq .msg button{appearance:none;background:none;border:0;padding:0;font:700 14px var(--f);color:var(--vert);text-decoration:underline;cursor:pointer}\
.cgq .sug{list-style:none;margin:6px 0 0;padding:0;border:1px solid var(--ligne);border-radius:8px;overflow:hidden}\
.cgq .sug li button{appearance:none;display:block;width:100%;text-align:left;background:#fff;border:0;border-top:1px solid var(--ligne);padding:14px 16px;font:400 16px var(--f);color:var(--txt);cursor:pointer}\
.cgq .sug li:first-child button{border-top:0}\
.cgq .sug li button:hover,.cgq .sug li button:focus{background:var(--brume);outline:none}\
.cgq .sug small{color:var(--muted)}\
.cgq .geo{appearance:none;background:none;border:0;padding:12px 0 0;font:500 15px var(--f);color:var(--vert);cursor:pointer;text-decoration:underline}\
.cgq .carte{position:relative;border-radius:12px;overflow:hidden;background:var(--gris);aspect-ratio:4/3;margin:4px 0 14px}\
.cgq .carte img,.cgq .carte svg{position:absolute;inset:0;width:100%;height:100%;display:block}\
.cgq .carte.vise{cursor:crosshair}\
.cgq .carte .bulle{position:absolute;left:10px;bottom:10px;background:rgba(255,255,255,.94);border-radius:8px;padding:6px 10px;font-size:13px;font-weight:500}\
.cgq .chiffres{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 0 6px}\
.cgq .chiffres div{background:var(--brume);border-radius:10px;padding:12px 14px}\
.cgq .chiffres b{display:block;font-size:22px;font-weight:800;line-height:1.1}\
.cgq .chiffres span{font-size:14px;color:var(--muted)}\
.cgq .squelette{background:linear-gradient(90deg,var(--gris) 25%,#e9ecee 50%,var(--gris) 75%);background-size:200% 100%;animation:cgqS 1.2s infinite}\
@keyframes cgqS{to{background-position:-200% 0}}\
.cgq .zone{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;width:100%;min-height:190px;border:2px dashed #9AA29E;border-radius:12px;background:var(--gris);\
cursor:pointer;padding:20px;text-align:center;font:inherit;color:var(--txt)}\
@media (hover:hover){.cgq .zone:hover{border-color:var(--vert);background:var(--brume)}}\
.cgq .zone b{font-size:17px}\
.cgq .zone small{color:var(--muted);font-size:14px}\
.cgq .zone svg{width:40px;height:40px;color:var(--vert)}\
.cgq .apercu{position:relative;border-radius:12px;overflow:hidden;aspect-ratio:4/3;background:var(--gris)}\
.cgq .apercu img{width:100%;height:100%;object-fit:cover;display:block}\
.cgq .apercu button{position:absolute;right:10px;bottom:10px;appearance:none;border:0;border-radius:8px;background:rgba(255,255,255,.94);padding:10px 14px;font:500 14px var(--f);cursor:pointer;color:var(--txt)}\
.cgq .conseils{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:6px;font-size:15px;color:var(--muted)}\
.cgq .conseils li:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--vert);margin-right:10px;vertical-align:middle}\
.cgq .case{display:flex;gap:12px;align-items:flex-start;margin:16px 0 0;font-size:15px;cursor:pointer}\
.cgq .case input{flex:none;width:22px;height:22px;margin:1px 0 0;accent-color:var(--vert)}\
.cgq .mention{font-size:13px;color:var(--muted);margin:14px 0 0;line-height:1.45}\
.cgq .mention a{color:var(--muted)}\
.cgq .confiance{font-size:14px;color:var(--muted);text-align:center;margin:14px 0 0}\
.cgq .confiance b{color:var(--txt)}\
.cgq .etapes{list-style:none;padding:0;margin:18px 0 22px;display:grid;gap:12px}\
.cgq .etapes li{display:flex;align-items:center;gap:12px;color:var(--muted);transition:color .3s}\
.cgq .etapes li i{flex:none;width:24px;height:24px;border-radius:50%;border:2px solid var(--ligne);display:grid;place-items:center;transition:all .3s}\
.cgq .etapes li.en i{border-color:var(--vert);border-top-color:transparent;animation:cgqR .8s linear infinite}\
.cgq .etapes li.ok{color:var(--txt)}\
.cgq .etapes li.ok i{background:var(--vert);border-color:var(--vert)}\
.cgq .etapes li.ok i:after{content:"";width:6px;height:11px;border:solid #fff;border-width:0 2px 2px 0;transform:translateY(-1px) rotate(45deg)}\
@keyframes cgqR{to{transform:rotate(360deg)}}\
.cgq .bonus{margin-top:26px;border-top:1px solid var(--ligne);padding-top:22px}\
.cgq .bonus h3{font:700 19px/1.3 var(--f);margin:0 0 4px}\
.cgq .points{display:flex;gap:6px;margin:0 0 14px}\
.cgq .points i{width:22px;height:4px;border-radius:2px;background:var(--ligne)}\
.cgq .points i.on{background:var(--vert)}\
.cgq .qb{font-weight:500;margin:0 0 12px}\
.cgq .merci{background:var(--brume);border-radius:12px;padding:16px;margin-top:4px}\
.cgq .erreur{background:var(--orange-pale);border-radius:10px;padding:14px 16px;margin:0 0 14px;font-size:15px}\
@media (min-width:600px){.cgq h2{font-size:32px}.cgq .cartes.deux{grid-template-columns:1fr 1fr}.cgq .cartes.deux .c{min-height:84px}}\
@media (prefers-reduced-motion:reduce){.cgq .ecran{animation:none}.cgq .barre i{transition:none}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  /* ---------- petits outils ---------- */
  function h(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function lire() { try { return JSON.parse(localStorage.getItem(CLE) || 'null'); } catch (e) { return null; } }
  function garder() { try { var c = {}; for (var k in S) if (k !== 'photo' && k !== 'photoUrl') c[k] = S[k]; localStorage.setItem(CLE, JSON.stringify(c)); } catch (e) { } }
  function ev(nom, p) { try { window.dataLayer = window.dataLayer || []; var o = { event: nom }; for (var k in p) o[k] = p[k]; window.dataLayer.push(o); } catch (e) { } }
  function maintenant() { return Date.now(); }
  var ICO = {
    intimite: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 21V8M9 21V5M14 21V8M19 21V5M2 12h20M2 17h20"/></svg>',
    ombre: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 9h18M4 9l2-4h12l2 4M6 9v12M18 9v12M9 9v4M12 9v4M15 9v4"/></svg>',
    recevoir: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 12h16M6 12v8M18 12v8M8 8h8l1 4H7z"/><circle cx="12" cy="4" r="1.5"/></svg>',
    embellir: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7zM7 21h10"/></svg>',
    sol: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 16l9-5 9 5-9 5zM7.5 13.5l9 5M16.5 13.5l-9 5"/></svg>',
    photo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>'
  };
  var ENVIES = [
    ['intimite', 'Être tranquille chez moi', 'À l\'abri des regards des voisins'],
    ['ombre', 'Profiter de l\'ombre', 'Ne plus subir le soleil en été'],
    ['recevoir', 'Recevoir famille et amis', 'Un vrai coin pour se retrouver dehors'],
    ['embellir', 'Un jardin dont je suis fier', 'Embellir et mettre en valeur'],
    ['sol', 'Un sol propre et agréable', 'Fini la boue et la pelouse abîmée']
  ];
  var STYLES = [
    ['contemporain', 'Contemporain', 'Lignes droites, gris et blanc', ['#3A3F3C', '#D9D9D6', '#8A8F8C', '#F4F4F0']],
    ['naturel', 'Naturel', 'Bois, lin et graminées', ['#A0764B', '#D8C7A6', '#7D8F5A', '#EFE6D6']],
    ['mediterraneen', 'Méditerranéen', 'Pierre claire, oliviers, lavandes', ['#E9E1D1', '#C2693E', '#8C9A6B', '#9C8BC0']],
    ['champetre', 'Champêtre', 'Fleurs généreuses, bois brut', ['#B85C7A', '#6E8B3D', '#E4C46A', '#A3784E']]
  ];
  var ENTRETIEN = [
    ['peu', 'Le moins possible', 'Des plantes qui se débrouillent seules'],
    ['moyen', 'Un peu le week-end', 'Tailler une ou deux fois par an, ça me va'],
    ['passion', 'J\'adore jardiner', 'Plus il y a de fleurs, plus je suis content']
  ];
  var ETAPES = ['envie', 'adresse', 'terrain', 'style', 'entretien', 'photo', 'contact'];
  var AVANCE = { envie: 6, adresse: 22, terrain: 38, style: 52, entretien: 64, photo: 76, contact: 92 };
  var RESTE = { envie: 'Environ 1 min', adresse: 'Environ 1 min', terrain: 'Moins d\'1 min', style: 'Moins d\'1 min', entretien: '30 secondes', photo: '20 secondes', contact: 'Dernière étape' };

  /* ---------- état ---------- */
  var S = lire();
  if (!S || !S.v || (S.cree && maintenant() - S.cree > 7 * 864e5)) S = null;
  if (!S) S = { v: 1, cree: maintenant(), etape: 'envie', temps: {}, infos: {}, suivi: null };
  // provenance (premier contact) : sert à savoir quels canaux amènent des projets, sans rien demander au client
  if (!S.suivi) {
    var q = new URLSearchParams(location.search), sv = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid', 'msclkid'].forEach(function (k) { if (q.get(k)) sv[k] = q.get(k).slice(0, 120); });
    sv.referrer = (document.referrer || '').slice(0, 200); sv.page = (location.origin + location.pathname).slice(0, 200);
    S.suivi = sv;
  }
  var tEtape = maintenant();
  var M = document.createElement('div'); M.className = 'cgq'; R.innerHTML = ''; R.appendChild(M);

  /* ---------- calage sous l'en-tête collant du site ---------- */
  function caler() {
    var hd = document.querySelector('#cgh-main'), nav = document.querySelector('#cgh-nav'), y = 0;
    [hd, nav].forEach(function (el) {
      if (!el) return; var cs = getComputedStyle(el), r = el.getBoundingClientRect();
      if ((cs.position === 'fixed' || cs.position === 'sticky') && r.bottom > 0 && r.top < 5 && !el.classList.contains('cgh-hide')) y = Math.max(y, r.bottom);
    });
    M.style.setProperty('--cgq-haut', Math.round(y) + 'px');
  }
  window.addEventListener('scroll', caler, { passive: true }); window.addEventListener('resize', caler);

  /* ---------- navigation ---------- */
  function aller(etape, sansHistorique) {
    var dt = Math.round((maintenant() - tEtape) / 1000); S.temps[S.etape] = (S.temps[S.etape] || 0) + Math.min(dt, 1800); tEtape = maintenant();
    S.etape = etape; garder();
    if (!sansHistorique) try { history.pushState({ cgq: etape }, '', location.href); } catch (e) { }
    rendre();
    var top = R.getBoundingClientRect().top + window.scrollY - 90;
    if (window.scrollY > top) window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    if (AVANCE[etape]) ev('cgp_q_etape', { etape: etape, numero: ETAPES.indexOf(etape) + 1 });
  }
  function precedente() {
    var i = ETAPES.indexOf(S.etape);
    if (S.etape === 'style' && !S.terrain) return 'adresse';
    return i > 0 ? ETAPES[i - 1] : null;
  }
  window.addEventListener('popstate', function (e) {
    var et = e.state && e.state.cgq;
    if (S.id) return;                         // déjà envoyé : on reste sur l'écran d'attente
    if (et && ETAPES.indexOf(et) >= 0) aller(et, true);
    else if (S.etape !== 'envie') aller(precedente() || 'envie', true);
  });

  function entete() {
    var p = AVANCE[S.etape] || 100, prev = precedente();
    return '<div class="haut"><button type="button" class="ret" data-a="retour"' + (prev ? '' : ' hidden') + '>Retour</button>'
      + '<div class="barre" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + p + '"><i style="width:' + p + '%"></i></div>'
      + '<span class="reste">' + (RESTE[S.etape] || '') + '</span></div>';
  }
  function cartes(liste, choisi, cls) {
    return '<div class="cartes ' + (cls || '') + '">' + liste.map(function (o) {
      return '<button type="button" class="c' + (choisi === o[0] ? ' on' : '') + '" data-v="' + o[0] + '">'
        + (o[3] ? '<span class="pal" aria-hidden="true">' + o[3].map(function (c) { return '<i style="background:' + c + '"></i>'; }).join('') + '</span>' : (ICO[o[0]] ? '<span class="ic" aria-hidden="true">' + ICO[o[0]] + '</span>' : ''))
        + '<span><b>' + h(o[1]) + '</b>' + (o[2] ? '<small>' + h(o[2]) + '</small>' : '') + '</span></button>';
    }).join('') + '</div>';
  }

  /* ---------- écrans ---------- */
  var E = {};
  E.envie = function () {
    var L = S.envies || [];
    return '<h2>Qu\'est-ce qui vous ferait plaisir dans votre jardin ?</h2><p class="sous">Choisissez-en une ou plusieurs, la plus importante en premier.</p>'
      + '<div class="cartes deux multi">' + ENVIES.map(function (o) {
        var k = L.indexOf(o[0]);
        return '<button type="button" class="c' + (k >= 0 ? ' on' : '') + '" data-envie="' + o[0] + '" aria-pressed="' + (k >= 0) + '">'
          + '<span class="ic" aria-hidden="true">' + (k >= 0 ? '<span class="rang">' + (k + 1) + '</span>' : ICO[o[0]]) + '</span>'
          + '<span><b>' + h(o[1]) + '</b><small>' + h(o[2]) + '</small></span></button>';
      }).join('') + '</div>'
      + '<div class="pile"><button type="button" class="cta" data-a="envie-ok"' + (L.length ? '' : ' disabled') + '>' + (L.length > 1 ? 'Continuer avec ces ' + L.length + ' envies' : 'Continuer') + '</button></div>';
  };
  E.style = function () { return '<h2>Quel style vous ressemble ?</h2><p class="sous">Nous habillerons votre idée d\'aménagement dans ce style.</p>' + cartes(STYLES, S.style, 'deux'); };
  E.entretien = function () { return '<h2>Et côté entretien des plantes ?</h2><p class="sous">Nous choisirons des plantes adaptées à votre climat et à votre temps.</p>' + cartes(ENTRETIEN, S.entretien); };
  E.adresse = function () {
    return '<h2>Où se trouve ce jardin ?</h2><p class="sous">Avec l\'adresse, nous calculons le soleil de chaque coin du jardin et les vues des voisins.</p>'
      + '<label class="ch" for="cgq-adr">Adresse</label><input id="cgq-adr" class="t" type="text" autocomplete="street-address" placeholder="Ex. 12 rue des Lilas, Nantes" value="' + h(S.adresse ? S.adresse.label : '') + '" aria-autocomplete="list" aria-controls="cgq-sug">'
      + '<ul class="sug" id="cgq-sug" role="listbox" hidden></ul><p class="msg" id="cgq-amsg" role="status"></p>'
      + ('geolocation' in navigator ? '<button type="button" class="geo" data-a="geo">Je suis dans le jardin : utiliser ma position</button>' : '')
      + (S.adresse ? '<div class="pile"><button type="button" class="cta" data-a="adresse-ok">Continuer</button></div>' : '');
  };
  E.terrain = function () {
    return '<h2>C\'est bien votre maison ?</h2><p class="sous" id="cgq-tsous">Nous cherchons votre terrain sur le cadastre…</p>'
      + '<div class="carte squelette" id="cgq-carte"></div><div id="cgq-tinfo"></div>'
      + '<div class="pile" id="cgq-tact" hidden><button type="button" class="cta" data-a="terrain-ok">Oui, c\'est bien ça</button>'
      + '<button type="button" class="cta sec" data-a="terrain-viser">Non, je la montre sur la photo</button></div>';
  };
  E.photo = function () {
    var a = S.photoUrl;
    return '<h2>Une photo de votre jardin</h2><p class="sous">Nous y placerons nos produits pour vous montrer le résultat chez vous.</p>'
      + (a ? '<div class="apercu"><img src="' + a + '" alt="Votre photo"><button type="button" data-a="photo-choisir">Changer</button></div>'
        : '<button type="button" class="zone" data-a="photo-choisir">' + ICO.photo + '<b>Prendre ou choisir une photo</b><small>Depuis votre téléphone ou votre ordinateur</small></button>'
        + '<ul class="conseils"><li>Prise depuis la maison ou la terrasse</li><li>De jour, téléphone à l\'horizontale</li><li>Le plus de jardin possible dans le cadre</li></ul>')
      + '<input type="file" id="cgq-f" accept="image/*" hidden><p class="msg" id="cgq-pmsg" role="status"></p>'
      + '<div class="pile">' + (a ? '<button type="button" class="cta" data-a="photo-ok">Continuer</button>' : '')
      + '<button type="button" class="lien" data-a="photo-sans">Je n\'ai pas de photo sous la main</button></div>';
  };
  E.contact = function () {
    return '<h2>Où vous envoyer votre diagnostic ?</h2><p class="sous">' + (S.photo || S.photoUrl ? 'Votre page projet arrive par email dans 2 à 3 minutes.' : 'Votre page projet arrive par email dans 2 minutes. Vous pourrez y ajouter une photo.') + '</p>'
      + '<form id="cgq-form" novalidate><label class="ch" for="cgq-mail">Votre email</label><input id="cgq-mail" class="t" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" value="' + h(S.email) + '" required><p class="msg" id="cgq-mmsg" role="status"></p>'
      + '<label class="case"><input type="checkbox" id="cgq-opt"' + (S.optin ? ' checked' : '') + '><span>Recevoir aussi nos idées et offres jardin, 2 emails par mois au plus</span></label>'
      + '<div class="pile"><button type="submit" class="cta">Recevoir mon diagnostic</button></div></form>'
      + '<p class="confiance"><b>Gratuit et sans engagement</b> · ★ 4,6/5 sur Trustpilot, plus de 300 avis</p>'
      + '<p class="mention">Vos réponses servent uniquement à préparer votre diagnostic et à vous l\'envoyer. Elles ne sont jamais revendues. Voir notre <a href="https://www.cover.green/politique-de-confidentialite/" target="_blank" rel="noopener">politique de confidentialité</a>.</p>';
  };
  E.attente = function () {
    var pret = S.statut === 'pret';
    return '<div class="ecran"><h2>' + (pret ? 'Votre diagnostic est prêt' : (S.prenom ? 'C\'est parti, ' + h(S.prenom) + ' !' : 'C\'est parti !')) + '</h2>'
      + '<p class="sous">' + (pret ? 'Retrouvez-le aussi dans l\'email envoyé à ' + h(S.email) + '.' : 'Nous préparons votre diagnostic. Il arrive par email à <b>' + h(S.email) + '</b> dans 2 à 3 minutes, vous pouvez aussi rester ici.') + '</p>'
      + (S.erreur ? '<div class="erreur">' + h(S.erreur) + '</div><div class="pile"><button type="button" class="cta" data-a="renvoyer">Réessayer</button><button type="button" class="lien" data-a="modifier">Modifier mes réponses</button></div>' : '')
      + (!S.erreur ? '<ul class="etapes" id="cgq-et">' + ['Le soleil de votre jardin, heure par heure', 'Les vis-à-vis des maisons voisines', 'Les plantes adaptées à votre climat', S.avecPhoto ? 'Votre idée d\'aménagement avec nos produits' : 'Les produits adaptés à votre envie'].map(function (t) { return '<li><i></i><span>' + t + '</span></li>'; }).join('') + '</ul>' : '')
      + '<div id="cgq-voir">' + (pret ? '<a class="cta" href="' + h(lienProjet()) + '" data-a="voir">Voir mon projet jardin</a>' : '') + '</div>'
      + '<div class="bonus" id="cgq-bonus"></div>'
      + '<button type="button" class="lien" data-a="nouveau">Faire le diagnostic d\'un autre jardin</button></div>';
  };

  function rendre() {
    if (S.id || S.envoi) { M.innerHTML = E.attente(); attente(); bonus(); return; }
    M.innerHTML = entete() + '<div class="ecran">' + E[S.etape]() + '</div>';
    caler();
    if (S.etape === 'adresse') adresse();
    if (S.etape === 'terrain') terrain();
    if (S.etape === 'contact') contact();
    if (S.etape === 'photo') photo();
  }

  /* ---------- clics ---------- */
  M.addEventListener('click', function (e) {
    var b = e.target.closest('button,a'); if (!b || !M.contains(b)) return;
    var a = b.getAttribute('data-a'), v = b.getAttribute('data-v');
    if (a === 'retour') { var p = precedente(); if (p) aller(p); return; }
    if (v && ['envie', 'style', 'entretien'].indexOf(S.etape) >= 0 && !S.id && !S.envoi) {
      S[S.etape] = v; b.classList.add('on');
      [].forEach.call(b.parentNode.children, function (x) { if (x !== b) x.classList.remove('on'); });
      var suite = { envie: 'adresse', style: 'entretien', entretien: 'photo' }[S.etape];
      setTimeout(function () { aller(suite); }, 180);     // un toucher suffit : on passe tout seul à la suite
      return;
    }
    var en = b.getAttribute('data-envie');
    if (en && S.etape === 'envie') {
      S.envies = S.envies || []; var k = S.envies.indexOf(en);
      if (k >= 0) S.envies.splice(k, 1); else S.envies.push(en);
      S.envie = S.envies[0] || null; garder(); rendre(); return;
    }
    if (a === 'envie-ok') { if (!(S.envies || []).length) return; ev('cgp_q_envies', { envie: S.envies.join(','), nombre: S.envies.length }); return aller('adresse'); }
    if (a === 'geo') return geolocaliser(b);
    if (a === 'adresse-ok') return aller('terrain');
    if (a === 'terrain-ok') return aller('style');
    if (a === 'terrain-viser') return viser();
    if (a === 'terrain-continuer') return aller('style');
    if (a === 'photo-choisir') { var f = M.querySelector('#cgq-f'); if (f) f.click(); return; }
    if (a === 'photo-ok') return aller('contact');
    if (a === 'photo-sans') { S.photo = null; S.photoUrl = null; S.sansPhoto = true; ev('cgp_q_sans_photo', {}); return aller('contact'); }
    if (a === 'modifier') { S.envoi = false; S.erreur = null; return aller('contact'); }
    if (a === 'renvoyer') { S.erreur = null; return envoyer(); }
    if (a === 'nouveau') { try { localStorage.removeItem(CLE); } catch (x) { } S = { v: 1, cree: maintenant(), etape: 'envie', temps: {}, infos: {}, suivi: S.suivi }; tEtape = maintenant(); rendre(); return; }
    if (a === 'voir') ev('cgp_q_voir', { projet_jardin: S.id });
    if (a === 'info') return repondre(b.getAttribute('data-q'), v);
    if (a === 'info-passer') return repondre(b.getAttribute('data-q'), null);
    if (a === 'rappel') return rappel(b);
  });

  /* ---------- adresse ---------- */
  var minuteur, ctrl;
  function adresse() {
    var I = M.querySelector('#cgq-adr'), L = M.querySelector('#cgq-sug'), msg = M.querySelector('#cgq-amsg'), res = [];
    if (!S.adresse) setTimeout(function () { try { I.focus({ preventScroll: true }); } catch (e) { } }, 250);
    function afficher(liste) {
      res = liste;
      if (!liste.length) { L.hidden = true; return; }
      L.innerHTML = liste.map(function (a, i) { return '<li role="option"><button type="button" data-i="' + i + '">' + h(a.name) + ' <small>' + h(a.postcode + ' ' + a.city) + '</small></button></li>'; }).join('');
      L.hidden = false;
    }
    I.addEventListener('input', function () {
      clearTimeout(minuteur); msg.textContent = ''; var t = I.value.trim(); var ok = M.querySelector('[data-a=adresse-ok]'); if (ok && S.adresse && t !== S.adresse.label) ok.parentNode.remove();
      if (t.length < 4) { L.hidden = true; return; }
      minuteur = setTimeout(function () {
        if (ctrl) ctrl.abort(); ctrl = window.AbortController ? new AbortController() : null;
        geocoder(t, ctrl && ctrl.signal).then(afficher).catch(function (e) { if (e.name !== 'AbortError') msg.textContent = 'La recherche d\'adresse ne répond pas, réessayez dans un instant.'; });
      }, 220);
    });
    I.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); if (res[0]) choisir(res[0]); else if (S.adresse && I.value.trim() === S.adresse.label) aller('terrain'); }
      if (e.key === 'ArrowDown' && !L.hidden) { e.preventDefault(); var b = L.querySelector('button'); if (b) b.focus(); }
    });
    L.addEventListener('click', function (e) { var b = e.target.closest('button[data-i]'); if (b) choisir(res[+b.getAttribute('data-i')]); });
    L.addEventListener('keydown', function (e) {
      var b = document.activeElement; if (!b || !b.closest('li')) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); var n = b.closest('li').nextElementSibling; if (n) n.querySelector('button').focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); var p = b.closest('li').previousElementSibling; (p ? p.querySelector('button') : I).focus(); }
    });
  }
  function versAdresse(f) {
    var p = f.properties || {}, c = f.geometry.coordinates;
    return { label: p.label, name: p.name || p.label, city: p.city, postcode: p.postcode || '', citycode: p.citycode, lat: c[1], lon: c[0], score: p.score, type: p.type };
  }
  function geocoder(t, signal) {
    var q = encodeURIComponent(t);
    var urls = ['https://data.geopf.fr/geocodage/search?q=' + q + '&limit=5&index=address&autocomplete=1', 'https://api-adresse.data.gouv.fr/search/?q=' + q + '&limit=5&autocomplete=1'];
    function essai(i) {
      if (i >= urls.length) return Promise.reject(new Error('indisponible'));
      return fetch(urls[i], { signal: signal }).then(function (r) { if (!r.ok) throw new Error('http'); return r.json(); })
        .then(function (d) { return (d.features || []).map(versAdresse); })
        .catch(function (e) { if (e.name === 'AbortError') throw e; return essai(i + 1); });
    }
    return essai(0);
  }
  function choisir(a) {
    if (!a) return;
    S.adresse = { label: a.label, city: a.city, postcode: a.postcode, citycode: a.citycode, lat: a.lat, lon: a.lon, score: a.score };
    S.terrain = null; S.corrections = 0;
    ev('cgp_q_adresse', { type: a.type || '' });
    aller('terrain');
  }
  function geolocaliser(b) {
    var msg = M.querySelector('#cgq-amsg'); b.textContent = 'Localisation en cours…';
    navigator.geolocation.getCurrentPosition(function (p) {
      var la = p.coords.latitude, lo = p.coords.longitude;
      fetch('https://data.geopf.fr/geocodage/reverse?lat=' + la + '&lon=' + lo + '&limit=1&index=address').then(function (r) { return r.json(); })
        .then(function (d) {
          var f = (d.features || [])[0]; if (!f) throw new Error('aucune');
          var a = versAdresse(f); a.lat = la; a.lon = lo; ev('cgp_q_geoloc', {}); choisir(a);
        }).catch(function () { msg.textContent = 'Nous n\'avons pas trouvé votre adresse, tapez-la simplement.'; b.textContent = 'Je suis dans le jardin : utiliser ma position'; });
    }, function () { msg.textContent = 'Position indisponible, tapez simplement votre adresse.'; b.textContent = 'Je suis dans le jardin : utiliser ma position'; }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  }

  /* ---------- terrain : « c'est bien chez vous ? » ---------- */
  var vue = null;   // cadrage de la photo aérienne : { lat0, lon0, kx, ky, w, h }
  function terrain() {
    if (S.terrain) return dessiner();
    chercherTerrain(S.adresse.lat, S.adresse.lon);
  }
  function chercherTerrain(lat, lon) {
    var sous = M.querySelector('#cgq-tsous');
    fetch(API + '/api/terrain?lat=' + lat + '&lon=' + lon).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (t) { S.terrain = t; S.adresse.lat = lat; S.adresse.lon = lon; garder(); dessiner(); })
      .catch(function () {
        S.terrain = null;
        if (sous) sous.textContent = 'Nous n\'avons pas trouvé le plan de ce terrain. Ce n\'est pas grave : nous continuerons avec votre photo.';
        var c = M.querySelector('#cgq-carte'); if (c) c.remove();
        var act = M.querySelector('#cgq-tact'); if (act) { act.hidden = false; act.innerHTML = '<button type="button" class="cta" data-a="terrain-continuer">Continuer</button>'; }
        ev('cgp_q_terrain', { trouve: 'non' });
      });
  }
  function dessiner() {
    var t = S.terrain, c = M.querySelector('#cgq-carte'); if (!c || !t) return;
    var pts = [].concat(t.parcel ? t.parcel.ring : [], t.building ? t.building.ring : []);
    var lat0 = S.adresse.lat, lon0 = S.adresse.lon, kx = 111320 * Math.cos(lat0 * Math.PI / 180), ky = 110540;
    var xs = pts.map(function (p) { return (p[0] - lon0) * kx; }), ys = pts.map(function (p) { return (p[1] - lat0) * ky; });
    var x0 = Math.min.apply(0, xs), x1 = Math.max.apply(0, xs), y0 = Math.min.apply(0, ys), y1 = Math.max.apply(0, ys);
    var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, w = Math.max(x1 - x0, (y1 - y0) * 4 / 3, 40) * 1.35, hh = w * 3 / 4;
    vue = { lat0: lat0, lon0: lon0, kx: kx, ky: ky, x0: cx - w / 2, y0: cy - hh / 2, w: w, h: hh };
    var la1 = lat0 + vue.y0 / ky, la2 = lat0 + (vue.y0 + hh) / ky, lo1 = lon0 + vue.x0 / kx, lo2 = lon0 + (vue.x0 + w) / kx;
    var img = 'https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS&STYLES=&CRS=EPSG:4326&FORMAT=image/jpeg'
      + '&WIDTH=960&HEIGHT=720&BBOX=' + [la1, lo1, la2, lo2].map(function (n) { return n.toFixed(7); }).join(',');
    function P(r) { return r.map(function (p) { return (((p[0] - lon0) * kx - vue.x0) / w * 960).toFixed(1) + ',' + ((1 - ((p[1] - lat0) * ky - vue.y0) / hh) * 720).toFixed(1); }).join(' '); }
    c.className = 'carte';
    c.innerHTML = '<img alt="Vue aérienne de votre terrain" src="' + img + '">'
      + '<svg viewBox="0 0 960 720" aria-hidden="true">' + (t.parcel ? '<polygon points="' + P(t.parcel.ring) + '" fill="rgba(4,158,0,.16)" stroke="#fff" stroke-width="7" stroke-linejoin="round"/><polygon points="' + P(t.parcel.ring) + '" fill="none" stroke="' + VERT + '" stroke-width="4" stroke-linejoin="round"/>' : '')
      + (t.building ? '<polygon points="' + P(t.building.ring) + '" fill="rgba(235,90,0,.35)" stroke="#EB5A00" stroke-width="4" stroke-linejoin="round"/>' : '')
      + '<g transform="translate(912,52)"><circle r="26" fill="rgba(255,255,255,.92)"/><path d="M0-16 L8 10 L0 5 L-8 10z" fill="#1E211F"/></g></svg>'
      + '<span class="bulle">' + (t.building ? 'En orange : votre maison' : 'En vert : votre terrain') + '</span>';
    var a = t.apercu || {}, sous = M.querySelector('#cgq-tsous'), info = M.querySelector('#cgq-tinfo');
    if (sous) sous.textContent = 'Nous avons trouvé votre terrain sur le cadastre.';
    if (info) info.innerHTML = a.parcelle_m2 ? '<div class="chiffres"><div><b>' + a.parcelle_m2 + ' m²</b><span>de terrain</span></div><div><b>' + (a.jardin_m2 || '?') + ' m²</b><span>de jardin' + (a.jardin_cote ? ', surtout côté ' + h(a.jardin_cote) : '') + '</span></div></div>' : '';
    var act = M.querySelector('#cgq-tact'); if (act) act.hidden = false;
    ev('cgp_q_terrain', { trouve: 'oui' });
  }
  function viser() {
    var c = M.querySelector('#cgq-carte'), sous = M.querySelector('#cgq-tsous'), act = M.querySelector('#cgq-tact');
    if (!c || !vue) return;
    c.classList.add('vise'); if (sous) sous.innerHTML = '<b>Touchez votre maison sur la photo.</b>';
    var bl = c.querySelector('.bulle'); if (bl) bl.textContent = 'Touchez votre maison';
    if (act) act.hidden = true;
    c.scrollIntoView({ behavior: 'smooth', block: 'center' });
    c.onclick = function (e) {
      var r = c.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      var x = vue.x0 + fx * vue.w, y = vue.y0 + (1 - fy) * vue.h;
      var lat = vue.lat0 + y / vue.ky, lon = vue.lon0 + x / vue.kx;
      c.onclick = null; c.className = 'carte squelette'; c.innerHTML = '';
      S.terrain = null; S.corrections = (S.corrections || 0) + 1;
      ev('cgp_q_correction', {});
      chercherTerrain(lat, lon);
    };
  }

  /* ---------- photo ---------- */
  function photo() {
    var f = M.querySelector('#cgq-f'), msg = M.querySelector('#cgq-pmsg');
    f.addEventListener('change', function () {
      var file = f.files && f.files[0]; if (!file) return;
      msg.className = 'msg ok'; msg.textContent = 'Préparation de la photo…';
      compresser(file).then(function (blob) {
        S.photo = blob; S.sansPhoto = false;
        try { if (S.photoUrl) URL.revokeObjectURL(S.photoUrl); S.photoUrl = URL.createObjectURL(blob); } catch (e) { S.photoUrl = null; }
        ev('cgp_q_photo', { taille_ko: Math.round(blob.size / 1024) });
        if (!S.photoUrl) return aller('contact');
        rendre();
      });
    });
  }
  // photo réduite dans le navigateur (envoi rapide même en 4G), orientation respectée ; à défaut, le fichier d'origine
  function compresser(file) {
    if (!window.createImageBitmap || !window.HTMLCanvasElement) return Promise.resolve(file);
    return createImageBitmap(file, { imageOrientation: 'from-image' }).then(function (bmp) {
      var k = Math.min(1, 1800 / Math.max(bmp.width, bmp.height)), cv = document.createElement('canvas');
      cv.width = Math.round(bmp.width * k); cv.height = Math.round(bmp.height * k);
      cv.getContext('2d').drawImage(bmp, 0, 0, cv.width, cv.height);
      return new Promise(function (ok) { cv.toBlob(function (b) { ok(b && b.size > 20000 ? b : file); }, 'image/jpeg', 0.86); });
    }).catch(function () { return file; });
  }

  /* ---------- contact ---------- */
  var DOM = ['gmail.com', 'hotmail.fr', 'hotmail.com', 'yahoo.fr', 'yahoo.com', 'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr', 'laposte.net', 'outlook.fr', 'outlook.com', 'icloud.com', 'live.fr', 'bbox.fr', 'neuf.fr', 'aol.com', 'gmx.fr', 'me.com'];
  function dist(a, b) {
    var d = []; for (var i = 0; i <= a.length; i++) { d[i] = [i]; } for (var j = 0; j <= b.length; j++) d[0][j] = j;
    for (i = 1; i <= a.length; i++) for (j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[a.length][b.length];
  }
  function suggestion(m) {
    var p = m.split('@'); if (p.length !== 2 || !p[1]) return null; var dm = p[1].toLowerCase();
    if (DOM.indexOf(dm) >= 0) return null;
    var best = null, bd = 3; DOM.forEach(function (x) { var k = dist(dm, x); if (k < bd) { bd = k; best = x; } });
    if (!best && /^gmail\./.test(dm)) best = 'gmail.com';
    return best ? p[0] + '@' + best : null;
  }
  function contact() {
    var F = M.querySelector('#cgq-form'), mail = M.querySelector('#cgq-mail'), msg = M.querySelector('#cgq-mmsg'), opt = M.querySelector('#cgq-opt');
    setTimeout(function () { try { mail.focus({ preventScroll: true }); } catch (e) { } }, 250);
    function verifier(final) {
      var v = mail.value.trim(), ok = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v), sg = ok && suggestion(v);
      mail.classList.toggle('err', final && !ok);
      msg.className = 'msg' + (sg ? ' ok' : '');
      msg.innerHTML = sg ? 'Vous vouliez dire <button type="button" id="cgq-corr">' + h(sg) + '</button> ?' : (final && !ok ? 'Vérifiez votre email : il nous servira à vous envoyer le diagnostic.' : '');
      var b = M.querySelector('#cgq-corr'); if (b) b.onclick = function () { mail.value = sg; msg.innerHTML = ''; S.email = sg; garder(); };
      return ok;
    }
    mail.addEventListener('blur', function () { if (mail.value.trim()) verifier(false); });
    mail.addEventListener('input', function () { S.email = mail.value.trim(); mail.classList.remove('err'); garder(); });
    opt.addEventListener('change', function () { S.optin = opt.checked; garder(); });
    F.addEventListener('submit', function (e) {
      e.preventDefault();
      S.email = mail.value.trim().slice(0, 120); S.optin = opt.checked;
      if (!verifier(true)) { mail.focus(); return; }
      envoyer();
    });
  }

  /* ---------- envoi ---------- */
  function gaClient() { var m = document.cookie.match(/_ga=GA\d\.\d\.(\d+\.\d+)/); return m ? m[1] : ''; }
  function envoyer() {
    var dt = Math.round((maintenant() - tEtape) / 1000); S.temps[S.etape] = (S.temps[S.etape] || 0) + dt; tEtape = maintenant();
    S.envoi = true; S.avecPhoto = !!S.photo; S.erreur = null; garder(); rendre();
    var T = S.terrain || {};
    var projet = {
      version: 2, createdAt: new Date().toISOString(), source: 'questionnaire',
      address: S.adresse, parcel: T.parcel || null, building: T.building || null, facades: T.facades || [],
      project: { need: S.envie, needs: S.envies || [S.envie] }, needs: { style: S.style || 'contemporain', upkeep: S.entretien || 'peu' },
      contact: { firstName: S.prenom || '', email: S.email, optin: !!S.optin, consent: true },
      suivi: Object.assign({}, S.suivi, {
        temps_s: S.temps, corrections_adresse: S.corrections || 0, terrain_trouve: !!S.terrain, sans_photo: !S.photo,
        appareil: (window.matchMedia && matchMedia('(pointer:coarse)').matches) ? 'mobile' : 'ordinateur', largeur: window.innerWidth, ga_client: gaClient()
      })
    };
    var fd = new FormData();
    fd.append('projet', JSON.stringify(projet)); fd.append('prenom', S.prenom || ''); fd.append('email', S.email);
    if (S.photo) fd.append('photo', S.photo, 'jardin.jpg');
    fetch(API + '/api/diagnostic', { method: 'POST', body: fd }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error(j.detail || 'Envoi impossible pour le moment.'); return j; });
    }).then(function (j) {
      S.id = j.id; S.statut = 'en_cours'; garder();
      ev('cgp_q_envoi', { projet_jardin: j.id, envie: (S.envies || [S.envie]).join(','), style: S.style, photo: S.photo ? 'oui' : 'non' });
      rendre();
    }).catch(function (e) {
      S.erreur = (e && e.message && !/fetch|network|Load failed/i.test(e.message)) ? e.message : 'La connexion a été interrompue. Vos réponses sont gardées, réessayez.';
      ev('cgp_q_erreur', { message: String(S.erreur).slice(0, 80) }); rendre();
    });
  }
  function lienProjet() { return PROJET + encodeURIComponent(S.id || ''); }

  /* ---------- attente : étapes qui avancent, puis lien vers le projet ---------- */
  var sondage;
  function attente() {
    var li = M.querySelectorAll('#cgq-et li'); if (!li.length) return;
    if (S.statut === 'pret') { [].forEach.call(li, function (x) { x.className = 'ok'; }); return; }
    var debut = S.debutAttente || (S.debutAttente = maintenant()), paliers = [6, 14, 22];
    function maj() {
      var s = (maintenant() - debut) / 1000, n = paliers.filter(function (p) { return s > p; }).length;
      [].forEach.call(li, function (x, i) { x.className = i < n ? 'ok' : (i === n ? 'en' : ''); });
    }
    maj(); var tick = setInterval(function () { if (!M.querySelector('#cgq-et')) return clearInterval(tick); maj(); }, 1000);
    if (!S.id) return;
    clearTimeout(sondage);
    (function sonder() {
      fetch(API + '/api/diagnostic/' + encodeURIComponent(S.id)).then(function (r) { return r.json(); }).then(function (j) {
        if (j.statut === 'pret' || j.statut === 'erreur') {
          S.statut = 'pret'; garder(); clearInterval(tick);
          [].forEach.call(M.querySelectorAll('#cgq-et li'), function (x) { x.className = 'ok'; });
          var h2 = M.querySelector('.ecran h2'); if (h2) h2.textContent = 'Votre diagnostic est prêt';
          var so = M.querySelector('.ecran .sous'); if (so) so.textContent = 'Retrouvez-le aussi dans l\'email envoyé à ' + S.email + '.';
          var v = M.querySelector('#cgq-voir'); if (v) v.innerHTML = '<a class="cta" href="' + h(lienProjet()) + '" data-a="voir">Voir mon projet jardin</a>';
          ev('cgp_q_pret', { projet_jardin: S.id });
        } else sondage = setTimeout(sonder, 5000);
      }).catch(function () { sondage = setTimeout(sonder, 8000); });
    })();
  }

  /* ---------- questions bonus (facultatives, une par une, après l'envoi) ---------- */
  function questions() {
    var m = new Date().getMonth() + 1;
    var saison = m <= 4 ? 'Avant l\'été' : m <= 7 ? 'Dès cet été' : m <= 9 ? 'Avant l\'hiver' : 'Pour le printemps';
    var Q = [
      ['delai', 'Quand aimeriez-vous en profiter ?', [['saison', saison], ['3mois', 'Dans les 3 mois'], ['annee', 'Dans l\'année'], ['reve', 'Je me renseigne']]],
      ['pose', 'Qui fera le montage ?', [['moi', 'Moi-même'], ['proche', 'Avec un proche'], ['poseur', 'Je cherche un poseur'], ['nsp', 'Je ne sais pas encore']]],
      ['budget', 'Quelle enveloppe pour l\'ensemble du projet ?', [['moins3', 'Moins de 3 000 €'], ['3a6', '3 000 à 6 000 €'], ['6a12', '6 000 à 12 000 €'], ['plus12', 'Plus de 12 000 €'], ['nsp', 'Je ne sais pas']]],
      ['frein', 'Qu\'est-ce qui vous a retenu jusqu\'ici ?', [['budget', 'Le budget'], ['montage', 'Le montage'], ['choix', 'Choisir les bons produits'], ['temps', 'Le temps'], ['rien', 'Rien, je me lance']]],
      ['statut', 'Vous êtes…', [['proprietaire', 'Propriétaire'], ['achat', 'En train d\'acheter'], ['locataire', 'Locataire']]]
    ];
    var sv = S.suivi || {};
    if (!(sv.utm_source || sv.gclid || sv.fbclid || sv.msclkid)) Q.push(['source', 'Comment nous avez-vous connus ?', [['google', 'Google'], ['social', 'Instagram ou Facebook'], ['pinterest', 'Pinterest'], ['bouche', 'Bouche-à-oreille'], ['client', 'Déjà client'], ['autre', 'Autre']]]);
    return Q;
  }
  function bonus() {
    var B = M.querySelector('#cgq-bonus'); if (!B || S.erreur) { if (B) B.remove(); return; }
    if (!S.id) { B.innerHTML = ''; return; }
    if (!('prenom' in S.infos)) {
      // le prénom n'est plus demandé avant l'envoi : on le demande ici, pendant l'attente, pour personnaliser l'email et la page
      B.innerHTML = '<h3>Comment vous appelle-t-on ?</h3><p class="sous" style="margin-bottom:12px">Pour personnaliser votre diagnostic et l\'email qui l\'accompagne.</p>'
        + '<form id="cgq-fp" novalidate><label class="ch" for="cgq-pre">Prénom</label><input id="cgq-pre" class="t" type="text" autocomplete="given-name" autocapitalize="words" enterkeyhint="done">'
        + '<div class="pile"><button type="submit" class="cta sec">Valider</button><button type="button" class="lien" data-a="info-passer" data-q="prenom">Passer</button></div></form>';
      B.querySelector('#cgq-fp').onsubmit = function (e) {
        e.preventDefault(); var I = B.querySelector('#cgq-pre'), v = I.value.trim().slice(0, 60);
        if (!v) { I.classList.add('err'); I.focus(); return; }
        S.prenom = v; S.infos.prenom = v; garder(); poster({ prenom: v }); ev('cgp_q_info', { question: 'prenom', reponse: 'oui' });
        var t = M.querySelector('.ecran h2'); if (t && S.statut !== 'pret') t.textContent = 'C\'est parti, ' + v + ' !';
        bonus();
      };
      return;
    }
    var Q = questions(), i = Q.findIndex(function (q) { return !(q[0] in S.infos); });
    if (i < 0) {
      if (S.infos.telephone || ('rappelFait' in S.infos)) { B.innerHTML = '<div class="merci"><b>Merci' + (S.prenom ? ' ' + h(S.prenom) : '') + ', c\'est noté.</b><br>Vos réponses nous aident à vous conseiller au plus juste.</div>'; return; }
      B.innerHTML = '<h3>Un conseil gratuit par téléphone ?</h3><p class="sous" style="margin-bottom:12px">Un conseiller Cover Green vous rappelle pour affiner votre projet, sans engagement.</p>'
        + '<label class="ch" for="cgq-tel">Téléphone</label><input id="cgq-tel" class="t" type="tel" inputmode="tel" autocomplete="tel" placeholder="06 12 34 56 78">'
        + '<p class="qb" style="margin:14px 0 8px">Le meilleur moment pour vous appeler</p><div class="cartes mini" id="cgq-cr">' + [['matin', 'Le matin'], ['midi', 'Entre midi et 14 h'], ['soir', 'En fin de journée'], ['indifferent', 'Peu importe']].map(function (o) { return '<button type="button" class="c" data-v="' + o[0] + '"><b>' + o[1] + '</b></button>'; }).join('') + '</div>'
        + '<p class="msg" id="cgq-tmsg"></p><div class="pile"><button type="button" class="cta sec" data-a="rappel">Être rappelé</button><button type="button" class="lien" data-a="info-passer" data-q="rappelFait">Non merci</button></div>';
      var cr = B.querySelector('#cgq-cr'); cr.onclick = function (e) { var b = e.target.closest('.c'); if (!b) return; [].forEach.call(cr.children, function (x) { x.classList.toggle('on', x === b); }); S.creneau = b.getAttribute('data-v'); };
      return;
    }
    var q = Q[i];
    B.innerHTML = (i === 0 ? '<h3>Pendant ce temps, affinons vos conseils</h3><p class="sous" style="margin-bottom:14px">' + Q.length + ' questions rapides, facultatives.</p>' : '')
      + '<div class="points" aria-hidden="true">' + Q.map(function (x, k) { return '<i class="' + (k <= i ? 'on' : '') + '"></i>'; }).join('') + '</div>'
      + '<p class="qb">' + h(q[1]) + '</p><div class="cartes mini">' + q[2].map(function (o) { return '<button type="button" class="c" data-a="info" data-q="' + q[0] + '" data-v="' + o[0] + '"><b>' + h(o[1]) + '</b></button>'; }).join('') + '</div>'
      + '<button type="button" class="lien" data-a="info-passer" data-q="' + q[0] + '">Passer</button>';
  }
  function poster(o) { try { fetch(API + '/api/infos/' + encodeURIComponent(S.id), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(o), keepalive: true }); } catch (e) { } }
  function repondre(cle, v) {
    if (!cle) return;
    S.infos[cle] = v; garder();
    if (v) { var o = {}; o[cle] = v; poster(o); ev('cgp_q_info', { question: cle, reponse: v }); }
    var B = M.querySelector('#cgq-bonus'); if (B) { B.style.opacity = '0'; setTimeout(function () { bonus(); B.style.transition = 'opacity .25s'; B.style.opacity = '1'; }, 140); }
  }
  function rappel(b) {
    var I = M.querySelector('#cgq-tel'), msg = M.querySelector('#cgq-tmsg'), t = (I.value || '').replace(/[^\d+]/g, '');
    if (t.length < 9) { I.classList.add('err'); msg.textContent = 'Indiquez un numéro de téléphone valide.'; I.focus(); return; }
    poster({ telephone: t, rappel: S.creneau || 'indifferent' }); S.infos.telephone = true; garder();
    ev('cgp_rappel', { projet_jardin: S.id, canal: 'questionnaire' }); bonus();
  }

  /* ---------- départ ---------- */
  if (S.envoi && !S.id && !S.erreur) S.erreur = 'L\'envoi a été interrompu. Vos réponses sont gardées, réessayez.';
  if (!S.envies && S.envie) S.envies = [S.envie];
  if (!S.id && !S.envoi) {
    if (ETAPES.indexOf(S.etape) < 0) S.etape = 'envie';
    if (S.etape === 'terrain' && !S.adresse) S.etape = 'adresse';
    if (S.etape === 'contact' && !S.sansPhoto) S.etape = 'photo';      // la photo n'est pas gardée d'une visite à l'autre
  }
  try { history.replaceState({ cgq: S.etape }, '', location.href); } catch (e) { }
  rendre();
  ev('cgp_q_vue', { etape: S.id ? 'attente' : S.etape, reprise: S.etape !== 'envie' && !S.id ? 'oui' : 'non' });
})();
