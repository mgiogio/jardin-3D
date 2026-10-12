# Finition d'un aménagement : ombre de contact sous le bord de la terrasse et sous les potées,
# et raccord de lumière des zones refaites par l'IA sur la lumière de la photo d'origine.
# Usage : python3 finition.py image.jpg calque_terrasse.png photo_ref.jpg zones_ia.json potees.json sortie.jpg
import sys, json, numpy as np, cv2
from PIL import Image, ImageDraw
img = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32); H, W = img.shape[:2]
ter = np.asarray(Image.open(sys.argv[2]).convert('RGBA').resize((W, H)).getchannel('A')) > 160
ref = np.asarray(Image.open(sys.argv[3]).convert('RGB').resize((W, H))).astype(np.uint8)
def poly(f):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for p in json.load(open(f)): d.polygon([tuple(q) for q in p], fill=255)
    return np.asarray(m) > 0
# 1) ombre de contact au sol sous le bord avant de la terrasse (le plancher est posé, pas flottant)
sh = np.zeros((H, W), np.float32)
for x in np.where(ter.any(0))[0]:
    y1 = np.where(ter[:, x])[0].max()
    for d in range(1, 26): 
        if y1 + d < H and not ter[y1 + d, x]: sh[y1 + d, x] = max(sh[y1 + d, x], 0.6 * (1 - d / 26) ** 1.4)
sh = cv2.GaussianBlur(sh, (0, 0), 2)
# 2) ombre d'appui sous chaque potée (ellipse au pied)
pm = Image.new('L', (W, H), 0); dp = ImageDraw.Draw(pm)
for (cx, cy, rx, ry) in json.load(open(sys.argv[5])): dp.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=190)
sh = np.maximum(sh, cv2.GaussianBlur(np.asarray(pm).astype(np.float32) / 255, (0, 0), 9))
out = img * (1 - sh[..., None])
# 3) lumière : les zones IA prennent la moyenne et le contraste (Lab) de la végétation d'origine, à moitié
z = poly(sys.argv[4])
lab = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
lr = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB).astype(np.float32)
veg = np.zeros((H, W), bool); veg[40:420, 300:1150] = True; veg &= ~ter
for c in range(3):
    a, b = lab[..., c][z], lr[..., c][veg]
    t = (lab[..., c] - a.mean()) / (a.std() + 1e-3) * (a.std() * 0.6 + b.std() * 0.4) + (a.mean() * 0.55 + b.mean() * 0.45)
    lab[..., c] = np.where(z, t, lab[..., c])
res = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
M = cv2.GaussianBlur(z.astype(np.float32), (0, 0), 6)[..., None]
out = out * (1 - M) + res * M
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[6], quality=94); print('ok')
