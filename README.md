# WebTours QA

Tests manuels (Jira/Xray) et automatiques (pytest + Selenium + requests) de l'application WebTours 1.0.

## Structure
- `manual/gen_xray_csv.py` : génère `xray_tests.csv` (36 tests : RSVA/RSVF/RSVI x FT/ET/BT/PT x 3) et `stories.csv` (7 user stories)
- `tests/` : suite automatique (même numérotation RSVx-24xx)
- `Jenkinsfile` : pipeline Jenkins

## Lancer
1. Installer Java 8 et Strawberry Perl, lancer `startserver.bat` (http://127.0.0.1:1080/WebTours/index.htm)
2. `pip install -r requirements.txt`
3. `pytest` (ou `pytest -m pt`)

Variable : `WEBTOURS_URL` (défaut http://127.0.0.1:1080), `HEADLESS=0` pour voir le navigateur.

Note : les noms de frames, champs et messages d'erreur sont écrits de mémoire pour WebTours ; à ajuster au premier run contre l'appli réelle.
