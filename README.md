# WebTours QA

Tests manuels (Jira / Xray) et tests automatiques (pytest, requests, Selenium) de l'application de démonstration **WebTours 1.0**, avec un pipeline Jenkins.

- **57 tests automatiques** : 12 par module (authentification, vols, itinéraire), 7 tests HTTP pour les anomalies sans test, 14 tests d'interface avec Chrome.
- **36 cas de test manuels** rédigés pour Xray, avec 7 user stories.
- **11 anomalies** de WebTours documentées, chacune couverte par un test.

## Contenu du dépôt

| Chemin | Rôle |
|---|---|
| `tests/test_rsva_auth.py` | Authentification (RSVA) : 12 tests |
| `tests/test_rsvf_flight.py` | Vols (RSVF) : 12 tests |
| `tests/test_rsvi_itinerary.py` | Itinéraire (RSVI) : 12 tests |
| `tests/test_ui_all.py` | 14 tests d'interface Selenium couvrant toutes les pages |
| `tests/test_ia_generated.py` | 7 tests HTTP pour BUG-02, 06, 07 et 11 |
| `tests/conftest.py` | Fixtures : client HTTP WebTours et navigateur Chrome |
| `capture_plugin.py` | Module pytest : capture d'écran de Chrome à la fin de chaque test d'interface |
| `manual/` | Cas de test Xray (`xray_tests.csv`, 36 cas), user stories (`stories.csv`), anomalies (`bugs.csv`), scripts de génération et d'import |
| `results/BUGS.md` | Les 11 anomalies avec leurs preuves |
| `Jenkinsfile` | Pipeline Jenkins |
| `pytest.ini`, `requirements.txt` | Marqueurs pytest (`ft`, `et`, `bt`, `pt`) et dépendances |

La suite principale suit une grille : 3 modules (RSVA, RSVF, RSVI) x 4 types de test (FT fonctionnel, ET erreur, BT limites, PT permissions) x 3 tests = 36 tests. Les identifiants `RSVx-24xx` sont les mêmes que ceux des cas manuels.

## Prérequis

- Python 3.12
- Google Chrome (pour les tests d'interface)
- WebTours en marche sur `http://127.0.0.1:1080/WebTours/index.htm` (Java 8 et Strawberry Perl, puis `StartServer.bat`)

```
pip install -r requirements.txt
```

## Lancer les tests

```
python -m pytest tests                       # toute la suite (57 tests)
python -m pytest tests -m pt                 # un type de test : ft, et, bt ou pt
python -m pytest tests/test_rsva_auth.py::test_ft_login_valide_http   # un seul test
python -m pytest tests -p capture_plugin     # avec captures d'écran (dossier results/captures/)
```

Rapports HTML et JUnit :

```
python -m pytest tests --html=results/report.html --self-contained-html --junitxml=results/report.xml
```

Variables d'environnement :

| Variable | Rôle | Défaut |
|---|---|---|
| `WEBTOURS_URL` | Adresse de WebTours | `http://127.0.0.1:1080` |
| `HEADLESS` | `0` pour voir la fenêtre Chrome | `1` (sans fenêtre) |

## Résultats

Dernière exécution complète (2026-11-21) : **39 réussis, 18 échoués** sur 57 tests.

Les 18 échecs sont **17 anomalies de WebTours** et **1 erreur de test** (`test_ft_recherche_ui`, dont le sélecteur cherche un lien « flights » alors que le lien est `welcome.pl?page=search`). Les tests décrivent le comportement attendu : ils échouent tant que l'anomalie existe.

| ID | Gravité | Anomalie | Test |
|---|---|---|---|
| BUG-01 | Critique | `reservations.pl` utilisable sans connexion | `test_pt_reservations_sans_login` |
| BUG-02 | Haute | Plantage du script Perl sur une date invalide | `test_et_date_invalide_sans_plantage` |
| BUG-03 | Haute | Identifiant de vol inexistant accepté | `test_pt_flightid_falsifie` |
| BUG-04 | Haute | Achat accepté avec une carte invalide | `test_et_carte_invalide` |
| BUG-05 | Haute | « Cancel All » échoue | `test_ft_annuler_tout` |
| BUG-06 | Haute | XSS réfléchi sur le champ `depart` | `test_et_xss_reflechi_depart` |
| BUG-07 | Haute | `admin.pl` accessible sans authentification | `test_pt_admin_sans_authentification`, `test_ui_administration_sans_authentification` |
| BUG-08 | Moyenne | Vols proposés de Paris vers Paris | `test_et_meme_ville` |
| BUG-09 | Moyenne | Date de retour avant le départ acceptée | `test_et_retour_avant_depart` |
| BUG-10 | Moyenne | Nombre de passagers hors bornes accepté | `test_bt_passagers` |
| BUG-11 | Basse | `printenv.pl` renvoie HTTP 500 | `test_et_printenv_sans_erreur_serveur` |

Le détail et les preuves sont dans `results/BUGS.md`.

## Intégration continue (Jenkins)

Le `Jenkinsfile` :

1. récupère ce dépôt (public, branche `main`) ;
2. installe les dépendances ;
3. vérifie que WebTours répond, et le démarre sinon (dossier `C:\WebTours` par défaut, paramètre `WEBTOURS_HOME`) ;
4. lance pytest avec les rapports JUnit et HTML ;
5. publie les résultats et archive `report.html`, `report.xml` et les captures.

- **Un seul test par défaut** : le paramètre `TESTS` vaut `tests/test_rsva_auth.py::test_ft_login_valide_http`. Mettre `tests` pour lancer toute la suite.
- **Déclencheurs** : vérification du dépôt toutes les 5 minutes et une exécution chaque nuit.
- **Résultat « instable »** (jaune) quand des tests échouent à cause des anomalies de WebTours ; « en erreur » (rouge) pour une vraie panne.
- **Job Jenkins** : « Pipeline script from SCM », SCM Git, URL du dépôt, branche `*/main`, chemin du script `Jenkinsfile`. L'agent doit être sous Windows avec Python 3.12, WebTours et, pour les tests d'interface, Google Chrome.

## Tests générés avec l'aide d'une IA

`tests/test_ui_all.py` et `tests/test_ia_generated.py` ont été écrits avec l'aide d'une IA et n'ont pas été relus par un humain. Un test attendu en échec qui passe est suspect : c'est ainsi qu'un faux succès a été trouvé et corrigé dans les tests d'interface.
