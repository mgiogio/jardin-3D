# Génère les visuels produits de la banque de mobilier (un objet, fond blanc, vue 3/4) avec gpt-image-1.
import json, os, sys, base64, urllib.request, concurrent.futures as cf
K = open('/tmp/claude-0/-home-claude-jardin-3d/4d30a8f4-3b79-52d4-b2d0-5ec853a40f6b/scratchpad/.openai_key').read().strip()
B = "Studio product photo of a single piece of contemporary outdoor garden furniture, isolated, centered, full object visible with margin, three-quarter front view from slightly above, plain pure white background, soft even light, no shadow on background, no text, no logo, no people, no other objects. Original design, not a copy of any brand. "
ITEMS = json.load(open('banque/items.json'))
def go(k):
    out = f'banque/{k}.png'
    if os.path.exists(out): return k, 'deja'
    body = json.dumps({"model": "gpt-image-1", "prompt": B + ITEMS[k]['prompt'], "size": "1024x1024", "quality": "high", "background": "opaque"}).encode()
    r = urllib.request.Request('https://api.openai.com/v1/images/generations', data=body, headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(r, timeout=400))
    open(out, 'wb').write(base64.b64decode(d['data'][0]['b64_json'])); return k, 'ok'
with cf.ThreadPoolExecutor(6) as ex:
    for k, s in ex.map(go, [a for a in ITEMS if len(sys.argv) < 2 or a in sys.argv[1:]]): print(k, s)
