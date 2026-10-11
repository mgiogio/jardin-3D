# Bas de clôture repris de l'image IA (plantes + lames redessinées autour d'elles = occlusion cohérente), clôture
# exacte au-dessus, fondu vertical court. Les lames de l'IA sont recalées en couleur sur la clôture exacte juste
# au-dessus du raccord. À n'utiliser que sur une clôture où les plantes passent vraiment devant.
# Usage : python3 bande_rampe.py base.jpg ia.jpg cloture.png sortie.jpg [part=0.35] [fondu=0.06] [dessous=0.25]
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
B = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float); H, W = B.shape[:2]
G = np.asarray(Image.open(sys.argv[2]).convert('RGB').resize((W, H), Image.LANCZOS)).astype(float)
part = float(sys.argv[5]) if len(sys.argv) > 5 else 0.35; fondu = float(sys.argv[6]) if len(sys.argv) > 6 else 0.06
dess = float(sys.argv[7]) if len(sys.argv) > 7 else 0.25
m = np.asarray(Image.open(sys.argv[3]).convert('RGBA').resize((W, H)).getchannel('A')) > 128
w = np.zeros((H, W)); raccord = np.zeros((H, W), bool); yy = np.arange(H)
for x in np.where(m.any(0))[0]:
    ys = np.where(m[:, x])[0]; y0, y1 = ys.min(), ys.max(); h = y1 - y0
    top = y1 - h * part; f = max(h * fondu, 3)
    col = np.clip((yy - top) / f, 0, 1); col[yy < y0] = 0
    n = int(h * dess); bas = yy > y1; col[bas] = np.clip(1 - (yy[bas] - y1) / max(n, 1), 0, 1) ** 0.6
    w[:, x] = col
    raccord[int(top - h * 0.12):int(top), x] = True
w = ndi.gaussian_filter(w, (0, 2))
# recalage couleur des lames de l'IA sur la clôture exacte (bande juste au-dessus du raccord, sur la clôture)
import colorsys
Gi = Image.fromarray(np.clip(G, 0, 255).astype('uint8')).convert('HSV'); hv = np.asarray(Gi).astype(float)
hue, sat = hv[..., 0] * 360 / 255, hv[..., 1] / 255
bois = (hue > 12) & (hue < 48) & (sat > 0.15) & (sat < 0.75)        # seules les lames sont recalées, pas les plantes
z = raccord & m & bois
for c in (range(3) if __import__("os").environ.get("RECALE") else []):
    mb, sb = B[..., c][z].mean(), B[..., c][z].std() + 1e-6; mg, sg = G[..., c][z].mean(), G[..., c][z].std() + 1e-6
    k = (w > 0) & bois & m
    G[..., c][k] = (G[..., c][k] - mg) * (sb / sg) + mb
out = B * (1 - w[..., None]) + G * w[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[4], quality=93); print('ok')
