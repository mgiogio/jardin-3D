// Détourage sur la photo : un toucher sur un arbre, une haie, un massif… et il s'allume.
// Modèle SlimSAM (famille « Segment Anything ») exécuté dans le navigateur via transformers.js.
// En production, la même chose tournera côté serveur avec un modèle plus fin, plus une
// pré-détection automatique des éléments (arbres, haies, piscine…).

const LIB = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2';
const MODEL_ID = 'Xenova/slimsam-77-uniform';

let libPromise = null;
let modelPromise = null;
const embeddingsCache = new Map(); // url de la photo -> { inputs, embeddings }

function lib() {
  if (!libPromise) libPromise = import(LIB);
  return libPromise;
}

async function model() {
  if (!modelPromise) {
    modelPromise = (async () => {
      const T = await lib();
      const [m, p] = await Promise.all([
        T.SamModel.from_pretrained(MODEL_ID, { dtype: 'q8' }),
        T.AutoProcessor.from_pretrained(MODEL_ID),
      ]);
      return { T, m, p };
    })();
    modelPromise.catch(() => { modelPromise = null; });
  }
  return modelPromise;
}

// Prépare la photo (calcul lourd, une seule fois par photo).
export async function prepare(url) {
  if (embeddingsCache.has(url)) return embeddingsCache.get(url);
  const { T, m, p } = await model();
  const image = await T.RawImage.read(url);
  const inputs = await p(image);
  const embeddings = await m.get_image_embeddings(inputs);
  const entry = { inputs, embeddings, width: image.width, height: image.height };
  embeddingsCache.set(url, entry);
  return entry;
}

// Renvoie le masque de l'objet touché : { width, height, data: Uint8Array (1 = objet), box }.
// x, y sont normalisés entre 0 et 1 sur la photo.
export async function maskAt(url, x, y) {
  const { T, m, p } = await model();
  const { inputs, embeddings } = await prepare(url);
  const [rh, rw] = inputs.reshaped_input_sizes[0];
  const input_points = new T.Tensor('float32', [x * rw, y * rh], [1, 1, 1, 2]);
  const input_labels = new T.Tensor('int64', [1n], [1, 1, 1]);
  const outputs = await m({ ...embeddings, input_points, input_labels });
  const masks = await p.post_process_masks(outputs.pred_masks, inputs.original_sizes, inputs.reshaped_input_sizes);
  const t = masks[0]; // [1, 3, H, W]
  const [, n, H, W] = t.dims;
  const scores = outputs.iou_scores.data;
  // On préfère le masque le mieux noté, en écartant ceux qui couvrent presque toute la photo.
  let best = 0, bestScore = -1;
  for (let k = 0; k < n; k++) {
    let count = 0;
    for (let i = k * H * W, e = (k + 1) * H * W; i < e; i++) if (t.data[i]) count++;
    const share = count / (H * W);
    const s = scores[k] - (share > 0.6 ? 1 : 0);
    if (s > bestScore) { bestScore = s; best = k; }
  }
  const data = new Uint8Array(H * W);
  let minX = W, minY = H, maxX = 0, maxY = 0;
  for (let i = 0, o = best * H * W; i < H * W; i++) {
    if (t.data[o + i]) {
      data[i] = 1;
      const px = i % W, py = (i / W) | 0;
      if (px < minX) minX = px; if (px > maxX) maxX = px;
      if (py < minY) minY = py; if (py > maxY) maxY = py;
    }
  }
  return { width: W, height: H, data, box: [minX / W, minY / H, maxX / W, maxY / H] };
}

// Dessine les éléments gardés sur un calque transparent posé sur la photo.
export function paint(canvas, zones) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const z of zones) {
    if (z.mask) {
      const { width: W, height: H, data } = z.mask;
      const img = ctx.createImageData(W, H);
      for (let i = 0; i < W * H; i++) {
        if (!data[i]) continue;
        // Contour plus marqué que l'intérieur
        const edge = !data[i - 1] || !data[i + 1] || !data[i - W] || !data[i + W];
        img.data[i * 4] = edge ? 255 : 4;
        img.data[i * 4 + 1] = edge ? 255 : 158;
        img.data[i * 4 + 2] = edge ? 255 : 0;
        img.data[i * 4 + 3] = edge ? 255 : 120;
      }
      const tmp = document.createElement('canvas');
      tmp.width = W; tmp.height = H;
      tmp.getContext('2d').putImageData(img, 0, 0);
      ctx.drawImage(tmp, 0, 0, canvas.width, canvas.height);
    }
    // Pastille numérotée au point touché
    const cx = z.point[0] * canvas.width, cy = z.point[1] * canvas.height;
    const r = Math.max(12, canvas.width / 45);
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = '#049E00'; ctx.fill();
    ctx.lineWidth = r / 4; ctx.strokeStyle = '#fff'; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = `700 ${Math.round(r * 1.1)}px Roboto, sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('✓', cx, cy + 1);
  }
}

export function hit(zones, x, y) {
  for (let i = zones.length - 1; i >= 0; i--) {
    const z = zones[i];
    if (z.mask) {
      const { width: W, height: H, data } = z.mask;
      if (data[Math.min(H - 1, (y * H) | 0) * W + Math.min(W - 1, (x * W) | 0)]) return i;
    } else if (Math.hypot(z.point[0] - x, z.point[1] - y) < 0.04) return i;
  }
  return -1;
}
