from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from rest_framework.permissions import IsAuthenticated
from .models import (
    Tutor, Student, Subject, Exam, Report,
    PerformanceEntry, MessageLog, Feedback
)
from .serializers import (
    TutorSerializer, StudentSerializer, SubjectSerializer, ExamSerializer,
    ReportSerializer, PerformanceEntrySerializer, MessageLogSerializer, FeedbackSerializer
)
from .utils import generate_report_pdf
import logging

logger = logging.getLogger(__name__)

class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all().select_related("user")
    serializer_class = TutorSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related("tutor")
    serializer_class = StudentSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    def get_queryset(self):
        qs = Subject.objects.all()
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(students__id=student_id)  # ← ONLY subjects linked to that student
        return qs.order_by("name")


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer


class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Report.objects.all().select_related("student", "tutor", "exam")
    serializer_class = ReportSerializer

    @action(detail=True, methods=['get'], url_path='generate_pdf')
    def generate_pdf(self, request, pk=None):
        """GET /api/reports/<pk>/generate_pdf/?lang=en|ur"""
        raw = (request.query_params.get('lang') or 'en').strip().lower()
        lang_map = {'en': 'en', 'eng': 'en', 'english': 'en', 'ur': 'ur', 'urdu': 'ur'}
        lang = lang_map.get(raw, 'en')

        # Ensure report exists (respects queryset filters/permissions)
        try:
            self.get_object()
        except Exception as e:
            logger.exception("Report not found: %s", pk)
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        try:
            pdf_bytes = generate_report_pdf(pk, lang=lang)
        except Exception as e:
            logger.exception("PDF generation failed for report=%s lang=%s", pk, lang)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Wrap bytes with language-aware headers and cache-busting filename
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="report_{pk}_{lang}.pdf"'
        resp['Content-Language'] = lang
        resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp['Pragma'] = 'no-cache'
        return resp

    @action(detail=False, methods=['get'], url_path=r'student_progress/(?P<student_id>[^/.]+)')
    def student_progress(self, request, student_id=None):
        entries = (
            PerformanceEntry.objects
            .filter(report__student__id=student_id)
            .select_related("report__exam", "subject")
            .order_by("report__exam__date", "subject__name")
        )
        data = {}
        for entry in entries:
            subject = entry.subject.name
            data.setdefault(subject, []).append({
                'exam': entry.report.exam.name,
                'exam_type': entry.report.exam.exam_type,   # <- include type
                'date': entry.report.exam.date,
                'marks_obtained': entry.marks_obtained,
                'total_marks': entry.total_marks,
                'percentage': entry.percentage,
            })
        return Response(data)

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        report = self.get_object()
        if not report.pdf_file:
            return Response({'detail': 'PDF not generated for this report.'}, status=404)
        response = FileResponse(report.pdf_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=report_{report.id}.pdf'
        return response

    @action(detail=True, methods=['post'])
    def send_report(self, request, pk=None):
        method = request.data.get("method")
        _ = self.get_object()
        if method == "whatsapp":
            return Response({"status": "sent via WhatsApp"})
        elif method == "sms":
            return Response({"status": "sent via SMS"})
        elif method == "email":
            return Response({"status": "sent via Email"})
        else:
            return Response({"error": "Invalid method"}, status=400)


class PerformanceEntryViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceEntrySerializer
    def get_queryset(self):
        qs = PerformanceEntry.objects.select_related("subject", "report", "report__exam")
        report_id = self.request.query_params.get("report")
        if report_id:
            qs = qs.filter(report_id=report_id)      # ← ONLY entries for this report
        return qs.order_by("id")

class MessageLogViewSet(viewsets.ModelViewSet):
    queryset = MessageLog.objects.all().select_related("student")
    serializer_class = MessageLogSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().select_related("tutor")
    serializer_class = FeedbackSerializer
