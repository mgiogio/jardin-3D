# Garde les abords validés d'un visuel (v8) et n'y remplace que la zone produits + mobilier par la nouvelle palette,
# avec les ombres portées des meubles (même soleil que la pergola), renforcées pour coller aux ombres de la photo.
# Usage : python3 compose_v8.py v8.jpg nouveau_d.jpg cal_ter cal_perg anciens_meubles.png nouveaux_meubles.png calque_palette.png calque_sans_meubles.png sortie.jpg
import sys, numpy as np
from PIL import Image, ImageFilter
v8 = Image.open(sys.argv[1]).convert('RGB'); W, H = v8.size
A = lambda f: np.asarray(Image.open(f).convert('RGBA').resize((W, H), Image.LANCZOS)).astype(float)
nd = np.asarray(Image.open(sys.argv[2]).convert('RGB').resize((W, H))).astype(float)
ter, per, old, new, cp, cs = (A(f) for f in sys.argv[3:9])
msk = lambda a, s=0: Image.fromarray(((a[..., 3] > 60) * 255).astype('uint8')).filter(ImageFilter.MaxFilter(s) if s else ImageFilter.BLUR)
M = np.maximum.reduce([np.asarray(msk(ter)), np.asarray(msk(per)), np.asarray(msk(old, 11)), np.asarray(msk(new, 5))]).astype(float)
M = np.asarray(Image.fromarray(M.astype('uint8')).filter(ImageFilter.GaussianBlur(2))) / 255
out = np.asarray(v8).astype(float) * (1 - M[..., None]) + nd * M[..., None]
import os
# tapis : pixels du tapis réellement visibles (pas cachés par un meuble), ombrés comme le plancher en dessous
rv = np.zeros((H, W), bool)
if os.environ.get('TAPIS'):
    tp = A(os.environ['TAPIS']); st = A(os.environ['SANS_TAPIS']); rv = (tp[..., 3] > 60) & (st[..., 3] < 60)   # tapis visible = tapis non caché par un meuble
    # ombre des lames sur le tapis : rendu 3D pergola + terrasse / terrasse seule, calé sur la force des ombres de la photo
    so = A(os.environ['TER_SEULE']); ok = (cs[..., 3] > 200) & (so[..., 3] > 200)
    rr = np.where(ok, (cs[..., :3].mean(2) + 2) / (so[..., :3].mean(2) + 2), 1.0); rr = np.clip(rr, 0.2, 1)
    lo = np.percentile(rr[ok & (rr < 0.97)], 10) if (ok & (rr < 0.97)).any() else 0.7
    k = np.log(0.55) / np.log(max(lo, 0.05)); f = rr ** k
    f = np.asarray(Image.fromarray((f * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1))) / 255
    if os.environ.get('MS'):   # ombres des meubles sur le tapis : rendu avec ombres / rendu du tapis seul
        ms = A(os.environ['MS']); f2 = np.clip((ms[..., :3].mean(2) + 1) / (tp[..., :3].mean(2) + 1), 0.5, 1) ** 2
        f = f * np.where(rv, f2, 1)
    out *= np.where(rv, f, 1)[..., None]
z = (cp[..., 3] > 200) & (cs[..., 3] > 200) & (new[..., 3] < 10)
r = np.where(z, (cp[..., :3].mean(2) + 1) / (cs[..., :3].mean(2) + 1), 1.0)
r = np.clip(r, 0.5, 1) ** 4
r = np.asarray(Image.fromarray((r * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5))) / 255
out *= np.clip(r, 0.45, 1)[..., None]
# ombre d'appui : une ellipse douce au pied de chaque meuble (les pieds fins ne portent presque pas d'ombre en 3D)
from scipy import ndimage
from PIL import ImageDraw
nm = (new[..., 3] > 60) & ~rv; lab, n = ndimage.label(ndimage.binary_dilation(nm, iterations=2))
blob = Image.new('L', (W, H), 0); d = ImageDraw.Draw(blob)
for sl in ndimage.find_objects(lab):
    if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) < 900: continue
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    w = (x1 - x0) * 0.85; h = max(6, min(w * 0.16, (y1 - y0) * 0.35)); cx = (x0 + x1) / 2 - w * 0.08
    d.ellipse([cx - w / 2, y1 - 8 - h * 1.0, cx + w / 2, y1 - 8 + h * 0.1], fill=175)
blob = np.asarray(blob.filter(ImageFilter.GaussianBlur(5))) / 255 * (ter[..., 3] > 200) * ((new[..., 3] < 30) | rv)
out *= (1 - blob)[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[9], quality=94); print('ok', sys.argv[9])
