# Passe "projet complet" : la cour est repensée (mobilier, plantations, sol), clôture exacte recollée, maison/olivier/escalier intacts.
import sys, io, os, json, base64, urllib.request, numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, cal, prompt, out = sys.argv[1:5]
img = Image.open(src).convert('RGB'); W, H = img.size
fen = np.asarray(Image.open(cal).convert('RGBA').getchannel('A')) > 120
m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
d.polygon([(0, 1400), (262, 1240), (262, 1050), (818, 1050), (818, 1190), (1095, 1190), (1120, 1380), (1180, 1500), (1180, 1920), (0, 1920)], fill=255)
edit = np.asarray(m) > 0
pied = np.zeros((H, W), bool)                       # plantes autorisées devant le bas de la clôture
for x in range(W):
    ys = np.where(fen[:, x])[0]
    if len(ys): y1 = ys.max(); y0 = ys.min(); pied[int(y1 - 0.3 * (y1 - y0)):y1 + 1, x] = True
edit = (edit & ~fen) | pied
if os.environ.get('PROTEGE'):
    pr = np.asarray(Image.open(os.environ['PROTEGE']).convert('RGBA').getchannel('A')) > 60; edit &= ~pr; fen = fen | pr
size = (1024, 1536)
def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
mk = Image.new('RGBA', (W, H), (0, 0, 0, 255)); A = np.array(mk); A[edit, 3] = 0; mk = Image.fromarray(A)
bd = 'xx' + os.urandom(8).hex()
def part(n, v, fn=None, ct=None):
    h = f'--{bd}\r\nContent-Disposition: form-data; name="{n}"' + (f'; filename="{fn}"' if fn else '') + '\r\n' + (f'Content-Type: {ct}\r\n' if ct else '') + '\r\n'
    return h.encode() + (v if isinstance(v, bytes) else v.encode()) + b'\r\n'
body = b''.join([part('model', os.environ.get('IMG_MODEL', 'gpt-image-2.5-sunburst')), part('prompt', open(prompt).read()), part('size', '1024x1536'), part('quality', 'high'),
                 part('image', png(img.resize(size)), 'i.png', 'image/png'), part('mask', png(mk.resize(size)), 'm.png', 'image/png')]) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': f'multipart/form-data; boundary={bd}'})
res = json.load(urllib.request.urlopen(req, timeout=500))
gen = Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGB').resize((W, H), Image.LANCZOS)
gen.save(out.replace('.jpg', '_ia.jpg'), quality=92)
# verrou : hors zone, photo d'origine ; clôture exacte recollée (sauf le feuillage ajouté devant son pied, pris tel quel)
k = np.asarray(Image.fromarray((edit * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(3))).astype(float)[..., None] / 255
k[fen & ~pied] = 0
o = np.asarray(gen).astype(float) * k + np.asarray(img).astype(float) * (1 - k)
Image.fromarray(np.clip(o, 0, 255).astype('uint8')).save(out, quality=94); print('ok', out)
