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
# au pied des clôtures, on ne garde que la végétation. Test : là où l'IA a gardé (ou redessiné) la clôture, ses rayures
# coïncident avec celles de la clôture exacte (corrélation locale forte) ; là où elle a posé une plante, non.
from scipy import ndimage as ndi
def hp(a): a = a - ndi.gaussian_filter(a, 4); return a
ga, gb = hp(np.asarray(gen.convert('L')).astype(float)), hp(np.asarray(img.convert('L')).astype(float))
w = 15; f = lambda a: ndi.uniform_filter(a, w)
ncc = (f(ga * gb) - f(ga) * f(gb)) / np.sqrt(np.maximum((f(ga * ga) - f(ga) ** 2) * (f(gb * gb) - f(gb) ** 2), 1e-6))
energie = f(ga * ga)
clo = np.zeros((H, W), bool)
for cp in sys.argv[7].split(','): clo |= alpha(cp)
gx, gy = ndi.sobel(ga, 1), ndi.sobel(ga, 0)
Sxx, Syy, Sxy = ndi.uniform_filter(gx * gx, 11), ndi.uniform_filter(gy * gy, 11), ndi.uniform_filter(gx * gy, 11)
coh = ((Sxx - Syy) ** 2 + 4 * Sxy ** 2) / ((Sxx + Syy) ** 2 + 1e-6)
R_, G_, B_ = G[..., 0], G[..., 1], G[..., 2]
bois = (R_ > G_ * 1.03) & (G_ > B_ * 1.02) & (R_ - B_ > 18)                  # brun / beige bois
vegetal_c = (G_ >= R_ * 0.97) | (B_ > G_ * 1.04)                            # vert ou violet / bleu
# même orientation que les lames de la clôture exacte à cet endroit (les graminées dorées, elles, partent dans tous les sens)
hx, hy = ndi.sobel(gb, 1), ndi.sobel(gb, 0)
Bxx, Byy, Bxy = ndi.uniform_filter(hx * hx, 11), ndi.uniform_filter(hy * hy, 11), ndi.uniform_filter(hx * hy, 11)
ta, tb = 0.5 * np.arctan2(2 * Sxy, Sxx - Syy), 0.5 * np.arctan2(2 * Bxy, Bxx - Byy)
dt = np.abs(np.angle(np.exp(2j * (ta - tb)))) / 2
lames_ia = ndi.uniform_filter(((coh > 0.45) & bois & ~vegetal_c & (dt < np.radians(10))).astype(float), 9) > 0.5   # clôture redessinée par l'IA
# 1) corrélation : là où l'IA n'a pas reproduit les lames exactes et n'a pas redessiné de lames -> plante
plante = libre & clo & ((ncc < 0.35) | (energie < 20)) & ~lames_ia
# 2) segmentation sémantique (CLIPSeg) "plantes" contre "clôture en bois", par tuiles : rattrape les graminées dorées
def seg_plantes(im, zone):
    try:
        import torch
        from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
    except Exception: return np.zeros(zone.shape, bool)
    P_ = CLIPSegProcessor.from_pretrained('CIDAS/clipseg-rd64-refined'); M_ = CLIPSegForImageSegmentation.from_pretrained('CIDAS/clipseg-rd64-refined')
    out_ = np.zeros(zone.shape, bool); ys_, xs_ = np.where(zone)
    if not len(ys_): return out_
    X0, X1, Y0, Y1 = xs_.min(), xs_.max(), ys_.min(), ys_.max(); T = 520
    for ty in range(Y0, Y1 + 1, T - 80):
        for tx in range(X0, X1 + 1, T - 80):
            b_ = (tx, ty, min(W, tx + T), min(H, ty + T)); c_ = im.crop(b_)
            inp = P_(text=['plants, shrubs, flowers and ornamental grasses', 'wooden fence'], images=[c_] * 2, return_tensors='pt', padding=True)
            with torch.no_grad(): lg = torch.sigmoid(M_(**inp).logits).numpy()
            pm = Image.fromarray(((lg[0] > lg[1]) & (lg[0] > 0.25)).astype('uint8') * 255).resize(c_.size, Image.BILINEAR)
            out_[b_[1]:b_[3], b_[0]:b_[2]] |= np.asarray(pm) > 127
    return ndi.binary_erosion(out_, iterations=5) & zone
plante |= seg_plantes(gen, libre & clo) & (diff > 25)
# paillage / terre : l'IA place parfois le massif plus loin que le vrai pied de clôture ; ce sol-là est caché par la
# clôture exacte (brun orangé, texture sans direction), seules les plantes passent devant.
import colorsys
hsv = np.asarray(gen.convert('HSV')).astype(float); hue, sat = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255
paillage = (hue > 12) & (hue < 42) & (sat > 0.3) & (coh < 0.4)
paillage = ndi.uniform_filter(paillage.astype(float), 7) > 0.6
plante &= ~paillage
plante = ndi.binary_opening(plante, iterations=2)
lab, n = ndi.label(plante); tailles = ndi.sum(plante, lab, range(1, n + 1))
plante = np.isin(lab, 1 + np.where(tailles > 400)[0])          # pas de miettes
plante = ndi.binary_closing(plante, iterations=3)
trous = ndi.binary_fill_holes(plante) & ~plante; lt, nt = ndi.label(trous)
if nt: plante |= np.isin(lt, 1 + np.where(ndi.sum(trous, lt, range(1, nt + 1)) < 3000)[0])   # trous de taille fleur seulement
plante &= libre
ajout = plante | (libre & ~clo & (diff > 38))
garde_ia |= ajout | (deck_sol if os.environ.get('SOL_IA') else False)                                    # pied des clôtures : seulement ce qu'elle a ajouté ; plancher : l'IA (mobilier posé dessus)
Mk = Image.fromarray((garde_ia * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5))
res_img = Image.composite(gen, img, Mk)
# ombre de contact au pied des clôtures (le bois fonce en approchant du sol, comme sur les photos réelles)
R = np.asarray(res_img).astype(float); ao = np.ones((H, W))
for cp in sys.argv[7].split(','):
    m = alpha(cp)
    for x in np.where(m.any(0))[0]:
        ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); hgt = y1 - y0; z = int(hgt * 0.12) + 1
        t = np.linspace(0, 1, z); ao[y1 - z + 1:y1 + 1, x] = np.minimum(ao[y1 - z + 1:y1 + 1, x], 1 - 0.35 * t ** 1.5)
ao = ndi.gaussian_filter(ao, 1.5); keep_ao = ~garde_ia
R[keep_ao] *= ao[keep_ao][:, None]
# sous la clôture (côté jardin) : l'IA a parfois prolongé les lames plus bas que le vrai pied -> on bouche ces restes
# avec le sol voisin, puis ombre de contact au sol le long du pied pour bien poser la clôture.
import cv2
dessous = np.zeros((H, W), bool); contact = np.ones((H, W))
for cp in sys.argv[7].split(','):
    m = alpha(cp)
    for x in np.where(m.any(0))[0]:
        ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); hgt = y1 - y0
        dessous[y1 + 1:min(H, y1 + 1 + int(hgt * 0.3)), x] = True
        z = int(hgt * 0.05) + 2; t = np.linspace(0, 1, z)
        contact[y1 + 1:min(H, y1 + 1 + z), x] = np.minimum(contact[y1 + 1:min(H, y1 + 1 + z), x], (0.62 + 0.38 * t ** 0.8)[:min(H, y1 + 1 + z) - y1 - 1])
Rg = cv2.cvtColor(np.clip(R, 0, 255).astype('uint8'), cv2.COLOR_RGB2GRAY).astype(float)
qx, qy = ndi.sobel(Rg, 1), ndi.sobel(Rg, 0)
Qxx, Qyy, Qxy = ndi.uniform_filter(qx * qx, 11), ndi.uniform_filter(qy * qy, 11), ndi.uniform_filter(qx * qy, 11)
qc = ((Qxx - Qyy) ** 2 + 4 * Qxy ** 2) / ((Qxx + Qyy) ** 2 + 1e-6)
Rr, Rgg, Rb = R[..., 0], R[..., 1], R[..., 2]
restes = dessous & (qc > 0.5) & (Rr > Rgg * 1.03) & (Rgg > Rb * 1.02) & (Qxx + Qyy > 600) & ~((Rgg >= Rr * 0.97))
restes = ndi.binary_opening(restes, iterations=2); restes = ndi.binary_dilation(restes, iterations=3) & dessous
contact = ndi.gaussian_filter(contact, 2.0)
R *= contact[..., None]
Image.fromarray(np.clip(R, 0, 255).astype('uint8')).save(sys.argv[5], quality=93)
Image.fromarray((np.stack([edit, libre, ajout], -1) * 255).astype('uint8')).save(sys.argv[5].replace('.jpg', '_masques.png'))
print('ok', res.get('usage'))
