# Lance un workflow sur fofr/any-comfyui-workflow. Usage : python3 run.py wf.json inputs.zip prefixe_sortie
import sys, os, json, time, urllib.request, subprocess
tok = os.environ['REPLICATE_API_TOKEN']; V = '16d0a881fbfc066f0471a3519a347db456fe8cbcbd53abb435a50a74efaeb427'
up = subprocess.run(['curl', '-sS', '-X', 'POST', '-H', 'Authorization: Bearer ' + tok, '-F', f'content=@{sys.argv[2]};type=application/zip',
                     'https://api.replicate.com/v1/files'], capture_output=True, text=True).stdout
zurl = json.loads(up)['urls']['get']
body = {'version': V, 'input': {'workflow_json': open(sys.argv[1]).read(), 'input_file': zurl, 'output_format': 'png', 'randomise_seeds': False}}
req = urllib.request.Request('https://api.replicate.com/v1/predictions', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
p = json.load(urllib.request.urlopen(req, timeout=60)); t0 = time.time()
while p['status'] not in ('succeeded', 'failed', 'canceled'):
    time.sleep(5); p = json.load(urllib.request.urlopen(urllib.request.Request(p['urls']['get'], headers={'Authorization': 'Bearer ' + tok})))
if p['status'] != 'succeeded':
    print('ÉCHEC', p.get('error')); print((p.get('logs') or '')[-2500:]); sys.exit(1)
for i, u in enumerate(p['output']):
    name = sys.argv[3] + '_' + u.split('/')[-1]; open(name, 'wb').write(urllib.request.urlopen(u).read()); print(name)
print('temps', round(time.time() - t0), 's', p.get('metrics'))
