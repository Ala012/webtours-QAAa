"""RSVI - Itinerary (FT / ET / BT / PT)."""
import re
import uuid
import pytest
from conftest import WebTours


def _book(c):
    r = c.search()
    m = re.search(r'name="outboundFlight"\s+value="([^"]+)"', r.text)
    assert m, "aucun vol à réserver"
    c.post("reservations.pl", {"outboundFlight": m.group(1), "numPassengers": "1",
                               "reserveFlights.x": 1, "reserveFlights.y": 1})
    c.post("reservations.pl", {"firstName": "A", "lastName": "B", "address1": "x", "address2": "y",
                               "pass1": "A B", "creditCard": "4111111111111111", "expDate": "12/30",
                               "outboundFlight": m.group(1), "numPassengers": "1",
                               "buyFlights.x": 1, "buyFlights.y": 1})


def _fresh_user():
    c = WebTours()
    c.home()
    u = "qa" + uuid.uuid4().hex[:8]
    c.get("login.pl", params={"username": u, "password": "pw", "passwordConfirm": "pw",
                              "firstName": "A", "lastName": "B", "register.x": 1, "register.y": 1})
    c.login(u, "pw")
    return c


# ---- FT ----
@pytest.mark.ft
def test_ft_affichage_itineraire(client):  # RSVI-2401
    _book(client)
    r = client.get("itinerary.pl")
    assert "flightID" in r.text or "Flight" in r.text


@pytest.mark.ft
def test_ft_annuler_un_vol(client):  # RSVI-2402
    _book(client)
    r = client.get("itinerary.pl")
    fid = re.search(r'name="flightID"\s+value="([^"]+)"', r.text)
    assert fid
    r2 = client.post("itinerary.pl", {"1": "on", "flightID": fid.group(1), "removeFlights.x": 1,
                                      "removeFlights.y": 1})
    assert fid.group(1) not in r2.text


@pytest.mark.ft
def test_ft_annuler_tout(client):  # RSVI-2403
    _book(client)
    _book(client)
    r = client.post("itinerary.pl", {"removeAllFlights.x": 1, "removeAllFlights.y": 1})
    assert "no flights have been reserved" in r.text.lower()


# ---- ET ----
@pytest.mark.et
def test_et_annuler_sans_selection(client):  # RSVI-2404
    r = client.post("itinerary.pl", {"removeFlights.x": 1, "removeFlights.y": 1})
    assert r.status_code < 500


@pytest.mark.et
def test_et_itineraire_vide_nouvel_user():  # RSVI-2405
    c = _fresh_user()
    assert "no flights have been reserved" in c.get("itinerary.pl").text.lower()


@pytest.mark.et
def test_et_double_annulation(client):  # RSVI-2406
    p = {"flightID": "999999-1", "removeFlights.x": 1, "removeFlights.y": 1}
    assert client.post("itinerary.pl", p).status_code < 500
    assert client.post("itinerary.pl", p).status_code < 500


# ---- BT ----
@pytest.mark.bt
def test_bt_un_seul_vol():  # RSVI-2407
    c = _fresh_user()
    _book(c)
    assert len(re.findall(r'name="flightID"', c.get("itinerary.pl").text)) == 1


@pytest.mark.bt
def test_bt_dix_vols():  # RSVI-2408
    c = _fresh_user()
    for _ in range(10):
        _book(c)
    assert len(re.findall(r'name="flightID"', c.get("itinerary.pl").text)) == 10


@pytest.mark.bt
def test_bt_flightid_500_caracteres(client):  # RSVI-2409
    r = client.post("itinerary.pl", {"flightID": "9" * 500, "removeFlights.x": 1, "removeFlights.y": 1})
    assert r.status_code < 500


# ---- PT ----
@pytest.mark.pt
def test_pt_itineraire_sans_login(anon):  # RSVI-2410
    r = anon.get("itinerary.pl")
    assert "flightID" not in r.text


@pytest.mark.pt
def test_pt_annuler_vol_autre_user():  # RSVI-2411 (IDOR)
    a, b = _fresh_user(), _fresh_user()
    _book(b)
    fid = re.search(r'name="flightID"\s+value="([^"]+)"', b.get("itinerary.pl").text).group(1)
    a.post("itinerary.pl", {"flightID": fid, "removeFlights.x": 1, "removeFlights.y": 1})
    assert fid in b.get("itinerary.pl").text, "BUG IDOR: vol d'un autre utilisateur annulé"


@pytest.mark.pt
def test_pt_itineraire_apres_signoff(client):  # RSVI-2412
    client.logout()
    assert "flightID" not in client.get("itinerary.pl").text
