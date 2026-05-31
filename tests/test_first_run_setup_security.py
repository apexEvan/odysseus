from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.auth_routes import setup_auth_routes


class FakeAuth:
    def __init__(self):
        self.users = {}
        self.signup_enabled = False

    @property
    def is_configured(self):
        return bool(self.users)

    def setup(self, username, password):
        if self.is_configured:
            return False
        self.users[username.strip().lower()] = {"password": password, "is_admin": True}
        return True

    def is_admin(self, username):
        return bool(self.users.get(username, {}).get("is_admin"))

    def get_username_for_token(self, token):
        return None

    def status(self, token):
        return {"authenticated": False, "configured": self.is_configured}


def _client(client_addr=("127.0.0.1", 50000)):
    auth = FakeAuth()
    app = FastAPI()
    app.state.first_run_setup_token = "setup-token"
    app.include_router(setup_auth_routes(auth))
    return auth, TestClient(app, client=client_addr)


def test_first_run_setup_requires_token():
    auth, client = _client()
    res = client.post("/api/auth/setup", json={"username": "admin", "password": "password123"})

    assert res.status_code == 403
    assert not auth.is_configured


def test_first_run_setup_accepts_valid_token():
    auth, client = _client()
    res = client.post(
        "/api/auth/setup",
        json={"username": "admin", "password": "password123", "setup_token": "setup-token"},
    )

    assert res.status_code == 200
    assert auth.is_configured
    assert auth.is_admin("admin")


def test_first_run_setup_blocks_remote_even_with_token(monkeypatch):
    monkeypatch.delenv("ODYSSEUS_ALLOW_REMOTE_FIRST_RUN_SETUP", raising=False)
    auth, client = _client(client_addr=("203.0.113.10", 50000))

    res = client.post(
        "/api/auth/setup",
        json={"username": "admin", "password": "password123", "setup_token": "setup-token"},
    )

    assert res.status_code == 403
    assert res.json()["detail"] == "First-run setup is restricted to localhost"
    assert not auth.is_configured
