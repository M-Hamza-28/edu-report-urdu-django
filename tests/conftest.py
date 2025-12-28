# tests/conftest.py
from rest_framework.test import APIClient
import json
import pytest
from model_bakery import baker
from django.db.models.options import Options

# Import only models that surely exist in your repo
from reports.models import (
    Organization, Tutor, Student, Subject, ExamSession,
    Grade, Section, Enrollment, Exam, ExamEvent, StudentExamMark,
    ReportTemplate, MessageLog, Feedback,
)

# Try optional models (present in some repos, not in others)
try:
    from reports.models import StudentSubject  # optional
except Exception:
    StudentSubject = None

pytestmark = pytest.mark.django_db


def has_field(model, name: str) -> bool:
    return any(getattr(f, "name", None) == name for f in model._meta.get_fields())


@pytest.fixture
def api_client(client):
    """DRF APIClient (supports .force_authenticate and multipart PUT/PATCH)."""
    return APIClient()

@pytest.fixture
def authed_api_client(django_user_model):
    user = django_user_model.objects.create_user(
        username="admin", password="x", is_staff=True, is_superuser=True
    )
    c = APIClient()
    c.force_authenticate(user=user)
    return c

@pytest.fixture
def seed_minimal():
    """
    Create minimal-but-valid data for lists, exams/events, and analytics to respond.
    Adapts to model shape differences (e.g., session vs academic_year).
    """
    org = baker.make(Organization, name="MA SmartWorks", domain="school.local")
    tutor = baker.make(Tutor)

    # Master data
    session = baker.make(ExamSession, name="2024-25", is_current=True)
    grade = baker.make(Grade, name="Grade 8")
    section = baker.make(Section, grade=grade, name="A")
    subject = baker.make(Subject, name="Mathematics")

    # Students
    students = baker.make(Student, tutor=tutor, _quantity=3)

    # Optional M2M student-subject
    if StudentSubject:
        for s in students:
            baker.make(StudentSubject, student=s, subject=subject)

    # Enrollments (support academic_year or session)
    for s in students:
        enroll_kwargs = dict(student=s, grade=grade, section=section, active=True)
        if has_field(Enrollment, "academic_year"):
            enroll_kwargs["academic_year"] = session
        elif has_field(Enrollment, "session"):
            enroll_kwargs["session"] = session
        baker.make(Enrollment, **enroll_kwargs)

    # Exam + Event
    exam_kwargs = dict(name="Term 1")
    if has_field(Exam, "exam_type"):
        exam_kwargs["exam_type"] = "Mid"
    if has_field(Exam, "session"):
        exam_kwargs["session"] = session
    exam = baker.make(Exam, **exam_kwargs)

    event_kwargs = dict(exam=exam, section=section, subject=subject)
    if has_field(ExamEvent, "max_marks"):
        event_kwargs["max_marks"] = 100
    ev = baker.make(ExamEvent, **event_kwargs)

    # Marks (only set fields that exist)
    for s in students:
        mark_kwargs = dict(student=s, subject=subject)
        if has_field(StudentExamMark, "session"):
            mark_kwargs["session"] = session
        if has_field(StudentExamMark, "term"):
            mark_kwargs["term"] = getattr(exam, "name", "Term 1")
        if has_field(StudentExamMark, "exam_type"):
            mark_kwargs["exam_type"] = getattr(exam, "exam_type", "Mid")
        if has_field(StudentExamMark, "exam_event"):
            mark_kwargs["exam_event"] = ev
        if has_field(StudentExamMark, "total_marks"):
            mark_kwargs["total_marks"] = 100
        if has_field(StudentExamMark, "marks_obtained"):
            mark_kwargs["marks_obtained"] = 70
        baker.make(StudentExamMark, **mark_kwargs)

    # Report template (so /report-templates/ doesn’t 404)
    tpl = baker.make(ReportTemplate, name="Default", is_default=True)

    # Legacy logs / feedback present in your repo
    baker.make(MessageLog, student=students[0], contact_type="SMS", message="Hello")
    baker.make(Feedback, tutor=tutor, message="All good!")

    return {
        "org": org,
        "tutor": tutor,
        "students": students,
        "session": session,
        "grade": grade,
        "section": section,
        "subject": subject,
        "exam": exam,
        "event": ev,
        "template": tpl,
    }


def _ok(status):
    return status in (200, 201, 204)


def _read_json(resp):
    try:
        return json.loads(resp.content.decode("utf-8"))
    except Exception:
        return None
