import pytest
pytestmark = pytest.mark.django_db

def test_me_unauth_status(api_client):
    r = api_client.get("/api/users/me")
    # Accept 200 (public stub) or 401 (auth required), but not 404
    assert r.status_code in (200, 401), f"/api/users/me -> {r.status_code}; wire this route if missing."

def test_me_authed_returns_profile(authed_api_client):
    r = authed_api_client.get("/api/users/me")
    assert r.status_code == 200, f"/api/users/me authed -> {r.status_code}"
    data = r.json()
    # Be flexible but expect core fields
    for k in ("id", "username"):
        assert k in data, f"Missing '{k}' in /api/users/me response"
