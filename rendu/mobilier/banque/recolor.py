# Recolore tout l'objet (métal laqué uni) par la couleur cible en gardant la luminance.
import sys, numpy as np, colorsys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); a = np.asarray(im).astype(float) / 255
c = [int(sys.argv[3][i:i+2], 16) / 255 for i in (1, 3, 5)]
hsv = np.asarray(im.convert('HSV')).astype(float) / 255
L = a.mean(2, keepdims=True); m = np.ones_like(L, bool); L = np.clip(L, 0.18, None) ** 0.6  # tout l'objet est du métal laqué ; ombres cuites adoucies
lc = np.mean(c); ref = np.median(L[m[..., 0]]) if m.any() else 0.5
new = np.clip(np.array(c) * np.clip(L / ref, 0.45, 1.12), 0, 1)
out = np.where(m, new, a)
Image.fromarray((out * 255).astype('uint8')).save(sys.argv[2])
