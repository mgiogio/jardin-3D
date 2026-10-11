# Plantes devant le bas des clôtures. L'IA a reçu l'image avec la vraie clôture et le massif déjà en place (passe 1)
# et a fait pousser des plantes devant le bas des lames. On compare SA sortie à SON entrée : ce qui a changé sur la
# clôture = plantes ajoutées (gardées pleines, détourage doux) ; le reste = clôture exacte de l'image finale.
# Sous le pied de la clôture, on reprend le sol de l'IA en fondu (raccord avec le massif).
# Usage : python3 bande_ia.py base_finale.jpg entree_ia.jpg sortie_ia.jpg cloture1.png[,..] sortie.jpg [part=0.45] [dessous=0.25]
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
base = Image.open(sys.argv[1]).convert('RGB'); W, H = base.size
ref = np.asarray(Image.open(sys.argv[2]).convert('RGB').resize((W, H))).astype(float)
G = np.asarray(Image.open(sys.argv[3]).convert('RGB').resize((W, H), Image.LANCZOS)).astype(float)
B = np.asarray(base).astype(float)
part = float(sys.argv[6]) if len(sys.argv) > 6 else 0.45; dess = float(sys.argv[7]) if len(sys.argv) > 7 else 0.25
clo = np.zeros((H, W), bool); band = np.zeros((H, W), bool); sous = np.zeros((H, W))
for cp in sys.argv[4].split(','):
    m = np.asarray(Image.open(cp).convert('RGBA').resize((W, H)).getchannel('A')) > 128; clo |= m
    for x in np.where(m.any(0))[0]:
        ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); h = y1 - y0
        band[int(y1 - h * part):y1 + 1, x] = True
        n = int(h * dess); yy = np.arange(y1 + 1, min(H, y1 + 1 + n))
        sous[yy, x] = np.maximum(sous[yy, x], (1 - (yy - y1) / max(n, 1)) ** 0.6)
band &= clo
d = ndi.uniform_filter(np.abs(G - ref).mean(-1), 3)
pl = band & (d > 26)
pl = ndi.binary_opening(pl, iterations=2)
lab, n = ndi.label(pl)
if n: pl = np.isin(lab, 1 + np.where(ndi.sum(pl, lab, range(1, n + 1)) > 300)[0])
pl = ndi.binary_closing(pl, iterations=4)
tr = ndi.binary_fill_holes(pl) & ~pl; lt, nt = ndi.label(tr)
if nt: pl |= np.isin(lt, 1 + np.where(ndi.sum(tr, lt, range(1, nt + 1)) < 2500)[0])
pl &= band
a = ndi.gaussian_filter(pl.astype(float), 1.0)
a = np.maximum(a, np.where(clo, 0, sous))
out = B * (1 - a[..., None]) + G * a[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[5], quality=93)
Image.fromarray((pl * 255).astype('uint8')).save(sys.argv[5].replace('.jpg', '_plantes.png')); print('ok', int(pl.sum()))
