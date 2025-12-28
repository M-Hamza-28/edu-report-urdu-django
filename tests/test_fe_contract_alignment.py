import json
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from reports.models import (
    Tutor, Student, Subject, Grade, Section, ExamSession, Exam, ExamEvent,
    Enrollment, StudentExamMark, Report
)

pytestmark = pytest.mark.django_db

def make_minimum_graph():
    User = get_user_model()
    u = User.objects.create_user(username="tutor1", password="x")
    t = Tutor.objects.create(user=u, full_name="Tutor One")
    s = Student.objects.create(tutor=t, full_name="Ali")
    subj = Subject.objects.create(name="Math")
    grade = Grade.objects.create(name="Grade 8")
    section = Section.objects.create(grade=grade, name="A")
    session = ExamSession.objects.create(name="2023-24")
    Enrollment.objects.create(student=s, academic_year=session, grade=grade, section=section, active=True)
    exam = Exam.objects.create(name="Mid-Term", exam_type="Mid-Term", session=session)
    event = ExamEvent.objects.create(exam=exam, section=section, subject=subj, max_marks=100)
    return dict(user=u, tutor=t, student=s, subject=subj, grade=grade, section=section, session=session, exam=exam, event=event)

def auth(client: APIClient):
    """Authenticate client with a superuser for ease of POST/PUT."""
    User = get_user_model()
    su = User.objects.create_superuser(username="admin", password="x", email="a@b.c")
    client.force_authenticate(user=su)
    return client

def test_student_subjects_bridge_contract():
    """
    FE uses /student-subjects/ for assign/remove.
    Contract: POST { student, subject } returns link with id + names.
    """
    g = make_minimum_graph()
    client = auth(APIClient())

    res = client.post("/api/student-subjects/", {"student": g["student"].id, "subject": g["subject"].id}, format="json")
    assert res.status_code in (200, 201)
    body = res.json()
    assert {"id", "student", "subject", "student_name", "subject_name"} <= set(body.keys())

def test_performance_entries_endpoint_alignment():
    """
    FE calls 'entries/?report=' but backend route is 'performance-entries/'.
    This test accepts either (at least one must work) to highlight wiring status.
    """
    g = make_minimum_graph()
    client = auth(APIClient())

    # Create a report so PerformanceEntry list filter makes sense (entries may be empty).
    rep = Report.objects.create(student=g["student"], tutor=g["tutor"], exam=g["exam"])

    ok = False
    for path in ("/api/performance-entries/", "/api/entries/"):
        resp = client.get(path, {"report": rep.id})
        if resp.status_code == 200:
            ok = True
            data = resp.json()
            assert isinstance(data, (list, dict))
            break
    assert ok, "Neither /performance-entries/ nor /entries/ worked — FE will fail."

def test_prefill_marks_shape_and_bulk_upsert_flow():
    """
    FE expects prefill payload with both 'items' and 'rows' keys (same list).
    Then bulk_upsert should create/update SEM rows.
    """
    g = make_minimum_graph()
    client = auth(APIClient())

    # Prefill
    pre = client.get("/api/prefill-marks", {"student": g["student"].id, "exam": g["exam"].id})
    assert pre.status_code == 200
    payload = pre.json()
    for key in ("student", "exam", "session", "term", "exam_type", "items", "rows", "count"):
        assert key in payload
    assert payload["items"] == payload["rows"]

    # Save marks
    items = payload["items"]
    assert len(items) >= 1
    items[0]["marks_obtained"] = 78
    items[0]["total_marks"] = 100

    up = client.post("/api/student-marks/bulk_upsert/", data=json.dumps({"items": items}), content_type="application/json")
    assert up.status_code in (200, 207)
    summary = up.json()
    assert "errors" in summary and "created" in summary

def test_analytics_distribution_alias_contract():
    """
    FE calls singular /analytics/session/<id>/distribution (alias).
    Contract: labels[], series[{name,data[]}], buckets[] present.
    """
    g = make_minimum_graph()
    client = APIClient()

    # Seed at least one mark so buckets are non-empty
    StudentExamMark.objects.create(
        student=g["student"], session=g["session"], term=g["exam"].name, exam_type=g["exam"].exam_type,
        subject=g["subject"], marks_obtained=80, total_marks=100
    )
    res = client.get(f"/api/analytics/session/{g['session'].id}/distribution")
    assert res.status_code == 200
    body = res.json()
    for k in ("labels", "series", "buckets"):
        assert k in body
    assert isinstance(body["labels"], list)
    assert isinstance(body["series"], list)
    assert isinstance(body["buckets"], list)
