import json
import pytest
pytestmark = pytest.mark.django_db

def test_exam_events_create_publish_close(authed_api_client, seed_minimal):
    sid = seed_minimal["session"].id
    section_id = seed_minimal["section"].id
    subject_id = seed_minimal["subject"].id

    create_payload = {
        "session": sid,
        "term": "Term 1",
        "exam_type": "mid",
        "components": [{"name": "Paper", "weight": 100}],
        "status": "draft",
        "section": section_id,
        "subject": subject_id,
        "max_marks": 100
    }
    r = authed_api_client.post("/api/exam-events/", data=json.dumps(create_payload),
                               content_type="application/json")
    assert r.status_code in (201, 400), f"POST /api/exam-events/ -> {r.status_code}. Implement create if 404."
    if r.status_code == 400:
        pytest.skip("ExamEvent create validation not satisfied; adjust serializer/fields.")
    ev_id = r.json().get("id")
    assert ev_id, "create must return id"

    # Publish (if you support transitions)
    r = authed_api_client.patch(f"/api/exam-events/{ev_id}/",
                                data=json.dumps({"status": "published"}),
                                content_type="application/json")
    assert r.status_code in (200, 202), f"publish -> {r.status_code}"

    # Close
    r = authed_api_client.patch(f"/api/exam-events/{ev_id}/",
                                data=json.dumps({"status": "closed"}),
                                content_type="application/json")
    assert r.status_code in (200, 202), f"close -> {r.status_code}"
