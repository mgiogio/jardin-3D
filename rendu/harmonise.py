# Passe finale sur toute l'image avec le modèle entraîné : unifie lumière, ombres et bords du produit.
# Usage : REPLICATE_API_TOKEN=... python3 harmonise.py entree.jpg sortie.jpg lora 'prompt' force [seed]
import sys, os, json, io, base64, time, urllib.request
from PIL import Image
img = Image.open(sys.argv[1]).convert('RGB'); W, H = img.size
b = io.BytesIO(); img.save(b, 'JPEG', quality=95)
tok = os.environ['REPLICATE_API_TOKEN']
inp = {'prompt': sys.argv[4], 'image': 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode(),
       'prompt_strength': float(sys.argv[5]), 'lora_weights': sys.argv[3], 'lora_scale': 0.9,
       'num_inference_steps': 36, 'guidance': 3.0, 'output_format': 'png', 'go_fast': False, 'megapixels': '1', 'aspect_ratio': '4:3'}
if len(sys.argv) > 6: inp['seed'] = int(sys.argv[6])
req = urllib.request.Request('https://api.replicate.com/v1/models/black-forest-labs/flux-dev-lora/predictions', data=json.dumps({'input': inp}).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'Prefer': 'wait=60'})
p = json.load(urllib.request.urlopen(req, timeout=120))
while p['status'] not in ('succeeded', 'failed', 'canceled'):
    time.sleep(2); p = json.load(urllib.request.urlopen(urllib.request.Request(p['urls']['get'], headers={'Authorization': 'Bearer ' + tok})))
if p['status'] != 'succeeded': sys.exit('échec : ' + str(p.get('error')))
u = p['output'][0] if isinstance(p['output'], list) else p['output']
raw = Image.open(io.BytesIO(urllib.request.urlopen(u).read())).convert('RGB'); print('brut', raw.size); raw.resize((W, H), Image.LANCZOS).save(sys.argv[2], quality=93)
print('ok')
