# Compose le rendu 3D sur la photo en recalant la teinte du bois sur une cible mesurée sur les réalisations clients.
import sys,json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
photo=Image.open(sys.argv[1]).convert('RGBA'); layer=Image.open(sys.argv[2]).convert('RGBA')
target=np.array([int(sys.argv[4][i:i+2],16) for i in (1,3,5)],float)
A=np.asarray(layer).astype(float); rgb=A[...,:3]; al=A[...,3]
mx=rgb.max(-1); mn=rgb.min(-1); sat=(mx-mn)/np.maximum(mx,1)
wood=(al>200)&(sat>0.25)&(mx>40)
L=rgb.mean(-1); Lref=np.percentile(L[wood],70)
# teinte imposée par la cible, veinage et ombrage conservés via la luminance du rendu
rgb[wood]=np.clip(target[None,:]*(L[wood]/Lref)[:,None],0,255)
print('Lref',round(Lref))
# le métal (gris) suit la luminosité de la photo : on le baisse un peu
metal=(al>200)&~wood; rgb[metal]=rgb[metal]*0.8
A[...,:3]=rgb; layer=Image.fromarray(A.astype('uint8'),'RGBA')
out=Image.alpha_composite(photo,layer)
if len(sys.argv)>5:
    m=Image.new('L',photo.size,0); d=ImageDraw.Draw(m)
    for p in json.load(open(sys.argv[5])): d.polygon([tuple(x) for x in p],fill=255)
    out=Image.composite(photo,out,m.filter(ImageFilter.GaussianBlur(1.5)))
out.convert('RGB').save(sys.argv[3],quality=90)
