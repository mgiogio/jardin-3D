# Efface un objet de la photo d'origine (vélo, bâche...) par remplissage Flux Fill, sur un cadrage autour de la zone.
# Les produits 3D (calque) sont recollés par-dessus ensuite. Usage :
# REPLICATE_API_TOKEN=... python3 effacer.py image.jpg x0,y0,x1,y1 'description du fond' sortie.jpg [calque_produits.png] [marge=120]
import sys, os, io, json, base64, time, urllib.request, numpy as np
from PIL import Image, ImageDraw, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
x0, y0, x1, y1 = map(int, sys.argv[2].split(',')); mg = int(sys.argv[6]) if len(sys.argv) > 6 else 120
bx = (max(0, x0 - mg), max(0, y0 - mg), min(W, x1 + mg), min(H, y1 + mg)); crop = img.crop(bx)
mask = Image.new('L', crop.size, 0); ImageDraw.Draw(mask).rectangle([x0 - bx[0], y0 - bx[1], x1 - bx[0], y1 - bx[1]], fill=255)
def uri(im, fmt='PNG'):
    b = io.BytesIO(); im.save(b, fmt); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
s = 1024 / max(crop.size); size = (int(crop.size[0] * s) // 16 * 16, int(crop.size[1] * s) // 16 * 16)
tok = os.environ['REPLICATE_API_TOKEN']
body = {'input': {'image': uri(crop.resize(size, Image.LANCZOS)), 'mask': uri(mask.resize(size)), 'prompt': sys.argv[3], 'num_inference_steps': 28, 'guidance': 30, 'output_format': 'png'}}
req = urllib.request.Request('https://api.replicate.com/v1/models/black-forest-labs/flux-fill-dev/predictions', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'Prefer': 'wait=60'})
p = json.load(urllib.request.urlopen(req, timeout=120))
while p['status'] not in ('succeeded', 'failed', 'canceled'):
    time.sleep(2); p = json.load(urllib.request.urlopen(urllib.request.Request(p['urls']['get'], headers={'Authorization': 'Bearer ' + tok})))
if p['status'] != 'succeeded': sys.exit('échec ' + str(p.get('error')))
u = p['output'][0] if isinstance(p['output'], list) else p['output']
out = Image.open(io.BytesIO(urllib.request.urlopen(u).read())).convert('RGB').resize(crop.size, Image.LANCZOS)
res = img.copy(); res.paste(Image.composite(out, crop, mask.filter(ImageFilter.GaussianBlur(2))), bx[:2])
if len(sys.argv) > 5 and sys.argv[5]:
    cal = Image.open(sys.argv[5]).convert('RGBA').resize((W, H)).getchannel('A').point(lambda a: 255 if a > 200 else 0)
    res = Image.composite(img, res, cal)            # produits exacts par-dessus
res.save(sys.argv[4], quality=94); print('ok')
