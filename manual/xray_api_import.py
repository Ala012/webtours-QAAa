"""Import des tests manuels dans Xray Cloud via l'API (sans passer par l'UI).

Prérequis (à définir vous-même, ne jamais commiter / partager) :
  set XRAY_CLIENT_ID=...        (Xray > Settings > API Keys)
  set XRAY_CLIENT_SECRET=...
  set JIRA_PROJECT_KEY=RSVV      (optionnel, défaut RSVV)

Usage :
  python xray_api_import.py --dry-run   # affiche le JSON sans rien envoyer
  python xray_api_import.py             # envoie les 36 tests

Limites : l'import JSON bulk d'Xray ne gère pas les dossiers du Test Repository ;
le chemin (/WebTours/RSVA.../FT...) est donc mis en label et en préfixe de description.
Endpoints Xray Cloud v2 écrits de mémoire : à vérifier à la première exécution.
"""
import json
import os
import sys

import requests

from gen_xray_csv import T, MODS, TYPES

BASE = "https://xray.cloud.getxray.app/api/v2"


def build(project):
    counters = {m: 2400 for m in MODS}
    out = []
    for mod, typ, title, pre, steps, exp in T:
        counters[mod] += 1
        name, lab = MODS[mod]
        lines = steps.split("\n")
        st = [{"action": a, "data": "", "result": exp if i == len(lines) - 1 else ""}
              for i, a in enumerate(lines)]
        out.append({
            "testtype": "Manual",
            "fields": {
                "summary": f"[{mod}-{counters[mod]}] {title}",
                "project": {"key": project},
                "description": f"Dossier : /WebTours/{mod} - {name}/{typ} - {TYPES[typ]}\nPréconditions : {pre}",
                "labels": ["MANUAL", lab, f"MODULE-{mod}", typ, mod, f"TYPE-{typ}", "WEBTOURS"],
            },
            "steps": st,
        })
    return out


def main():
    project = os.getenv("JIRA_PROJECT_KEY", "RSVV")
    payload = build(project)
    if "--dry-run" in sys.argv:
        print(json.dumps(payload[:2], indent=2, ensure_ascii=False))
        print(f"... {len(payload)} tests au total")
        return
    cid, sec = os.getenv("XRAY_CLIENT_ID"), os.getenv("XRAY_CLIENT_SECRET")
    if not cid or not sec:
        sys.exit("XRAY_CLIENT_ID / XRAY_CLIENT_SECRET non définis")
    tok = requests.post(f"{BASE}/authenticate", json={"client_id": cid, "client_secret": sec})
    tok.raise_for_status()
    h = {"Authorization": f"Bearer {tok.json()}", "Content-Type": "application/json"}
    r = requests.post(f"{BASE}/import/test/bulk", headers=h, json=payload)
    print(r.status_code, r.text)
    r.raise_for_status()


if __name__ == "__main__":
    main()
