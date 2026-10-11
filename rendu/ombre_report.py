# Reporte les ombres portées des produits (ex. lames de la pergola sur la terrasse) après une retouche IA qui les a effacées.
# Usage : python3 ombre_report.py image.jpg calque_complet.png calque_surface_seule.png sortie.jpg
import sys, numpy as np
from PIL import Image, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
full = np.asarray(Image.open(sys.argv[2]).convert('RGBA').resize((W, H))).astype(float)
surf = np.asarray(Image.open(sys.argv[3]).convert('RGBA').resize((W, H))).astype(float)
m = (surf[..., 3] > 200) & (full[..., 3] > 200)
Lf, Ls = full[..., :3].mean(-1), surf[..., :3].mean(-1)
r = np.ones((H, W)); r[m] = np.clip((Lf[m] + 3) / (Ls[m] + 3), 0.35, 1.0)
r = np.asarray(Image.fromarray((r * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255
out = np.asarray(img).astype(float) * r[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[4], quality=94); print('ok', round(float((r < 0.9).mean()), 3))
