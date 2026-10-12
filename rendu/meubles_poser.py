# Pose le mobilier 3D (calque à part) sur l'image : couleurs d'origine des modèles, accordées à la lumière de la photo.
# Usage : python3 meubles_poser.py image.jpg calque_meubles.png sortie.jpg
import sys, numpy as np
from PIL import Image, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
lay = Image.open(sys.argv[2]).convert('RGBA').resize((W, H), Image.LANCZOS)
A = np.asarray(lay).astype(float); I = np.asarray(img).astype(float); al = A[..., 3:] / 255
m = al[..., 0] > 0.5
ring = np.asarray(Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MaxFilter(41))) > 0
ring &= ~m
if m.any() and ring.any():
    gain = np.clip(I[ring].mean(0) / np.maximum(A[..., :3][m].mean(0), 1), 0.75, 1.25) ** 0.5   # même dominante que la scène
    A[..., :3] = np.clip(A[..., :3] * gain, 0, 255)
lay = Image.fromarray(A.astype('uint8'), 'RGBA').filter(ImageFilter.GaussianBlur(0.5))
out = img.convert('RGBA'); out.alpha_composite(lay); out.convert('RGB').save(sys.argv[3], quality=94); print('ok')
