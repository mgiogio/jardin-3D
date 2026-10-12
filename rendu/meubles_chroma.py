# Mobilier sur une terrasse sans que l'IA redessine la terrasse : le plancher est remplacé par un aplat cyan, l'IA pose les
# meubles dessus (avec leurs ombres), puis on détoure : meubles = ce qui n'est pas cyan ; ombres = assombrissement du cyan,
# reporté sur le vrai plancher. Le plancher (pose, vis, joints) reste celui du produit.
# Usage : OPENAI_API_KEY=... python3 meubles_chroma.py image.jpg terrasse.png pergola_seule.png consigne.txt sortie.jpg [haut=170]
import sys, os, io, json, base64, urllib.request, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size; haut = int(sys.argv[6]) if len(sys.argv) > 6 else 170
A = lambda p: np.asarray(Image.open(p).convert('RGBA').resize((W, H)).getchannel('A')) > 160
deck, per = A(sys.argv[2]), A(sys.argv[3])
sol = deck & ~per
band = deck.copy()
for x in np.where(deck.any(0))[0]:
    y0 = np.where(deck[:, x])[0].min(); band[max(0, y0 - haut):y0, x] = True
edit = band & ~per
CY = np.array([0, 230, 230], float)
I = np.asarray(img).astype(float); src = I.copy(); src[sol] = CY
x0, y0, x1, y1 = Image.fromarray((band * 255).astype('uint8')).getbbox()
cw = int(max(x1 - x0, (y1 - y0) * 1.5) * 1.2); ch = int(cw / 1.5); cx, cy_ = (x0 + x1) // 2, (y0 + y1) // 2
bx = (max(0, cx - cw // 2), max(0, cy_ - ch // 2)); box = (bx[0], bx[1], min(W, bx[0] + cw), min(H, bx[1] + ch))
S = Image.fromarray(src.astype('uint8')); crop = S.crop(box); em = Image.fromarray((edit * 255).astype('uint8')).crop(box)
mask = crop.convert('RGBA'); mask.putalpha(em.point(lambda v: 0 if v else 255))
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
Z = (1536, 1024); bd = 'cgb'
def prt(n, v, fn=None, ct=None):
    h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '')
    return h.encode() + b'\r\n' + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
ia_p = sys.argv[5].replace('.jpg', '_ia.png'); crop.save(sys.argv[5].replace('.jpg', '_entree.png'))
if os.environ.get('REPRENDRE') and os.path.exists(ia_p): gen = Image.open(ia_p).convert('RGB')
else:
    body = b''.join([prt('model', 'gpt-image-1'), prt('prompt', open(sys.argv[4]).read()), prt('size', f'{Z[0]}x{Z[1]}'), prt('quality', 'high'), prt('input_fidelity', 'high'),
                     prt('image', png(crop.resize(Z, Image.LANCZOS)), 'i.png', 'image/png'), prt('mask', png(mask.resize(Z)), 'm.png', 'image/png')]) + f'--{bd}--\r\n'.encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY', ''), 'Content-Type': f'multipart/form-data; boundary={bd}'})
    res = json.load(urllib.request.urlopen(req, timeout=400))
    gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize(crop.size, Image.LANCZOS); gen.save(ia_p)
G = np.asarray(gen).astype(float); E = I[box[1]:box[3], box[0]:box[2]].copy(); emA = np.asarray(em) > 0
solc = sol[box[1]:box[3], box[0]:box[2]]
r, g, b = G[..., 0], G[..., 1], G[..., 2]
cyan = np.minimum(g, b) - r                                     # fort sur le fond cyan (même ombré), faible sur bois et feuillage
lum = (g + b) / 2
# couleur locale du cyan non ombré (référence pour mesurer les ombres)
pur = (cyan > 120) & (np.abs(g - b) < 40)
ref = ndi.maximum_filter(np.where(pur, lum, 0), size=61); ref = np.where(ref > 0, ref, 230)
k = np.clip((cyan - 25) / 90, 0, 1)                             # 1 = fond, 0 = meuble
k = np.where(emA, k, 1.0)
meuble = (k < 0.5) & emA
meuble = ndi.binary_opening(meuble, iterations=1)
lab, n = ndi.label(meuble)
if n: meuble = np.isin(lab, 1 + np.where(ndi.sum(meuble, lab, range(1, n + 1)) > 120)[0])
a = np.where(meuble, 1 - k, 0.0); a = np.maximum(a, ndi.gaussian_filter(meuble.astype(float), 0.7) * 0.0)
a = ndi.gaussian_filter(a, 0.6)
# décontamination : retirer le reflet cyan sur les bords
Gd = G.copy()
bord = (ndi.binary_dilation(meuble, iterations=1) & ~ndi.binary_erosion(meuble, iterations=3)) | ((a > 0.02) & (a < 0.98))
vert_ok = (g > r * 1.15) & (g > b * 1.15) & (hsv_s := 1) if False else np.zeros_like(bord)
# bords : vert et bleu ramenés sous le rouge (bois, terre cuite) ; le feuillage (vert franc et peu bleu) est épargné
feuil = (g > r * 1.1) & (b < g * 0.8)
fix = bord & ~feuil
Gd[..., 1] = np.where(fix, np.minimum(g, r * 0.98 + 4), g); Gd[..., 2] = np.where(fix, np.minimum(b, r * 0.85), b)
Gd[..., 2] = np.where(bord & feuil, np.minimum(b, g * 0.7), Gd[..., 2])
# reflet cyan du sol sur le bas des meubles (pieds, bas des pots) : sur le plancher, aucun meuble n'est vert
bas = meuble & solc
Gd[..., 1] = np.where(bas, np.minimum(Gd[..., 1], r * 0.93 + 2), Gd[..., 1]); Gd[..., 2] = np.where(bas, np.minimum(Gd[..., 2], r * 0.78), Gd[..., 2])
# ombres sur le plancher : rapport de luminance du cyan ombré / cyan pur
omb = np.clip(lum / ref, 0.45, 1.0); omb = np.where(solc & ~meuble, omb, 1.0); omb = ndi.gaussian_filter(omb, 1.2)
out = E * omb[..., None]
out = out * (1 - a[..., None]) + np.clip(Gd, 0, 255) * a[..., None]
res = I.copy(); res[box[1]:box[3], box[0]:box[2]] = out
Image.fromarray(np.clip(res, 0, 255).astype('uint8')).save(sys.argv[5], quality=94); print('ok', box, int(meuble.sum()))
