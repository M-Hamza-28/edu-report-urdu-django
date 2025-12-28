# tests/test_exams_marks.py
import pytest

pytestmark = pytest.mark.django_db


def test_exam_events_list(api_client, seed_minimal):
    r = api_client.get("/api/exam-events/")
    assert r.status_code == 200
    data = r.json()
    arr = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(arr) >= 1


def test_prefill_marks_endpoint(api_client, seed_minimal):
    student = seed_minimal["students"][0]
    exam = seed_minimal["exam"]
    r = api_client.get(f"/api/prefill-marks?student={student.id}&exam={exam.id}")
    assert r.status_code == 200, r.content[:200]
    # Should contain at least one row for the event/subject
    payload = r.json()
    assert isinstance(payload, dict)
    assert "rows" in payload or "subjects" in payload
