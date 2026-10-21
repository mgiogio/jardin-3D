# Pose la pergola (rendu 3D) : teinte des réalisations, modelé, connecteurs sombres ; ombres des lames et ombres de contact si demandé.
# Usage : python3 perg_pose.py base.jpg perg_a.png perg_b.png sortie.jpg [avec_ombres 0/1]
import sys, subprocess, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
base, fa, fb, out = sys.argv[1:5]; omb = len(sys.argv) > 5 and sys.argv[5] == '1'
R = '/home/claude/jardin-3d/rendu'
p = np.asarray(Image.open(base).convert('RGB')).astype(float)
a = np.asarray(Image.open(fa).convert('RGBA')).astype(float); b = np.asarray(Image.open(fb).convert('RGBA')).astype(float)
H, W = p.shape[:2]; pa = a[..., 3] / 255
o = p.copy()
if omb:
    sh = np.where(pa < 0.05, b[..., 3] / 255, 0)
    lab, n = ndi.label(pa > 0.5); ct = np.zeros((H, W)); yy, xx = np.ogrid[:H, :W]
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if ys.max() - ys.min() < 200 or xs.max() - xs.min() > 200 or ys.max() >= H - 2: continue
        yb, xc, w = ys.max(), xs.mean(), xs.max() - xs.min()
        ct = np.maximum(ct, np.clip(1 - ((xx - xc) / (w * 1.6)) ** 2 - ((yy - yb) / (w * 0.35)) ** 2, 0, 1) * 0.5)
    o = o * (1 - 0.85 * sh[..., None]) * (1 - ndi.gaussian_filter(ct, 3)[..., None])
o = o * (1 - pa[..., None]) + a[..., :3] * pa[..., None]
tmp = out + '.tmp.jpg'; Image.fromarray(np.clip(o, 0, 255).astype('uint8')).save(tmp, quality=95)
subprocess.run(['python3', f'{R}/teinte.py', tmp, tmp, f'{R}/teinte_ref.json', 'soleil', fa, '0.5'], capture_output=True)
im = np.asarray(Image.open(tmp)).astype(float); os.remove(tmp)
rgb = a[..., :3]; sat = (rgb.max(-1) - rgb.min(-1)) / np.maximum(rgb.max(-1), 1)
metal = ndi.binary_opening((pa > 0.5) & (sat < 0.12), iterations=1); m = (pa > 0.5) & ~metal
mu = im.mean(-1)[m].mean(); w = im.copy()
w[m] = mu + (im[m] - mu) * 1.35; w[m] *= np.array([1.04, 0.97, 0.86]); w[metal] = im[metal] * 0.45
k = cv2.GaussianBlur((pa > 0.5).astype(np.float32), (0, 0), 0.8)[..., None]
Image.fromarray(np.clip(im * (1 - k) + w * k, 0, 255).astype('uint8')).save(out, quality=94); print('ok', out)
