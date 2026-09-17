import pytest
import secrets
from app import create_app
from db import db


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", secrets.token_hex(32))

    app = create_app("sqlite://")
    app.config.update(TESTING=True)
    # Only hold the app context while creating/dropping tables. Each request
    # made through the test client pushes and tears down its own app
    # context (like a real WSGI request), so a session left in a failed
    # transaction by one request does not leak into the next one.
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, username="alice", password="secret"):
    """Helper used by resource tests: registers a user and returns their tokens."""
    client.post("/register", json={"username": username, "password": password})
    login_response = client.post("/login", json={"username": username, "password": password})
    return login_response.get_json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
