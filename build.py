#!/usr/bin/env python3
"""Assemble finvd.ch : page d'accueil + un site par entité (canton, communes), avec un sélecteur.

Chaque entité est publiée par son propre dépôt (site autonome « site/index.html »). Ce script récupère
la dernière version de chacun, y ajoute la barre de sélection et isole la mémoire du navigateur
(un préfixe par entité, car tous les sites partagent le même domaine), puis écrit le dossier dist/.

Utilisation : python3 build.py              (clone les dépôts publics listés dans communes.json)
              python3 build.py --local vaud=/chemin/index.html epalinges=/chemin/index.html
"""
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(RACINE, "dist")
TAILLE_MIN = 100_000  # un site plus petit est sans doute cassé : on ne publie pas


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def ecrire(chemin, texte):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)


def recuperer(e, tmp, locaux):
    """Renvoie (html, version) du site de l'entité."""
    if e["id"] in locaux:
        return lire(locaux[e["id"]]), "local"
    dest = os.path.join(tmp, e["id"])
    subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", e["branche"],
                    f"https://github.com/{e['depot']}", dest], check=True)
    sha = subprocess.run(["git", "-C", dest, "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                         check=True).stdout.strip()
    return lire(os.path.join(dest, e["page"])), sha


def barre(entites, courant):
    options = "".join(f'<option value="{html.escape(e["id"])}"{" selected" if e["id"] == courant else ""}>'
                      f'{html.escape(e["nom"])}</option>' for e in entites)
    return f'''<style id="finvd-css">
#finvd-bar{{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;padding:7px 16px;background:#14202b;color:#e8edf2;
font:600 13px/1.3 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;position:relative;z-index:50}}
#finvd-bar a{{color:#e8edf2;text-decoration:none}}#finvd-bar .logo{{letter-spacing:.02em}}#finvd-bar .logo b{{color:#7fb6e6}}
#finvd-bar label{{display:flex;align-items:center;gap:8px;font-weight:500;color:#b9c4ce}}
#finvd-bar select{{font:inherit;font-weight:600;color:#14202b;background:#e8edf2;border:0;border-radius:6px;padding:4px 8px}}
#finvd-bar .sp{{flex:1}}#finvd-bar .note{{font-weight:400;color:#8fa0ae;font-size:12px}}
</style>
<div id="finvd-bar"><a class="logo" href="../">fin<b>vd</b>.ch</a>
<label>Voir les finances de <select id="finvd-sel" aria-label="Choisir le canton ou la commune">{options}</select></label>
<span class="sp"></span><span class="note">Projet indépendant, sans lien avec l'administration</span></div>
<script>document.getElementById("finvd-sel").addEventListener("change",function(){{location.href="../"+this.value+"/"}});</script>
'''


def prefixe(id_):
    """Chaque entité garde ses propres réglages (onglet, service choisi) malgré le domaine partagé."""
    return ('<script>(function(){try{var P=%s,S=Storage.prototype,g=S.getItem,s=S.setItem,r=S.removeItem;'
            'S.getItem=function(k){return this===window.localStorage?g.call(this,P+k):g.call(this,k)};'
            'S.setItem=function(k,v){return this===window.localStorage?s.call(this,P+k,v):s.call(this,k,v)};'
            'S.removeItem=function(k){return this===window.localStorage?r.call(this,P+k):r.call(this,k)};}'
            'catch(e){}})();</script>' % json.dumps(id_ + ":"))


def transformer(page, e, entites):
    if "<body>" not in page or "<head>" not in page:
        raise SystemExit(f"{e['id']} : structure de page inattendue (balises head/body)")
    if '<meta charset="utf-8">' in page:  # le jeu de caractères doit rester dans les 1024 premiers octets
        page = page.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + prefixe(e["id"]), 1)
    else:
        page = page.replace("<head>", "<head>" + prefixe(e["id"]), 1)
    page = page.replace("<body>", "<body>" + barre(entites, e["id"]), 1)
    return page


def accueil(cfg, versions):
    cartes = "".join(f'''<a class="card" href="{html.escape(e["id"])}/"><h2>{html.escape(e["nom"])}</h2>
<p>{html.escape(e["description"])}</p><span class="go">Ouvrir le site</span></a>''' for e in cfg["entites"])
    sources = "".join(f'<li><a href="https://github.com/{html.escape(e["depot"])}">{html.escape(e["nom"])}</a> '
                      f'(version {html.escape(versions[e["id"]])})</li>' for e in cfg["entites"])
    modele = lire(os.path.join(RACINE, "templates", "accueil.html"))
    return modele.replace("{{CARTES}}", cartes).replace("{{SOURCES}}", sources).replace("{{DOMAINE}}", cfg["domaine"])


def main():
    cfg = json.loads(lire(os.path.join(RACINE, "communes.json")))
    locaux = {}
    if "--local" in sys.argv:
        for a in sys.argv[sys.argv.index("--local") + 1:]:
            k, v = a.split("=", 1)
            locaux[k] = v
    shutil.rmtree(DIST, ignore_errors=True)
    versions = {}
    with tempfile.TemporaryDirectory() as tmp:
        for e in cfg["entites"]:
            page, versions[e["id"]] = recuperer(e, tmp, locaux)
            if len(page) < TAILLE_MIN:
                raise SystemExit(f"{e['id']} : page trop petite ({len(page)} octets), publication annulée")
            ecrire(os.path.join(DIST, e["id"], "index.html"), transformer(page, e, cfg["entites"]))
            print(f"{e['id']}: {len(page) // 1024} ko, version {versions[e['id']]}")
    ecrire(os.path.join(DIST, "index.html"), accueil(cfg, versions))
    ecrire(os.path.join(DIST, "404.html"), '<meta http-equiv="refresh" content="0;url=/"><a href="/">finvd.ch</a>')
    ecrire(os.path.join(DIST, "CNAME"), cfg["domaine"] + "\n")
    ecrire(os.path.join(DIST, ".nojekyll"), "")
    ecrire(os.path.join(DIST, "versions.json"), json.dumps(versions, indent=1))


if __name__ == "__main__":
    main()
