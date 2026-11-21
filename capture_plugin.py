"""Plugin pytest : copie d'écran du navigateur à la fin de chaque test d'interface.

Utilisation :  python -m pytest tests -p capture_plugin
Les images vont dans results/captures/ et sont aussi jointes au rapport HTML.
Ne modifie aucun test : il utilise la fixture `driver` de conftest.py.
"""
import base64
import os
import re

import pytest

OUT = os.path.join("results", "captures")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    driver = item.funcargs.get("driver")
    if driver is None:
        return  # test HTTP : pas de navigateur
    try:
        os.makedirs(OUT, exist_ok=True)
        driver.switch_to.default_content()  # page entière, pas une frame
        status = "OK" if rep.passed else "ECHEC"
        name = re.sub(r"[^\w\-]+", "_", item.name)
        path = os.path.join(OUT, f"{name}_{status}.png")
        driver.save_screenshot(path)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        try:
            from pytest_html import extras
            rep.extras = getattr(rep, "extras", []) + [extras.png(b64)]
        except Exception:
            pass
        print(f"\n[capture] {path}")
    except Exception as e:  # une capture ratée ne doit jamais faire échouer un test
        print(f"\n[capture] impossible : {e}")
