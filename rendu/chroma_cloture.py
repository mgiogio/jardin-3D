# Plantes devant les clôtures par incrustation (fond cyan) : la clôture est remplacée par un aplat cyan,
# l'IA fait pousser les plantes devant, puis tout ce qui est resté magenta redevient la clôture exacte.
# Séparation nette et prévisible, sans deviner ce qui est plante ou bois.
# Usage : OPENAI_API_KEY=... python3 chroma_cloture.py image.jpg cloture1.png[,..] consigne.txt sortie.jpg [part=0.4] [dessous=0.25]
import sys, json, base64, io, os, urllib.request, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
part = float(sys.argv[5]) if len(sys.argv) > 5 else 0.4; dess = float(sys.argv[6]) if len(sys.argv) > 6 else 0.25
alpha = lambda p: np.asarray(Image.open(p).convert('RGBA').resize((W, H)).getchannel('A')) > 128
clo = np.zeros((H, W), bool); zone = np.zeros((H, W), bool)
for cp in sys.argv[2].split(','):
    m = alpha(cp); clo |= m
    for x in np.where(m.any(0))[0]:
        ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); h = y1 - y0
        zone[int(y1 - h * part):min(H, int(y1 + h * dess)), x] = True
MAG = np.array([0, 255, 255], float)          # cyan : aucune plante n'a cette couleur (le magenta se confond avec la lavande)
I = np.asarray(img).astype(float).copy(); I[clo] = MAG
src = Image.fromarray(I.astype('uint8'))
mask = src.convert('RGBA'); mask.putalpha(Image.fromarray((zone * 255).astype('uint8')).point(lambda v: 0 if v else 255))
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
S = (1536, 1024); bd = 'cgb'
def prt(n, v, fn=None, ct=None):
    h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '')
    return h.encode() + b'\r\n' + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
ia_p = sys.argv[4].replace('.jpg', '_ia.png'); src.save(sys.argv[4].replace('.jpg', '_entree.png'))
if os.environ.get('REPRENDRE') and os.path.exists(ia_p): gen = Image.open(ia_p).convert('RGB')
else:
    body = b''.join([prt('model', 'gpt-image-1'), prt('prompt', open(sys.argv[3]).read()), prt('size', f'{S[0]}x{S[1]}'), prt('quality', 'high'), prt('input_fidelity', 'high'),
                     prt('image', png(src.resize(S, Image.LANCZOS)), 'i.png', 'image/png'), prt('mask', png(mask.resize(S)), 'm.png', 'image/png')]) + f'--{bd}--\r\n'.encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY', ''), 'Content-Type': f'multipart/form-data; boundary={bd}'})
    res = json.load(urllib.request.urlopen(req, timeout=400))
    gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS); gen.save(ia_p)
G = np.asarray(gen).astype(float); E = np.asarray(img).astype(float)
r, g, b = G[..., 0], G[..., 1], G[..., 2]
# part de fond cyan dans chaque pixel (0 = plante pleine, 1 = fond) ; bords des feuilles et épis fins = mélange
# couleur du fond cyan localement (l'IA l'assombrit dans les ombres) : moyenne des pixels franchement cyan autour
cy = np.minimum(g, b) - r
hsvk = np.asarray(gen.convert('HSV')).astype(float); hk, sk = hsvk[..., 0] * 360 / 255, hsvk[..., 1] / 255
pur = (np.abs(hk - 180) < 18) & (sk > 0.6)
wts = ndi.gaussian_filter(pur.astype(float), 12) + 1e-6
keyc = np.stack([ndi.gaussian_filter(G[..., c] * pur, 12) / wts for c in range(3)], -1)
keyc = np.where((wts > 0.02)[..., None], keyc, MAG)
kcy = np.maximum(np.minimum(keyc[..., 1], keyc[..., 2]) - keyc[..., 0], 40)
k = np.clip((cy - 8) / kcy, 0, 1)
# le sol (paillis, terre) n'est jamais devant une clôture : si l'IA en a mis sur l'aplat, la clôture reprend sa place
hsv = np.asarray(gen.convert('HSV')).astype(float); hue, sat = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255
gg = np.asarray(gen.convert('L')).astype(float); gx, gy = ndi.sobel(gg, 1), ndi.sobel(gg, 0)
Sxx, Syy, Sxy = ndi.uniform_filter(gx * gx, 11), ndi.uniform_filter(gy * gy, 11), ndi.uniform_filter(gx * gy, 11)
coh = ((Sxx - Syy) ** 2 + 4 * Sxy ** 2) / ((Sxx + Syy) ** 2 + 1e-6)
sol = (hue > 8) & (hue < 42) & (sat > 0.3) & (coh < 0.5) & clo
vk = np.asarray(gen.convert('HSV')).astype(float)[..., 2] / 255
sol |= clo & ((hue < 48) | (hue > 340)) & (sat > 0.25) & (vk < 0.55)        # paillis sombre, terre
sol = ndi.binary_opening(sol, iterations=1)
sol = ndi.binary_dilation(sol, iterations=1) & clo
force = sol.copy()
# petites taches isolées de "plante" sur la clôture = bruit
pl = clo & (k < 0.5) & ~sol; lab, n = ndi.label(pl)
if n: force |= pl & ~np.isin(lab, 1 + np.where(ndi.sum(pl, lab, range(1, n + 1)) > 150)[0])
# démélange : observé = (1-k)*plante + k*cyan  ->  résultat = observé + k*(fond réel - cyan)
out = G + k[..., None] * (E - keyc)
# reflets cyan restés sur les épis et feuilles fines : on les ramène vers le vert-jaune naturel
o = np.clip(out, 0, 255); ho = np.asarray(Image.fromarray(o.astype('uint8')).convert('HSV')).astype(float)[..., 0] * 360 / 255
teinte = zone & (ho > 115) & (ho < 215) & ndi.binary_dilation(clo, iterations=6)
orr, og, ob = o[..., 0], o[..., 1], o[..., 2]
nb = np.minimum(ob, (orr + og) / 2 * 0.82); ng = np.minimum(og, orr * 1.12 + 6)
o[..., 1] = np.where(teinte, ng, og); o[..., 2] = np.where(teinte, nb, ob); out = o
res = np.where(zone[..., None], out, E)
res[force] = E[force]
res[clo & ~zone] = E[clo & ~zone]
Image.fromarray(np.clip(res, 0, 255).astype('uint8')).save(sys.argv[4], quality=93)
print('ok', 'part plante sur la clôture', round(float((1 - k)[clo & zone].mean()), 3))
