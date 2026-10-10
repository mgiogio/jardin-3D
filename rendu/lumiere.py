# Passe "waouh" complète : (recadrage si le produit est petit) -> profondeur photo + 3D exacte -> lumière ComfyUI
# -> retouche du produit par le modèle entraîné. Usage :
# REPLICATE_API_TOKEN=... python3 lumiere.py image.jpg calque.png depth3d.png lora_url 'prompt scène' 'prompt produit' sortie.jpg [denoise] [seed]
import sys, os, json, subprocess, zipfile
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
img_p, cal_p, dep_p, lora, ps, pp, out = sys.argv[1:8]
den = float(sys.argv[8]) if len(sys.argv) > 8 else 0.66; seed = int(sys.argv[9]) if len(sys.argv) > 9 else 7
base = os.path.splitext(out)[0]
img = Image.open(img_p).convert('RGB'); W, H = img.size
cal = Image.open(cal_p).convert('RGBA').resize((W, H)); dep = Image.open(dep_p).convert('RGBA').resize((W, H), Image.NEAREST)
x0, y0, x1, y1 = cal.getchannel('A').point(lambda a: 255 if a > 160 else 0).getbbox()
share = (x1 - x0) * (y1 - y0) / (W * H)
box = (0, 0, W, H)
if share < 0.15:   # produit trop petit : on cadre sur le projet (rapport 4:3, produit ~ 40 % de la largeur)
    cw = min(W, max(int((x1 - x0) / 0.40), int((y1 - y0) / 0.45 * 4 / 3), int(W * 0.35))); ch = int(cw * 3 / 4)
    cx, cy = (x0 + x1) // 2, int(y0 + (y1 - y0) * 0.6)
    bx0 = max(0, min(W - cw, cx - cw // 2)); by0 = max(0, min(H - ch, cy - ch // 2)); box = (bx0, by0, bx0 + cw, by0 + ch)
    print('recadrage', round(share * 100, 1), '% ->', box)
img_c, cal_c, dep_c = img.crop(box), cal.crop(box), dep.crop(box)
img_c.save(base + '_in.jpg', quality=95); cal_c.save(base + '_cal.png'); dep_c.save(base + '_dep3d.png')
py = sys.executable
subprocess.run([py, os.path.join(here, 'profondeur.py'), base + '_in.jpg', base + '_dep3d.png', base + '_depth.png'], check=True)
d = os.path.join(here, 'comfy'); zp = base + '_in.zip'
with zipfile.ZipFile(zp, 'w') as z:
    z.write(base + '_in.jpg', 'scene.png'); z.write(base + '_depth.png', 'depth.png')
wf = subprocess.run([py, os.path.join(d, 'wf.py'), ps, str(den), str(seed), '1408', '1056', 'depth'], capture_output=True, text=True, check=True).stdout
open(base + '_wf.json', 'w').write(wf)
r = subprocess.run([py, os.path.join(d, 'run.py'), base + '_wf.json', zp, base], capture_output=True, text=True); print(r.stdout[-400:], r.stderr[-400:])
rendu = [l for l in r.stdout.split() if 'rendu' in l and l.endswith('.png')][0]
R = Image.open(rendu).convert('RGB'); R.save(base + '_lumiere.jpg', quality=95)   # sortie en pleine définition (1408 x 1056)
cal_c.resize(R.size, Image.LANCZOS).save(base + '_cal.png')
subprocess.run([py, os.path.join(here, 'affine.py'), base + '_lumiere.jpg', base + '_cal.png', out, lora, pp, '0.45', '50'], check=True)
print('final', out)
