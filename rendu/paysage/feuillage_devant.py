# Dans une zone où la végétation peut passer devant un produit : on ne garde de l'IA que le feuillage,
# le produit exact (image de base) reste partout ailleurs.
# Usage : python3 feuillage_devant.py ia.jpg base.jpg zones.json calque_produits.png sortie.jpg
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi
ia = Image.open(sys.argv[1]).convert('RGB'); W, H = ia.size; base = Image.open(sys.argv[2]).convert('RGB').resize((W, H))
z = Image.new('L', (W, H), 0); d = ImageDraw.Draw(z)
for p in json.load(open(sys.argv[3])): d.polygon([tuple(q) for q in p], fill=255)
z = np.asarray(z) > 0
prod = np.asarray(Image.open(sys.argv[4]).convert('RGBA').resize((W, H)).getchannel('A')) > 160
A, B = np.asarray(ia).astype(float), np.asarray(base).astype(float)
hsv = np.asarray(ia.convert('HSV')).astype(float); h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
bois = (h > 15) & (h < 48) & (s > 0.3) & (v > 0.35)                      # plancher bois
diff = np.abs(A - B).mean(2) > 35
feuille = z & prod & diff & ~bois
feuille = ndi.binary_opening(feuille, iterations=1); feuille = ndi.binary_closing(feuille, iterations=2)
lab, n = ndi.label(feuille); t = ndi.sum(feuille, lab, range(1, n + 1)); feuille = np.isin(lab, 1 + np.where(t > 150)[0])
keep_base = z & prod & ~feuille
M = np.asarray(Image.fromarray((keep_base * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8))).astype(float)[..., None] / 255
out = A * (1 - M) + B * M
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[5], quality=94); print('ok', int(feuille.sum()), 'px de feuillage gardés devant')
