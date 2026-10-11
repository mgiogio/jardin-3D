#!/bin/bash
# Chaîne finale Les Mureaux à partir de la composition fidèle + pergola retouchée (fin/k_a.jpg). Les passes IA coûteuses
# (aménagement, plantes au pied des clôtures, mobilier) sont reprises depuis leurs sorties déjà validées.
set -e
W=$(cat lora/weights_url_cloture); F=${FORCE_CLOTURE:-0.35}
P="a photo of a CVGCLO horizontal slatted douglas fir wooden privacy fence along a garden, real garden photo, warm late afternoon sunlight"
# clôture vue de loin : retouche générique douce (le modèle y sème des nœuds en taches) ; clôture proche : modèle entraîné
FP="photo of a new horizontal slatted douglas fir wooden privacy fence along a garden lawn, clean new boards, fine wood grain, few small tight knots, slight color variation between boards, thin even gaps, no holes, no cracks, warm late afternoon sunlight, realistic smartphone photo"
PROTEGE=cas/mureaux_v4_calque.png python3 affine.py fin/k_a.jpg fin/clo_g.png fin/m_b.jpg none "$FP" 0.22 30 >/dev/null
PROTEGE=cas/mureaux_v4_calque.png python3 affine.py fin/m_b.jpg fin/clo_d.png fin/m_c.jpg "$W" "$P" $F 30 >/dev/null
python3 teinte.py fin/m_c.jpg fin/m9x.jpg teinte_ref.json soleil cas/mureaux_v4_calque.png,fin/clo_g.png,fin/clo_d.png 0.5 >/dev/null 2>&1
cp fin/a1_ia.jpg fin/m1x_ia.jpg
MOBILIER_SEPARE=1 HAUT_MOBILIER=110 REPRENDRE=1 python3 amenage.py fin/m9x.jpg cas/mureaux_zone.json 1.462857 cas/mureaux_amenage.txt fin/m1x.jpg cas/mureaux_v4cl_calque.png fin/clo_g.png,fin/clo_d.png fin/cal_terrasse.png 0.0 >/dev/null 2>&1
python3 bande_rampe.py fin/m1x.jpg fin/a2_ia.jpg fin/clo_g_ancien.png fin/m2x.jpg 0.35 0.06 0.25 >/dev/null
python3 - <<'PY'
import numpy as np, cv2
from PIL import Image
im=np.array(Image.open('fin/m2x.jpg').convert('RGB')).astype(np.float32); H,W=im.shape[:2]
cal=np.array(Image.open('cas/mureaux_v4_calque.png').getchannel('A'))>200
y0,y1,x0,x1=550,608,1192,1340; s=y1-y0
vv=np.array([1019.86,3432.48]); yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
slope=((vv[0]-xx)/(vv[1]-yy)).astype(np.float32)
patch=cv2.remap(im,(xx-slope*s).astype(np.float32),(yy-s).astype(np.float32),cv2.INTER_LINEAR)
m=np.zeros((H,W),np.float32); m[y0:y1,x0:x1]=1; m=cv2.GaussianBlur(m,(0,0),5)
out=im*(1-m[...,None])+patch*m[...,None]; out[cal]=im[cal]; out=np.clip(out,0,255).astype('uint8')
a,b,c,d=536,568,1222,1250; out[a:b,c:d]=out[a:b,c+32:d+32]
Image.fromarray(out).save('fin/m3x.jpg',quality=94)
PY
cp fin/k4_ia.jpg fin/m4x_ia.jpg
PLEIN=1 REPRENDRE=1 python3 mobilier.py fin/m3x.jpg fin/cal_terrasse.png cas/mureaux_v4_calque.png cas/mureaux_mobilier.txt fin/m4x.jpg 170 >/dev/null
sed -i "s#fin/k4_ia.jpg#fin/m4x_ia.jpg#" retouches.py
python3 retouches.py fin/m4x.jpg fin/m5x.jpg
echo fini fin/m5x.jpg
