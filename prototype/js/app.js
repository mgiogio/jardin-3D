// Parcours "Mon jardin aménagé" : moteur d'étapes, état, et contenu de chaque étape.
import { PRODUCTS, ENDPOINTS } from './config.js';
import { geocode, reverseGeocode, fetchBuildings, fetchParcel, facadesOf, visibleFacades, bearingDeg, rectFromSide, polylineLength, compassLabel, ringAreaM2, distanceM } from './geo.js';
import { startSensors, sensorSnapshot, readExifView } from './capture.js';
import { prepare as prepareZones, maskAt as maskZone, paint as paintZones, hit as hitZone } from './zones.js';
import { GardenMap, outwardSide, snapToFacades } from './map.js';

const STORE_KEY = 'cg-jardin-amenage-v1';
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const m = (x) => `${x.toFixed(1).replace('.', ',')} m`;
// Le client choisit un besoin ; les produits en découlent (règles à affiner avec le catalogue).
const NEEDS = [
  { id: 'ombre', label: 'Un coin à l\'ombre', sub: 'Pour manger ou se détendre dehors', products: ['pergola-adossee', 'pergola-autoportante', 'terrasse'] },
  { id: 'intimite', label: 'Être tranquille chez soi', sub: 'À l\'abri des regards des voisins ou de la rue', products: ['cloture'] },
  { id: 'sol', label: 'Un sol propre et agréable', sub: 'Remplacer la pelouse, la terre ou le béton', products: ['terrasse'] },
  { id: 'mur', label: 'Embellir un mur', sub: 'Un mur ou une façade triste', products: ['bardage'] },
  { id: 'entree', label: 'Une belle entrée', sub: 'Fermer ou marquer l\'accès depuis la rue', products: ['cloture', 'portillon'] },
  { id: 'rangement', label: 'Ranger le jardin', sub: 'Vélos, outils, mobilier', products: ['abri'] },
  { id: 'piece', label: 'Une pièce en plus', sub: 'Bureau, chambre d\'amis, atelier', products: ['studio'] },
  { id: 'surprise', label: 'Je ne sais pas encore', sub: 'Proposez-moi la meilleure idée', products: [] },
];

// ---------- État ----------

const blank = () => ({
  step: 0,
  address: null, buildings: [], building: null, facades: [], parcel: null,
  photos: [],
  need: null, freeText: '', view: null,
  keepZones: [], problems: [], style: null, upkeep: null,
  budget: null, horizon: null,
  contact: { firstName: '', email: '', phone: '', optin: false, consent: false },
});

let state = load();
function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return { ...blank(), ...JSON.parse(raw), photos: [] };
  } catch (e) { /* stockage indisponible : on repart de zéro */ }
  return blank();
}
function save() {
  try {
    const { photos, buildings, keepZones, ...rest } = state;
    localStorage.setItem(STORE_KEY, JSON.stringify({ ...rest, photos: [], buildings: [], keepZones: [] }));
  } catch (e) { /* ignoré */ }
}

// ---------- Carte partagée ----------

let gmap = null;
function mapIn(container) {
  if (!gmap) gmap = new GardenMap(document.createElement('div'));
  gmap.attach(container);
  gmap.reset(); gmap.onClick(null); gmap.onMove(null); gmap.setCursor('');
  return gmap;
}

// ---------- Composants ----------

function chips(name, options, { multi = false, value } = {}) {
  const current = multi ? (value || []) : value;
  return `<div class="chips" data-name="${name}" data-multi="${multi}">${options.map((o) => {
    const [id, label, sub] = Array.isArray(o) ? o : [o, o];
    const on = multi ? current.includes(id) : current === id;
    return `<button type="button" class="chip${on ? ' is-on' : ''}" data-id="${esc(id)}" aria-pressed="${on}">
      <span class="chip-label">${esc(label)}</span>${sub ? `<span class="chip-sub">${esc(sub)}</span>` : ''}</button>`;
  }).join('')}</div>`;
}

function bindChips(root, onChange) {
  root.querySelectorAll('.chips').forEach((group) => {
    const name = group.dataset.name;
    const multi = group.dataset.multi === 'true';
    group.addEventListener('click', (e) => {
      const btn = e.target.closest('.chip');
      if (!btn) return;
      const id = btn.dataset.id;
      if (multi) {
        const set = new Set(state[name] || []);
        set.has(id) ? set.delete(id) : set.add(id);
        state[name] = [...set];
      } else {
        state[name] = state[name] === id ? null : id;
      }
      group.querySelectorAll('.chip').forEach((c) => {
        const on = multi ? state[name].includes(c.dataset.id) : state[name] === c.dataset.id;
        c.classList.toggle('is-on', on);
        c.setAttribute('aria-pressed', on);
      });
      save();
      onChange && onChange();
    });
  });
}

function advice(text) {
  return `<button type="button" class="link-advice" data-advice>${esc(text || 'Je ne sais pas, conseillez-moi')}</button>`;
}

// ---------- Étapes ----------

const STEPS = [
  {
    id: 'intro', title: null,
    render: () => `
      <div class="hero">
        <p class="eyebrow">Gratuit · 5 minutes</p>
        <h1>Voyez votre jardin aménagé, avec les conseils d'un paysagiste</h1>
        <p class="lead">Une photo de votre jardin, quelques questions, et vous recevez un visuel de votre propre jardin avec nos pergolas, clôtures ou terrasses, les plantes adaptées à votre région et nos conseils.</p>
        <ul class="ticks"><li>Vos vraies dimensions, calculées depuis la carte IGN</li><li>Des produits réels, aux bonnes tailles et aux bons prix</li><li>Des plantes choisies pour votre climat</li></ul>
      </div>`,
    next: 'Commencer',
  },
  {
    id: 'photos', title: 'Votre jardin en photo',
    help: 'Prenez la photo depuis l\'endroit d\'où vous aimeriez voir votre futur jardin, à hauteur d\'yeux, en reculant le plus possible.',
    render: () => `
      <div id="photo-list" class="photo-grid"></div>
      <label class="upload upload-main" id="photo-label"><input id="files" type="file" accept="image/*" multiple>
        <span>Ajouter une photo</span><small>Prenez-la maintenant ou choisissez-la dans vos photos</small></label>
      <p class="small" id="photo-more"></p>`,
    mount(root) {
      const list = $('#photo-list', root), more = $('#photo-more', root);
      const draw = () => {
        list.innerHTML = state.photos.map((p, i) => `<figure class="photo-card${i === 0 ? ' is-main' : ''}">
            <img src="${p.url}" alt="Photo ${i + 1}">
            <figcaption>${i === 0 ? 'Photo principale' : `Photo ${i + 1}`}</figcaption>
            <button type="button" class="photo-del" data-del="${i}" aria-label="Retirer la photo ${i + 1}">Retirer</button>
          </figure>`).join('');
        more.textContent = state.photos.length === 0 ? ''
          : state.photos.length < 3 ? 'D\'autres vues du jardin nous aident à mieux le comprendre.' : '';
        const lab = $('#photo-label', root);
        lab.querySelector('span').textContent = state.photos.length ? 'Ajouter une autre photo (facultatif)' : 'Ajouter une photo';
        lab.querySelector('small').classList.toggle('is-hidden', state.photos.length > 0);
        lab.classList.toggle('is-secondary', state.photos.length > 0);
        $('#photo-label', root).classList.toggle('is-hidden', state.photos.length >= 3);
        refreshNav();
      };
      // Le téléphone propose lui-même « Prendre une photo » ou « Photothèque ».
      // Capteurs allumés au clic ; une photo datée de moins de 2 minutes vient d'être prise sur place.
      $('#photo-label', root).addEventListener('click', () => { startSensors(); });
      $('#files', root).addEventListener('change', async (e) => {
        const snap = sensorSnapshot();
        for (const f of [...e.target.files].slice(0, 3 - state.photos.length)) {
          const p = { name: f.name, size: f.size, type: f.type, file: f, url: URL.createObjectURL(f), guess: null };
          const justTaken = Date.now() - (f.lastModified || 0) < 120000;
          const ex = await readExifView(f);
          if (ex) p.guess = { lat: ex.lat, lon: ex.lon, heading: ex.heading ?? (justTaken ? snap.heading : null), source: 'photo' };
          else if (justTaken && snap.fix) p.guess = { lat: snap.fix.lat, lon: snap.fix.lon, heading: snap.heading, source: 'telephone' };
          state.photos.push(p);
          if (state.photos.length === 1) state.view = null;
        }
        e.target.value = ''; draw();
      });
      list.addEventListener('click', (e) => {
        const del = e.target.closest('[data-del]'); if (!del) return;
        const i = +del.dataset.del; URL.revokeObjectURL(state.photos[i].url); state.photos.splice(i, 1);
        if (i === 0) state.view = null;
        draw();
      });
      draw();
    },
    valid: () => state.photos.length > 0,
  },
  {
    id: 'adresse', title: 'Où se trouve votre jardin ?',
    help: 'Votre adresse nous sert à mesurer votre maison et à choisir des plantes adaptées à votre climat.',
    render: () => `
      <div id="addr-guess"></div>
      <label class="field"><span>Adresse</span>
        <input id="addr" type="text" autocomplete="off" placeholder="Ex. 12 rue des Lilas, Lyon" value="${esc(state.address?.label || '')}">
      </label>
      <ul id="addr-list" class="suggest" role="listbox"></ul>
      <p id="addr-msg" class="msg"></p>`,
    mount(root) {
      const input = $('#addr', root), list = $('#addr-list', root), msg = $('#addr-msg', root), guessBox = $('#addr-guess', root);
      const choose = (a) => {
        if (state.address?.label !== a.label) { state.building = null; state.facades = []; state.parcel = null; state.buildings = []; state.view = null; }
        state.address = a; input.value = a.label; list.innerHTML = ''; guessBox.innerHTML = ''; save(); refreshNav();
      };
      // La photo connaît parfois l'adresse : on la propose, il suffit de toucher.
      const g = mainPhoto()?.guess;
      if (g && !state.address) {
        reverseGeocode(g.lat, g.lon).then((a) => {
          if (!a || state.address) return;
          guessBox.innerHTML = `<button type="button" class="suggest-big"><span class="small">D'après votre photo</span><b>${esc(a.label)}</b><span class="small">Touchez pour choisir cette adresse</span></button>`;
          guessBox.querySelector('button').addEventListener('click', () => choose(a));
        }).catch(() => {});
      }
      let ctrl, timer;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          ctrl?.abort(); ctrl = new AbortController();
          try {
            const res = await geocode(input.value, { signal: ctrl.signal });
            msg.textContent = '';
            list.innerHTML = res.map((a, i) => `<li><button type="button" data-i="${i}">${esc(a.label)}</button></li>`).join('');
            list.onclick = (e) => { const b = e.target.closest('button'); if (b) choose(res[+b.dataset.i]); };
          } catch (e) {
            if (e.name !== 'AbortError') msg.textContent = 'La recherche d\'adresse ne répond pas. Réessayez dans un instant.';
          }
        }, 250);
      });
    },
    valid: () => !!state.address,
  },
  {
    id: 'maison', title: 'C\'est bien votre maison ?',
    help: 'Elle est entourée en orange. Si ce n\'est pas la bonne, touchez votre maison sur la carte.',
    render: () => `
      <div class="map-wrap" id="map-slot"></div>
      <div id="house-info" class="info"></div>`,
    async mount(root) {
      const map = mapIn($('#map-slot', root));
      const info = $('#house-info', root);
      const { lat, lon } = state.address;
      map.focus(lat, lon, 19);

      const select = (b) => {
        if (state.building?.id !== b.id) state.view = null;
        state.building = { id: b.id, ring: b.ring, height: b.height, floors: b.floors };
        state.facades = facadesOf(b.ring);
        map.showBuildings(state.buildings, b.id, select);
        renderInfo(); save(); refreshNav();
      };
      const renderInfo = () => {
        if (!state.building) { info.innerHTML = '<p class="msg">Touchez votre maison sur la carte.</p>'; return; }
        info.innerHTML = '';
      };

      info.innerHTML = '<p class="msg">Nous cherchons votre maison…</p>';
      try {
        const [buildings, parcel] = await Promise.all([
          fetchBuildings(lat, lon),
          fetchParcel(lat, lon).catch(() => null),
        ]);
        // Une parcelle très grande ou couverte de bâtiments est une copropriété ou un lotissement :
        // sa surface ne décrit pas le jardin du client, on ne s'en sert pas.
        const inParcel = parcel?.ring ? buildings.filter((b) => isInParcel(b.ring, parcel.ring)) : [];
        const usable = parcel && parcel.area && parcel.area <= 3000 && inParcel.length <= 4;
        state.buildings = buildings; state.parcel = usable ? parcel : null;
        inParcel.sort((a, b) => ringAreaM2(b.ring) - ringAreaM2(a.ring));
        const hit = (state.building && buildings.find((b) => b.id === state.building.id)) || (usable && inParcel[0]) || nearest(buildings, lon, lat);
        map.showBuildings(buildings, hit?.id, select);
        if (hit) select(hit); else renderInfo();
        // Un seul cadrage, au chargement : la carte ne bouge plus ensuite.
        map.fitTo(hit?.ring, 20);
      } catch (e) {
        info.innerHTML = '<p class="msg is-error">La carte ne répond pas pour le moment. Vous pouvez continuer.</p>';
        state.building = null; refreshNav(true);
      }
    },
    valid: () => !!state.building,
    next: 'Oui, c\'est elle',
    skippable: 'Je ne la trouve pas',
  },
  {
    id: 'ou-photo', title: 'Où étiez-vous pour prendre la photo ?',
    when: () => !!state.building,
    render: () => `
      <img class="photo-hero" src="${mainPhoto()?.url || ''}" alt="Votre photo principale">
      <p class="big-instruction" id="pos-msg"></p>
      <div class="map-wrap" id="map-slot"></div>`,
    mount(root) {
      const map = mapIn($('#map-slot', root));
      const msg = $('#pos-msg', root);
      map.showBuildings([{ id: state.building.id, ring: state.building.ring }], state.building.id);
      map.fitTo(state.building.ring, 20);
      const g = mainPhoto()?.guess;
      const near = g && distanceM([g.lon, g.lat], houseCenter()) < 80;
      if (!state.view?.origin && near) state.view = { origin: [g.lon, g.lat], bearing: null, source: g.source, headingGuess: g.heading };
      const draw = () => {
        if (state.view?.origin) {
          map.setViewpoint(state.view.origin, null, mainPhoto()?.url);
          msg.textContent = state.view.source === 'carte'
            ? 'C\'est noté. Touchez ailleurs pour corriger, sinon continuez.'
            : 'Nous pensons que vous étiez ici. Si ce n\'est pas ça, touchez le bon endroit.';
        } else {
          msg.textContent = 'Touchez la carte à l\'endroit où vous vous teniez.';
        }
        refreshNav();
      };
      map.onClick((pt) => {
        state.view = { origin: pt, bearing: null, source: 'carte' };
        save(); draw();
      });
      draw();
    },
    valid: () => !!state.view?.origin,
    skippable: 'Je ne sais plus',
    onSkip: () => { state.view = { unknown: true }; },
  },
  {
    id: 'direction', title: 'Que regardiez-vous ?',
    when: () => !!state.view?.origin,
    render: () => `
      <img class="photo-hero" src="${mainPhoto()?.url || ''}" alt="Votre photo principale">
      <p class="big-instruction" id="dir-msg"></p>
      <div class="map-wrap" id="map-slot"></div>`,
    mount(root) {
      const map = mapIn($('#map-slot', root));
      const msg = $('#dir-msg', root);
      map.showBuildings([{ id: state.building.id, ring: state.building.ring }], state.building.id);
      map.fitTo(state.building.ring, 20, state.view.origin);
      if (state.view.bearing == null && typeof state.view.headingGuess === 'number') state.view.bearing = state.view.headingGuess;
      const draw = () => {
        map.setViewpoint(state.view.origin, state.view.bearing, mainPhoto()?.url);
        msg.textContent = state.view.bearing == null
          ? 'Touchez sur la carte ce qui se trouve au milieu de votre photo.'
          : 'Le cône orange montre ce que voit votre photo. Touchez ailleurs pour corriger, sinon continuez.';
        refreshNav();
      };
      map.onClick((pt) => { state.view.bearing = bearingDeg(state.view.origin, pt); state.view.check = null; save(); draw(); });
      draw();
    },
    valid: () => state.view?.bearing != null,
  },
  {
    id: 'echelle', title: 'Une dernière vérification sur votre photo',
    render: () => `
      <img class="photo-hero" src="${mainPhoto()?.url || ''}" alt="Votre photo principale">
      <div id="check-box"></div>
      <div class="map-wrap is-hidden" id="map-slot"></div>`,
    mount(root) {
      const box = $('#check-box', root), slot = $('#map-slot', root);
      const v = state.view || (state.view = { unknown: true });
      const walls = v.origin && v.bearing != null && state.facades.length
        ? visibleFacades(state.facades, v.origin, v.bearing).slice(0, 3) : [];
      let map = null;
      const showWall = (f) => {
        slot.classList.remove('is-hidden');
        if (!map) {
          map = mapIn(slot);
          map.showBuildings([{ id: state.building.id, ring: state.building.ring }], state.building.id);
          map.fitTo(state.building.ring, 21, v.origin);
        }
        map.setViewpoint(v.origin, null, mainPhoto()?.url);
        map.showFacades(state.facades, [f.index], true);
      };
      const ask = () => {
        if (v.check) {
          const c = v.check;
          slot.classList.add('is-hidden');
          box.innerHTML = `<div class="callout is-done"><b>C'est tout bon</b><span>${c.type === 'estimate' ? 'Nous estimerons les dimensions à partir de votre photo.' : 'Merci, nous avons tout ce qu\'il nous faut.'}</span>
            <button type="button" class="link-advice" data-act="redo">Modifier ma réponse</button></div>`;
          refreshNav(); return;
        }
        const f = walls[v.alt || 0];
        if (f) {
          showWall(f);
          box.innerHTML = `<div class="callout"><b>Voit-on ce mur de votre maison sur la photo ?</b>
            <span>C'est le trait orange sur la carte.</span>
            <div class="row"><button type="button" class="btn-pri" data-act="yes">Oui</button>
            <button type="button" class="btn-sec" data-act="no">Non</button></div></div>`;
        } else {
          slot.classList.add('is-hidden');
          box.innerHTML = `<div class="callout"><b>Connaissez-vous une longueur visible sur la photo ?</b>
            <span>Un portail, une porte de garage, un mur… même à peu près.</span>
            <div class="row length-row">
              <select id="len-what" aria-label="Élément mesuré"><option>Portail</option><option>Porte de garage</option><option>Mur</option><option>Clôture</option><option>Terrasse</option><option>Autre</option></select>
              <input id="len-val" type="number" inputmode="decimal" min="0.5" max="60" step="0.1" placeholder="Mètres" aria-label="Longueur en mètres">
              <button type="button" class="btn-pri btn-sm" data-act="len">Valider</button>
            </div>
            <button type="button" class="link-advice" data-act="unknown">Je ne sais pas, estimez-la pour moi</button></div>`;
        }
        refreshNav();
      };
      box.addEventListener('click', (e) => {
        const act = e.target.closest('[data-act]')?.dataset.act;
        if (!act) return;
        if (act === 'yes') { const f = walls[v.alt || 0]; v.check = { type: 'facade', index: f.index, length: f.length }; }
        if (act === 'no') v.alt = (v.alt || 0) + 1;
        if (act === 'len') {
          const n = parseFloat(String($('#len-val', box).value).replace(',', '.'));
          if (!(n > 0.3 && n < 100)) { $('#len-val', box).focus(); return; }
          v.check = { type: 'length', label: $('#len-what', box).value.toLowerCase(), length: n };
        }
        if (act === 'unknown') v.check = { type: 'estimate' };
        if (act === 'redo') { v.check = null; v.alt = 0; }
        save(); ask();
      });
      ask();
    },
    valid: () => !!state.view?.check,
  },
  {
    id: 'garder', title: 'Qu\'est-ce que vous voulez garder ?',
    render: () => `
      <p class="big-instruction" id="keep-msg">Touchez sur la photo ce que vous voulez garder : un arbre, une haie, un massif…</p>
      <div class="zone-stage" id="stage">
        <img id="zone-img" src="${mainPhoto()?.url || ''}" alt="Votre photo principale">
        <canvas id="zone-layer" aria-hidden="true"></canvas>
        <div class="zone-busy" id="zone-busy">Préparation de votre photo…</div>
      </div>
      <p class="small" id="keep-count"></p>`,
    mount(root) {
      const img = $('#zone-img', root), layer = $('#zone-layer', root), busy = $('#zone-busy', root);
      const msg = $('#keep-msg', root), count = $('#keep-count', root);
      const url = mainPhoto()?.url;
      // Les masques ne sont pas conservés d'une visite à l'autre : on garde les points touchés.
      state.keepZones = (state.keepZones || []).filter((z) => z.url === url);
      let ready = false, working = false, failed = false;
      const draw = () => {
        layer.width = img.clientWidth * devicePixelRatio; layer.height = img.clientHeight * devicePixelRatio;
        paintZones(layer, state.keepZones);
        const n = state.keepZones.length;
        count.textContent = n ? `${n} élément${n > 1 ? 's' : ''} gardé${n > 1 ? 's' : ''}. Touchez un élément vert pour le retirer.` : '';
        $('#next').textContent = n ? 'Continuer' : 'Rien de particulier';
        save(); refreshNav();
      };
      const setBusy = (t) => { busy.textContent = t || ''; busy.classList.toggle('is-hidden', !t); };
      img.addEventListener('load', draw);
      if (img.complete) draw();
      window.addEventListener('resize', draw, { once: true });
      prepareZones(url).then(() => { ready = true; setBusy(''); }).catch(() => {
        failed = true; setBusy('');
        msg.textContent = 'Touchez sur la photo ce que vous voulez garder. Une pastille verte le signale.';
      });
      layer.addEventListener('click', async (e) => {
        if (working) return;
        const r = layer.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        const i = hitZone(state.keepZones, x, y);
        if (i >= 0) { state.keepZones.splice(i, 1); draw(); return; }
        const zone = { url, point: [x, y], mask: null, box: null };
        if (!failed) {
          working = true; setBusy(ready ? 'Un instant…' : 'Préparation de votre photo…');
          try {
            zone.mask = await maskZone(url, x, y);
            zone.box = zone.mask.box;
          } catch (err) { failed = true; }
          working = false; setBusy('');
        }
        state.keepZones.push(zone); draw();
      });
    },
    valid: () => true,
  },
  {
    id: 'besoin', title: 'Que voulez-vous faire de cet espace ?',
    help: 'Choisissez ce qui compte le plus pour vous. Nous choisirons les aménagements adaptés.',
    render: () => `
      <div class="needs">${NEEDS.map((n) => `<button type="button" class="chip need${state.need === n.id ? ' is-on' : ''}" data-need="${n.id}" aria-pressed="${state.need === n.id}">
          <span class="chip-label">${esc(n.label)}</span><span class="chip-sub">${esc(n.sub)}</span></button>`).join('')}</div>
      <label class="field"><span>Une précision ? (facultatif)</span>
        <textarea id="free" rows="3" placeholder="Ex. pour manger dehors en famille, à côté de la porte-fenêtre">${esc(state.freeText)}</textarea></label>`,
    mount(root) {
      root.querySelector('.needs').addEventListener('click', (e) => {
        const b = e.target.closest('[data-need]'); if (!b) return;
        state.need = b.dataset.need;
        root.querySelectorAll('[data-need]').forEach((x) => { const on = x.dataset.need === state.need; x.classList.toggle('is-on', on); x.setAttribute('aria-pressed', on); });
        save(); refreshNav();
      });
      $('#free', root).addEventListener('input', (e) => { state.freeText = e.target.value; save(); });
    },
    valid: () => !!state.need,
  },
  {
    id: 'problemes', title: 'Qu\'est-ce qui vous gêne aujourd\'hui ?',
    help: 'Facultatif, plusieurs réponses possibles.',
    render: () => chips('problems', [
      ['vis-a-vis', 'Vis-à-vis', 'Les voisins ou la rue voient chez vous'],
      ['soleil', 'Trop de soleil', 'Impossible de rester dehors l\'après-midi'],
      ['vent', 'Vent'], ['bruit', 'Bruit'],
      ['vide', 'Jardin vide ou triste'], ['neglige', 'Jardin négligé', 'La végétation a pris le dessus'],
      ['mur', 'Mur ou façade disgracieux'], ['rangement', 'Manque de rangement'],
    ], { multi: true, value: state.problems }),
    mount: (root) => bindChips(root, refreshNav),
    valid: () => true,
  },
  {
    id: 'style', title: 'Quelle ambiance vous fait envie ?',
    render: () => `
      <div class="styles chips" data-name="style" data-multi="false">${[
        ['mediterraneen', 'Méditerranéen', 'Oliviers, lavandes, tons chauds'],
        ['contemporain', 'Contemporain', 'Lignes nettes, graminées, sobre'],
        ['nature', 'Nature', 'Généreux, fleuri, un peu sauvage'],
        ['boheme', 'Bohème', 'Coussins, lumières, plantes en pots'],
        ['zen', 'Zen', 'Minéral, bambous, érables'],
      ].map(([id, label, sub]) => `<button type="button" class="chip style-card style-${id}${state.style === id ? ' is-on' : ''}" data-id="${id}">
          <span class="swatch"></span><span class="chip-label">${label}</span><span class="chip-sub">${sub}</span></button>`).join('')}</div>
      <p class="label">Pour les plantes, vous préférez</p>
      ${chips('upkeep', [['zero', 'Zéro entretien'], ['peu', 'Un peu d\'entretien'], ['passion', 'Je suis jardinier dans l\'âme']], { value: state.upkeep })}`,
    mount: (root) => bindChips(root, refreshNav),
    valid: () => !!state.style && !!state.upkeep,
  },
  {
    id: 'budget', title: 'Votre budget et votre calendrier',
    help: 'Pour vous proposer des produits réalistes. Le budget concerne le bois (kits), hors plantes.',
    render: () => `
      <p class="label">Budget pour les aménagements bois</p>
      ${chips('budget', [['<2000', 'Moins de 2 000 €'], ['2000-5000', '2 000 à 5 000 €'], ['5000-10000', '5 000 à 10 000 €'], ['>10000', 'Plus de 10 000 €'], ['?', 'Je ne sais pas encore']], { value: state.budget })}
      <p class="label">Quand voulez-vous commencer ?</p>
      ${chips('horizon', [['vite', 'Dès que possible'], ['printemps', 'Au printemps'], ['annee', 'Dans l\'année'], ['reflexion', 'Je réfléchis']], { value: state.horizon })}`,
    mount: (root) => bindChips(root, refreshNav),
    valid: () => !!state.budget && !!state.horizon,
  },
  {
    id: 'etude', title: null, auto: true,
    render: () => `<div class="study"><div class="spinner" aria-hidden="true"></div><h2>Nous étudions votre jardin</h2><ul id="study-list" class="study-list"></ul></div>`,
    mount(root) {
      const list = $('#study-list', root);
      const lines = studyLines();
      let i = 0;
      const tick = () => {
        if (i > 0) list.children[i - 1]?.classList.add('is-done');
        if (i < lines.length) {
          const li = document.createElement('li'); li.textContent = lines[i]; list.appendChild(li); i++;
          setTimeout(tick, 1100);
        } else setTimeout(() => go(1), 900);
      };
      tick();
    },
  },
  {
    id: 'contact', title: 'Votre projet est prêt',
    help: 'Indiquez où vous l\'envoyer. Vous recevez votre visuel et nos conseils par email dans quelques minutes.',
    render: () => `
      <label class="field"><span>Prénom</span><input id="fn" type="text" autocomplete="given-name" value="${esc(state.contact.firstName)}"></label>
      <label class="field"><span>Email</span><input id="em" type="email" autocomplete="email" value="${esc(state.contact.email)}"></label>
      <label class="field"><span>Téléphone (facultatif, pour être rappelé par un conseiller)</span><input id="ph" type="tel" autocomplete="tel" value="${esc(state.contact.phone)}"></label>
      <label class="check"><input id="consent" type="checkbox" ${state.contact.consent ? 'checked' : ''}> <span>J'accepte que Cover Green utilise mon adresse et mes photos pour réaliser mon projet. <a href="#" onclick="return false">En savoir plus</a></span></label>
      <label class="check"><input id="optin" type="checkbox" ${state.contact.optin ? 'checked' : ''}> <span>Je souhaite recevoir les conseils et offres de Cover Green par email.</span></label>`,
    mount(root) {
      const bind = (id, key, prop = 'value') => $(`#${id}`, root).addEventListener(prop === 'value' ? 'input' : 'change', (e) => { state.contact[key] = e.target[prop]; save(); refreshNav(); });
      bind('fn', 'firstName'); bind('em', 'email'); bind('ph', 'phone'); bind('consent', 'consent', 'checked'); bind('optin', 'optin', 'checked');
    },
    valid: () => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(state.contact.email) && state.contact.firstName.trim().length > 0 && state.contact.consent,
    next: 'Recevoir mon projet',
    onNext: submit,
  },
  {
    id: 'merci', title: null, final: true,
    render: () => `
      <div class="hero">
        <p class="eyebrow">C'est envoyé</p>
        <h1>Merci ${esc(state.contact.firstName)}, votre jardin est entre de bonnes mains</h1>
        <p class="lead">Vous allez recevoir votre visuel et nos conseils à <b>${esc(state.contact.email)}</b> dans quelques minutes. Pensez à regarder dans vos courriers indésirables.</p>
      </div>
      <details class="dev"><summary>Données envoyées (prototype)</summary><pre id="payload"></pre>
        <button type="button" class="btn-sec btn-sm" id="dl">Télécharger le JSON</button>
        <button type="button" class="btn-ghost btn-sm" id="reset">Recommencer</button></details>`,
    mount(root) {
      const payload = buildPayload();
      $('#payload', root).textContent = JSON.stringify(payload, null, 2);
      $('#dl', root).addEventListener('click', () => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
        a.download = 'projet-jardin.json'; a.click();
      });
      $('#reset', root).addEventListener('click', () => { try { localStorage.removeItem(STORE_KEY); } catch (e) { /* */ } state = blank(); render(); });
    },
  },
];

// ---------- Contenu dérivé ----------

function mainPhoto() { return state.photos[0]; }
function houseCenter() {
  const r = state.building?.ring; if (!r) return null;
  return r.slice(0, -1).reduce((s, p) => [s[0] + p[0], s[1] + p[1]], [0, 0]).map((v) => v / (r.length - 1));
}

function nearest(buildings, lon, lat) {
  const containing = buildings.find((b) => isInParcel([[lon, lat]], b.ring));
  if (containing) return containing;
  let best = null, bd = Infinity;
  buildings.forEach((b) => {
    const c = b.ring.reduce((s, p) => [s[0] + p[0], s[1] + p[1]], [0, 0]).map((v) => v / b.ring.length);
    const d = (c[0] - lon) ** 2 + (c[1] - lat) ** 2;
    if (d < bd) { bd = d; best = b; }
  });
  return best;
}
function isInParcel(ring, parcelRing) {
  const c = ring.reduce((s, p) => [s[0] + p[0], s[1] + p[1]], [0, 0]).map((v) => v / ring.length);
  let inside = false;
  for (let i = 0, j = parcelRing.length - 1; i < parcelRing.length; j = i++) {
    const [xi, yi] = parcelRing[i], [xj, yj] = parcelRing[j];
    if (yi > c[1] !== yj > c[1] && c[0] < ((xj - xi) * (c[1] - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function studyLines() {
  const lines = [];
  const city = state.address?.city;
  const scale = state.view?.check && state.view.check.type !== 'estimate' ? state.view.check : null;
  if (state.parcel?.area) lines.push(`Lecture de votre terrain : ${state.parcel.area} m²`);
  if (scale) lines.push('Mise à l\'échelle de votre photo');
  else lines.push('Analyse de votre photo et estimation des dimensions');
  if (state.facades.length) {
    const sunny = state.facades.filter((f) => ['sud', 'sud-ouest', 'ouest'].includes(f.facing)).sort((a, b) => b.length - a.length)[0];
    lines.push(sunny ? `Ensoleillement : façade ${sunny.facing} très exposée l'après-midi` : 'Calcul de l\'ensoleillement');
  }
  lines.push(city ? `Choix des plantes adaptées au climat de ${city}` : 'Choix des plantes adaptées à votre climat');
  lines.push('Sélection des aménagements Cover Green adaptés à votre projet');
  lines.push('Préparation de votre projet');
  return lines;
}

function buildPayload() {
  return {
    version: 1,
    createdAt: new Date().toISOString(),
    address: state.address,
    parcel: state.parcel && { area: state.parcel.area, ref: state.parcel.ref, ring: state.parcel.ring },
    building: state.building && { ring: state.building.ring, height: state.building.height, floors: state.building.floors },
    facades: state.facades.map(({ index, length, azimuth, facing, a, b }) => ({ index, length: +length.toFixed(2), azimuth: Math.round(azimuth), facing, a, b })),
    photos: state.photos.map((p, i) => ({ name: p.name, size: p.size, type: p.type, main: i === 0, guess: p.guess })),
    view: state.view,
    project: {
      need: state.need, products: NEEDS.find((n) => n.id === state.need)?.products || [], freeText: state.freeText,
    },
    keep: (state.keepZones || []).map((z) => ({ point: z.point, box: z.box })),
    needs: { problems: state.problems, style: state.style, upkeep: state.upkeep },
    budget: state.budget, horizon: state.horizon,
    contact: state.contact,
  };
}

async function submit() {
  const payload = buildPayload();
  if (!ENDPOINTS.projectApi) return true; // prototype : pas encore d'API
  const form = new FormData();
  form.append('project', JSON.stringify(payload));
  state.photos.forEach((p, i) => form.append(`photo${i}`, p.file, p.name));
  const r = await fetch(ENDPOINTS.projectApi, { method: 'POST', body: form });
  return r.ok;
}

// ---------- Moteur ----------

const app = $('#app');
const activeSteps = () => STEPS.filter((s) => !s.when || s.when());

function go(delta) {
  const list = activeSteps();
  let idx = list.findIndex((s) => s.id === STEPS[state.step]?.id);
  if (idx < 0) idx = 0;
  let next = Math.max(0, Math.min(list.length - 1, idx + delta));
  while (delta < 0 && next > 0 && list[next].auto) next--;
  const target = list[next];
  state.step = STEPS.indexOf(target);
  save(); render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

let forceSkip = false;
function refreshNav(allowSkip) {
  if (allowSkip) forceSkip = true;
  const s = STEPS[state.step];
  const btn = $('#next');
  if (btn) btn.disabled = !(forceSkip || !s.valid || s.valid() || (s.optional && s.optional()));
}

function render() {
  forceSkip = false;
  if (!STEPS[state.step] || (STEPS[state.step].when && !STEPS[state.step].when())) state.step = 0;
  // Les photos et les bâtiments ne sont pas conservés d'une visite à l'autre : on revient à l'étape adaptée.
  const s = STEPS[state.step];
  const list = activeSteps();
  const pos = list.findIndex((x) => x.id === s.id);
  const total = list.filter((x) => !x.auto && x.id !== 'intro' && !x.final).length;
  const num = list.slice(0, pos + 1).filter((x) => !x.auto && x.id !== 'intro' && !x.final).length;
  const showNav = !s.auto && !s.final;

  app.innerHTML = `
    ${s.id !== 'intro' && !s.final && !s.auto ? `<div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round((num / total) * 100)}"><div style="width:${(num / total) * 100}%"></div></div>` : ''}
    <section class="step step-${s.id}">
      ${s.title ? `<h2>${esc(s.title)}</h2>` : ''}
      ${s.help ? `<p class="help">${esc(s.help)}</p>` : ''}
      ${s.optional && s.optional() ? '<p class="small">Facultatif : vous savez déjà ce que vous voulez.</p>' : ''}
      <div class="step-body">${s.render()}</div>
    </section>
    ${showNav ? `<nav class="nav">
      ${pos > 0 ? '<button type="button" class="btn-ghost" id="prev">Retour</button>' : '<span></span>'}
      <div class="nav-right">
        ${s.skippable ? `<button type="button" class="btn-ghost" id="skip">${esc(s.skippable)}</button>` : ''}
        <button type="button" class="btn-pri" id="next">${esc(s.next || 'Continuer')}</button>
      </div></nav>` : ''}`;

  const body = $('.step-body', app);
  s.mount && s.mount(body);
  if (showNav) {
    $('#prev')?.addEventListener('click', () => go(-1));
    $('#skip')?.addEventListener('click', () => { s.onSkip?.(); save(); go(1); });
    $('#next').addEventListener('click', async (e) => {
      if (s.onNext) {
        e.target.disabled = true; e.target.textContent = 'Envoi…';
        const ok = await s.onNext().catch(() => false);
        if (!ok) { e.target.disabled = false; e.target.textContent = s.next; alert('L\'envoi n\'a pas fonctionné, réessayez.'); return; }
      }
      go(1);
    });
    refreshNav();
  }
  body.querySelectorAll('[data-advice]').forEach((b) => b.addEventListener('click', () => go(1)));
}

// Au rechargement, les photos sont perdues : on reprend à l'étape photos au plus tard.
const photosIdx = STEPS.findIndex((s) => s.id === 'photos');
// Les photos ne sont pas conservées d'une visite à l'autre : on reprend à l'étape photo.
if (state.step > photosIdx && !STEPS[state.step]?.final) state.step = photosIdx;
if (STEPS[state.step]?.auto) state.step = photosIdx;
render();
