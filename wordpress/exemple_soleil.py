# Image d'exemple de la page d'entrée « Diagnostic jardin » : le vrai calcul de soleil (21 juin) d'un jardin, épuré
# (parcelle et maison seules, sans voisins ni textes), tourné et retourné :
# l'adresse n'est pas reconnaissable. Les annotations sont posées en HTML par service/lp.py.
# Exemple publié : un pavillon de l'Hérault (242 m² de jardin), calculé par diagnostic/diag.py.
# Usage : python3 wordpress/exemple_soleil.py dossier_diag/geo.npz sortie.webp
import sys, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import Polygon

g = np.load(sys.argv[1], allow_pickle=True); out = sys.argv[2]
pts, ete, par, mai = g['pts'].astype(float), g['ete'].astype(float), g['parcelle'].astype(float), g['maison'].astype(float)
# rotation : grand côté de la parcelle à l'horizontale, le nord à gauche (ombre de la maison à gauche, jardin au soleil à droite),
# puis miroir nord-sud de l'image : la forme ne se superpose plus au cadastre
r = list(Polygon(par).minimum_rotated_rectangle.exterior.coords)
a, b, c = np.array(r[0]), np.array(r[1]), np.array(r[2])
v = (b - a) if np.linalg.norm(b - a) > np.linalg.norm(c - b) else (c - b)
if v[1] < 0: v = -v
th = math.pi - math.atan2(v[1], v[0])
R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
tr = lambda P: (P @ R.T) * np.array([1, -1])
pts, par, mai = tr(pts), tr(par), tr(mai)
S = 24; M = 0.6                                                  # px par mètre, marge en mètres
x0, y0, x1, y1 = par[:, 0].min() - M, par[:, 1].min() - M, par[:, 0].max() + M, par[:, 1].max() + M
W, H = int((x1 - x0) * S), int((y1 - y0) * S)
T = lambda x, y: ((x - x0) * S, (y1 - y) * S)
acc = np.zeros((H, W), np.float32); cnt = np.zeros((H, W), np.float32)
for (x, y), h in zip(pts, ete):
    X, Y = map(int, T(x, y)); k = int(0.26 * S) + 1
    acc[max(0, Y - k):Y + k, max(0, X - k):X + k] += h; cnt[max(0, Y - k):Y + k, max(0, X - k):X + k] += 1
gc = ndi.gaussian_filter(cnt, 0.9 * S)
val = ndi.gaussian_filter(acc, 0.9 * S) / np.maximum(gc, 1e-6)
stops = [(4, (150, 172, 196)), (7, (196, 210, 200)), (9, (255, 222, 140)), (11, (247, 170, 60)), (13, (232, 116, 42))]
def cm(v):
    v = np.clip(v, stops[0][0], stops[-1][0]); o = np.zeros(v.shape + (3,), np.float32)
    for (a_, ca), (b_, cb) in zip(stops, stops[1:]):
        m = (v >= a_) & (v <= b_); t = ((v - a_) / (b_ - a_))[m][:, None]; o[m] = np.array(ca) * (1 - t) + np.array(cb) * t
    return o
pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).polygon([T(*p) for p in par], fill=255)
A = np.zeros((H, W, 4), np.uint8)
m = (np.asarray(pm) > 0) & (gc > 0.02)
A[m, :3] = cm(val[m]).astype(np.uint8); A[m, 3] = 255
im = Image.fromarray(A, 'RGBA'); d = ImageDraw.Draw(im)
mp = Polygon(mai).buffer(0).intersection(Polygon(par).buffer(0))            # maison limitée à la parcelle (mur mitoyen)
for gm in getattr(mp, 'geoms', [mp]):
    if gm.geom_type == 'Polygon': d.polygon([T(*p) for p in gm.exterior.coords], fill=(52, 66, 57, 255))
d.line([T(*p) for p in par] + [T(*par[0])], fill=(31, 90, 61, 255), width=4, joint='curve')
im.save(out, 'WEBP', quality=88, method=6)
# positions utiles pour les annotations (en % de l'image) : coin le plus ombragé et coin le plus ensoleillé du jardin
q = np.array([T(x, y) for x, y in pts]); ins = ~np.array([Polygon(mai).buffer(0.8).contains(Polygon([(x, y), (x + .01, y), (x, y + .01)])) for x, y in pts])
pc = lambda i: (round(100 * q[i][0] / W, 1), round(100 * q[i][1] / H, 1))
ok = np.where(ins)[0]
print(out, W, H, 'ombre', pc(ok[np.argmin(ete[ok])]), 'soleil', pc(ok[np.argmax(ete[ok])]),
      'maison', tuple(round(100 * z / n, 1) for z, n in zip(T(*mp.centroid.coords[0]), (W, H))))
