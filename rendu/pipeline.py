# Pipeline complet : rendu 3D des produits -> teinte réelle du bois -> ambiance IA -> produits recollés.
# Usage : python3 pipeline.py cas.json [--grille] [--sans-ia]
import json, sys, subprocess, os
here = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(sys.argv[1])); base = os.path.splitext(sys.argv[1])[0]
from PIL import Image
W, H = Image.open(C['photo']).size
scene = {k: C.get(k) for k in ('cam', 'items', 'sun', 'sunAz', 'sunEl', 'hemi', 'env', 'shadow', 'shadowBlur', 'exposure') if C.get(k) is not None}
scene['size'] = [W, H]
def run(*a): subprocess.run(a, check=True, cwd=here)
if '--grille' in sys.argv:
    g = dict(scene, items=[], grid=True, gridPosts=C.get('gridPosts', []), gridSize=C.get('gridSize', 80), gridDiv=C.get('gridDiv', 40))
    json.dump(g, open(base + '_grille.json', 'w')); run('node', 'scene.mjs', base + '_grille.json', base + '_grille.png')
    ph = Image.open(C['photo']).convert('RGBA'); ph.alpha_composite(Image.open(base + '_grille.png').convert('RGBA'))
    ph.convert('RGB').save(base + '_grille.jpg', quality=85); print(base + '_grille.jpg'); sys.exit()
json.dump(scene, open(base + '_scene.json', 'w'))
run('node', 'scene.mjs', base + '_scene.json', base + '_calque.png')
json.dump(C.get('devant', []), open(base + '_devant.json', 'w'))
run('python3', 'comp2.py', C['photo'], base + '_calque.png', base + '_3d.jpg', C.get('teinte', '#7a6858'), base + '_devant.json')
if '--sans-ia' in sys.argv: print(base + '_3d.jpg'); sys.exit()
json.dump(C['zone_ia'], open(base + '_zone.json', 'w'))
json.dump(C.get('devant', []) + C.get('garder', []), open(base + '_garder.json', 'w'))
open(base + '_consigne.txt', 'w').write(C['consigne'])
run('python3', 'ambiance.py', base + '_3d.jpg', base + '_calque.png', base + '_zone.json', base + '_consigne.txt', base + '_final.jpg', base + '_garder.json')
print(base + '_final.jpg')
