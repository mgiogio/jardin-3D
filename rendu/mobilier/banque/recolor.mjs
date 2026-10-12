// Recolore un modèle de la banque : extrait la texture, la passe dans recolor.py, réécrit le GLB.
import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import fs from 'fs'; import { execFileSync } from 'child_process';
const [src, dst, cible] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS); const doc = await io.read(src);
for (const [i, t] of doc.getRoot().listTextures().entries()) {
  const mats = doc.getRoot().listMaterials().filter(m => m.getBaseColorTexture() === t); if (!mats.length) continue;
  fs.writeFileSync('/tmp/_tex_in', t.getImage());
  execFileSync('python3', ['banque/recolor.py', '/tmp/_tex_in', '/tmp/_tex_out.png', cible]);
  t.setImage(fs.readFileSync('/tmp/_tex_out.png')).setMimeType('image/png');
}
await io.write(dst, doc); console.log('ok', dst);
