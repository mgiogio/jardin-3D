# Plan vu du ciel pour la page « Mon projet jardin » : soleil d'été lissé, voisins et hauteurs, vis-à-vis, produits proposés.
# Usage : python3 plan.py dossier_diagnostic sortie.png
import sys, json, math, io, urllib.request, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
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
# taille des textes et repères proportionnelle à la largeur du plan : il s'affiche sur environ 700 px de large dans la page,
# quelle que soit la taille du terrain ; sans ça, un grand terrain donne des textes minuscules
K = max(1.0, (x1 - x0) * S * 2 / SS / 900); U = SS * K        # U : unité de taille des textes et repères
W, H = int((x1 - x0) * S), int((y1 - y0) * S) + int(70 * U)
T = lambda x, y: ((x - x0) * S, (y1 - y) * S)
C = dict(bg=(238, 240, 233), road=(222, 224, 218), nb=(214, 218, 210), nbl=(176, 182, 172), house=(52, 66, 57), parcel=(31, 90, 61),
         ink=(29, 42, 34), muted=(93, 107, 98), fence=(150, 96, 52), perg=(232, 116, 42), red=(196, 52, 40))
im = Image.new('RGB', (W, H), C['bg'])
# photo aérienne IGN (licence ouverte) sous le plan : on reconnaît son jardin, le plan est posé dessus en transparence
AERIEN = False
if os.environ.get('PLAN_LAT') and os.environ.get('PLAN_LON'):
    try:
        la0, lo0 = float(os.environ['PLAN_LAT']), float(os.environ['PLAN_LON'])
        kx, ky = 111320 * math.cos(math.radians(la0)), 110540
        hc = int((y1 - y0) * S)                                   # hauteur de la carte, sans la bande de légende
        wq = min(2048, W * 2 // SS); hq = max(1, round(wq * hc / W))
        bb = f'{la0 + y0 / ky:.7f},{lo0 + x0 / kx:.7f},{la0 + y1 / ky:.7f},{lo0 + x1 / kx:.7f}'
        u = ('https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS&STYLES=&CRS=EPSG:4326'
             f'&FORMAT=image/jpeg&WIDTH={wq}&HEIGHT={hq}&BBOX={bb}')
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'CoverGreen-Diagnostic/1.0'}), timeout=30) as r:
            ph = Image.open(io.BytesIO(r.read())).convert('RGB')
        ph = ImageEnhance.Color(ph).enhance(0.8)
        ph = Image.blend(ph, Image.new('RGB', ph.size, (255, 255, 255)), 0.12).resize((W, hc), Image.LANCZOS)
        im.paste(ph, (0, 0)); AERIEN = True
    except Exception as e:
        print('photo aérienne indisponible :', e, file=sys.stderr)
d = ImageDraw.Draw(im)
_txt = ImageDraw.ImageDraw.text
def halo(self, xy, t, *a, **k):
    if not a and k.get('fill') not in ('white',) and 'stroke_width' not in k: k.update(stroke_width=int(3 * U), stroke_fill=(255, 255, 255))
    return _txt(self, xy, t, *a, **k)
ImageDraw.ImageDraw.text = halo
# rue au sud de la parcelle
ys = par[:, 1].min()
if not AUTO:
    d.rectangle([0, T(0, ys - 1.2)[1], W, T(0, ys - 6.5)[1]], fill=C['road'])
    d.text((W / 2, T(0, ys - 3.9)[1]), 'RUE', font=font(int(11 * U), True), fill=C['muted'], anchor='mm')
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
A = np.asarray(im).astype(np.float32)
OP = 0.6 if AERIEN else 1.0                                       # sur la photo aérienne, le soleil est en transparence
A[mask] = A[mask] * (1 - OP) + cm(val[mask]) * OP; im = Image.fromarray(A.astype(np.uint8)); d = ImageDraw.Draw(im)
# bâtiments (sur la photo aérienne : contours blancs et voile léger, pour garder les toits visibles)
_ovi = Image.new('RGBA', (W, H), (0, 0, 0, 0)); _ov = ImageDraw.Draw(_ovi); _etiq = []
for b, h, c in zip(bats, hb, cli):
    if c: continue
    P = [T(*p) for p in b]
    if max(p[0] for p in P) < 0 or min(p[0] for p in P) > W or max(p[1] for p in P) < 0 or min(p[1] for p in P) > H: continue
    if AERIEN: _ov.polygon(P, fill=(255, 255, 255, 70), outline=(255, 255, 255, 235), width=2 * SS)
    else: d.polygon(P, fill=C['nb'], outline=C['nbl'], width=SS)
    cx, cy = np.mean(b[:-1, 0]), np.mean(b[:-1, 1]); X, Y = T(cx, cy)
    # hauteur écrite seulement si elle tient dans le bâtiment (sinon les étiquettes se chevauchent)
    if 0 < X < W and 0 < Y < H - 80 * U and (max(p[0] for p in P) - min(p[0] for p in P)) > 2.2 * 10 * U: _etiq.append(((X, Y), f'{h:.0f} m'))
if AERIEN:
    _ov.polygon([T(*p) for p in mai], fill=C['house'] + (215,))
    im = Image.alpha_composite(im.convert('RGBA'), _ovi).convert('RGB'); d = ImageDraw.Draw(im)
else: d.polygon([T(*p) for p in mai], fill=C['house'])
VAV = [v for v in dg['vis_a_vis'] if v.get('oeil_m', 0) >= (3 if 'denivele_m' in v else 4.5)][:2]     # voisins qui ont vue, marqués en rouge plus bas
_pv = [T(*v['centre']) for v in VAV]
for xy, t in _etiq:
    if any(math.hypot(xy[0] - q[0], xy[1] - q[1]) < 40 * U for q in _pv): continue     # le repère rouge dit déjà tout sur ce voisin
    f_ = font(int(10 * U), AERIEN); tw = d.textlength(t, font=f_)
    if xy[0] - tw / 2 < 4 * U or xy[0] + tw / 2 > W - 4 * U or xy[1] < 10 * U: continue      # étiquette coupée par le bord : on ne l'écrit pas
    d.text(xy, t, font=f_, fill=C['ink'] if AERIEN else C['muted'], anchor='mm')
mc = T(np.mean(mai[:-1, 0]), np.mean(mai[:-1, 1])); d.text(mc, 'Votre\nmaison', font=font(int(10 * U), True), fill='white', anchor='mm', align='center')
if AERIEN:   # limite du terrain : liseré blanc puis vert Cover Green, lisible sur la photo
    d.line([T(*p) for p in par], fill=(255, 255, 255), width=6 * SS, joint='curve'); d.line([T(*p) for p in par], fill=(4, 158, 0), width=3 * SS, joint='curve')
else: d.line([T(*p) for p in par], fill=C['parcel'], width=3 * SS, joint='curve')
# bande de légende du bas : fond uni, sans bout de toit ni de photo qui dépasse
d.rectangle([0, int((y1 - y0) * S), W, H], fill=C['bg'])
# vis-à-vis : 2 voisins les plus proches et hauts
for v in VAV:
    cx, cy = v['centre']
    tx = par[:, 0].min() + 1.5 if cx < par[:, 0].mean() else par[:, 0].max() - 1.5
    a, b_ = T(cx, cy), T(tx, cy)
    n = 9
    for k in range(n):
        if k % 2: continue
        p0 = (a[0] + (b_[0] - a[0]) * k / n, a[1]); p1 = (a[0] + (b_[0] - a[0]) * (k + 1) / n, a[1])
        d.line([p0, p1], fill=C['red'], width=int(2 * U))
    d.ellipse([a[0] - 5 * U, a[1] - 5 * U, a[0] + 5 * U, a[1] + 5 * U], fill=C['red'])
    d.text((a[0], a[1] + 9 * U), "vue depuis l'étage", font=font(int(10 * U), True), fill=C['red'], anchor='mt')
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
    d.text(T(*far), f'Votre jardin\n{h:.0f} h de soleil en juin'.replace('.', ','), font=font(int(12 * U), True), fill=C['ink'], anchor='mm', align='center')
else:
    jy = (mai[:, 1].max() + par[:, 1].max()) / 2
    d.text(T(par[:, 0].mean(), jy), 'Jardin arrière\nplein soleil', font=font(12 * SS, True), fill=C['ink'], anchor='mm', align='center')
# nord + échelle
nx, ny = W - 26 * U, 30 * U
if AERIEN: d.ellipse([nx - 20 * U, ny - 22 * U, nx + 20 * U, ny + 30 * U], fill=(255, 255, 255))
d.polygon([(nx, ny - 16 * U), (nx - 8 * U, ny + 8 * U), (nx, ny + 3 * U), (nx + 8 * U, ny + 8 * U)], fill=C['ink'])
d.text((nx, ny + 12 * U), 'N', font=font(int(11 * U), True), fill=C['ink'], anchor='mt')
by = H - 52 * U; bx = 16 * U
d.rectangle([bx, by, bx + 5 * S, by + 4 * U], fill=C['ink']); d.text((bx + 5 * S + 6 * U, by + 2 * U), '5 m', font=font(int(10 * U)), fill=C['ink'], anchor='lm')
# légende soleil
ly = H - 26 * U; lw = int(W - 32 * U)
for k in range(lw):
    v = 4 + 9 * k / lw; d.line([(bx + k, ly), (bx + k, ly + 8 * U)], fill=tuple(int(c) for c in cm(np.array([v]))[0]))
d.text((bx, ly + 11 * U), '4 h', font=font(int(10 * U)), fill=C['muted'], anchor='lt')
d.text((bx + lw, ly + 11 * U), '13 h de soleil le 21 juin', font=font(int(10 * U)), fill=C['muted'], anchor='rt')
im = im.resize((W * 2 // SS, H * 2 // SS), Image.LANCZOS); im.save(out, optimize=True)   # 2x pour les écrans haute définition
print('aerien' if AERIEN else 'plat')              # lu par le service : la légende de la page en dépend
