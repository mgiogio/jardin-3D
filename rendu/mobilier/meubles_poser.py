# Pose le mobilier 3D (calque à part) sur l'image : couleurs d'origine des modèles, accordées à la lumière de la photo.
# Usage : python3 meubles_poser.py image.jpg calque_meubles.png sortie.jpg
import sys, numpy as np
from PIL import Image, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
lay = Image.open(sys.argv[2]).convert('RGBA').resize((W, H), Image.LANCZOS)
A = np.asarray(lay).astype(float); I = np.asarray(img).astype(float); al = A[..., 3:] / 255
m = al[..., 0] > 0.5
ring = np.asarray(Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MaxFilter(41))) > 0
ring &= ~m
if m.any() and ring.any():
    gain = np.clip(I[ring].mean(0) / np.maximum(A[..., :3][m].mean(0), 1), 0.75, 1.25) ** 0.5   # même dominante que la scène
    A[..., :3] = np.clip(A[..., :3] * gain, 0, 255)
lay = Image.fromarray(A.astype('uint8'), 'RGBA').filter(ImageFilter.GaussianBlur(0.5))
# ombre de contact : silhouette floutée, décalée vers le bas, plus dense au pied des meubles
k = max(3, W // 180); sil = Image.fromarray((m * 255).astype('uint8'))
pied = np.zeros_like(m); ys, xs = np.nonzero(m)
if len(ys):
    col_bas = {}
    for y, x in zip(ys, xs): col_bas[x] = max(col_bas.get(x, 0), y)
    for x, y in col_bas.items(): pied[max(0, y - k):y + 1, x] = True
sh = (np.asarray(sil.filter(ImageFilter.GaussianBlur(k * 2))) / 255 * 0.35 + np.asarray(Image.fromarray((pied * 255).astype('uint8')).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(k))) / 255 * 0.6)
sh = np.roll(sh, k // 2, axis=0); sh = np.clip(sh, 0, 0.55)[..., None]
I = I * (1 - sh); img = Image.fromarray(np.clip(I, 0, 255).astype('uint8'))
out = img.convert('RGBA'); out.alpha_composite(lay); out.convert('RGB').save(sys.argv[3], quality=94); print('ok')
