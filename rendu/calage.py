# Calage automatique de la caméra sur une façade : lignes de fuite (horizontales de la façade + verticales)
# -> focale (vfov), inclinaison (pitch), roulis (roll) et direction de la façade dans la scène.
# Usage : python3 calage.py photo.jpg x0,y0,x1,y1 [hauteur_appareil=1.5] [coin_bas_x,coin_bas_y]
# x0..y1 = rectangle autour de la façade (lignes de toiture, fenêtres, portes).
import sys, json, cv2, numpy as np
im = cv2.imread(sys.argv[1]); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); Hh, Ww = g.shape
x0, y0, x1, y1 = map(int, sys.argv[2].split(',')); h = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
segs = cv2.createLineSegmentDetector(0).detect(g[y0:y1, x0:x1])[0].reshape(-1, 4) + [x0, y0, x0, y0]
Hs, Vs = [], []
for a, b, c, d in segs:
    if np.hypot(c - a, d - b) < 35: continue
    ang = np.degrees(np.arctan2(d - b, c - a)) % 180
    (Hs if ang < 25 or ang > 155 else Vs if 70 < ang < 110 else []).append((a, b, c, d))
def vp(S):
    S = np.array(S); L = [np.cross([a, b, 1], [c, d, 1]) for a, b, c, d in S]; L = [l / np.hypot(l[0], l[1]) for l in L]
    rng = np.random.default_rng(0); best = None
    for _ in range(3000):
        i, j = rng.choice(len(L), 2, replace=False); p = np.cross(L[i], L[j])
        if abs(p[2]) < 1e-9: continue
        p = p / p[2]; e = []
        for a, b, c, d in S:
            m = np.array([(a + c) / 2, (b + d) / 2]); v1 = np.array([c - a, d - b]); v2 = p[:2] - m
            e.append(np.degrees(np.arccos(min(1, abs(v1 @ v2) / np.linalg.norm(v1) / np.linalg.norm(v2)))))
        inl = np.array(e) < 1.0
        if best is None or inl.sum() > best[0]: best = (inl.sum(), inl)
    A = np.array([L[k] for k in range(len(L)) if best[1][k]]); q = np.linalg.svd(A)[2][-1]; return q[:2] / q[2], int(best[0]), len(S)
(vh, nh, th), (vv, nv, tv) = vp(Hs), vp(Vs)
cx, cy = Ww / 2, Hh / 2; d = (vh - [cx, cy]) @ (vv - [cx, cy]); f = np.sqrt(-d)
cdir = lambda u, v: np.array([(u - cx) / f, (v - cy) / f, 1.0])
down = cdir(*vv); down /= np.linalg.norm(down)
pitch = np.degrees(np.arcsin(down[2])); roll = np.degrees(np.arctan2(down[0], down[1])); p = np.radians(pitch)
def toworld(dc):
    t = np.array([dc[0], -dc[1], -dc[2]]); c, s = np.cos(-p), np.sin(-p); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]]) @ t
u = toworld(cdir(*vh)); u[1] = 0; u /= np.linalg.norm(u)
if u[0] < 0: u = -u                       # direction de la façade vers la droite de l'image
n = np.array([u[2], 0, -u[0]]) if np.array([u[2], 0, -u[0]])[2] > 0 else np.array([-u[2], 0, u[0]])  # normale vers l'appareil
out = {'cam': {'h': h, 'pitch': round(pitch, 2), 'roll': round(roll, 2), 'vfov': round(2 * np.degrees(np.arctan(cy / f)), 2), 'yaw': 0},
       'facade_dir': u[[0, 2]].round(3).tolist(), 'facade_normale': n[[0, 2]].round(3).tolist(),
       'rotY_murale': round(float(np.degrees(np.arctan2(n[2], -n[0]))), 1),  # mur du modèle (+x local) tourné vers la maison
       'lignes': {'horizontales': [nh, th], 'verticales': [nv, tv]}}
if len(sys.argv) > 4:
    a, b = map(float, sys.argv[4].split(',')); dw = toworld(cdir(a, b)); t = h / -dw[1]; out['coin_bas'] = [round(dw[0] * t, 2), round(dw[2] * t, 2)]
print(json.dumps(out, indent=1))
