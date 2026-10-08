// Parcours "Mon jardin aménagé" : moteur d'étapes, état, et contenu de chaque étape.
import { PRODUCTS, ENDPOINTS } from './config.js';
import { geocode, fetchBuildings, fetchParcel, facadesOf, visibleFacades, bearingDeg, rectFromSide, polylineLength, compassLabel, ringAreaM2 } from './geo.js';
import { GardenMap, outwardSide, snapToFacades } from './map.js';

const STORE_KEY = 'cg-jardin-amenage-v1';
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const m = (x) => `${x.toFixed(1).replace('.', ',')} m`;
const productLabel = Object.fromEntries(PRODUCTS.map((p) => [p.id, p.label]));

// ---------- État ----------

const blank = () => ({
  step: 0,
  address: null, buildings: [], building: null, facades: [], parcel: null,
  photos: [],
  knows: null, products: [], placements: [], freeText: '',
  ground: [], keep: [], problems: [], uses: [], style: null, upkeep: null,
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
    const { photos, buildings, ...rest } = state;
    localStorage.setItem(STORE_KEY, JSON.stringify({ ...rest, photos: [], buildings: [] }));
  } catch (e) { /* ignoré */ }
}

// ---------- Carte partagée ----------

let gmap = null;
function mapIn(container) {
  if (!gmap) gmap = new GardenMap(document.createElement('div'));
  gmap.attach(container);
  gmap.onClick(null); gmap.onMove(null); gmap.setCursor(''); gmap.clearDraft();
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
    id: 'adresse', title: 'Où se trouve votre jardin ?',
    help: 'Votre adresse nous sert à mesurer votre maison et votre terrain, et à choisir des plantes adaptées à votre climat.',
    render: () => `
      <label class="field"><span>Adresse</span>
        <input id="addr" type="text" autocomplete="off" placeholder="Ex. 12 rue des Lilas, Lyon" value="${esc(state.address?.label || '')}">
      </label>
      <ul id="addr-list" class="suggest" role="listbox"></ul>
      <p id="addr-msg" class="msg"></p>`,
    mount(root) {
      const input = $('#addr', root), list = $('#addr-list', root), msg = $('#addr-msg', root);
      let ctrl, timer;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          ctrl?.abort(); ctrl = new AbortController();
          try {
            const res = await geocode(input.value, { signal: ctrl.signal });
            msg.textContent = '';
            list.innerHTML = res.map((a, i) => `<li><button type="button" data-i="${i}">${esc(a.label)}</button></li>`).join('');
            list.onclick = (e) => {
              const b = e.target.closest('button'); if (!b) return;
              const a = res[+b.dataset.i];
              state.address = a; state.building = null; state.facades = []; state.parcel = null; state.buildings = [];
              input.value = a.label; list.innerHTML = ''; save(); refreshNav();
            };
          } catch (e) {
            if (e.name !== 'AbortError') msg.textContent = 'La recherche d\'adresse ne répond pas. Réessayez dans un instant.';
          }
        }, 250);
      });
      input.focus();
    },
    valid: () => !!state.address,
  },
  {
    id: 'maison', title: 'Touchez votre maison sur la vue aérienne',
    help: 'On récupère ses dimensions et l\'orientation de chaque façade. Si votre maison n\'est pas surlignée, touchez-la directement.',
    render: () => `
      <div class="map-wrap" id="map-slot"></div>
      <div id="house-info" class="info"></div>
      <label class="toggle"><input type="checkbox" id="cad"> Afficher le cadastre</label>`,
    async mount(root) {
      const map = mapIn($('#map-slot', root));
      const info = $('#house-info', root);
      const { lat, lon } = state.address;
      map.focus(lat, lon, 19);
      map.showAddress(lat, lon);
      $('#cad', root).addEventListener('change', (e) => map.showCadastre(e.target.checked));

      const select = (b) => {
        state.building = { id: b.id, ring: b.ring, height: b.height, floors: b.floors };
        state.facades = facadesOf(b.ring);
        map.showBuildings(state.buildings, b.id, select);
        map.showFacades(state.facades);
        renderInfo(); save(); refreshNav();
      };
      const renderInfo = () => {
        if (!state.building) { info.innerHTML = '<p class="msg">Touchez votre maison sur la carte.</p>'; return; }
        const longest = [...state.facades].sort((a, b) => b.length - a.length).slice(0, 4);
        info.innerHTML = `
          <div class="facts">
            ${state.parcel?.area ? `<div><b>${state.parcel.area} m²</b><span>terrain</span></div>` : ''}
            ${state.building.height ? `<div><b>${m(state.building.height)}</b><span>hauteur</span></div>` : ''}
            <div><b>${state.facades.length}</b><span>façades</span></div>
          </div>
          <p class="small">Plus grandes façades : ${longest.map((f) => `${m(f.length)} côté ${f.facing}`).join(' · ')}</p>`;
      };

      info.innerHTML = '<p class="msg">Chargement des données IGN…</p>';
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
        map.showParcel(state.parcel);
        // Bâtiment proposé : le plus grand de la parcelle (la maison plutôt que le garage), sinon le plus proche du point d'adresse.
        inParcel.sort((a, b) => ringAreaM2(b.ring) - ringAreaM2(a.ring));
        const hit = (state.building && buildings.find((b) => b.id === state.building.id)) || (usable && inParcel[0]) || nearest(buildings, lon, lat);
        map.showBuildings(buildings, hit?.id, select);
        if (hit) select(hit); else renderInfo();
        map.fitTo(parcel?.ring || hit?.ring);
      } catch (e) {
        info.innerHTML = '<p class="msg is-error">Les données IGN ne répondent pas pour le moment. Vous pouvez continuer, on vous demandera une dimension sur la photo.</p>';
        state.building = null; refreshNav(true);
      }
    },
    valid: () => !!state.building,
    skippable: 'Je ne trouve pas ma maison',
  },
  {
    id: 'photos', title: 'Vos photos du jardin',
    help: 'Prenez 1 à 3 photos depuis l\'endroit où vous aimeriez voir votre projet, à hauteur d\'yeux, en reculant au maximum. Puis indiquez sur la carte d\'où vous les avez prises.',
    render: () => `
      <label class="upload"><input id="files" type="file" accept="image/*" multiple>
        <span>Ajouter des photos</span><small>JPG ou PNG, 3 maximum</small></label>
      <div id="photo-list" class="photo-list"></div>
      <div class="map-wrap" id="map-slot"></div>
      <p id="cone-msg" class="msg"></p>`,
    mount(root) {
      const map = mapIn($('#map-slot', root));
      const list = $('#photo-list', root), msg = $('#cone-msg', root);
      if (state.building) { map.showBuildings([{ id: state.building.id, ring: state.building.ring }], state.building.id); map.showFacades(state.facades); map.fitTo(state.parcel?.ring || state.building.ring); }
      else if (state.address) map.focus(state.address.lat, state.address.lon, 19);

      let placing = -1, origin = null;
      const draw = () => {
        map.showCones(state.photos, placing);
        list.innerHTML = state.photos.map((p, i) => {
          const vis = p.view?.facades?.[0];
          return `<div class="photo${i === placing ? ' is-active' : ''}">
            <img src="${p.url}" alt="Photo ${i + 1}">
            <div class="photo-body">
              <b>Photo ${i + 1}</b>
              <span class="small">${p.view ? (vis ? `Façade visible : ${m(vis.length)}, côté ${vis.facing}` : 'Position enregistrée') : 'Position à indiquer sur la carte'}</span>
              <div class="row">
                <button type="button" class="btn-sec btn-sm" data-place="${i}">${p.view ? 'Replacer' : 'Placer sur la carte'}</button>
                <button type="button" class="btn-ghost btn-sm" data-del="${i}">Retirer</button>
              </div>
            </div></div>`;
        }).join('');
        refreshNav();
      };
      const finish = (target) => {
        const p = state.photos[placing];
        const bearing = bearingDeg(origin, target);
        const vis = state.facades.length ? visibleFacades(state.facades, origin, bearing) : [];
        p.view = { origin, bearing, facing: compassLabel(bearing), facades: vis.slice(0, 2).map(({ index, length, facing }) => ({ index, length, facing })) };
        map.showFacades(state.facades, vis.slice(0, 1).map((f) => f.index));
        placing = -1; origin = null;
        map.onClick(null); map.onMove(null); map.clearDraft(); map.setCursor('');
        msg.textContent = vis.length ? '' : 'Aucune façade dans le champ : ce n\'est pas grave, on vous demandera une dimension.';
        draw();
      };
      list.addEventListener('click', (e) => {
        const pl = e.target.closest('[data-place]'), dl = e.target.closest('[data-del]');
        if (pl) {
          placing = +pl.dataset.place; origin = null; draw();
          msg.textContent = '1. Touchez l\'endroit où vous étiez. 2. Touchez dans la direction où vous regardiez.';
          map.setCursor('crosshair');
          map.onClick((pt) => {
            if (!origin) { origin = pt; map.previewCone(origin); map.onMove((cur) => map.previewCone(origin, cur)); }
            else finish(pt);
          });
          $('#map-slot', root).scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (dl) { const i = +dl.dataset.del; URL.revokeObjectURL(state.photos[i].url); state.photos.splice(i, 1); draw(); }
      });
      $('#files', root).addEventListener('change', (e) => {
        [...e.target.files].slice(0, 3 - state.photos.length).forEach((f) => {
          state.photos.push({ name: f.name, size: f.size, type: f.type, file: f, url: URL.createObjectURL(f), view: null });
        });
        e.target.value = ''; draw();
      });
      draw();
    },
    valid: () => state.photos.length > 0,
  },
  {
    id: 'projet', title: 'Vous savez déjà ce que vous voulez ?',
    render: () => `
      ${chips('knows', [['oui', 'Oui, j\'ai une idée précise'], ['non', 'Non, conseillez-moi']], { value: state.knows })}
      <div id="prod" class="${state.knows === 'oui' ? '' : 'is-hidden'}">
        <p class="label">Quels aménagements ?</p>
        ${chips('products', PRODUCTS.map((p) => [p.id, p.label, p.hint]), { multi: true, value: state.products })}
      </div>`,
    mount(root) { bindChips(root, () => { $('#prod', root).classList.toggle('is-hidden', state.knows !== 'oui'); refreshNav(); }); },
    valid: () => state.knows === 'non' || (state.knows === 'oui' && state.products.length > 0),
  },
  {
    id: 'placement', title: 'Où voulez-vous vos aménagements ?',
    help: 'Dessinez chaque élément sur la vue aérienne. Près d\'une façade, le tracé s\'y aimante tout seul.',
    when: () => state.knows === 'oui' && state.products.length > 0,
    render: () => `
      <div class="tools" id="tools"></div>
      <div class="map-wrap" id="map-slot"></div>
      <div id="draw-panel" class="draw-panel"></div>
      <ul id="placed" class="placed"></ul>
      <label class="field"><span>Précisions (facultatif)</span>
        <textarea id="free" rows="3" placeholder="Ex. pergola collée à la façade côté salon, ouverte vers la piscine">${esc(state.freeText)}</textarea></label>`,
    mount(root) {
      const map = mapIn($('#map-slot', root));
      const tools = $('#tools', root), panel = $('#draw-panel', root), placed = $('#placed', root);
      if (state.building) { map.showBuildings([{ id: state.building.id, ring: state.building.ring }], state.building.id); map.showFacades(state.facades); map.fitTo(state.parcel?.ring || state.building.ring); }
      else if (state.address) map.focus(state.address.lat, state.address.lon, 19);
      $('#free', root).addEventListener('input', (e) => { state.freeText = e.target.value; save(); });

      let draft = null;
      const products = PRODUCTS.filter((p) => state.products.includes(p.id));
      const snap = (pt) => (state.facades.length ? snapToFacades(pt, state.facades, 2.5) : null);

      const redraw = () => {
        map.showPlacements(state.placements, productLabel);
        tools.innerHTML = products.map((p) => `<button type="button" class="chip${draft?.product.id === p.id ? ' is-on' : ''}" data-tool="${p.id}">
          <span class="chip-label">${esc(p.label)}</span><span class="chip-sub">${state.placements.filter((x) => x.productId === p.id).length ? 'Placé' : 'À placer'}</span></button>`).join('');
        placed.innerHTML = state.placements.map((p, i) => `<li><span><b>${esc(productLabel[p.productId])}</b> ${p.width ? `${m(p.width)} × ${m(p.depth)}` : m(p.length)}${p.facade ? `, contre la façade ${p.facade.facing}` : ''}</span>
          <button type="button" class="btn-ghost btn-sm" data-rm="${i}">Retirer</button></li>`).join('');
        panel.innerHTML = draftPanel();
        refreshNav(); save();
      };
      const draftPanel = () => {
        if (!draft) return '<p class="msg">Choisissez un aménagement ci-dessus pour le dessiner.</p>';
        const p = draft.product;
        if (p.mode === 'ligne') {
          return `<p class="msg">Touchez les points successifs de votre ${esc(p.label.toLowerCase())}.</p>
            <div class="row"><button type="button" class="btn-pri btn-sm" data-act="done" ${draft.points.length < 2 ? 'disabled' : ''}>Terminer</button>
            <button type="button" class="btn-ghost btn-sm" data-act="cancel">Annuler</button></div>`;
        }
        if (draft.points.length < 2) {
          return `<p class="msg">${p.snapFacade ? 'Touchez les deux extrémités du côté posé contre la façade.' : 'Touchez les deux extrémités d\'un côté.'}</p>
            <div class="row"><button type="button" class="btn-ghost btn-sm" data-act="cancel">Annuler</button></div>`;
        }
        return `<label class="field"><span>Profondeur : <b id="dv">${m(draft.depth)}</b></span>
            <input type="range" min="1" max="8" step="0.5" value="${draft.depth}" data-act="depth"></label>
          <div class="row"><button type="button" class="btn-pri btn-sm" data-act="ok">Valider</button>
          <button type="button" class="btn-sec btn-sm" data-act="flip">Changer de côté</button>
          <button type="button" class="btn-ghost btn-sm" data-act="cancel">Annuler</button></div>`;
      };
      const showDraft = (cursor) => {
        const p = draft.product;
        if (p.mode === 'ligne') map.draftLine(draft.points, cursor);
        else if (draft.points.length === 1) map.draftLine(draft.points, cursor);
        else if (draft.points.length === 2) draft.rect = map.draftRect(draft.points[0], draft.points[1], draft.depth, draft.side);
      };
      const stop = () => { draft = null; map.onClick(null); map.onMove(null); map.clearDraft(); map.setCursor(''); redraw(); };

      tools.addEventListener('click', (e) => {
        const b = e.target.closest('[data-tool]'); if (!b) return;
        const product = PRODUCTS.find((p) => p.id === b.dataset.tool);
        draft = { product, points: [], depth: product.defaultDepth || 3, side: 1, facade: null };
        map.setCursor('crosshair');
        map.onMove((pt) => { if (draft.points.length < 2 || product.mode === 'ligne') showDraft(snap(pt)?.point || pt); });
        map.onClick((raw) => {
          if (product.mode === 'zone' && draft.points.length >= 2) return;
          const s = snap(raw);
          draft.points.push(s ? s.point : raw);
          if (s && !draft.facade) draft.facade = s.facade;
          if (product.mode === 'zone' && draft.points.length === 2) {
            draft.side = state.building ? outwardSide(draft.points[0], draft.points[1], state.building.ring) : 1;
            map.onMove(null);
          }
          showDraft(); panel.innerHTML = draftPanel();
        });
        redraw();
      });
      panel.addEventListener('input', (e) => {
        if (e.target.dataset.act === 'depth') { draft.depth = +e.target.value; $('#dv', root).textContent = m(draft.depth); showDraft(); }
      });
      panel.addEventListener('click', (e) => {
        const act = e.target.closest('[data-act]')?.dataset.act;
        if (!act || !draft) return;
        if (act === 'cancel') stop();
        if (act === 'flip') { draft.side *= -1; showDraft(); }
        if (act === 'ok') {
          const r = rectFromSide(draft.points[0], draft.points[1], draft.depth, draft.side);
          state.placements.push({ productId: draft.product.id, ring: r.ring, width: r.width, depth: r.depth, facade: draft.facade ? { index: draft.facade.index, facing: draft.facade.facing } : null });
          stop();
        }
        if (act === 'done') {
          state.placements.push({ productId: draft.product.id, line: draft.points, length: polylineLength(draft.points), facade: draft.facade ? { index: draft.facade.index, facing: draft.facade.facing } : null });
          stop();
        }
      });
      placed.addEventListener('click', (e) => {
        const b = e.target.closest('[data-rm]'); if (!b) return;
        state.placements.splice(+b.dataset.rm, 1); redraw();
      });
      redraw();
    },
    valid: () => true,
  },
  {
    id: 'terrain', title: 'Votre terrain aujourd\'hui',
    render: () => `
      <p class="label">Le sol là où vous voulez aménager</p>
      ${chips('ground', [['pelouse', 'Pelouse'], ['gravier', 'Gravier'], ['dalle', 'Dalle béton'], ['terre', 'Terre nue'], ['dallage', 'Dallage, pavés'], ['pente', 'Terrain en pente']], { multi: true, value: state.ground })}
      <p class="label">Ce que vous voulez garder</p>
      ${chips('keep', [['arbres', 'Arbres'], ['massifs', 'Massifs, haies'], ['piscine', 'Piscine'], ['terrasse', 'Terrasse existante'], ['potager', 'Potager'], ['rien', 'Rien de particulier']], { multi: true, value: state.keep })}`,
    mount: (root) => bindChips(root, refreshNav),
    valid: () => state.ground.length > 0,
  },
  {
    id: 'problemes', title: 'Qu\'est-ce qui vous gêne aujourd\'hui ?',
    optional: () => state.knows === 'oui',
    render: () => chips('problems', [
      ['vis-a-vis', 'Vis-à-vis', 'Les voisins ou la rue voient chez vous'],
      ['soleil', 'Trop de soleil', 'Impossible de rester dehors l\'après-midi'],
      ['vent', 'Vent'], ['bruit', 'Bruit'],
      ['vide', 'Jardin vide ou triste'], ['neglige', 'Jardin négligé', 'La végétation a pris le dessus'],
      ['mur', 'Mur ou façade disgracieux'], ['rangement', 'Manque de rangement'],
    ], { multi: true, value: state.problems }),
    mount: (root) => bindChips(root, refreshNav),
    valid: () => state.problems.length > 0 || state.knows === 'oui',
  },
  {
    id: 'usages', title: 'Comment voulez-vous en profiter ?',
    optional: () => state.knows === 'oui',
    render: () => chips('uses', [
      ['repas', 'Repas dehors'], ['detente', 'Détente, lecture'], ['enfants', 'Jeux des enfants'],
      ['piscine', 'Autour de la piscine'], ['potager', 'Potager'], ['recevoir', 'Recevoir des amis'],
      ['bureau', 'Télétravail ou pièce en plus'],
    ], { multi: true, value: state.uses }),
    mount: (root) => bindChips(root, refreshNav),
    valid: () => state.uses.length > 0 || state.knows === 'oui',
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
      <label class="check"><input id="consent" type="checkbox" ${state.contact.consent ? 'checked' : ''}> J'accepte que Cover Green utilise mon adresse et mes photos pour réaliser mon projet. <a href="#" onclick="return false">En savoir plus</a></label>
      <label class="check"><input id="optin" type="checkbox" ${state.contact.optin ? 'checked' : ''}> Je souhaite recevoir les conseils et offres de Cover Green par email.</label>`,
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
  const photoFacade = state.photos.find((p) => p.view?.facades?.length)?.view.facades[0];
  if (state.parcel?.area) lines.push(`Lecture de votre terrain : ${state.parcel.area} m²`);
  if (photoFacade) lines.push(`Mise à l'échelle de vos photos : façade de ${m(photoFacade.length)} côté ${photoFacade.facing}`);
  else lines.push('Analyse de vos photos');
  if (state.facades.length) {
    const sunny = state.facades.filter((f) => ['sud', 'sud-ouest', 'ouest'].includes(f.facing)).sort((a, b) => b.length - a.length)[0];
    lines.push(sunny ? `Ensoleillement : façade ${sunny.facing} très exposée l'après-midi` : 'Calcul de l\'ensoleillement');
  }
  lines.push(city ? `Choix des plantes adaptées au climat de ${city}` : 'Choix des plantes adaptées à votre climat');
  lines.push(state.knows === 'oui' ? 'Vérification des tailles de nos kits pour vos emplacements' : 'Sélection des aménagements Cover Green adaptés');
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
    photos: state.photos.map((p) => ({ name: p.name, size: p.size, type: p.type, view: p.view })),
    project: {
      knows: state.knows, products: state.products, freeText: state.freeText,
      placements: state.placements.map((p) => ({ ...p, width: p.width && +p.width.toFixed(2), length: p.length && +p.length.toFixed(2) })),
    },
    site: { ground: state.ground, keep: state.keep },
    needs: { problems: state.problems, uses: state.uses, style: state.style, upkeep: state.upkeep },
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
  const target = list[Math.max(0, Math.min(list.length - 1, idx + delta))];
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
    ${s.id !== 'intro' && !s.final && !s.auto ? `<div class="progress"><div style="width:${(num / total) * 100}%"></div></div><p class="step-count">Étape ${num} sur ${total}</p>` : ''}
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
    $('#skip')?.addEventListener('click', () => go(1));
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
if (state.step > photosIdx && !STEPS[state.step].final) state.step = state.address ? STEPS.findIndex((s) => s.id === 'maison') : 0;
if (STEPS[state.step]?.auto) state.step = photosIdx;
render();
