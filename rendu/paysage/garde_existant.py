# Garde-fou après génération : l'IA ne doit qu'AJOUTER du végétal. Tout ce qui existait et n'est pas du végétal ou du sol
# (maisons, toits, fenêtres, voitures, caissons, portails, clôtures, murs) est remis à l'identique, sauf là où l'IA a posé
# du feuillage devant dans une zone autorisée (couronne du point focal).
# Usage : python3 garde_existant.py ia.jpg base.jpg zones.json sortie.jpg [feuillage_autorise.json]
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi
import torch
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation

ia = Image.open(sys.argv[1]).convert('RGB'); W, H = ia.size
base = Image.open(sys.argv[2]).convert('RGB').resize((W, H))
def poly(f):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for p in json.load(open(f)): d.polygon([tuple(q) for q in p], fill=255)
    return np.asarray(m) > 0
zones = poly(sys.argv[3]); libre = poly(sys.argv[5]) if len(sys.argv) > 5 else np.zeros((H, W), bool)

P = CLIPSegProcessor.from_pretrained('CIDAS/clipseg-rd64-refined'); M = CLIPSegForImageSegmentation.from_pretrained('CIDAS/clipseg-rd64-refined')
STRUCT = ['house wall', 'roof', 'window', 'car', 'green box', 'metal gate', 'wooden fence', 'concrete post', 'paved path', 'heat pump',
          'existing shrub', 'flower bed', 'hedge', 'tree', 'mulch', 'bark mulch bed', 'ornamental grass', 'lavender']
VEG = ['lawn grass', 'bare soil', 'gravel', 'sky']
def probas(im, textes):
    out = np.zeros((len(textes), H, W), np.float32); T = 520
    for ty in range(0, H, T - 80):
        for tx in range(0, W, T - 80):
            b = (tx, ty, min(W, tx + T), min(H, ty + T)); c = im.crop(b)
            inp = P(text=textes, images=[c] * len(textes), return_tensors='pt', padding=True)
            with torch.no_grad(): lg = torch.sigmoid(M(**inp).logits).numpy()
            if lg.ndim == 2: lg = lg[None]
            for i in range(len(textes)):
                pm = np.asarray(Image.fromarray((lg[i] * 255).astype('uint8')).resize(c.size, Image.BILINEAR)) / 255
                out[i, b[1]:b[3], b[0]:b[2]] = np.maximum(out[i, b[1]:b[3], b[0]:b[2]], pm)
    return out
pb = probas(base, STRUCT + VEG); s_base, v_base = pb[:len(STRUCT)].max(0), pb[len(STRUCT):].max(0)
existant = (s_base > 0.35) & (s_base > v_base) & zones                     # structure du client ou des voisins dans les zones
pi = probas(ia, ['plants and flowers', 'shrub', 'tree foliage']).max(0)
feuillage_devant = libre & (pi > 0.4)
remettre = existant & ~feuillage_devant
remettre = ndi.binary_closing(remettre, iterations=2); remettre = ndi.binary_opening(remettre, iterations=1)
Mk = np.asarray(Image.fromarray((remettre * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))).astype(float)[..., None] / 255
out = np.asarray(ia).astype(float) * (1 - Mk) + np.asarray(base).astype(float) * Mk
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(sys.argv[4], quality=94)
print('ok', round(float(remettre.sum()) / max(1, zones.sum()) * 100, 1), '% des zones remis à l\'identique')
