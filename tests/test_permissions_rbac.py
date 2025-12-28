# reports/tests/test_permissions_rbac.py
import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from reports.models import (
    Student, Tutor, Enrollment, AcademicYear, Section, Exam, Subject, ReportTemplate
)

# Skip RBAC tests for now; re-enable when feature set is finalized.
pytestmark = pytest.mark.skip(reason="RBAC tests deferred until functionality is complete.")

# -----------------
# Test fixtures
# -----------------

@pytest.fixture
def groups(db):
    viewer, _ = Group.objects.get_or_create(name="Viewer")
    editor, _ = Group.objects.get_or_create(name="Editor")
    return {"viewer": viewer, "editor": editor}

@pytest.fixture
def users(db, groups):
    viewer = User.objects.create_user(username="viewer", password="v123")
    editor = User.objects.create_user(username="editor", password="e123", is_staff=True)
    viewer.groups.add(groups["viewer"])
    editor.groups.add(groups["editor"])
    return {"viewer": viewer, "editor": editor}

@pytest.fixture
def core(db):
    """
    Minimal core data so we can create a valid report.
    Adjust field names if your models differ (kept generic here).
    """
    year = AcademicYear.objects.create(name="2024-25")
    section = Section.objects.create(name="A")
    subj = Subject.objects.create(name="Math")
    exam = Exam.objects.create(name="Midterm", exam_type="term", session=year)
    tutor = Tutor.objects.create(name="T1")
    student = Student.objects.create(name="S1", tutor=tutor)
    Enrollment.objects.create(student=student, academic_year=year, section=section, active=True)
    tpl = ReportTemplate.objects.create(title="Std", name="std")
    return {"year": year, "section": section, "subject": subj, "exam": exam, "student": student, "tpl": tpl}

def _client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c

# -----------------
# Tests (kept for later)
# -----------------

@pytest.mark.django_db
def test_viewer_cannot_create_report(users, core):
    viewer = users["viewer"]
    c = _client(viewer)
    payload = {
        "student": core["student"].id,
        "exam": core["exam"].id,
        "template": core["tpl"].id,
        "session": core["year"].id,
        "section": core["section"].id,
        "title": "R1",
    }
    r = c.post("/api/reports/", payload, format="json")
    assert r.status_code in (401, 403), r.data

@pytest.mark.django_db
def test_editor_can_create_report(users, core):
    editor = users["editor"]
    c = _client(editor)
    payload = {
        "student": core["student"].id,
        "exam": core["exam"].id,
        "template": core["tpl"].id,
        "session": core["year"].id,
        "section": core["section"].id,
        "title": "R2",
    }
    r = c.post("/api/reports/", payload, format="json")
    assert r.status_code in (200, 201), r.data

@pytest.mark.django_db
def test_viewer_cannot_mutate_template(users, core):
    viewer = users["viewer"]
    c = _client(viewer)
    tpl = core["tpl"]
    r = c.patch(f"/api/templates/{tpl.id}/", {"title": "Nope"}, format="json")
    assert r.status_code in (401, 403), r.data

@pytest.mark.django_db
def test_editor_can_mutate_template(users, core):
    editor = users["editor"]
    c = _client(editor)
    tpl = core["tpl"]
    r = c.patch(f"/api/templates/{tpl.id}/", {"title": "Ok"}, format="json")
    assert r.status_code in (200, 202), r.data
