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
body = {'input': {'prompt': sys.argv[5], 'image': uri, 'prompt_strength': float(sys.argv[6]), 'lora_weights': sys.argv[4], 'lora_scale': 1.0,
                  'num_inference_steps': 32, 'guidance': 3.0, 'output_format': 'png', 'go_fast': False, 'megapixels': '1'}}
req = urllib.request.Request('https://api.replicate.com/v1/models/black-forest-labs/flux-dev-lora/predictions', data=json.dumps(body).encode(),
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
