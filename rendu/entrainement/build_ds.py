import json, os, zipfile
from PIL import Image, ImageOps
m=json.load(open('meta.json'))
F="CVGCLO horizontal slatted douglas fir wooden privacy fence"
sel={3:"on a rooftop terrace with blue outdoor sofas and plants",6:"behind blue outdoor cushions and potted plants",7:"behind a blue outdoor bench, sunny day",
11:"around a small garden with artificial grass and tropical plants",18:"around a garden with potted palms",21:"behind a terracotta tiled patio with palms",
22:"along a lawn with shrubs",23:"cladding a wall next to a stone pillar",26:"behind a swimming pool with sun loungers and climbing plants",28:"with trellis and young trees",
32:"along a street sidewalk",33:"along a narrow street next to a brick wall",35:"above a raised flower bed",38:"behind a lawn and a bare tree",39:"behind a flower bed and lawn",
42:"behind tropical plants and a concrete path",44:"in a cottage garden with potted plants",49:"behind a gravel bed with palms and a patio",52:"along a narrow paved backyard",
53:"at the end of a lawn",55:"around a lawn next to a house",56:"around a large lawn with young trees",61:"around a lawn, corner view",62:"around a lawn with gravel path",
63:"behind a swimming pool on artificial grass",65:"around a swimming pool, low angle",67:"behind a round pool with white roses",69:"around artificial grass with a playhouse",
73:"behind a swimming pool with sun loungers",77:"behind a raised planter with young olive trees",78:"behind a lawn with a tree",80:"in a corner of a tiled patio",83:"behind rattan chairs on a tiled patio",
86:"cladding a wall above planters by a pool",87:"with a lower return, gravel driveway",89:"along a paved driveway",94:"behind a lawn with a standard tree",95:"behind a lawn and flower bed",
98:"along a garden with a willow tree",104:"behind shrubs and garden furniture",105:"around a patio with outdoor armchairs",106:"long fence along a lawn, close perspective",
108:"long fence along a lawn with a playhouse",109:"long fence along a lawn, grazing light"}
T="CVGTER pressure treated pine wooden deck terrace with smooth boards"
selt={101:"next to a house, with pergola posts",102:"in front of patio doors with chairs",103:"under a wooden pergola with garden furniture",99:"raised on a mobile home with steps and a pergola",100:"raised with steps and railings"}
os.makedirs('ds',exist_ok=True)
for f in os.listdir('ds'): os.remove('ds/'+f)
n=0
for d,base,p in ((sel,F,'clo'),(selt,T,'ter')):
    for i,sc in d.items():
        im=ImageOps.exif_transpose(Image.open(m[i]['f'])).convert('RGB'); im.thumbnail((1536,1536))
        name=f"{p}_{i:03d}"; im.save(f'ds/{name}.jpg',quality=94)
        open(f'ds/{name}.txt','w').write(f"a photo of a {base}, {sc}, real garden photo"); n+=1
print(n)
with zipfile.ZipFile('ds.zip','w') as z:
    for f in sorted(os.listdir('ds')): z.write('ds/'+f,f)
