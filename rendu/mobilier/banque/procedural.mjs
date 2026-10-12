// Objets procéduraux de la banque : tapis (pavé fin texturé) et guirlande guinguette (fils en chaînette + ampoules).
import { Document, NodeIO } from '@gltf-transform/core'; import fs from 'fs';
const io = new NodeIO();
function mesh(doc, buf, name, pos, nor, uv, idx, mat) {
  const acc = (a, t) => doc.createAccessor().setType(t).setArray(a).setBuffer(buf);
  const p = doc.createPrimitive().setAttribute('POSITION', acc(new Float32Array(pos), 'VEC3')).setAttribute('NORMAL', acc(new Float32Array(nor), 'VEC3')).setIndices(acc(new Uint32Array(idx), 'SCALAR')).setMaterial(mat);
  if (uv) p.setAttribute('TEXCOORD_0', acc(new Float32Array(uv), 'VEC2'));
  return doc.createNode(name).setMesh(doc.createMesh(name).addPrimitive(p));
}
function boite(x0, x1, y0, y1, z0, z1, P, N, U, I) {   // 6 faces, UV du dessus = 0..1
  const f = (v, n, uv) => { const b = P.length / 3; v.forEach(q => P.push(...q)); for (let i = 0; i < 4; i++) N.push(...n); uv.forEach(q => U.push(...q)); I.push(b, b + 1, b + 2, b, b + 2, b + 3); };
  const s = [[0.02, 0.02], [0.02, 0.02], [0.02, 0.02], [0.02, 0.02]];
  f([[x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0]], [0, 1, 0], [[0, 1], [1, 1], [1, 0], [0, 0]]);
  f([[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], [0, -1, 0], s);
  f([[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], [0, 0, 1], s);
  f([[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]], [0, 0, -1], s);
  f([[x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1]], [1, 0, 0], s);
  f([[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]], [-1, 0, 0], s);
}
async function tapis(nom, w, d) {
  const doc = new Document(); const buf = doc.createBuffer();
  const tex = doc.createTexture(nom).setImage(fs.readFileSync(`banque/tex/${nom}.jpg`)).setMimeType('image/jpeg');
  const mat = doc.createMaterial(nom).setBaseColorTexture(tex).setRoughnessFactor(0.95).setMetallicFactor(0);
  const P = [], N = [], U = [], I = []; boite(-w / 2, w / 2, 0, 0.012, -d / 2, d / 2, P, N, U, I);
  doc.createScene().addChild(mesh(doc, buf, nom, P, N, U, I, mat)); await io.write(`models/B_${nom}.glb`, doc); console.log('tapis', nom);
}
async function guirlande() {   // 3 fils d'avant en arrière, en chaînette, sous les solives (repère : haut des fils à y = 0.35)
  const doc = new Document(); const buf = doc.createBuffer();
  const fil = doc.createMaterial('fil').setBaseColorFactor([0.05, 0.05, 0.05, 1]).setRoughnessFactor(0.6);
  const amp = doc.createMaterial('ampoule').setBaseColorFactor([1, 0.85, 0.6, 1]).setEmissiveFactor([1, 0.72, 0.38]).setRoughnessFactor(0.2);
  const root = doc.createNode('guirlande'); const L = 2.7, sag = 0.22, top = 0.35;
  const sph = (cx, cy, cz, r, P, N, I) => { const b = P.length / 3, n = 8; for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) { const t = Math.PI * i / n, p = 2 * Math.PI * j / n; const v = [Math.sin(t) * Math.cos(p), Math.cos(t), Math.sin(t) * Math.sin(p)]; P.push(cx + r * v[0], cy + r * v[1] * 1.3, cz + r * v[2]); N.push(...v); } for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const a = b + i * (n + 1) + j; I.push(a, a + n + 1, a + 1, a + 1, a + n + 1, a + n + 2); } };
  const Pf = [], Nf = [], If = [], Pa = [], Na = [], Ia = [];
  for (const z of [-0.95, 0, 0.95]) {   // fils tendus de gauche à droite : vus de face, ils dessinent des festons
    const y = x => top - sag * (1 - (2 * x / L) ** 2);
    for (let k = 0; k < 60; k++) {   // fil continu : deux rubans croisés qui suivent la pente
      const x0 = -L / 2 + L * k / 60, x1 = -L / 2 + L * (k + 1) / 60, e = 0.007, a = y(x0), c = y(x1);
      const q = (v, n) => { const b = Pf.length / 3; v.forEach(p => Pf.push(...p)); for (let i = 0; i < 4; i++) Nf.push(...n); If.push(b, b + 1, b + 2, b, b + 2, b + 3, b, b + 2, b + 1, b, b + 3, b + 2); };
      q([[x0, a - e, z], [x1, c - e, z], [x1, c + e, z], [x0, a + e, z]], [0, 0, 1]);
      q([[x0, a, z - e], [x1, c, z - e], [x1, c, z + e], [x0, a, z + e]], [0, 1, 0]);
    }
    for (let k = 1; k < 11; k++) { const x = -L / 2 + L * k / 11; boite(x - 0.008, x + 0.008, y(x) - 0.04, y(x), z - 0.008, z + 0.008, Pf, Nf, [], If); sph(x, y(x) - 0.065, z, 0.021, Pa, Na, Ia); }
  }
  root.addChild(mesh(doc, buf, 'fils', Pf, Nf, null, If, fil)); root.addChild(mesh(doc, buf, 'ampoules', Pa, Na, null, Ia, amp));
  doc.createScene().addChild(root); await io.write('models/B_guirlande.glb', doc); console.log('guirlande');
}
await tapis('tapis_terracotta', 2.0, 1.4); await tapis('tapis_rayures', 1.7, 1.25); await tapis('tapis_jute', 2.4, 1.7); await guirlande();
