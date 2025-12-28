import json
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
pytestmark = pytest.mark.django_db

def _file():
    return SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")

def test_threads_and_messages_flow(authed_api_client):
    # Create thread
    payload = {"subject": "Hello", "is_announcement": False, "audience": {"role": "student", "id": 1}}
    r = authed_api_client.post("/api/messages/threads/",
                               data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (201,), f"POST threads -> {r.status_code}"
    thread_id = r.json().get("id"); assert thread_id

    # Post message without attachment
    r = authed_api_client.post(f"/api/messages/threads/{thread_id}/messages/",
                               data={"language_mode": "en", "body_en": "Hi there"}, format="multipart")
    assert r.status_code in (200, 201), f"POST message -> {r.status_code}"

    # Post message with attachment
    r = authed_api_client.post(f"/api/messages/threads/{thread_id}/messages/",
                               data={"language_mode": "en", "body_en": "With file", "attachment": _file()},
                               format="multipart")
    assert r.status_code in (200, 201), f"POST message file -> {r.status_code}"

    # Folder filter should return this thread (inbox by default or drafts/scheduled if you move it)
    r = authed_api_client.get("/api/messages/threads/?ordering=-updated_at")
    assert r.status_code == 200
    arr = r.json().get("results", [])
    assert any(t.get("id") == thread_id for t in arr), "thread not listed in GET /threads"
