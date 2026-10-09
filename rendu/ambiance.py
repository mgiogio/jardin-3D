# Étape IA générative : plantes et ambiance autour des produits, produits recollés à l'identique ensuite.
# Usage : OPENAI_API_KEY=... python3 ambiance.py photo_composee.jpg calque_produits.png zone_jardin.json prompt.txt sortie.jpg
import sys, json, base64, io, os, urllib.request
from PIL import Image, ImageDraw, ImageFilter
comp = Image.open(sys.argv[1]).convert('RGB'); layer = Image.open(sys.argv[2]).convert('RGBA')
W, H = comp.size
# Masque OpenAI : transparent = zone que l'IA peut repeindre (le jardin), opaque = à garder.
edit = Image.new('L', (W, H), 0); d = ImageDraw.Draw(edit)
for poly in json.load(open(sys.argv[3])): d.polygon([tuple(p) for p in poly], fill=255)
if len(sys.argv) > 6:  # éléments à ne jamais repeindre (piliers, boîte aux lettres...)
    for poly in json.load(open(sys.argv[6])): d.polygon([tuple(p) for p in poly], fill=0)
prod = layer.getchannel('A').point(lambda a: 255 if a > 160 else 0).filter(ImageFilter.MaxFilter(9))
edit.paste(0, (0, 0), prod)                     # jamais repeindre les produits
mask = comp.convert('RGBA'); mask.putalpha(edit.point(lambda v: 0 if v else 255))
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
size = (1536, 1024) if W >= H else (1024, 1536)
img_b, mask_b = png(comp.resize(size)), png(mask.resize(size))
boundary = 'cgboundary'
def part(name, val, fn=None, ct=None):
    h = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"' + (f'; filename="{fn}"' if fn else '') + '\r\n'
    if ct: h += f'Content-Type: {ct}\r\n'
    return h.encode() + b'\r\n' + (val if isinstance(val, bytes) else val.encode()) + b'\r\n'
body = b''.join([part('model', 'gpt-image-1'), part('prompt', open(sys.argv[4]).read()), part('size', f'{size[0]}x{size[1]}'),
                 part('quality', 'high'), part('image', img_b, 'image.png', 'image/png'), part('mask', mask_b, 'mask.png', 'image/png')]) + f'--{boundary}--\r\n'.encode()
req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={
    'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': f'multipart/form-data; boundary={boundary}'})
res = json.load(urllib.request.urlopen(req, timeout=300))
gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS)
# Hors zone jardin : la photo d'origine. Produits : recollés pixel pour pixel depuis la composition 3D.
keep = edit.filter(ImageFilter.GaussianBlur(3))
out = Image.composite(gen, comp, keep)
out = Image.composite(comp, out, prod.filter(ImageFilter.GaussianBlur(1)))
out.save(sys.argv[5], quality=92); print('ok', res.get('usage'))
