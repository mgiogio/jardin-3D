// Met chaque GLB de la banque à l'échelle réelle (hauteur cible), Y en haut, pied au sol ; écrit models/B_<nom>.glb
import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { getBounds } from '@gltf-transform/functions'; import fs from 'fs';
const items = JSON.parse(fs.readFileSync('banque/items.json'));
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
for (const k of Object.keys(items)) {
  if (!fs.existsSync(`banque/${k}.glb`)) continue;
  const doc = await io.read(`banque/${k}.glb`); const sc = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
  const b = getBounds(sc); const s = [0,1,2].map(i => b.max[i] - b.min[i]);
  const it = items[k]; const ref = it.h ? it.h / s[1] : it.d / s[2];
  const sc3 = [it.w ? it.w / s[0] : ref, it.h ? it.h / s[1] : ref, it.d ? it.d / s[2] : ref]; const f = ref;
  const root = doc.createNode('B_' + k).setScale(sc3);
  for (const n of sc.listChildren()) { sc.removeChild(n); root.addChild(n); }
  sc.addChild(root);
  await io.write(`models/B_${k}.glb`, doc);
  console.log(k, 'taille brute', s.map(v => v.toFixed(2)).join('x'), '-> m', s.map((v, i) => (v * sc3[i]).toFixed(2)).join('x'));
}
