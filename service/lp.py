# Page d'entrée du « Diagnostic jardin » : un visuel, un encadré avec un seul bouton pour commencer, trois cartes de réassurance.
# Rendu côté serveur (indexable), inséré par le shortcode [cg_diagnostic_jardin] au-dessus du questionnaire, qui reste caché
# jusqu'au clic sur « Je commence ». Styles préfixés .cglp. On ne dévoile pas ici le contenu du diagnostic (plantes, produits).
import html

e = lambda s: html.escape(str(s or ''))

CSS = '''<style>
.cglp{--vert:#049E00;--orange:#EB5A00;--orange-survol:#C84800;--brume:#EAF7E5;--gris:#F4F6F7;--ligne:#E1E5E3;--txt:#1E211F;--muted:#5B625E;
--f:"Roboto","Roboto Secours",Arial,sans-serif;font:400 16px/1.55 var(--f);color:var(--txt);max-width:1080px;margin:0 auto;padding:32px 16px 8px}
.cglp *,.cglp *:before,.cglp *:after{box-sizing:border-box}
.cglp .entree{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(30,33,31,.08),0 8px 30px rgba(30,33,31,.06)}
.cglp .visuel{position:relative;min-height:420px;background:var(--gris) center/cover no-repeat}
.cglp .bulle{position:absolute;display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:10px 14px;font-size:14px;font-weight:500;
box-shadow:0 6px 18px rgba(0,0,0,.18);max-width:78%}
.cglp .bulle svg{flex:none;width:20px;height:20px}
.cglp .bulle.b1{left:18px;top:22px}.cglp .bulle.b2{right:18px;top:42%}.cglp .bulle.b3{left:18px;bottom:22px;background:var(--vert);color:#fff}
.cglp .boite{margin:20px;border:2px dashed #9AA29E;border-radius:12px;padding:36px 28px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:14px}
.cglp h1{font:800 34px/1.12 var(--f);margin:0;letter-spacing:-.01em;color:var(--txt)}
.cglp h1 .v{color:var(--vert)}.cglp h1 .o{color:var(--orange)}
.cglp .boite p{margin:0;color:var(--muted);font-size:16px;max-width:380px}
.cglp .cta{appearance:none;display:inline-flex;align-items:center;justify-content:center;height:56px;padding:0 32px;border-radius:8px;border:1px solid var(--orange);
background:var(--orange);color:#fff;font:600 17px/1 var(--f);cursor:pointer;margin-top:6px;min-width:260px}
.cglp .cta:hover{background:var(--orange-survol);border-color:var(--orange-survol)}
.cglp .cta:focus-visible{outline:3px solid var(--vert);outline-offset:2px}
.cglp .petit{font-size:14px;color:var(--muted)}.cglp .petit b{color:var(--txt)}
.cglp .atouts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
.cglp .atouts div{background:#fff;border-radius:14px;padding:22px 20px;text-align:center;box-shadow:0 1px 3px rgba(30,33,31,.06)}
.cglp .atouts i{display:inline-grid;place-items:center;width:44px;height:44px;border-radius:10px;background:var(--brume);color:var(--vert);margin-bottom:10px}
.cglp .atouts i svg{width:24px;height:24px}
.cglp .atouts b{display:block;font-size:17px;margin-bottom:4px}.cglp .atouts p{margin:0;color:var(--muted);font-size:14px}
@media (max-width:820px){.cglp{padding-top:16px}.cglp .entree{grid-template-columns:1fr}.cglp .visuel{min-height:260px}
.cglp .boite{margin:14px;padding:26px 18px}.cglp h1{font-size:28px}.cglp .cta{width:100%;min-width:0;padding:0 14px;font-size:16px;white-space:nowrap}.cglp .atouts{grid-template-columns:1fr}
.cglp .bulle{font-size:13px;padding:8px 11px}.cglp .bulle.b2{top:auto;bottom:64px}}
</style>'''

SOLEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#EB5A00" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
OEIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#1E211F" stroke-width="2" stroke-linecap="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>'
FEUILLE_V = '<svg viewBox="0 0 24 24" fill="none" stroke="#049E00" stroke-width="2" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7z"/></svg>'
FEUILLE = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15M5 19l7-7"/></svg>'
ICO = {'plante': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 21v-8M12 13c-4 0-6-3-6-7 4 0 6 3 6 7zM12 13c4 0 6-3 6-7-4 0-6 3-6 7zM7 21h10"/></svg>',
       'soleil': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
       'cadeau': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13M12 7c-2-4-6-3-5 0M12 7c2-4 6-3 5 0"/></svg>',
       'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg>',
       'plan': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 9h18M5 9l2-4h10l2 4M6 9v11M18 9v11M3 20h18"/></svg>'}


def rendre(base=''):
    fond = f'{base}/assets/refs/pergola_ensemble.jpg'
    return CSS + f'''<div class="cglp" id="cglp-accueil">
<div class="entree">
<div class="visuel" style="background-image:url('{e(fond)}')" role="img" aria-label="Une pergola Cover Green posée chez un client">
<span class="bulle b1">{SOLEIL}Le soleil heure par heure</span>
<span class="bulle b2">{FEUILLE_V}Quoi planter, et quand</span>
<span class="bulle b3">{FEUILLE}Le potentiel de votre jardin</span></div>
<div class="boite">
<h1>Le diagnostic gratuit de votre <span class="v">jardin</span><span class="o">.</span></h1>
<p>Découvrez ce que votre jardin peut devenir : quoi planter et quand, où créer de l'ombre et de l'intimité, et votre jardin imaginé avec nos produits.</p>
<button type="button" class="cta" data-cgq-commencer>Je commence mon diagnostic</button>
<span class="petit"><b>Gratuit</b> · dans votre boîte mail en 3 minutes · ★ 4,6/5 sur Trustpilot</span>
</div></div>
<div class="atouts">
<div><i>{ICO['plante']}</i><b>Quoi planter, et quand</b><p>Des plantes choisies pour votre région, votre soleil et votre temps, avec le bon mois pour les planter.</p></div>
<div><i>{ICO['soleil']}</i><b>Le potentiel de votre jardin</b><p>Le soleil heure par heure, les vis-à-vis, les coins à valoriser : ce que votre jardin peut devenir.</p></div>
<div><i>{ICO['plan']}</i><b>Votre jardin imaginé</b><p>À partir de votre photo, nos produits posés chez vous, au bon endroit, avec un budget clair.</p></div>
</div></div>'''
