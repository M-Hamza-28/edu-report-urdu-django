import json
import pytest

pytestmark = pytest.mark.django_db

def test_message_templates_list(api_client):
    r = api_client.get("/api/messages/templates/")
    assert r.status_code in (200, 404), f"/api/messages/templates/ -> {r.status_code}"

def test_guardians_list(api_client):
    r = api_client.get("/api/guardians/")
    assert r.status_code in (200, 404), f"/api/guardians/ -> {r.status_code}"

def test_message_threads_crud(client, django_user_model):
    # If not implemented this will 404 — that’s what we want to learn.
    user = django_user_model.objects.create_user(username="admin", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)

    # Create a DM thread
    payload = {"subject": "Hello", "is_announcement": False, "audience": {"role": "student", "id": 1}}
    r = client.post("/api/messages/threads/", data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (201, 404), f"POST threads -> {r.status_code} {r.content[:200]}"
    if r.status_code == 404:
        pytest.fail("Missing /api/messages/threads/ (create ViewSet + route)")
    thread_id = r.json().get("id")
    assert thread_id, "Thread creation must return id"

    # Post a message (multipart) to that thread
    r = client.post(f"/api/messages/threads/{thread_id}/messages/", data={"language_mode": "en", "body_en": "Hi"}, format="multipart")
    assert r.status_code in (201, 200), f"POST messages -> {r.status_code} {r.content[:200]}"

    # Patch thread status
    r = client.patch(f"/api/messages/threads/{thread_id}/", data=json.dumps({"tags": ["important"]}), content_type="application/json")
    assert r.status_code in (200, 202), f"PATCH thread -> {r.status_code} {r.content[:200]}"
