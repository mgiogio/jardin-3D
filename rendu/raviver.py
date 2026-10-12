# Photo client délavée (tirage scanné, contre-jour, voile) : niveaux et couleurs remis d'aplomb AVANT tout le reste,
# pour que les zones retouchées par l'IA (nettes, saturées) ne tranchent pas avec le reste de la photo.
# Usage : python3 raviver.py photo.jpg sortie.jpg [force=1.0]
import sys, numpy as np
from PIL import Image, ImageEnhance
im = Image.open(sys.argv[1]).convert('RGB'); k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
a = np.asarray(im).astype(float)
lo, hi = np.percentile(a.mean(-1), 0.7), np.percentile(a.mean(-1), 99.5)
b = np.clip((a - lo) / max(hi - lo, 1) * 255, 0, 255)
b = 255 * (b / 255) ** 1.08                                  # léger contraste dans les tons moyens
out = Image.fromarray((a * (1 - k) + b * k).astype('uint8'))
out = ImageEnhance.Color(out).enhance(1 + 0.25 * k)
out.save(sys.argv[2], quality=95); print('niveaux', round(lo), round(hi))
