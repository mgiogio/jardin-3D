# Génère les découpes des grands sujets (fond transparent) : sujets/<clé>.png
import json, os, sys, base64, urllib.request, concurrent.futures as cf
S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sujets.json')))
K = os.environ['OPENAI_API_KEY']; out = sys.argv[1]
B = ("Real photograph, not an illustration: a single real potted plant as found in a French garden center, natural irregular "
     "growth, botanically accurate, isolated, entirely visible from the bottom of the pot to the top of the foliage with margin, "
     "straight-on view at eye level, soft overcast daylight, natural colors (not oversaturated), no shadow, transparent background, "
     "no text, no other object. ")
def go(k):
    f = os.path.join(out, k + '.png')
    if os.path.exists(f): return k, 'deja'
    body = json.dumps({"model": os.environ.get('IMG_MODEL', 'gpt-image-1'), "prompt": B + S[k]['prompt'], "size": "1024x1536",
                       "quality": "high", "background": "transparent", "output_format": "png"}).encode()
    r = urllib.request.Request('https://api.openai.com/v1/images/generations', data=body, headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(r, timeout=500)); open(f, 'wb').write(base64.b64decode(d['data'][0]['b64_json'])); return k, 'ok'
with cf.ThreadPoolExecutor(7) as ex:
    for k, s in ex.map(go, [k for k in S if not k.startswith('_')]): print(k, s, flush=True)
