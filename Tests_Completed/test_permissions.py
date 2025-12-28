import json
import pytest

pytestmark = pytest.mark.django_db

def test_public_gets_ok(api_client):
    for p in ["/api/students/", "/api/subjects/", "/api/exam-sessions/"]:
        r = api_client.get(p)
        assert r.status_code == 200, f"{p} -> {r.status_code}"

def test_writes_require_auth(client):
    # try writing without auth
    r = client.post("/api/subjects/", data=json.dumps({"name": "Chem"}), content_type="application/json")
    assert r.status_code in (401, 403, 405, 404)
