# Mobilier et pots sur la terrasse, sous la pergola : édition gpt-image-1 sur un cadrage serré autour de la terrasse.
# Les produits (poteaux, brise-vue, plancher) restent exacts : on ne garde de l'IA que ce qu'elle a posé (écart fort).
# Usage : OPENAI_API_KEY=... python3 mobilier.py image.jpg terrasse.png produits.png consigne.txt sortie.jpg [haut_px=110]
import sys, json, base64, io, os, urllib.request, numpy as np
from PIL import Image, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size; haut = int(sys.argv[6]) if len(sys.argv) > 6 else 110
A = lambda p: np.asarray(Image.open(p).convert('RGBA').resize((W, H)).getchannel('A')) > 160
deck = A(sys.argv[2]); prod = A(sys.argv[3])
band = deck.copy()
for x in np.where(deck.any(0))[0]:
    y0 = np.where(deck[:, x])[0].min(); band[max(0, y0 - haut):y0, x] = True
# meubles seulement sous la pergola : colonnes comprises entre ses poteaux extrêmes (pas de panneau inventé à côté)
per = prod & ~deck; cols = np.where(per.sum(0) > 0.6 * per.sum(0).max() * 0 + 60)[0]   # colonnes des poteaux et du brise-vue
if len(cols): band[:, :cols.min() + 8] &= deck[:, :cols.min() + 8]; band[:, cols.max() - 8:] &= deck[:, cols.max() - 8:]
edit = band & ~(prod & ~deck)                       # plancher + volume au-dessus, sans les poteaux et le brise-vue
x0, y0, x1, y1 = Image.fromarray((band * 255).astype('uint8')).getbbox()
cw = int(max(x1 - x0, (y1 - y0) * 1.5) * 1.25); ch = int(cw / 1.5); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
bx = (max(0, cx - cw // 2), max(0, cy - ch // 2)); box = (bx[0], bx[1], min(W, bx[0] + cw), min(H, bx[1] + ch))
crop = img.crop(box); em = Image.fromarray((edit * 255).astype('uint8')).crop(box)
mask = crop.convert('RGBA'); mask.putalpha(em.point(lambda v: 0 if v else 255))
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
S = (1536, 1024); bd = 'cgb'
def part(n, v, fn=None, ct=None):
    h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '')
    return h.encode() + b'\r\n' + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
body = b''.join([part('model', 'gpt-image-1'), part('prompt', open(sys.argv[4]).read()), part('size', f'{S[0]}x{S[1]}'), part('quality', 'high'),
                 part('input_fidelity', 'high'), part('image', png(crop.resize(S, Image.LANCZOS)), 'i.png', 'image/png'), part('mask', png(mask.resize(S)), 'm.png', 'image/png')]) + f'--{bd}--\r\n'.encode()
ia_p = sys.argv[5].replace('.jpg', '_ia.jpg')
if os.environ.get('REPRENDRE') and os.path.exists(ia_p): gen = Image.open(ia_p).convert('RGB')
else:
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY', ''), 'Content-Type': f'multipart/form-data; boundary={bd}'})
    res = json.load(urllib.request.urlopen(req, timeout=400))
    gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize(crop.size, Image.LANCZOS); gen.save(ia_p, quality=92)
d = np.abs(np.asarray(gen).astype(float) - np.asarray(crop).astype(float)).mean(-1)
ajout = (np.asarray(Image.fromarray(((d > float(os.environ.get('SEUIL', '30'))) * 255).astype('uint8')).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5))) > 0) & (np.asarray(em) > 0)
# objets entiers : on comble les trous à l'intérieur des meubles
Mk = Image.fromarray((ajout * 255).astype('uint8')).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
Mk = Image.fromarray(np.minimum(np.asarray(Mk), np.asarray(em)).astype('uint8'))
if os.environ.get('MEUBLES_SEG'):   # on ne garde de l'IA que les meubles et pots reconnus (le plancher reste celui du produit)
    import torch
    from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
    from scipy import ndimage as ndi
    P_ = CLIPSegProcessor.from_pretrained('CIDAS/clipseg-rd64-refined'); M_ = CLIPSegForImageSegmentation.from_pretrained('CIDAS/clipseg-rd64-refined')
    txt = ['garden table and chairs', 'flower pot with plant', 'wooden deck floor', 'wooden pergola posts']
    inp = P_(text=txt, images=[gen] * len(txt), return_tensors='pt', padding=True)
    with torch.no_grad(): lg = torch.sigmoid(M_(**inp).logits).numpy()
    lg = np.stack([np.asarray(Image.fromarray(l.astype('float32')).resize(gen.size, Image.BILINEAR)) for l in lg])
    meuble = (np.maximum(lg[0], lg[1]) > np.maximum(lg[2], lg[3])) & (np.maximum(lg[0], lg[1]) > 0.3) & (d > 18)
    meuble = ndi.binary_opening(meuble, iterations=2); meuble = ndi.binary_closing(meuble, iterations=3)
    meuble = ndi.binary_fill_holes(meuble) & (np.asarray(em) > 0)
    # pieds de chaises, tronc et feuillage fins : dans le cadre de chaque meuble (prolongé jusqu'au plancher), tout ce que l'IA a changé
    lab_, n_ = ndi.label(meuble); boite = np.zeros_like(meuble)
    for sl in ndi.find_objects(lab_):
        if sl is None: continue
        y0_, y1_ = sl[0].start, sl[0].stop; x0_, x1_ = sl[1].start, sl[1].stop; h_ = y1_ - y0_
        boite[max(0, y0_ - h_ // 3):min(meuble.shape[0], y1_ + h_ // 3), x0_:x1_] = True
    plancher = (lg[2] > np.maximum(lg[0], lg[1]) * 0.8) & (lg[2] > 0.2)
    meuble |= boite & (d > 22) & (np.asarray(em) > 0) & ~plancher
    meuble = ndi.binary_closing(meuble, iterations=2)
    Mk = Image.fromarray((meuble * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.0))
if os.environ.get('PLEIN'):   # toute la zone autorisée vient de l'IA (évite les meubles à moitié transparents sur les objets d'origine)
    Mk = em.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
out = img.copy(); out.paste(Image.composite(gen, crop, Mk), box[:2]); out.save(sys.argv[5], quality=93)
print('ok', box)
