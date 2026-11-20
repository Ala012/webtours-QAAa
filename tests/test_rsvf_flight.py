"""RSVF - Flight (FT / ET / BT / PT)."""
import pytest
from selenium.webdriver.common.by import By
from conftest import ROOT, USER, PWD


# ---- FT ----
@pytest.mark.ft
def test_ft_recherche_valide(client):  # RSVF-2401
    r = client.search()
    assert "outboundFlight" in r.text


@pytest.mark.ft
def test_ft_reservation_complete(client):  # RSVF-2402
    r = client.search()
    import re
    m = re.search(r'name="outboundFlight"\s+value="([^"]+)"', r.text)
    assert m, "aucun vol proposé"
    r2 = client.post("reservations.pl", {
        "outboundFlight": m.group(1), "numPassengers": "1", "advanceDiscount": "0",
        "seatType": "Coach", "seatPref": "None", "reserveFlights.x": 40, "reserveFlights.y": 10})
    r3 = client.post("reservations.pl", {
        "firstName": "Jo", "lastName": "Jo", "address1": "1 rue A", "address2": "Tunis",
        "pass1": "Jo Jo", "creditCard": "4111111111111111", "expDate": "12/30",
        "oldCCOption": "", "numPassengers": "1", "seatType": "Coach", "seatPref": "None",
        "outboundFlight": m.group(1), "advanceDiscount": "0", "buyFlights.x": 40, "buyFlights.y": 10,
        ".cgifields": "saveCC"})
    assert "thank you for booking" in r3.text.lower()


@pytest.mark.ft
def test_ft_recherche_ui(driver):  # RSVF-2403 (parcours UI)
    driver.get(f"{ROOT}/index.htm")
    driver.switch_to.frame("body")
    driver.switch_to.frame("navbar")
    driver.find_element(By.NAME, "username").send_keys(USER)
    driver.find_element(By.NAME, "password").send_keys(PWD)
    driver.find_element(By.NAME, "login").click()
    driver.switch_to.default_content()
    driver.switch_to.frame("body")
    driver.switch_to.frame("navbar")
    driver.find_element(By.CSS_SELECTOR, 'a[href*="flights"]').click()
    driver.switch_to.default_content()
    driver.switch_to.frame("body")
    driver.switch_to.frame("info")
    assert "Flight Selection" in driver.page_source or "depart" in driver.page_source.lower()


# ---- ET ----
@pytest.mark.et
def test_et_meme_ville(client):  # RSVF-2404 (bug potentiel)
    r = client.search(depart="Paris", arrive="Paris")
    assert "outboundFlight" not in r.text, "BUG: vol Paris->Paris proposé"


@pytest.mark.et
def test_et_retour_avant_depart(client):  # RSVF-2405
    r = client.search(date="12/20/2026", ret="12/10/2026")
    assert "outboundFlight" not in r.text, "BUG: date retour < départ acceptée"


@pytest.mark.et
def test_et_carte_invalide(client):  # RSVF-2406
    r = client.post("reservations.pl", {"firstName": "A", "lastName": "B", "creditCard": "abcd",
                                        "expDate": "12/30", "buyFlights.x": 1, "buyFlights.y": 1})
    assert "thank you for booking" not in r.text.lower()


# ---- BT ----
@pytest.mark.bt
@pytest.mark.parametrize("pax", ["0", "-1", "9999"])
def test_bt_passagers(client, pax):  # RSVF-2407/2408/2409
    r = client.search(pax=pax)
    assert r.status_code < 500
    assert "outboundFlight" not in r.text, f"BUG: numPassengers={pax} accepté"


# ---- PT ----
@pytest.mark.pt
def test_pt_reservations_sans_login(anon):  # RSVF-2410
    r = anon.search()
    assert "outboundFlight" not in r.text


@pytest.mark.pt
def test_pt_prix_manipule(client):  # RSVF-2411
    r = client.post("reservations.pl", {"outboundFlight": "000;999;12/20/2026", "numPassengers": "1",
                                        "reserveFlights.x": 1, "reserveFlights.y": 1})
    assert "thank you for booking" not in r.text.lower()


@pytest.mark.pt
def test_pt_flightid_falsifie(client):  # RSVF-2412
    r = client.post("reservations.pl", {"outboundFlight": "INEXISTANT", "numPassengers": "1",
                                        "buyFlights.x": 1, "buyFlights.y": 1})
    assert r.status_code < 500 and "thank you for booking" not in r.text.lower()
