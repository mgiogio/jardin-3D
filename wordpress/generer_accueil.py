# Génère wordpress/accueil-diagnostic.html : la page d'entrée « Diagnostic jardin », servie par WordPress (snippet),
# à partir du même gabarit que le service (service/lp.py) et de la même bordure de plantes que le questionnaire.
# Usage : python3 wordpress/generer_accueil.py   puis recopier le fichier dans le snippet (bloc ACCUEIL).
import os, re, subprocess, sys
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, '..', 'service'))
import lp
js = open(os.path.join(ICI, '..', 'service', 'questionnaire', 'q.js'), encoding='utf-8').read()
i = js.index('  function bordure() {'); j = js.index('  var FRISE =')
svg = subprocess.run(['node', '-e', js[i:j] + '\nprocess.stdout.write(bordure())'], capture_output=True, text=True, check=True).stdout
svg = re.sub(r'(\d+\.\d{2})\d+', r'\1', svg)                       # arrondi : fichier plus léger
html = lp.rendre('', '{{QUESTIONNAIRE}}')
html = html.replace("/assets/refs/pergola_ensemble.jpg", "/wp-content/uploads/2026/08/brottier-2-768x1024.jpg")
css_frise = ('<style>.cglp-page{background:#F4F6F7;display:flex;flex-direction:column}.cglp .cta{text-decoration:none}.cglp .cta:hover{color:#fff}'
             '.cglp-frise{margin-top:auto;padding-top:24px;height:110px;overflow:hidden;pointer-events:none}.cglp-frise svg{display:block;width:100%;height:110px}'
             '@media (min-width:768px){.cglp-frise,.cglp-frise svg{height:160px}}</style>')
js_page = ('<script>(function(){var p=document.getElementById("cglp-page");function f(){try{var t=p.getBoundingClientRect().top+window.scrollY;'
           'p.style.minHeight=Math.max(0,innerHeight-t)+"px"}catch(e){}}f();addEventListener("resize",f)})()</script>')
out = css_frise + '<div class="cglp-page" id="cglp-page">' + html + '<div class="cglp-frise">' + svg + '</div></div>' + js_page
open(os.path.join(ICI, 'accueil-diagnostic.html'), 'w', encoding='utf-8').write(out)
print(len(out), 'octets')

# recopie dans le snippet (bloc ACCUEIL)
sn = os.path.join(ICI, 'snippet-diagnostic-jardin.php'); p = open(sn, encoding='utf-8').read()
i = p.index("<<<'HTML'\n") + len("<<<'HTML'\n"); j = p.index("\nHTML;")
open(sn, 'w', encoding='utf-8').write(p[:i] + out + p[j:]); print('snippet mis à jour')
