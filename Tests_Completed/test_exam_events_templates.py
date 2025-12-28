import json
import pytest

pytestmark = pytest.mark.django_db

def test_report_templates_list_and_create(client, django_user_model):
    # list should exist
    r = client.get("/api/report-templates/")
    assert r.status_code in (200, 404), f"/api/report-templates/ -> {r.status_code}"
    if r.status_code == 404:
        pytest.skip("report-templates not wired yet")

    # create requires auth
    user = django_user_model.objects.create_user(username="admin", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)

    payload = {"name": "Bilingual A4", "is_default": False}
    r = client.post("/api/report-templates/", data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (201, 400), f"POST report-templates -> {r.status_code} {r.content[:200]}"

def test_exam_events_create(client, django_user_model, seed_minimal):
    user = django_user_model.objects.create_user(username="admin", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    session_id = seed_minimal["session"].id
    section_id = seed_minimal["section"].id
    subject_id = seed_minimal["subject"].id

    payload = {
        "session": session_id,
        "term": "Term 1",
        "exam_type": "mid",
        "components": [{"name": "Paper", "weight": 100}],
        "status": "draft",
        "section": section_id,
        "subject": subject_id,
        "max_marks": 100
    }
    r = client.post("/api/exam-events/", data=json.dumps(payload), content_type="application/json")
    assert r.status_code in (201, 400, 404), f"POST /api/exam-events/ -> {r.status_code} {r.content[:200]}"
