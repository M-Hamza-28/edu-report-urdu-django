import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from reports.models import Tutor, Student, Subject, Grade, Section, ExamSession, Exam, StudentExamMark, Enrollment, ExamEvent

pytestmark = pytest.mark.django_db

def seed():
    u = get_user_model().objects.create_user(username="tx", password="x")
    t = Tutor.objects.create(user=u, full_name="T")
    s1 = Student.objects.create(tutor=t, full_name="A")
    s2 = Student.objects.create(tutor=t, full_name="B")
    sub = Subject.objects.create(name="Math")
    grade = Grade.objects.create(name="G8")
    sec = Section.objects.create(grade=grade, name="A")
    sess = ExamSession.objects.create(name="2023-24")
    Enrollment.objects.create(student=s1, academic_year=sess, grade=grade, section=sec)
    Enrollment.objects.create(student=s2, academic_year=sess, grade=grade, section=sec)
    exam = Exam.objects.create(name="Mid-Term", exam_type="Mid-Term", session=sess)
    ExamEvent.objects.create(exam=exam, section=sec, subject=sub, max_marks=100)
    StudentExamMark.objects.create(student=s1, session=sess, term=exam.name, exam_type=exam.exam_type, subject=sub, marks_obtained=60, total_marks=100)
    StudentExamMark.objects.create(student=s2, session=sess, term=exam.name, exam_type=exam.exam_type, subject=sub, marks_obtained=90, total_marks=100)
    return dict(session=sess, subject=sub, section=sec)

def test_overview_keys_and_avg_score_reasonable():
    g = seed()
    res = APIClient().get(f"/api/analytics/session/{g['session'].id}/overview")
    assert res.status_code == 200
    body = res.json()
    for k in ("avg_score", "summary", "top_subjects", "bottom_subjects"):
        assert k in body
    assert 70.0 <= body["avg_score"] <= 80.0  # average of 60 and 90 is 75

def test_trends_points_shape():
    g = seed()
    res = APIClient().get(f"/api/analytics/session/{g['session'].id}/trends", {"subject": g["subject"].id})
    assert res.status_code == 200
    points = res.json().get("points")
    assert isinstance(points, list)
    assert all("label" in p and "avg_pct" in p for p in points)

def test_subject_difficulty_scatter_shape():
    g = seed()
    res = APIClient().get(f"/api/analytics/session/{g['session'].id}/subject-difficulty")
    assert res.status_code == 200
    pts = res.json().get("points")
    assert isinstance(pts, list)
    if pts:
        assert {"subject", "mean", "spread"} <= set(pts[0].keys())
