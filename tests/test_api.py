import os
import pytest
import time

# Set a predictable JWT secret for token generation/verification in local/dev
os.environ.setdefault("JWT_SECRETS", "testsecret")

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db


# --- Pytest fixtures ---
@pytest.fixture(scope="session", autouse=True)
def _ensure_db():
    # Ensure database tables exist before running tests
    init_db()

@pytest.fixture(scope="session")
def client():
    # Use context manager so FastAPI lifespan/startup events run
    with TestClient(app) as c:
        yield c


def _signup_and_login(client: TestClient, email: str, password: str) -> str:
    r = client.post("/users", json={"email": email, "password": password})
    # Allow 201 (created) or 409 if test reruns
    assert r.status_code in (201, 409)
    r = client.post("/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required(client: TestClient):
    r = client.post("/predict", json={})
    assert r.status_code == 401


def test_predict_sample_1(client: TestClient):
    token = _signup_and_login(client, "user@example.com", "StrongPass123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "longitude": -122.64,
        "latitude": 38.01,
        "housing_median_age": 36.0,
        "total_rooms": 1336.0,
        "total_bedrooms": 258.0,
        "population": 678.0,
        "households": 249.0,
        "median_income": 5.5789,
        "ocean_proximity": "NEAR OCEAN",
    }
    r = client.post("/predict", headers=headers, json=payload)
    assert r.status_code == 200
    pred = r.json()["prediction"]
    assert abs(pred - 320201.58554044) < 1e-3




def test_rate_limit_predict(client, monkeypatch):
    # Temporarily override rate limit settings
    monkeypatch.setenv("RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")

    token = _signup_and_login(client, "limit@example.com", "StrongPass123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "longitude": -122.64,
        "latitude": 38.01,
        "housing_median_age": 36.0,
        "total_rooms": 1336.0,
        "total_bedrooms": 258.0,
        "population": 678.0,
        "households": 249.0,
        "median_income": 5.5789,
        "ocean_proximity": "NEAR OCEAN",
    }

    # First two requests are OK
    assert client.post("/predict", headers=headers, json=payload).status_code == 200
    assert client.post("/predict", headers=headers, json=payload).status_code == 200

    # Third request hits the limit
    r = client.post("/predict", headers=headers, json=payload)
    assert r.status_code in (429, 403)
    data = r.json()
    assert any(k in data for k in ("detail", "error", "message"))


def test_login_nonexistent_user(client):
    """Login with an unregistered email should fail with 401"""
    r = client.post("/login", json={"email": "noone@example.com", "password": "DoesNotMatter"})
    assert r.status_code == 401


def test_predict_unauthorized_without_token(client):
    """Predict endpoint must return 401 when token missing"""
    payload = {
        "longitude": -122.64,
        "latitude": 38.01,
        "housing_median_age": 36.0,
        "total_rooms": 1336.0,
        "total_bedrooms": 258.0,
        "population": 678.0,
        "households": 249.0,
        "median_income": 5.5789,
        "ocean_proximity": "NEAR OCEAN",
    }
    r = client.post("/predict", json=payload)
    assert r.status_code == 401
