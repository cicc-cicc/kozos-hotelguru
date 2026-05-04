import os
import sys
import pytest

# Ensure project root is on sys.path so tests can import the package `WebApp`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from WebApp import create_app, db


@pytest.fixture
def app():
    """Ez a fixture létrehozza az appot, és kikapcsolja a CSRF-et minden teszthez."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()  # Táblák létrehozása
        yield app  # Visszaadjuk az appot a teszteknek


@pytest.fixture
def client(app):
    """Ez a fixture adja a teszt klienst, amit a POST/GET kérésekhez használunk."""
    return app.test_client()
