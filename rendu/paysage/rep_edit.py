# Édition d'image via Replicate (modèle, image, consigne) -> sortie
import sys, json, base64, subprocess, time
K = open('/tmp/claude-0/-home-claude-jardin-3d/4d30a8f4-3b79-52d4-b2d0-5ec853a40f6b/scratchpad/.replicate_key').read().strip()
model, src, prompt, out = sys.argv[1:5]; extra = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
uri = 'data:image/png;base64,' + base64.b64encode(open(src, 'rb').read()).decode()
inp = {"prompt": prompt, **extra}
inp['image_input' if 'nano-banana' in model else 'input_image'] = [uri] if 'nano-banana' in model else uri
def api(u, d=None):
    c = ['curl', '-s', '-H', 'Authorization: Bearer ' + K, '-H', 'Content-Type: application/json'] + (['-d', '@-'] if d else []) + [u]
    return json.loads(subprocess.run(c, input=json.dumps(d) if d else None, capture_output=True, text=True).stdout)
p = api(f'https://api.replicate.com/v1/models/{model}/predictions', {"input": inp})
while p.get('status') not in ('succeeded', 'failed', 'canceled'):
    time.sleep(3); p = api(p['urls']['get'])
if p['status'] != 'succeeded': print('ECHEC', p.get('error')); sys.exit(1)
o = p['output']; o = o[0] if isinstance(o, list) else o
subprocess.run(['curl', '-s', '-o', out, o]); print('ok', out)
