# tests/test_messages_contract.py
import pytest

pytestmark = pytest.mark.django_db

def test_legacy_message_logs_exist(api_client, seed_minimal):
    r = api_client.get("/api/message-logs/")
    assert r.status_code == 200

@pytest.mark.parametrize("path", [
    "/api/messages/threads/",
    "/api/messages/templates/",
    "/api/guardians/",
])
def test_new_messaging_contract_missing_for_now(api_client, path):
    r = api_client.get(path)
    assert r.status_code in (200, 404)
    if r.status_code == 404:
        pytest.fail(f"Missing endpoint: {path} (add models/views/urls for threaded messages)")
