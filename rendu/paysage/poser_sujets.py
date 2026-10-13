# Pose les grands sujets (découpes détourées) à l'échelle exacte, d'après la caméra de la scène 3D.
# Usage : python3 poser_sujets.py image.jpg placements.json cam.json calque_produits.png sortie.jpg [dossier_sujets]
#   placements.json : [{"sujet": "erable_potee", "x": 640, "y": 1210}, ...]  (x, y = point de contact au sol, en px de l'image)
#   cam.json        : {"h": 1.5, "pitch": 16.9, "vfov": 87, "regle": [y_pied, hauteur_px, hauteur_m]} (regle facultative :
#                     un objet de hauteur connue, pergola ou clôture, pour recaler l'échelle quand la caméra est approximative)
import sys, json, math, os, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

ICI = os.path.dirname(os.path.abspath(__file__))
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
pl = json.load(open(sys.argv[2])); cam = json.load(open(sys.argv[3]))
prod = np.asarray(Image.open(sys.argv[4]).convert('RGBA').resize((W, H)).getchannel('A')) > 120
dossier = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != '-' else os.path.join(ICI, 'sujets')
sortie_masque = sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] != '-' else None
APRES_IA = len(sys.argv) > 8 and sys.argv[8] == 'apres_ia'
COUVERT = cam.get('couvert', False)
masque = np.zeros((H, W), np.float32)
SUJ = json.load(open(os.path.join(ICI, 'sujets.json')))
f = (H / 2) / math.tan(math.radians(cam['vfov'] / 2))
def ppm(y):   # pixels par mètre (hauteur) pour un objet posé au sol dont le pied est à la ligne y
    a = math.radians(cam['pitch']) + math.atan((y - H / 2) / f)
    if a <= 0.01: return 1.0
    d = cam['h'] / math.tan(a); return f / (d / math.cos(a))
k = 1.0
if cam.get('regle'):
    yp, hp, hm = cam['regle']; k = hp / (hm * ppm(yp))
base = np.asarray(img).astype(np.float32); out = base.copy()
# profondeur des produits : pour chaque pixel produit, la ligne de son pied (bas du segment vertical continu de produit)
pied = np.full((H, W), -1, np.int32)
for x in range(W):
    col = prod[:, x]
    if not col.any(): continue
    y = H - 1; bas = -1
    while y >= 0:
        if col[y]:
            if bas < 0: bas = y
            pied[y, x] = bas
        else: bas = -1
        y -= 1
for p in sorted(pl, key=lambda q: q['y']):                 # du plus loin au plus proche
    s = Image.open(os.path.join(dossier, p['sujet'] + '.png')).convert('RGBA')
    s = s.crop(s.getchannel('A').point(lambda a: 255 if a > 20 else 0).getbbox())
    hpx = SUJ[p['sujet']]['h'] * ppm(p['y']) * k * p.get('echelle', 1.0)
    wpx = s.width * hpx / s.height
    s = s.resize((max(2, round(wpx)), max(2, round(hpx))), Image.LANCZOS)
    S = np.asarray(s).astype(np.float32); a = S[..., 3:] / 255
    x0, y0 = round(p['x'] - s.width / 2), round(p['y'] - s.height)
    # zone d'image couverte (avec découpage aux bords)
    sx0, sy0 = max(0, -x0), max(0, -y0); X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(W, x0 + s.width), min(H, y0 + s.height)
    if X1 <= X0 or Y1 <= Y0: continue
    Sc = S[sy0:sy0 + (Y1 - Y0), sx0:sx0 + (X1 - X0)]; ac = Sc[..., 3:] / 255
    # lumière : on ramène la moyenne et le contraste du sujet vers ceux de la scène autour (à moitié)
    r = max(40, s.width)
    env = base[max(0, Y0 - r // 2):min(H, Y1 + r // 4), max(0, X0 - r):min(W, X1 + r)].reshape(-1, 3)
    m = ac[..., 0] > 0.5
    if m.any():
        sm, ss = Sc[..., :3][m].mean(0), Sc[..., :3][m].std(0) + 1
        em, es = env.mean(0), env.std(0) + 1
        g = (0.35 + 0.65 * em.mean() / max(sm.mean(), 1))         # luminosité de la scène autour
        Sc[..., :3] = Sc[..., :3] * g
        ls = Sc[..., :3].mean(-1, keepdims=True)
        sat_s = (Sc[..., :3][m].std(-1)).mean() + 1; sat_e = env.std(-1).mean() + 1
        Sc[..., :3] = ls + (Sc[..., :3] - ls) * min(1.0, 0.55 + 0.45 * sat_e / sat_s)   # pas plus saturé que la scène
        if COUVERT:   # ciel couvert : moins de contraste et de saturation, comme la photo
            mu = Sc[..., :3][m].mean(); Sc[..., :3] = mu + (Sc[..., :3] - mu) * 0.8
            ls = Sc[..., :3].mean(-1, keepdims=True); Sc[..., :3] = ls + (Sc[..., :3] - ls) * 0.75
        for c_ in range(3): Sc[..., c_] = ndi.gaussian_filter(Sc[..., c_], 0.6)
    # ombres : ombre de contact (ellipse au pied) et ombre portée douce vers l'arrière gauche
    sh = np.zeros((H, W), np.float32)
    yy, xx = np.ogrid[:H, :W]
    rx, ry = s.width * 0.45, max(4, s.width * 0.12)
    sh = np.maximum(sh, np.clip(1 - ((xx - p['x']) / rx) ** 2 - ((yy - p['y'] + ry * 0.3) / ry) ** 2, 0, 1) * 0.55)
    sil = np.zeros((H, W), np.float32); sil[Y0:Y1, X0:X1] = ac[..., 0]
    # projection de la silhouette sur le sol : écrasée (x0,18) et cisaillée vers la gauche (soleil avant droit)
    gy = p['y']; e, cc = 0.18, 0.35 / 0.18
    proj = np.asarray(Image.fromarray((sil * 255).astype('uint8')).transform((W, H), Image.AFFINE,
            (1, -cc, cc * gy, 0, 1 / e, gy * (1 - 1 / e)), resample=Image.BILINEAR)).astype(np.float32) / 255
    proj[:max(0, int(gy - (Y1 - Y0) * e) - 2)] = 0; proj[int(gy) + 3:] = 0
    proj = ndi.gaussian_filter(proj, max(2, s.width * (0.08 if COUVERT else 0.03))) * (0.18 if COUVERT else 0.45)
    sh = np.clip(np.maximum(sh, proj), 0, 0.6)
    sh = ndi.gaussian_filter(sh, 2) * (1 - sil)
    out *= (1 - sh[..., None])
    ac = ndi.gaussian_filter(ac[..., 0], 0.7)[..., None]            # bord adouci (pas de détourage au cutter)
    if APRES_IA:   # le bas du pot appartient à la passe IA (plantes devant) : on ne recolle que le haut
        pass
    out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - ac) + Sc[..., :3] * ac
    # produits plus proches que le sujet (leur pied est plus bas dans l'image) : ils repassent devant
    mz = np.zeros((H, W), np.float32); mz[Y0:Y1, X0:X1] = ac[..., 0]
    masque = np.maximum(masque, ndi.binary_dilation(mz > 0.3, iterations=6).astype(np.float32))   # sujet entier protégé, avec une marge
    devant = (pied > p['y'] + 12)
    out[devant] = base[devant]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[5], quality=94)
if sortie_masque:
    o = Image.new('RGBA', (W, H), (0, 0, 0, 0)); o.putalpha(Image.fromarray(((masque > 0.4) * 255).astype('uint8'))); o.save(sortie_masque)
print('ok', len(pl), 'sujets posés')
