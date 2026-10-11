# Affinage des produits par le modèle entraîné (LoRA Cover Green) : on reprend la zone du produit
# en image-à-image à faible force, pour garder la géométrie exacte de la 3D et gagner le réalisme.
# Usage : REPLICATE_API_TOKEN=... python3 affine.py image.jpg calque.png sortie.jpg lora 'prompt' force [marge]
import sys, os, json, io, base64, time, urllib.request
from PIL import Image, ImageFilter
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
lay = Image.open(sys.argv[2]).convert('RGBA').resize((W, H)).getchannel('A').point(lambda a: 255 if a > 160 else 0)
x0, y0, x1, y1 = lay.getbbox(); m = int(sys.argv[7]) if len(sys.argv) > 7 else 60
x0, y0, x1, y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
crop = img.crop((x0, y0, x1, y1)); cw, ch = crop.size
s = 1024 / max(cw, ch); up = crop.resize((max(64, int(cw * s) // 16 * 16), max(64, int(ch * s) // 16 * 16)), Image.LANCZOS)
b = io.BytesIO(); up.save(b, 'PNG'); uri = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
tok = os.environ['REPLICATE_API_TOKEN']
# rapport d'image le plus proche de la zone (la zone peut être une clôture très allongée)
ars = {'1:1': 1, '16:9': 16 / 9, '21:9': 21 / 9, '3:2': 1.5, '2:3': 2 / 3, '4:5': 0.8, '5:4': 1.25, '3:4': 0.75, '4:3': 4 / 3, '9:16': 9 / 16, '9:21': 9 / 21}
ar = min(ars, key=lambda k: abs(ars[k] - cw / ch))
inp = {'prompt': sys.argv[5], 'image': uri, 'prompt_strength': float(sys.argv[6]),
       'num_inference_steps': 32, 'guidance': 3.0, 'output_format': 'png', 'go_fast': False, 'megapixels': '1', 'aspect_ratio': ar}
modele = 'flux-dev'                       # lora = 'none' : réalisme générique (clôture, terrasse), sans modèle entraîné
if sys.argv[4] != 'none': inp.update(lora_weights=sys.argv[4], lora_scale=1.0); modele = 'flux-dev-lora'
body = {'input': inp}
req = urllib.request.Request(f'https://api.replicate.com/v1/models/black-forest-labs/{modele}/predictions', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'Prefer': 'wait=60'})
p = json.load(urllib.request.urlopen(req, timeout=120))
while p['status'] not in ('succeeded', 'failed', 'canceled'):
    time.sleep(2); p = json.load(urllib.request.urlopen(urllib.request.Request(p['urls']['get'], headers={'Authorization': 'Bearer ' + tok})))
if p['status'] != 'succeeded': sys.exit('échec : ' + str(p.get('error')))
url = p['output'][0] if isinstance(p['output'], list) else p['output']
out = Image.open(io.BytesIO(urllib.request.urlopen(url).read())).convert('RGB').resize((cw, ch), Image.LANCZOS)
out.save(sys.argv[3].replace('.jpg', '_zone.jpg'))
# On ne remplace que le produit et son voisinage immédiat (ombres de contact), en fondu.
mk = lay.crop((x0, y0, x1, y1)).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(6))
res = img.copy(); res.paste(Image.composite(out, crop, mk), (x0, y0)); res.save(sys.argv[3], quality=92)
print('ok', p.get('metrics'))
