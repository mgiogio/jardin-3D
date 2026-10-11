# Retouches finales : nœuds noirs ronds sur les clôtures (trous) -> nœuds brun-roux fondus ; objet IA devant un produit
# (olivier devant le brise-vue) ; petites taches. Usage : python3 retouches.py entree.jpg sortie.jpg
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
im = np.array(Image.open(sys.argv[1]).convert('RGB')); H, W = im.shape[:2]
A = lambda p: np.asarray(Image.open(p).convert('RGBA').resize((W, H)).getchannel('A')) > 160
clo = A('fin/clo_g.png') | A('fin/clo_d.png')
# 1) trous : taches sombres isolées. Une fermeture le long d'une ligne bouche une tache ronde quelle que soit l'orientation,
#    mais pas un jour entre lames si la ligne suit les lames ; le minimum sur 12 orientations ne bouche donc que les taches.
L = cv2.cvtColor(im, cv2.COLOR_RGB2LAB)[..., 0]
fer = []
for ang in range(0, 180, 15):
    k = np.zeros((31, 31), np.uint8); t = np.radians(ang)
    cv2.line(k, (int(15 - 15 * np.cos(t)), int(15 - 15 * np.sin(t))), (int(15 + 15 * np.cos(t)), int(15 + 15 * np.sin(t))), 1, 1)
    fer.append(cv2.morphologyEx(L, cv2.MORPH_CLOSE, k))
fond = np.min(fer, 0).astype(float)
proche = A('fin/clo_d.png')                      # clôture vue de près : lames larges, les nœuds s'y voient
proche[575:610, 40:75] = True                     # point noir isolé sur la clôture gauche
trous = proche & (fond - L.astype(float) > 45)
lab, n = ndi.label(trous)
if n: trous = np.isin(lab, 1 + np.where(ndi.sum(trous, lab, range(1, n + 1)) <= 500)[0])
trous = ndi.binary_dilation(trous, iterations=2) & clo
fill = cv2.inpaint(im, (trous * 255).astype('uint8'), 4, cv2.INPAINT_TELEA)
# nœud discret : légère teinte brun-roux au centre plutôt qu'un trou
noeud = ndi.gaussian_filter(trous.astype(float), 1.5)
tint = fill.astype(float) * (1 - 0.18 * noeud[..., None]) + np.array([95, 55, 30]) * 0.18 * noeud[..., None]
im = np.where(trous[..., None] | (noeud[..., None] > 0.05), tint, im).astype('uint8')
print('trous corrigés :', ndi.label(trous)[1])
# 2) olivier devant le brise-vue : le feuillage et le tronc de la passe mobilier passent devant les lames
ia = np.array(Image.open('fin/k4_ia.jpg').convert('RGB')); bx = (904, 327)
reg = (slice(470, 610), slice(1060, 1140))
sub_ia = ia[reg[0].start - bx[1]:reg[0].stop - bx[1], reg[1].start - bx[0]:reg[1].stop - bx[0]].astype(float)
sub = im[reg].astype(float)
r, g, b = sub_ia[..., 0], sub_ia[..., 1], sub_ia[..., 2]
hsv = cv2.cvtColor(sub_ia.astype('uint8'), cv2.COLOR_RGB2HSV).astype(float)
feuil = (hsv[..., 0] > 25) & (hsv[..., 0] < 75) & (hsv[..., 1] > 25)        # vert olive
tronc = np.zeros_like(feuil); tronc[60:, 40:60] = (np.abs(sub_ia[60:, 40:60] - sub[60:, 40:60]).mean(-1) > 25)
m = ndi.binary_closing(feuil | tronc, iterations=2); m = ndi.binary_opening(m, iterations=1)
a = ndi.gaussian_filter(m.astype(float), 0.8)[..., None]
im[reg] = (sub * (1 - a) + sub_ia * a).astype('uint8')
# 3) tache brune / forme blanche au pied de la terrasse : on reprend la haie voisine
y0, y1, x0, x1 = 632, 674, 1398, 1470
src = im[y0:y1, x0 + 75:x1 + 75].copy()
mk = np.zeros((y1 - y0, x1 - x0)); mk[3:-3, 3:-3] = 1; mk = ndi.gaussian_filter(mk, 3)[..., None]
im[y0:y1, x0:x1] = (im[y0:y1, x0:x1] * (1 - mk) + src * mk).astype('uint8')
# 4) bande claire au pied de l'extension : adoucie (flou vertical léger)
Image.fromarray(im).save(sys.argv[2], quality=94)
