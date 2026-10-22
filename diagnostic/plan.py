# Plan vu du ciel pour la page « Mon projet jardin » : soleil d'été lissé, voisins et hauteurs, vis-à-vis, produits proposés.
# Usage : python3 plan.py dossier_diagnostic sortie.png
import sys, json, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as ndi
D, out = sys.argv[1], sys.argv[2]
import os
AUTO = os.environ.get('PLAN_AUTO') == '1'          # mode automatique : pas de rue supposée ni de produits placés à la main
g = np.load(f'{D}/geo.npz', allow_pickle=True); dg = json.load(open(f'{D}/diagnostic.json'))
pts, ete, par, mai = g['pts'], g['ete'], g['parcelle'], g['maison']
bats, hb, cli = g['bats'], g['hb'], g['client']
F = '/usr/share/fonts/truetype/dejavu/'
font = lambda s, b=False: ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), s)
SS = 3; S = 14 * SS                                     # px par mètre (sur-échantillonné)
x0, y0, x1, y1 = par[:, 0].min() - 13, par[:, 1].min() - 7, par[:, 0].max() + 13, par[:, 1].max() + 3
W, H = int((x1 - x0) * S), int((y1 - y0) * S) + 70 * SS
T = lambda x, y: ((x - x0) * S, (y1 - y) * S)
C = dict(bg=(238, 240, 233), road=(222, 224, 218), nb=(214, 218, 210), nbl=(176, 182, 172), house=(52, 66, 57), parcel=(31, 90, 61),
         ink=(29, 42, 34), muted=(93, 107, 98), fence=(150, 96, 52), perg=(232, 116, 42), red=(196, 52, 40))
im = Image.new('RGB', (W, H), C['bg']); d = ImageDraw.Draw(im)
_txt = ImageDraw.ImageDraw.text
def halo(self, xy, t, **k):
    if k.get('fill') not in ('white',) and 'stroke_width' not in k: k.update(stroke_width=3 * SS, stroke_fill=(255, 255, 255))
    return _txt(self, xy, t, **k)
ImageDraw.ImageDraw.text = halo
# rue au sud de la parcelle
ys = par[:, 1].min()
if not AUTO:
    d.rectangle([0, T(0, ys - 1.2)[1], W, T(0, ys - 6.5)[1]], fill=C['road'])
    d.text((W / 2, T(0, ys - 3.9)[1]), 'RUE', font=font(11 * SS, True), fill=C['muted'], anchor='mm')
# soleil : raster lissé, limité au jardin
grid = np.full((H, W), np.nan, np.float32)
acc = np.zeros((H, W), np.float32); cnt = np.zeros((H, W), np.float32)
for (x, y), h in zip(pts, ete):
    X, Y = T(x, y); X, Y = int(X), int(Y)
    r = int(0.26 * S) + 1
    acc[max(0, Y - r):Y + r, max(0, X - r):X + r] += h; cnt[max(0, Y - r):Y + r, max(0, X - r):X + r] += 1
mask = cnt > 0
val = ndi.gaussian_filter(acc, 0.6 * S) / np.maximum(ndi.gaussian_filter(cnt, 0.6 * S), 1e-6)
stops = [(4, (150, 172, 196)), (7, (196, 210, 200)), (9, (255, 222, 140)), (11, (247, 170, 60)), (13, (232, 116, 42))]
def cm(v):
    v = np.clip(v, stops[0][0], stops[-1][0]); out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (v >= a) & (v <= b); t = ((v - a) / (b - a))[m][:, None]; out[m] = np.array(ca) * (1 - t) + np.array(cb) * t
    return out
pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).polygon([T(*p) for p in par], fill=255)
hm = Image.new('L', (W, H), 0); ImageDraw.Draw(hm).polygon([T(*p) for p in mai], fill=255)
mask = (np.asarray(pm) > 0) & ~(np.asarray(hm) > 0) & (ndi.gaussian_filter(cnt, 0.6 * S) > 0.05)
A = np.asarray(im).astype(np.float32); A[mask] = cm(val[mask]); im = Image.fromarray(A.astype(np.uint8)); d = ImageDraw.Draw(im)
# bâtiments
for b, h, c in zip(bats, hb, cli):
    if c: continue
    P = [T(*p) for p in b]
    if max(p[0] for p in P) < 0 or min(p[0] for p in P) > W or max(p[1] for p in P) < 0 or min(p[1] for p in P) > H: continue
    d.polygon(P, fill=C['nb'], outline=C['nbl'], width=SS)
    cx, cy = np.mean(b[:-1, 0]), np.mean(b[:-1, 1]); X, Y = T(cx, cy)
    if 0 < X < W and 0 < Y < H - 80 * SS: d.text((X, Y), f'{h:.0f} m', font=font(10 * SS), fill=C['muted'], anchor='mm')
d.polygon([T(*p) for p in mai], fill=C['house'])
mc = T(np.mean(mai[:-1, 0]), np.mean(mai[:-1, 1])); d.text(mc, 'Votre\nmaison', font=font(10 * SS, True), fill='white', anchor='mm', align='center')
d.line([T(*p) for p in par], fill=C['parcel'], width=3 * SS, joint='curve')
# vis-à-vis : 2 voisins les plus proches et hauts
for v in [v for v in dg['vis_a_vis'] if v['hauteur_m'] >= 6][:2]:
    cx, cy = v['centre']
    tx = par[:, 0].min() + 1.5 if cx < par[:, 0].mean() else par[:, 0].max() - 1.5
    a, b_ = T(cx, cy), T(tx, cy)
    n = 9
    for k in range(n):
        if k % 2: continue
        p0 = (a[0] + (b_[0] - a[0]) * k / n, a[1]); p1 = (a[0] + (b_[0] - a[0]) * (k + 1) / n, a[1])
        d.line([p0, p1], fill=C['red'], width=2 * SS)
    d.ellipse([a[0] - 5 * SS, a[1] - 5 * SS, a[0] + 5 * SS, a[1] + 5 * SS], fill=C['red'])
    d.text((a[0], a[1] + 9 * SS), "vue depuis l'étage", font=font(9 * SS, True), fill=C['red'], anchor='mt')
if not AUTO:
    # produits proposés (cour avant)
    xs = par[:, 0].min(); yh = mai[:, 1].min()
    fx = xs + 0.35
    d.line([T(fx, yh + 0.3), T(fx, ys + 0.2)], fill=C['fence'], width=5 * SS)
    d.text((T(fx, (yh + ys) / 2)[0] - 8 * SS, T(fx, (yh + ys) / 2)[1]), 'Clôture 1,80 m', font=font(10 * SS, True), fill=C['fence'], anchor='rm')
    px0 = xs + 1.0; py0 = ys + 0.3
    d.rectangle([T(px0, py0 + 3)[0], T(px0, py0 + 3)[1], T(px0 + 3, py0)[0], T(px0 + 3, py0)[1]], fill=(255, 255, 255), outline=C['perg'], width=3 * SS)
    for k in range(1, 10):
        xx = px0 + 3 * k / 10; d.line([T(xx, py0 + 3), T(xx, py0)], fill=C['perg'], width=SS)
    d.text((T(px0 + 3, py0 + 1.5)[0] + 8 * SS, T(px0 + 3, py0 + 1.5)[1]), 'Pergola\n3 x 3 m', font=font(10 * SS, True), fill=C['perg'], anchor='lm')
# étiquette jardin arrière
if AUTO:   # étiquette au point du jardin le plus loin de la maison
    from shapely.geometry import Polygon as _P, Point as _Pt
    mp = _P(mai); pp = _P(par); ok = [q for q in pts if pp.exterior.distance(_Pt(q)) > 2.5] or list(pts)
    far = max(ok, key=lambda q: min(mp.distance(_Pt(q)), 12) - 0.3 * abs(mp.distance(_Pt(q)) - 12)); h = float(np.mean(ete))
    d.text(T(*far), f'Votre jardin\n{h:.0f} h de soleil en juin'.replace('.', ','), font=font(11 * SS, True), fill=C['ink'], anchor='mm', align='center')
else:
    jy = (mai[:, 1].max() + par[:, 1].max()) / 2
    d.text(T(par[:, 0].mean(), jy), 'Jardin arrière\nplein soleil', font=font(12 * SS, True), fill=C['ink'], anchor='mm', align='center')
# nord + échelle
nx, ny = W - 26 * SS, 30 * SS
d.polygon([(nx, ny - 16 * SS), (nx - 8 * SS, ny + 8 * SS), (nx, ny + 3 * SS), (nx + 8 * SS, ny + 8 * SS)], fill=C['ink'])
d.text((nx, ny + 12 * SS), 'N', font=font(11 * SS, True), fill=C['ink'], anchor='mt')
by = H - 52 * SS; bx = 16 * SS
d.rectangle([bx, by, bx + 5 * S, by + 4 * SS], fill=C['ink']); d.text((bx + 5 * S + 6 * SS, by + 2 * SS), '5 m', font=font(10 * SS), fill=C['ink'], anchor='lm')
# légende soleil
ly = H - 26 * SS; lw = W - 32 * SS
for k in range(lw):
    v = 4 + 9 * k / lw; d.line([(bx + k, ly), (bx + k, ly + 8 * SS)], fill=tuple(int(c) for c in cm(np.array([v]))[0]))
d.text((bx, ly + 11 * SS), '4 h', font=font(9 * SS), fill=C['muted'], anchor='lt')
d.text((bx + lw, ly + 11 * SS), '13 h de soleil le 21 juin', font=font(9 * SS), fill=C['muted'], anchor='rt')
im = im.resize((W // SS, H // SS), Image.LANCZOS); im.save(out); print('ok', im.size)
