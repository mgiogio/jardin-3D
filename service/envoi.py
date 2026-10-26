# Email « Votre diagnostic jardin est prêt » (Brevo, email transactionnel).
# Le diagnostic complet (plantes, budget, jardin imaginé) ne s'ouvre que depuis cet email : ça confirme l'adresse du client
# et l'ouverture + le clic améliorent la réputation d'envoi de Cover Green chez Gmail, Outlook, Orange...
#   ENVOI_EMAIL = off  : aucun envoi (l'écran de fin garde le bouton « Voir mon projet jardin »)
#                 test : envoi seulement aux adresses de EMAILS_TEST (recette)
#                 on   : envoi à tous les clients
import os, json, time, html, re, urllib.request

MODE = os.environ.get('ENVOI_EMAIL', 'test')
TESTS = {x.strip().lower() for x in os.environ.get('EMAILS_TEST', 'manuel@cover.green').split(',') if x.strip()}
CLE = os.environ.get('BREVO_API_KEY', '')
EXPEDITEUR = {'name': 'Cover Green', 'email': os.environ.get('EMAIL_EXPEDITEUR', 'notifications@service.cover.green')}
REPONSE = {'email': 'contact@cover.green', 'name': 'Cover Green'}
PAGE_DEFAUT = 'https://www.cover.green/mon-projet-jardin/?projet='
MAX_ENVOIS = 4
e = lambda s: html.escape(str(s or ''))
EMAIL_OK = re.compile(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', re.I)


def lire(d):
    f = f'{d}/email.json'
    return json.load(open(f)) if os.path.exists(f) else {'envois': [], 'clics': []}


def ecrire(d, M):
    json.dump(M, open(f'{d}/email.json', 'w'), ensure_ascii=False, indent=1)


def actif(email):
    if not CLE or MODE == 'off': return False
    return MODE == 'on' or (email or '').lower() in TESTS


def lien(d, pid):
    P = json.load(open(f'{d}/projet.json'))
    base = (P.get('page_projet') or PAGE_DEFAUT)
    return base + pid + '&src=email'


def contenu(d, pid):
    P = json.load(open(f'{d}/projet.json')); D = json.load(open(f'{d}/data.json')) if os.path.exists(f'{d}/data.json') else {}
    g = D.get('diag') or {}; prenom = ((P.get('contact') or {}).get('firstName') or '').strip()
    url = lien(d, pid)
    faits = []
    if g.get('soleil_ete_h_moyen'): faits.append(f"{str(g['soleil_ete_h_moyen']).replace('.', ',')} h de soleil par jour en été")
    if g.get('surface_jardin_m2'): faits.append(f"{g['surface_jardin_m2']} m² de jardin")
    intro = ('Bonjour ' + e(prenom) + ',') if prenom else 'Bonjour,'
    ville = (P.get('address') or {}).get('city') or D.get('ville') or ''
    li = ''.join(f'<tr><td style="padding:6px 0;font-size:15px;color:#1E211F">&#10003;&nbsp; {x}</td></tr>' for x in
                 ['Les plantes à planter chez vous, et quand', "Où créer de l'ombre et de l'intimité", 'Ce que coûte chaque idée', 'Votre jardin imaginé avec nos produits'])
    corps = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Votre diagnostic jardin est prêt</title></head>
<body style="margin:0;padding:0;background:#F4F6F7;font-family:Roboto,Arial,sans-serif">
<div style="display:none;max-height:0;overflow:hidden">{e(', '.join(faits) + '. ' if faits else '')}Vos plantes, vos idées et leur budget vous attendent.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F7"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px">
<tr><td style="padding:28px 28px 8px"><span style="display:inline-block;background:#049E00;color:#fff;font-weight:800;font-size:15px;padding:6px 10px;border-radius:4px;letter-spacing:.02em">COVER GREEN</span></td></tr>
<tr><td style="padding:8px 28px 0;font-size:16px;color:#1E211F">{intro}</td></tr>
<tr><td style="padding:10px 28px 0"><h1 style="margin:0;font-size:26px;line-height:1.2;color:#1E211F">Le diagnostic de votre jardin{(' à ' + e(ville)) if ville else ''} est prêt.</h1></td></tr>
{f'<tr><td style="padding:14px 28px 0"><div style="background:#EAF7E5;border-radius:10px;padding:12px 14px;font-size:15px;color:#1E211F">{e(" · ".join(faits))}</div></td></tr>' if faits else ''}
<tr><td style="padding:16px 28px 0"><table role="presentation" cellpadding="0" cellspacing="0">{li}</table></td></tr>
<tr><td style="padding:22px 28px 6px"><a href="{e(url)}" style="display:block;background:#EB5A00;color:#ffffff;text-decoration:none;text-align:center;font-weight:700;font-size:17px;padding:16px 20px;border-radius:8px">Voir mon diagnostic</a></td></tr>
<tr><td style="padding:6px 28px 24px;font-size:13px;color:#5B625E">Votre page reste disponible à tout moment depuis ce lien. Une question ? Répondez simplement à cet email.</td></tr>
</table>
<p style="font-size:12px;color:#5B625E;margin:16px 0 0">Cover Green · 300 avenue de la Royale, 34160 Castries · <a href="https://www.cover.green/" style="color:#5B625E">www.cover.green</a></p>
</td></tr></table></body></html>'''
    texte = (f"{'Bonjour ' + prenom if prenom else 'Bonjour'},\n\nLe diagnostic de votre jardin est prêt.\n" + (' · '.join(faits) + '\n' if faits else '')
             + f"\nVoir mon diagnostic : {url}\n\nUne question ? Répondez simplement à cet email.\nCover Green, www.cover.green\n")
    return corps, texte


def envoyer(d, pid, force=False):
    """Envoie l'email si l'envoi est actif pour ce client. Renvoie True si parti."""
    P = json.load(open(f'{d}/projet.json')); C = P.get('contact') or {}; email = (C.get('email') or '').strip()
    M = lire(d)
    if not EMAIL_OK.match(email) or not actif(email): return False
    if M['envois'] and not force: return True              # déjà envoyé (ex. photo ajoutée ensuite)
    if len(M['envois']) >= MAX_ENVOIS: return False
    corps, texte = contenu(d, pid)
    charge = {'sender': EXPEDITEUR, 'replyTo': REPONSE, 'to': [{'email': email, **({'name': C['firstName']} if C.get('firstName') else {})}],
              'subject': 'Votre diagnostic jardin est prêt', 'htmlContent': corps, 'textContent': texte, 'tags': ['diagnostic-jardin']}
    req = urllib.request.Request('https://api.brevo.com/v3/smtp/email', data=json.dumps(charge).encode(), method='POST',
                                 headers={'api-key': CLE, 'content-type': 'application/json', 'accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: rep = json.loads(r.read() or b'{}')
    except Exception as x:
        M.setdefault('erreurs', []).append({'le': time.strftime('%Y-%m-%d %H:%M'), 'erreur': str(x)[:200]}); ecrire(d, M); return False
    M['envois'].append({'le': time.strftime('%Y-%m-%d %H:%M'), 'a': email, 'id': rep.get('messageId', '')}); ecrire(d, M)
    return True


def etat(d):
    M = lire(d)
    return {'envoye': bool(M['envois']), 'n': len(M['envois']), 'clic': bool(M['clics'])}
