# Masque de la végétation existante du client (massifs, arbustes, paillage, haies) : on la garde et on la complète, jamais repeinte.
# Usage : python3 vegetation_existante.py photo.jpg calque_produits.png sortie.png
import sys, numpy as np, torch
from PIL import Image
from scipy import ndimage as ndi
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
prod = np.asarray(Image.open(sys.argv[2]).convert('RGBA').resize((W, H)).getchannel('A')) > 120
P = CLIPSegProcessor.from_pretrained('CIDAS/clipseg-rd64-refined'); M = CLIPSegForImageSegmentation.from_pretrained('CIDAS/clipseg-rd64-refined')
EXIST = ['flower bed', 'shrub', 'bark mulch', 'lavender', 'hydrangea', 'ornamental grass clump', 'hedge', 'tree']
AUTRE = ['mown lawn grass', 'paving stones', 'sky', 'house wall', 'wooden fence']
T = 520; pe = np.zeros((H, W), np.float32); pa = np.zeros((H, W), np.float32)
for ty in range(0, H, T - 80):
    for tx in range(0, W, T - 80):
        b = (tx, ty, min(W, tx + T), min(H, ty + T)); c = im.crop(b); tx_ = EXIST + AUTRE
        inp = P(text=tx_, images=[c] * len(tx_), return_tensors='pt', padding=True)
        with torch.no_grad(): lg = torch.sigmoid(M(**inp).logits).numpy()
        rs = lambda a: np.asarray(Image.fromarray((a * 255).astype('uint8')).resize(c.size, Image.BILINEAR)) / 255
        e = rs(lg[:len(EXIST)].max(0)); o = rs(lg[len(EXIST):].max(0))
        pe[b[1]:b[3], b[0]:b[2]] = np.maximum(pe[b[1]:b[3], b[0]:b[2]], e); pa[b[1]:b[3], b[0]:b[2]] = np.maximum(pa[b[1]:b[3], b[0]:b[2]], o)
m = (pe > 0.35) & (pe > pa) & ~prod
m = ndi.binary_opening(m, iterations=2); m = ndi.binary_dilation(m, iterations=6)
lab, n = ndi.label(m); t = ndi.sum(m, lab, range(1, n + 1)); m = np.isin(lab, 1 + np.where(t > 0.0015 * W * H)[0])
Image.fromarray((m * 255).astype('uint8')).save(sys.argv[3]); print('ok', round(m.mean() * 100, 1), '% de végétation existante protégée')
