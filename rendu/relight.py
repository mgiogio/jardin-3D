# Lumière sans retouche de la scène : on ne prend à la passe IA que sa lumière (basses fréquences),
# appliquée à la photo fidèle (maison, extension, produits 3D intacts). Usage :
# python3 relight.py fidele_crop.jpg ia_lumiere.jpg sortie.jpg [rayon] [force]
import sys, numpy as np
from PIL import Image, ImageFilter
f = Image.open(sys.argv[1]).convert('RGB'); ia = Image.open(sys.argv[2]).convert('RGB').resize(f.size, Image.LANCZOS)
r = float(sys.argv[4]) if len(sys.argv) > 4 else f.size[0] * 0.02; k = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
bf = np.asarray(f.filter(ImageFilter.GaussianBlur(r))).astype(float) + 4
bi = np.asarray(ia.filter(ImageFilter.GaussianBlur(r))).astype(float) + 4
ratio = np.clip(bi / bf, 0.6, 1.6) ** k
out = np.clip(np.asarray(f).astype(float) * ratio, 0, 255)
Image.fromarray(out.astype('uint8')).save(sys.argv[3], quality=94)
