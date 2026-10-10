# Carte de profondeur pour la passe lumière : profondeur estimée de la photo (Depth Anything V2),
# remplacée sur le produit par la profondeur exacte de la 3D (lames, poteaux, connecteurs nets), recalée sur la photo.
# Usage : python3 profondeur.py image.jpg depth3d.png sortie.png
import sys, numpy as np, torch
from PIL import Image, ImageFilter
from transformers import pipeline
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
pipe = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Base-hf', device='cpu')
da = np.asarray(pipe(img)['predicted_depth'].squeeze().numpy(), float)
da = np.asarray(Image.fromarray(da.astype('float32')).resize((W, H), Image.BICUBIC), float)   # disparité relative (proche = grand)
a = np.asarray(Image.open(sys.argv[2]).convert('RGBA').resize((W, H), Image.NEAREST)).astype(float) / 255
z = (a[..., 0] + a[..., 1] / 255 + a[..., 2] / 65025) * 100; m = (a[..., 3] > .5) & (z > .1)
out = da.copy()
if m.sum() > 500:
    inv = 1 / z[m]; X = np.stack([inv, np.ones_like(inv)], 1)
    # recalage robuste : disparité photo ≈ a / z + b sur les pixels du produit
    coef = np.linalg.lstsq(X, da[m], rcond=None)[0]
    for _ in range(3):
        r = np.abs(X @ coef - da[m]); k = r < np.percentile(r, 70)
        coef = np.linalg.lstsq(X[k], da[m][k], rcond=None)[0]
    out[m] = X @ coef
    print('recalage', coef.round(3))
lo, hi = np.percentile(out, 1), np.percentile(out, 99.5)
g = np.clip((out - lo) / (hi - lo), 0, 1)
Image.fromarray((g * 255).astype('uint8')).convert('RGB').save(sys.argv[3]); print('ok', sys.argv[3])
