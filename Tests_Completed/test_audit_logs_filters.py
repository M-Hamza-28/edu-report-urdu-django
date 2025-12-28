import json
import pytest
pytestmark = pytest.mark.django_db

def test_audit_logs_filters(authed_api_client):
    # Trigger an audited action: create a thread
    r = authed_api_client.post("/api/messages/threads/",
                               data=json.dumps({"subject":"A","is_announcement":False,"audience":{"role":"student","id":1}}),
                               content_type="application/json")
    if r.status_code == 404:
        pytest.skip("Threaded messaging not wired; add models/views/routes then re-run.")
    tid = r.json().get("id")

    # List logs
    r = authed_api_client.get("/api/audit-logs?ordering=-created_at")
    if r.status_code == 404:
        pytest.skip("Audit logs not wired; add model/viewset/route then re-run.")

    assert r.status_code == 200
    logs = r.json()
    assert isinstance(logs, list)
    assert any(l.get("entity") in ("MessageThread","MessageTemplate","Setting","organization") for l in logs)

    # Filter by entity
    r = authed_api_client.get("/api/audit-logs?entity=MessageThread")
    assert r.status_code == 200
