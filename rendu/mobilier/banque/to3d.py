# Image produit -> GLB texturé via Trellis (Replicate). Fichiers sortie : banque/<nom>.glb
import json, os, sys, base64, time, glob, subprocess, concurrent.futures as cf
K = open('/tmp/claude-0/-home-claude-jardin-3d/4d30a8f4-3b79-52d4-b2d0-5ec853a40f6b/scratchpad/.replicate_key').read().strip()
V = 'e8f6c45206993f297372f5436b90350817bd9b4a0d52d2a76df50c1c8afa2b3c'
def api(url, data=None):
    cmd = ['curl', '-s', '-H', 'Authorization: Bearer ' + K, '-H', 'Content-Type: application/json']
    if data: cmd += ['-d', '@-']
    return json.loads(subprocess.run(cmd + [url], input=json.dumps(data) if data else None, capture_output=True, text=True).stdout)
def go(png):
    k = os.path.basename(png)[:-4]; out = f'banque/{k}.glb'
    if os.path.exists(out): return k, 'deja'
    uri = 'data:image/png;base64,' + base64.b64encode(open(png, 'rb').read()).decode()
    p = api('https://api.replicate.com/v1/predictions', {"version": V, "input": {"images": [uri], "generate_model": True, "generate_color": False, "texture_size": 2048, "mesh_simplify": 0.95, "ss_sampling_steps": 25, "slat_sampling_steps": 25, "randomize_seed": False, "seed": int(os.environ.get("SEED", 1))}})
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(5); p = api(p['urls']['get'])
    if p['status'] != 'succeeded': return k, 'ECHEC ' + str(p.get('error'))[:200]
    subprocess.run(['curl', '-s', '-o', out, p['output']['model_file']]); return k, 'ok'
fs = [f for f in sorted(glob.glob('banque/*.png')) if len(sys.argv) < 2 or os.path.basename(f)[:-4] in sys.argv[1:]]
with cf.ThreadPoolExecutor(7) as ex:
    for k, s in ex.map(go, fs): print(k, s, flush=True)
