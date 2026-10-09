# Approche "IA d'abord" : l'IA générative produit toute l'image à partir de
# 1) la photo du client avec le rendu 3D des produits posé dessus (guide de forme, d'échelle et d'emplacement),
# 2) des photos réelles des produits Cover Green (références pour le bois et les détails).
# Usage : OPENAI_API_KEY=... python3 integre.py guide.jpg consigne.txt sortie.jpg ref1.jpg [ref2.jpg ...]
import sys, json, base64, io, os, urllib.request
from PIL import Image
guide = Image.open(sys.argv[1]).convert('RGB'); W, H = guide.size
size = (1536, 1024) if W >= H else (1024, 1536)
def png(im, s=None):
    b = io.BytesIO(); (im.resize(s) if s else im).save(b, 'PNG'); return b.getvalue()
imgs = [png(guide, size)]
for r in sys.argv[4:]:
    im = Image.open(r).convert('RGB'); im.thumbnail((1024, 1024)); imgs.append(png(im))
B = 'cgb'
def part(name, val, fn=None, ct=None):
    h = f'--{B}\r\nContent-Disposition: form-data; name="{name}"' + (f'; filename="{fn}"' if fn else '') + '\r\n'
    if ct: h += f'Content-Type: {ct}\r\n'
    return h.encode() + b'\r\n' + (val if isinstance(val, bytes) else val.encode()) + b'\r\n'
parts = [part('model', 'gpt-image-1'), part('prompt', open(sys.argv[2]).read()), part('size', f'{size[0]}x{size[1]}'),
         part('quality', 'high'), part('input_fidelity', 'high')]
parts += [part('image[]', b, f'img{i}.png', 'image/png') for i, b in enumerate(imgs)]
body = b''.join(parts) + f'--{B}--\r\n'.encode()
req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={
    'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': f'multipart/form-data; boundary={B}'})
res = json.load(urllib.request.urlopen(req, timeout=400))
Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS).save(sys.argv[3], quality=92)
print('ok', res.get('usage', {}).get('total_tokens'))
