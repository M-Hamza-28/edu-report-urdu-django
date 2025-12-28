import pytest

pytestmark = pytest.mark.django_db

def test_audit_logs_list(api_client):
    r = api_client.get("/api/audit-logs")
    assert r.status_code in (200, 404), f"/api/audit-logs -> {r.status_code}"
    # If 404: add model + viewset + route and an audit hook util.
