# Massifs « de paysagiste » : on prépare le lit de plantation avant l'IA (paillage d'écorce dans les zones), puis on trace
# après l'IA une bordure acier nette là où le massif touche la pelouse.
# Usage :
#   python3 bordures.py preparer image.jpg zones.json exclus.png sortie.jpg      (paillage dans les zones, hors exclus)
#   python3 bordures.py border   image.jpg zones.json exclus.png sortie.jpg      (bordure acier côté pelouse)
import sys, json, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

mode, src, zf, exf, out = sys.argv[1:6]
im = np.asarray(Image.open(src).convert('RGB')).astype(np.float32); H, W = im.shape[:2]
ex = np.asarray(Image.open(exf).convert('RGBA').resize((W, H)).getchannel('A')) > 120 if exf != '-' else np.zeros((H, W), bool)
polys = [[tuple(p) for p in z] for z in json.load(open(zf))]
zm = Image.new('L', (W, H), 0); d = ImageDraw.Draw(zm)
for p in polys: d.polygon(p, fill=255)
zone = (np.asarray(zm) > 0) & ~ex
hsv = cv2.cvtColor(np.clip(im, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
pelouse = (hsv[..., 0] > 28) & (hsv[..., 0] < 90) & (hsv[..., 1] > 50) & (hsv[..., 2] > 50)

if mode == 'preparer':
    # paillage d'écorce : grain plus fin au loin, plus gros devant ; garde la lumière locale de la photo
    rng = np.random.default_rng(3); paillage = np.zeros((H, W, 3), np.float32)
    lum = cv2.GaussianBlur(im.mean(2), (0, 0), 25) / 128
    for y0 in range(0, H, 16):
        k = 1.5 + 6 * (y0 / H)                                # taille du grain selon la profondeur
        bande = rng.normal(0, 1, (16 + 8, W)); bande = ndi.gaussian_filter(bande, k * 0.6)
        bande = (bande - bande.mean()) / (bande.std() + 1e-6)
        b = bande[:min(16, H - y0)]
        base = np.array([92, 62, 40], np.float32)             # écorce brun moyen
        paillage[y0:y0 + b.shape[0]] = base + b[..., None] * np.array([26, 20, 15])
    paillage *= np.clip(lum, 0.5, 1.4)[..., None]
    m = cv2.GaussianBlur(zone.astype(np.float32), (0, 0), 1.5)[..., None]
    res = im * (1 - m) + paillage * m
else:
    # bordure : là où le massif réellement planté (non-pelouse dans la zone) touche la pelouse
    res = im.copy()
    # pelouse = grandes plages vertes seulement (les feuilles des massifs ne comptent pas)
    pl_ = ndi.binary_opening(pelouse, iterations=4)
    lab_, n_ = ndi.label(pl_); t_ = ndi.sum(pl_, lab_, range(1, n_ + 1))
    pelouse = np.isin(lab_, 1 + np.where(t_ > 0.01 * W * H)[0]) if n_ else pl_
    zl = ndi.binary_dilation(zone, iterations=10)
    lit = zl & ~pelouse
    lit = ndi.binary_opening(lit, iterations=2); lit = ndi.binary_closing(lit, iterations=12); lit = ndi.binary_fill_holes(lit)
    lab, n = ndi.label(lit); t = ndi.sum(lit, lab, range(1, n + 1)); lit = np.isin(lab, 1 + np.where(t > 0.002 * W * H)[0])
    # contour lissé du lit, côté pelouse seulement
    lit_l = cv2.GaussianBlur(lit.astype(np.float32), (0, 0), max(6, W / 250)) > 0.5
    bord = lit_l & ~ndi.binary_erosion(lit_l, iterations=1)
    voisin_pelouse = ndi.binary_dilation(pelouse & ~lit_l & ~ex, iterations=3)
    bord &= voisin_pelouse & ~ex
    for y, x in zip(*np.nonzero(bord)):
        ep = max(1, int(round(1 + 4 * y / H)))
        y1 = min(H, y + ep)
        res[y:y1, x] = res[y:y1, x] * 0.25 + np.array([38, 34, 30]) * 0.75
        if y1 < H: res[y1:min(H, y1 + ep), x] *= 0.85
        if y > 0: res[y - 1, x] = res[y - 1, x] * 0.65 + np.array([120, 110, 100]) * 0.35
    res = cv2.GaussianBlur(res, (0, 0), 0.5) * 0.5 + res * 0.5
Image.fromarray(np.clip(res, 0, 255).astype('uint8')).save(out, quality=94); print('ok', mode)
