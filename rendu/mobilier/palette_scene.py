# Remplace le mobilier d'une scène par une palette d'ambiance (palettes.json), placée par rapport à la pergola.
# Usage : python3 palette_scene.py scene.json palette sortie_scene.json sortie_meubles.json [hauteur_plancher=0.15]
import sys, json, math
sc = json.load(open(sys.argv[1])); pal = json.load(open('palettes.json'))[sys.argv[2]]; lift = float(sys.argv[5]) if len(sys.argv) > 5 else 0.15
per = next(it for it in sc['items'] if it['m'].startswith('Pergola'))
cx, cz = per['pos']; a = math.radians(per.get('rotY', 0))
def monde(x, z):   # rotation autour de Y (sens three.js) puis translation
    return [round(cx + x * math.cos(a) + z * math.sin(a), 3), round(cz - x * math.sin(a) + z * math.cos(a), 3)]
meubles = []
for it in pal['items']:
    m = {"m": it['m'], "excl": "^$", "pos": monde(*it['p']), "rotY": per.get('rotY', 0) + it.get('r', 0), "lift": lift}
    if 's' in it: m['scale'] = it['s']
    meubles.append(m)
sc['items'] = [it for it in sc['items'] if not it['m'].startswith('M_')] + meubles
json.dump(sc, open(sys.argv[3], 'w'))
m = dict(sc); m['items'] = meubles; m['shadow'] = 0; json.dump(m, open(sys.argv[4], 'w')); print(pal['nom'], len(meubles), 'meubles')
