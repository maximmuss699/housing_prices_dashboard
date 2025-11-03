import os

# Set a predictable JWT secret for token generation/verification in local/dev
os.environ.setdefault("JWT_SECRETS", "testsecret")

from fastapi.testclient import TestClient
from app.main import app

# Single TestClient instance for simple tests
client = TestClient(app)


def _signup_and_login(email: str, password: str) -> str:
    r = client.post("/users", json={"email": email, "password": password})
    # Allow 201 (created) or 409 if test reruns
    assert r.status_code in (201, 409)
    r = client.post("/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required():
    r = client.post("/predict", json={})
    assert r.status_code == 401


def test_predict_sample_1():
    token = _signup_and_login("user@example.com", "StrongPass123")
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
