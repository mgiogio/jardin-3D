# Aménagement paysager "waouh" autour des produits (plantes, massifs, mobilier, pots), par édition masquée gpt-image-1.
# Les produits restent exacts : ils sont recollés pixel pour pixel, sauf dans deux bandes où l'IA a le droit de passer devant
# (pied des clôtures pour les massifs, plancher de la terrasse pour le mobilier). Au pied des clôtures, on ne garde l'IA
# que là où elle a vraiment ajouté quelque chose (écart fort avec l'image d'origine). terrasse.png = calque du plancher seul.
# Usage : OPENAI_API_KEY=... python3 amenage.py image.jpg zone.json echelle_zone consigne.txt sortie.jpg \
#         produits.png pied_clotures.png[,..] terrasse.png [part_pied=0.3]
import sys, json, base64, io, os, urllib.request, numpy as np
from PIL import Image, ImageDraw, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
k = float(sys.argv[3]); part_pied = float(sys.argv[9]) if len(sys.argv) > 9 else 0.3
alpha = lambda p: np.asarray(Image.open(p).convert('RGBA').resize((W, H)).getchannel('A')) > 160
prod = alpha(sys.argv[6])
# bande au pied des clôtures : le bas de chaque colonne de clôture, sur part_pied de sa hauteur
pied = np.zeros((H, W), bool)
for cp in sys.argv[7].split(','):
    m = alpha(cp)
    for x in np.where(m.any(0))[0]:
        ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); pied[int(y1 - (y1 - y0) * part_pied):y1 + 1, x] = True
    pied &= m | pied
deck = alpha(sys.argv[8])
mrgb = np.asarray(Image.open(sys.argv[8]).convert('RGBA').resize((W, H))).astype(float)
deck &= (mrgb[..., :3].max(-1) - mrgb[..., :3].min(-1)) / np.maximum(mrgb[..., :3].max(-1), 1) > 0.2   # plancher seulement (pas les poteaux gris)
# volume au-dessus du plancher (là où se posent table et chaises) : le plancher prolongé vers le haut d'environ 1 m
haut = int(os.environ.get('HAUT_MOBILIER', '90'))
dk = deck.copy()
for x in np.where(deck.any(0))[0]:
    y0 = np.where(deck[:, x])[0].min(); dk[max(0, y0 - haut):y0, x] = True
deck_sol = deck.copy(); deck = dk
sep = bool(os.environ.get('MOBILIER_SEPARE'))   # mobilier traité à part (mobilier.py) : terrasse et volume au-dessus exclus ici
libre = pied | (False if sep else deck)
zone = Image.new('L', (W, H), 0); d = ImageDraw.Draw(zone)
for poly in json.load(open(sys.argv[2])): d.polygon([(x * k, y * k) for x, y in poly], fill=255)
edit = (np.asarray(zone) > 0) | libre
edit &= ~(prod & ~libre)
if sep: edit &= ~deck
E = Image.fromarray((edit * 255).astype('uint8'))
mask = img.convert('RGBA'); mask.putalpha(E.point(lambda v: 0 if v else 255))
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
size = (1536, 1024) if W >= H else (1024, 1536)
bd = 'cgb'
def part(n, v, fn=None, ct=None):
    h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '')
    return h.encode() + b'\r\n' + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
body = b''.join([part('model', 'gpt-image-1'), part('prompt', open(sys.argv[4]).read()), part('size', f'{size[0]}x{size[1]}'), part('quality', 'high'),
                 part('input_fidelity', 'high'), part('image', png(img.resize(size)), 'i.png', 'image/png'), part('mask', png(mask.resize(size)), 'm.png', 'image/png')]) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY', ''), 'Content-Type': f'multipart/form-data; boundary={bd}'})
ia_p = sys.argv[5].replace('.jpg', '_ia.jpg')
if os.environ.get('REPRENDRE') and os.path.exists(ia_p): gen = Image.open(ia_p).convert('RGB'); res = {}
else:
    res = json.load(urllib.request.urlopen(req, timeout=400))
    gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS)
gen.save(sys.argv[5].replace('.jpg', '_ia.jpg'), quality=92)
G, I = np.asarray(gen).astype(float), np.asarray(img).astype(float)
diff = np.abs(G - I).mean(-1)
garde_ia = edit & ~libre                                   # zone jardin : l'IA
ajout = libre & (np.asarray(Image.fromarray((diff > 38).astype('uint8') * 255).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(7))) > 0)
garde_ia |= ajout | (deck_sol if os.environ.get('SOL_IA') else False)                                    # pied des clôtures : seulement ce qu'elle a ajouté ; plancher : l'IA (mobilier posé dessus)
Mk = Image.fromarray((garde_ia * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5))
Image.composite(gen, img, Mk).save(sys.argv[5], quality=93)
Image.fromarray((np.stack([edit, libre, ajout], -1) * 255).astype('uint8')).save(sys.argv[5].replace('.jpg', '_masques.png'))
print('ok', res.get('usage'))
