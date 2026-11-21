"""Tests d'interface (Selenium + Chrome) : toutes les pages de WebTours.

Chaque test pilote le navigateur comme un utilisateur : accueil, inscription, connexion,
menu, recherche de vols, paiement, itinéraire, annulation, déconnexion.
Les comptes de test sont créés à la volée (HTTP, rapide) pour ne pas polluer le compte jojo.
Structure des pages : index.htm contient la frame « body », qui contient « navbar » et « info ».
"""
import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from conftest import ROOT, USER, PWD, WebTours


# ---------- aides ----------
def frame(driver, *names):
    driver.switch_to.default_content()
    for n in names:
        driver.switch_to.frame(n)


def info_text(driver):
    frame(driver, "body", "info")
    return driver.find_element(By.TAG_NAME, "body").text.lower()


def new_user():
    """Crée un compte neuf par HTTP et renvoie (nom, mot de passe)."""
    c = WebTours()
    c.home()
    u, pw = "ui" + uuid.uuid4().hex[:8], "pw123"
    c.get("login.pl", params={"username": u, "password": pw, "passwordConfirm": pw,
                              "firstName": "Ali", "lastName": "Test", "address1": "1 rue A",
                              "address2": "Tunis", "register.x": 1, "register.y": 1})
    return u, pw


def login_ui(driver, user, pwd):
    driver.get(f"{ROOT}/index.htm")
    frame(driver, "body", "navbar")
    driver.find_element(By.NAME, "username").send_keys(user)
    driver.find_element(By.NAME, "password").send_keys(pwd)
    driver.find_element(By.NAME, "login").click()


def menu(driver, page):
    """page : search, itinerary, menus ou signOff."""
    frame(driver, "body", "navbar")
    driver.find_element(By.CSS_SELECTOR, f'a[href*="{page}"]').click()


def search_ui(driver, depart="Denver", arrive="London"):
    menu(driver, "page=search")
    frame(driver, "body", "info")
    Select(driver.find_element(By.NAME, "depart")).select_by_visible_text(depart)
    Select(driver.find_element(By.NAME, "arrive")).select_by_visible_text(arrive)
    driver.find_element(By.NAME, "findFlights").click()
    frame(driver, "body", "info")


def book_ui(driver):
    """Recherche, choix du premier vol, paiement. Renvoie le texte de la confirmation."""
    search_ui(driver)
    driver.find_elements(By.NAME, "outboundFlight")[0].click()
    driver.find_element(By.NAME, "reserveFlights").click()
    frame(driver, "body", "info")
    driver.find_element(By.NAME, "creditCard").send_keys("4111111111111111")
    driver.find_element(By.NAME, "expDate").send_keys("12/30")
    driver.find_element(By.NAME, "buyFlights").click()
    return info_text(driver)


@pytest.fixture
def user_ui(driver):
    """Navigateur déjà connecté avec un compte neuf."""
    u, pw = new_user()
    login_ui(driver, u, pw)
    return driver, u


# ---------- accueil et inscription ----------
@pytest.mark.ft
def test_ui_accueil_visiteur(driver):  # UI-01
    driver.get(f"{ROOT}/index.htm")
    frame(driver, "body", "navbar")
    for name in ("username", "password", "login"):
        assert driver.find_element(By.NAME, name).is_displayed(), f"champ {name} absent"
    txt = info_text(driver)
    assert "welcome to the web tours site" in txt
    frame(driver, "body", "info")
    assert driver.find_elements(By.PARTIAL_LINK_TEXT, "sign up"), "lien « sign up now » absent"


@pytest.mark.ft
def test_ui_inscription(driver):  # UI-02
    u = "ui" + uuid.uuid4().hex[:8]
    driver.get(f"{ROOT}/index.htm")
    frame(driver, "body", "info")
    driver.find_element(By.PARTIAL_LINK_TEXT, "sign up").click()
    frame(driver, "body", "info")
    for name, val in [("username", u), ("password", "pw123"), ("passwordConfirm", "pw123"),
                      ("firstName", "Ali"), ("lastName", "Test"), ("address1", "1 rue A"), ("address2", "Tunis")]:
        driver.find_element(By.NAME, name).send_keys(val)
    driver.find_element(By.NAME, "register").click()
    assert "for registering" in info_text(driver)


@pytest.mark.ft
def test_ui_connexion_nouveau_compte(driver):  # UI-03
    u, pw = new_user()
    login_ui(driver, u, pw)
    assert f"welcome, {u}" in info_text(driver)


# ---------- connexion : erreurs et limites ----------
@pytest.mark.et
def test_ui_connexion_mauvais_mot_de_passe(driver):  # UI-04
    login_ui(driver, USER, "mauvais")
    txt = info_text(driver)
    assert "welcome, jojo" not in txt
    assert "incorrect" in txt


@pytest.mark.bt
def test_ui_connexion_champs_vides(driver):  # UI-05
    login_ui(driver, "", "")
    assert "welcome, " not in info_text(driver)


# ---------- menu et pages ----------
@pytest.mark.ft
def test_ui_navigation_menu(user_ui):  # UI-06
    driver, u = user_ui
    menu(driver, "page=itinerary")
    assert "no flights have been reserved" in info_text(driver)
    menu(driver, "page=search")
    assert "find flight" in info_text(driver)
    menu(driver, "page=menus")
    assert f"welcome, {u}" in info_text(driver)


@pytest.mark.ft
def test_ui_formulaire_recherche(user_ui):  # UI-07
    driver, _ = user_ui
    menu(driver, "page=search")
    frame(driver, "body", "info")
    villes = [o.text for o in Select(driver.find_element(By.NAME, "depart")).options]
    assert {"Denver", "London", "Paris"} <= set(villes)
    for name in ("departDate", "returnDate", "numPassengers", "findFlights"):
        assert driver.find_element(By.NAME, name), f"champ {name} absent"


# ---------- recherche et réservation ----------
@pytest.mark.ft
def test_ui_recherche_vols(user_ui):  # UI-08
    driver, _ = user_ui
    search_ui(driver, "Denver", "London")
    assert "flight departing from denver to london" in driver.find_element(By.TAG_NAME, "body").text.lower()
    assert len(driver.find_elements(By.NAME, "outboundFlight")) >= 1


@pytest.mark.ft
def test_ui_reservation_complete(user_ui):  # UI-09
    driver, _ = user_ui
    assert "thank you for booking" in book_ui(driver)


@pytest.mark.ft
def test_ui_itineraire_apres_reservation(user_ui):  # UI-10
    driver, _ = user_ui
    book_ui(driver)
    menu(driver, "page=itinerary")
    txt = info_text(driver)
    assert "flight details" in txt and "denver" in txt and "london" in txt


# ---------- annulation ----------
@pytest.mark.ft
def test_ui_annuler_un_vol(user_ui):  # UI-11
    driver, _ = user_ui
    book_ui(driver)
    menu(driver, "page=itinerary")
    frame(driver, "body", "info")
    driver.find_element(By.CSS_SELECTOR, "input[type=checkbox]").click()
    driver.find_element(By.NAME, "removeFlights").click()
    assert "no flights have been reserved" in info_text(driver)


@pytest.mark.ft
def test_ui_annuler_tout(user_ui):  # UI-12
    driver, _ = user_ui
    book_ui(driver)
    book_ui(driver)
    menu(driver, "page=itinerary")
    frame(driver, "body", "info")
    driver.find_element(By.NAME, "removeAllFlights").click()
    assert "no flights have been reserved" in info_text(driver)


# ---------- déconnexion et permissions ----------
@pytest.mark.ft
def test_ui_deconnexion(user_ui):  # UI-13
    driver, _ = user_ui
    menu(driver, "signOff")
    frame(driver, "body", "navbar")
    assert driver.find_elements(By.NAME, "username"), "formulaire de login absent après Sign Off"


@pytest.mark.pt
def test_ui_administration_sans_authentification(driver):  # UI-14 (voir BUG-07)
    driver.get(f"{ROOT}/index.htm")
    frame(driver, "body", "info")
    driver.find_element(By.PARTIAL_LINK_TEXT, "administration").click()
    # le lien a target="body" : la page s'ouvre dans la frame « body » (et non dans la fenêtre principale)
    frame(driver, "body")
    page = driver.page_source.lower()
    assert "admin page" not in page, "BUG-07: page d'administration accessible depuis l'accueil sans authentification"
