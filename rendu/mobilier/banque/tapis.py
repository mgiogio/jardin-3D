# Textures de tapis vues de dessus (plates, bord à bord) pour les tapis procéduraux.
import json, base64, urllib.request, concurrent.futures as cf, os
K = open('/tmp/claude-0/-home-claude-jardin-3d/4d30a8f4-3b79-52d4-b2d0-5ec853a40f6b/scratchpad/.openai_key').read().strip()
B = "Perfectly flat top-down orthographic scan of an entire rectangular outdoor rug, the rug fills the whole image edge to edge with no background, no perspective, no shadow, no furniture, even lighting, visible woven texture. "
T = {"tapis_terracotta": "Flat-woven recycled polypropylene, natural beige with a wide terracotta and ochre geometric border, a few fine stripes, mediterranean style.",
     "tapis_rayures": "Flat-woven outdoor rug with wide stripes in cream, sage green and soft blue, cheerful and fresh.",
     "tapis_jute": "Natural jute-look outdoor rug, warm sand color with a simple thin charcoal double-line border, chunky weave."}
def go(k):
    if os.path.exists(f'banque/{k}.png'): return k
    body = json.dumps({"model": "gpt-image-1", "prompt": B + T[k], "size": "1536x1024", "quality": "high"}).encode()
    r = urllib.request.Request('https://api.openai.com/v1/images/generations', data=body, headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    open(f'banque/{k}.png', 'wb').write(base64.b64decode(json.load(urllib.request.urlopen(r, timeout=400))['data'][0]['b64_json'])); return k
with cf.ThreadPoolExecutor(3) as ex: print(list(ex.map(go, T)))
