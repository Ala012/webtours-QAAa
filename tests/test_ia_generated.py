"""Tests générés avec l'aide d'une IA pour les 4 anomalies sans test automatique.

Anomalies : BUG-02, BUG-06, BUG-07, BUG-11 (voir results/BUGS.md).
Chaque test décrit le comportement CORRECT attendu : il échoue tant que l'anomalie existe.
Sondage préalable des 4 anomalies le 2026-11-21 : toutes reproduites.
À relire par un humain avant d'être intégrés à la suite principale.
"""
import pytest
import requests

from conftest import CGI


@pytest.mark.pt
def test_pt_admin_sans_authentification():  # BUG-07
    r = requests.get(f"{CGI}/admin.pl", timeout=15)
    assert "admin page" not in r.text.lower(), "BUG-07: page d'administration accessible sans authentification"


@pytest.mark.et
def test_et_printenv_sans_erreur_serveur():  # BUG-11
    r = requests.get(f"{CGI}/printenv.pl", timeout=15)
    assert r.status_code < 500, f"BUG-11: printenv.pl renvoie HTTP {r.status_code}"


@pytest.mark.et
def test_et_xss_reflechi_depart(client):  # BUG-06
    payload = "<script>alert(1)</script>"
    r = client.search(depart=payload)
    assert payload not in r.text, "BUG-06: le champ depart est renvoyé sans échappement (XSS réfléchi)"


@pytest.mark.et
@pytest.mark.parametrize("date", ["13/45/2026", "abc", "", "00/00/0000"])
def test_et_date_invalide_sans_plantage(client, date):  # BUG-02
    r = client.search(date=date)
    assert "</html>" in r.text.lower(), f"BUG-02: page tronquée (plantage du script) pour la date {date!r}"
