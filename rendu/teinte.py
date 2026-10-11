# Teinte fidèle aux réalisations : transfert de couleur (espace Lab) du bois des produits vers les statistiques
# mesurées sur de vraies clôtures Cover Green posées (teinte_ref.json). Seul le bois est touché (pas les connecteurs),
# et chaque produit garde sa propre lumière.
# Usage : python3 teinte.py image.jpg sortie.jpg ref.json lumiere(soleil|couvert) calque1.png[,calque2.png...] [part_L=0.5]
# Chaque calque = un produit (ou groupe). Un pixel appartient au premier calque qui le couvre.
import sys, json, numpy as np
from PIL import Image, ImageFilter
from skimage import color
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
ref = json.load(open(sys.argv[3]))[sys.argv[4]]; mu_r, sd_r = np.array(ref['moy']), np.array(ref['ecart'])
kL = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
lab = color.rgb2lab(np.asarray(img) / 255.0); out = lab.copy(); pris = np.zeros((H, W), bool); tout = np.zeros((H, W), bool)
for cp in sys.argv[5].split(','):
    c = np.asarray(Image.open(cp).convert('RGBA').resize((W, H))).astype(float)
    rgb, a = c[..., :3], c[..., 3]; mx, mn = rgb.max(-1), rgb.min(-1)
    bois = (a > 200) & ((mx - mn) / np.maximum(mx, 1) > 0.2) & ~pris   # bois = pixels colorés du rendu (le métal est gris)
    pris |= a > 200
    if bois.sum() < 200: continue
    px = lab[bois]; mu, sd = px.mean(0), px.std(0) + 1e-6
    t_mu = mu_r.copy(); t_mu[0] = mu[0] * (1 - kL) + mu_r[0] * kL
    k = np.minimum(sd_r / sd, 1.5); k[0] = (sd[0] * (1 - kL) + sd_r[0] * kL) / sd[0]   # variations entre lames : renforcées, sans excès
    out[bois] = (px - mu) * k + t_mu; tout |= bois
    print(cp, 'avant', mu.round(1), 'après', t_mu.round(1))
res = Image.fromarray((np.clip(color.lab2rgb(out), 0, 1) * 255).astype('uint8'))
soft = Image.fromarray((tout * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7))
Image.composite(res, img, soft).save(sys.argv[2], quality=94)
