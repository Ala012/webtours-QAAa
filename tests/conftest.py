import os
import re
import pytest
import requests

BASE = os.getenv("WEBTOURS_URL", "http://127.0.0.1:1080")
ROOT = f"{BASE}/WebTours"
CGI = f"{BASE}/cgi-bin"
USER, PWD = "jojo", "bean"


class WebTours:
    """Client HTTP minimal pour WebTours (les pages sont en frames)."""

    def __init__(self):
        self.s = requests.Session()
        self.user_session = None

    def home(self):
        r = self.s.get(f"{CGI}/nav.pl", params={"in": "home"})
        m = re.search(r'name="userSession"\s+value="([^"]*)"', r.text)
        self.user_session = m.group(1) if m else ""
        return r

    def login(self, user=USER, pwd=PWD):
        self.home()
        return self.s.post(f"{CGI}/login.pl", data={
            "userSession": self.user_session, "username": user, "password": pwd,
            "login.x": 0, "login.y": 0, "JSFormSubmit": "off"})

    def logout(self):
        return self.s.get(f"{CGI}/welcome.pl", params={"signOff": "1"})

    def get(self, path, **kw):
        return self.s.get(f"{CGI}/{path}", **kw)

    def post(self, path, data=None, **kw):
        return self.s.post(f"{CGI}/{path}", data=data, **kw)

    def search(self, depart="Denver", arrive="London", date="12/20/2026",
               ret="12/21/2026", pax="1"):
        return self.post("reservations.pl", {
            "advanceDiscount": "0", "depart": depart, "departDate": date,
            "arrive": arrive, "returnDate": ret, "numPassengers": pax,
            "seatPref": "None", "seatType": "Coach",
            "findFlights.x": 40, "findFlights.y": 10, ".cgifields": "roundtrip,seatType,seatPref"})


@pytest.fixture
def anon():
    c = WebTours()
    c.home()
    return c


@pytest.fixture
def client():
    c = WebTours()
    r = c.login()
    assert "password was correct" in r.text, "login jojo/bean impossible : WebTours démarré ?"
    return c


@pytest.fixture
def driver():
    from selenium import webdriver
    opts = webdriver.ChromeOptions()
    if os.getenv("HEADLESS", "1") == "1":
        opts.add_argument("--headless=new")
    d = webdriver.Chrome(options=opts)  # Selenium Manager télécharge le driver
    d.implicitly_wait(5)
    yield d
    d.quit()
