import pytest
from django.db import IntegrityError
from reports.models import (
    Grade, Section, ExamSession, Student, Tutor, Exam, ExamEvent, Enrollment, Subject, StudentExamMark
)
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

def base_graph():
    U = get_user_model()
    u = U.objects.create_user(username="u1", password="x")
    t = Tutor.objects.create(user=u, full_name="T")
    stu = Student.objects.create(tutor=t, full_name="Student")
    sess = ExamSession.objects.create(name="2022-23")
    grade = Grade.objects.create(name="G8")
    sec = Section.objects.create(grade=grade, name="A")
    sub = Subject.objects.create(name="Science")
    return dict(user=u, tutor=t, student=stu, session=sess, grade=grade, section=sec, subject=sub)

def test_enrollment_unique_student_session():
    g = base_graph()
    Enrollment.objects.create(student=g["student"], academic_year=g["session"], grade=g["grade"], section=g["section"])
    with pytest.raises(IntegrityError):
        Enrollment.objects.create(student=g["student"], academic_year=g["session"], grade=g["grade"], section=g["section"])

def test_examevent_unique_exam_section_subject():
    g = base_graph()
    exam = Exam.objects.create(name="Final", exam_type="Final", session=g["session"])
    ExamEvent.objects.create(exam=exam, section=g["section"], subject=g["subject"], max_marks=100)
    with pytest.raises(IntegrityError):
        ExamEvent.objects.create(exam=exam, section=g["section"], subject=g["subject"], max_marks=100)

def test_student_exam_mark_unique_sem_key():
    g = base_graph()
    StudentExamMark.objects.create(
        student=g["student"], session=g["session"], term="Mid-Term", exam_type="Mid-Term",
        subject=g["subject"], marks_obtained=50, total_marks=100
    )
    with pytest.raises(IntegrityError):
        StudentExamMark.objects.create(
            student=g["student"], session=g["session"], term="Mid-Term", exam_type="Mid-Term",
            subject=g["subject"], marks_obtained=60, total_marks=100
        )
