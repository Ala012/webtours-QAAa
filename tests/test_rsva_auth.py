"""RSVA - Authentification (FT / ET / BT / PT)."""
import uuid
import pytest
from selenium.webdriver.common.by import By
from conftest import ROOT, CGI, USER, PWD, WebTours


def _login_ui(driver, user, pwd):
    driver.get(f"{ROOT}/index.htm")
    driver.switch_to.frame("body")
    driver.switch_to.frame("navbar")
    driver.find_element(By.NAME, "username").send_keys(user)
    driver.find_element(By.NAME, "password").send_keys(pwd)
    driver.find_element(By.NAME, "login").click()
    driver.switch_to.default_content()


# ---- FT ----
@pytest.mark.ft
def test_ft_login_valide_ui(driver):  # RSVA-2401
    _login_ui(driver, USER, PWD)
    driver.switch_to.frame("body")
    driver.switch_to.frame("info")
    assert "Welcome to Web Tours" in driver.page_source


@pytest.mark.ft
def test_ft_login_valide_http():  # RSVA-2401 (variante rapide)
    c = WebTours()
    assert "password was correct" in c.login().text


@pytest.mark.ft
def test_ft_signup(anon):  # RSVA-2402
    u = "qa" + uuid.uuid4().hex[:8]
    r = anon.get("login.pl", params={"username": u, "password": "pw123", "passwordConfirm": "pw123",
                                     "firstName": "A", "lastName": "B", "address1": "x", "address2": "y",
                                     "register.x": 1, "register.y": 1})
    assert "thank you" in r.text.lower()


# ---- ET ----
@pytest.mark.et
def test_et_mauvais_mdp(anon):  # RSVA-2404
    r = anon.login(USER, "mauvais")
    assert "incorrect" in r.text.lower()


@pytest.mark.et
def test_et_user_inconnu(anon):  # RSVA-2405
    r = anon.login("inconnu_" + uuid.uuid4().hex[:6], "x")
    assert "unable to find" in r.text.lower() or "incorrect" in r.text.lower()


@pytest.mark.et
def test_et_signup_confirmation_differente(anon):  # RSVA-2406 (bug potentiel)
    u = "qa" + uuid.uuid4().hex[:8]
    r = anon.get("login.pl", params={"username": u, "password": "abc", "passwordConfirm": "xyz",
                                     "firstName": "A", "lastName": "B", "register.x": 1, "register.y": 1})
    assert "thank you" not in r.text.lower(), "BUG: compte créé malgré confirmation différente"


# ---- BT ----
@pytest.mark.bt
def test_bt_champs_vides(anon):  # RSVA-2407
    r = anon.login("", "")
    assert "welcome" not in r.text.lower() or "please" in r.text.lower()


@pytest.mark.bt
def test_bt_username_256(anon):  # RSVA-2408
    r = anon.login("a" * 256, "x")
    assert r.status_code < 500


@pytest.mark.bt
def test_bt_injection_sql(anon):  # RSVA-2409
    r = anon.login("' OR 1=1 --", "x")
    assert "welcome, " not in r.text.lower()


# ---- PT ----
@pytest.mark.pt
def test_pt_welcome_sans_session(anon):  # RSVA-2410
    r = anon.get("welcome.pl", params={"page": "menu"})
    assert "jojo" not in r.text.lower()


@pytest.mark.pt
def test_pt_session_apres_signoff(client):  # RSVA-2411
    client.logout()
    r = client.get("itinerary.pl")
    assert "cancel" not in r.text.lower() and "jojo" not in r.text.lower()


@pytest.mark.pt
def test_pt_profil_autre_user(client):  # RSVA-2412
    r = client.get("login.pl", params={"username": "autre_user", "getInfo": "true"})
    assert 'name="firstName" value="' not in r.text, "BUG: données d'un autre utilisateur exposées"
