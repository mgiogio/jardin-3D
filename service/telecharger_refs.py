# Télécharge les photos de nos réalisations (modèles des produits), publiques sur www.cover.green
import json, os, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(ICI, 'assets', 'refs'); os.makedirs(D, exist_ok=True)
for f, u in json.load(open(os.path.join(ICI, 'produits.json')))['refs_urls'].items():
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36', 'Accept': 'image/*'})
    open(os.path.join(D, f), 'wb').write(urllib.request.urlopen(r, timeout=60).read()); print('ok', f)
