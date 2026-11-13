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
LOGO = os.environ.get('LOGO_EMAIL', 'https://diagnostic-jardin-349938922301.europe-west1.run.app/q/logo-email.png')
MAX_ENVOIS = 4
e = lambda s: html.escape(str(s or ''))
maj = lambda s: s[:1].upper() + s[1:]
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
    g = D.get('diag') or {}
    url = lien(d, pid)
    mot = 'terrasse' if g.get('mode') == 'etage' else 'jardin'
    faits = []
    if g.get('soleil_ete_h_moyen'): faits.append(f"{max(1, round(g['soleil_ete_h_moyen']))} h de soleil par jour en été")
    if g.get('surface_jardin_m2') and mot == 'jardin': faits.append(f"{round(g['surface_jardin_m2'])} m² de jardin")
    if g.get('mode') == 'etage' and g.get('etage'): faits.append(f"terrasse au {g['etage']}{'er' if g['etage'] == 1 else 'e'} étage")
    photo = bool(P.get('photos')) or os.path.exists(f'{d}/photo.jpg')
    ville = (P.get('address') or {}).get('city') or D.get('ville') or ''
    titre = f"Le diagnostic de votre {mot}{(' à ' + ville) if ville else ''} est prêt"
    li = ''.join(f'<tr><td width="26" valign="top" style="padding:7px 0;font-size:15px;line-height:22px;color:#049E00;font-weight:700">&#10003;</td>'
                 f'<td style="padding:7px 0;font-size:15px;line-height:22px;color:#1E211F">{x}</td></tr>' for x in
                 ['Les plantes adaptées à votre exposition, et quand les planter', "Où créer de l'ombre et de l'intimité",
                  'Le budget de chaque idée'] + ([f'Votre {mot} imaginé{"e" if mot == "terrasse" else ""} en image'] if photo else []))
    corps = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{e(titre)}</title></head>
<body style="margin:0;padding:0;background:#F4F6F7;font-family:Roboto,Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(maj(', '.join(faits)) + '. ' if faits else '')}Vos plantes, vos idées et leur budget vous attendent.&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F4F6F7"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;background:#ffffff;border-radius:14px">
<tr><td style="padding:28px 28px 0"><a href="https://www.cover.green/" style="text-decoration:none"><img src="{LOGO}" width="108" height="48" alt="Cover Green" style="display:block;border:0;outline:none;width:108px;height:48px"></a></td></tr>
<tr><td style="padding:24px 28px 0"><h1 style="margin:0;font-size:26px;line-height:1.25;font-weight:800;color:#1E211F">Le diagnostic de votre {mot}{(' à <span style="white-space:nowrap">' + e(ville) + '</span>') if ville else ''} est prêt.</h1></td></tr>
{f'<tr><td style="padding:16px 28px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="background:#EAF7E5;border-radius:10px;padding:12px 16px;font-size:15px;line-height:22px;color:#1E211F">{e(maj(", ".join(faits))).replace(" h ", "&nbsp;h ").replace(" m²", "&nbsp;m²")}.</td></tr></table></td></tr>' if faits else ''}
<tr><td style="padding:18px 28px 0;font-size:15px;line-height:22px;color:#1E211F">Nous avons étudié l'ensoleillement et les vis-à-vis de votre {mot}, heure par heure. Dans votre diagnostic :</td></tr>
<tr><td style="padding:8px 28px 0"><table role="presentation" cellpadding="0" cellspacing="0" border="0">{li}</table></td></tr>
<tr><td style="padding:24px 28px 8px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" bgcolor="#EB5A00" style="border-radius:8px"><a href="{e(url)}" style="display:block;color:#ffffff;text-decoration:none;font-weight:700;font-size:17px;line-height:22px;padding:16px 20px">Voir mon diagnostic</a></td></tr></table></td></tr>
<tr><td style="padding:8px 28px 28px;font-size:13px;line-height:19px;color:#5B625E">Ce lien reste valable : gardez cet email pour retrouver votre diagnostic. Une question ? Répondez simplement, nous vous lisons.</td></tr>
</table>
<p style="font-size:12px;line-height:18px;color:#5B625E;margin:16px 0 0">Cover Green - 300 avenue de la Royale, 34160 Castries - <a href="https://www.cover.green/" style="color:#5B625E">www.cover.green</a><br>Vous recevez cet email car vous avez demandé un diagnostic sur www.cover.green.</p>
</td></tr></table></body></html>'''
    texte = (f"{titre}.\n\n" + (maj(', '.join(faits)) + '.\n\n' if faits else '')
             + f"Dans votre diagnostic : les plantes adaptées à votre exposition, où créer de l'ombre et de l'intimité, le budget de chaque idée{(' et votre ' + mot + ' en image') if photo else ''}.\n\n"
             + f"Voir mon diagnostic : {url}\n\nCe lien reste valable : gardez cet email pour retrouver votre diagnostic. Une question ? Répondez simplement, nous vous lisons.\n\nCover Green - www.cover.green\n")
    return corps, texte


def SUJET(d):
    D = json.load(open(f'{d}/data.json')) if os.path.exists(f'{d}/data.json') else {}
    return f"Votre diagnostic {'terrasse' if (D.get('diag') or {}).get('mode') == 'etage' else 'jardin'} est prêt"


def envoyer(d, pid, force=False):
    """Envoie l'email si l'envoi est actif pour ce client. Renvoie True si parti."""
    P = json.load(open(f'{d}/projet.json')); C = P.get('contact') or {}; email = (C.get('email') or '').strip()
    M = lire(d)
    if not EMAIL_OK.match(email) or not actif(email): return False
    if M['envois'] and not force: return True              # déjà envoyé (ex. photo ajoutée ensuite)
    if len(M['envois']) >= MAX_ENVOIS: return False
    corps, texte = contenu(d, pid)
    charge = {'sender': EXPEDITEUR, 'replyTo': REPONSE, 'to': [{'email': email, **({'name': C['firstName']} if C.get('firstName') else {})}],
              'subject': SUJET(d), 'htmlContent': corps, 'textContent': texte, 'tags': ['diagnostic-jardin']}
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
