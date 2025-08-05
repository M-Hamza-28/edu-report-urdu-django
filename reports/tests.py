from django.test import TestCase
from django.contrib.auth.models import User
from .models import Tutor, Student, Exam, Subject, Report, PerformanceEntry

class ReportAPITestCase(TestCase):
    def setUp(self):
        self.tutor_user = User.objects.create_user(username='tutor1', password='testpass123')
        self.tutor = Tutor.objects.create(user=self.tutor_user, full_name='Mr. John', phone='1234567890')
        self.student = Student.objects.create(
            tutor=self.tutor,
            full_name='Ali Ahmad',
            gender='M',
            grade_level='10',
            registration_date='2025-07-29'
        )
        self.subject = Subject.objects.create(name='Math')
        self.exam = Exam.objects.create(name='Midterm Exam', date='2025-07-20')
        self.report = Report.objects.create(student=self.student, tutor=self.tutor, exam=self.exam)
        self.performance_entry = PerformanceEntry.objects.create(
            report=self.report,
            subject=self.subject,
            marks_obtained=85,
            total_marks=100
        )

    def test_create_report(self):
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(self.report.student.full_name, 'Ali Ahmad')

    def test_delete_report(self):
        self.report.delete()
        self.assertEqual(Report.objects.count(), 0)

    def test_get_report_list(self):
        reports = Report.objects.all()
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].student.full_name, 'Ali Ahmad')

    def test_update_report(self):
        new_exam = Exam.objects.create(name='Final Exam', date='2025-08-20')
        self.report.exam = new_exam
        self.report.save()
        updated_report = Report.objects.get(pk=self.report.pk)
        self.assertEqual(updated_report.exam.name, 'Final Exam')

    def test_pdf_generation(self):
        try:
            from .utils import generate_report_pdf
            pdf = generate_report_pdf(self.report.id)
            self.assertIsNotNone(pdf)
        except ImportError:
            self.fail('PDF utility import failed.')
