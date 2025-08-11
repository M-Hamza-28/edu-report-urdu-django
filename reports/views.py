from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from .models import Tutor, Student, Subject, Exam, Report, PerformanceEntry, MessageLog, Feedback
from .serializers import (
    TutorSerializer,
    StudentSerializer,
    SubjectSerializer,
    ExamSerializer,
    ReportSerializer,
    PerformanceEntrySerializer,
    MessageLogSerializer,
    FeedbackSerializer,
)
from .utils import generate_report_pdf

logger = logging.getLogger(__name__)

# Example: To restrict API access, uncomment and adjust permissions:
# from rest_framework.permissions import IsAuthenticated


class TutorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on Tutor.
    """
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer
    # permission_classes = [IsAuthenticated]  # Uncomment to require login


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on Student.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    # permission_classes = [IsAuthenticated]


class SubjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on Subject.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    # permission_classes = [IsAuthenticated]


class ExamViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on Exam.
    """
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    # permission_classes = [IsAuthenticated]


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on Report.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @action(detail=True, methods=['get'], url_path='generate_pdf')
    def generate_pdf(self, request, pk=None):
        """
        GET /api/reports/<pk>/generate_pdf/?lang=en|ur

        - Validates lang
        - Fetches Report (via self.get_object())
        - Calls generate_report_pdf safely
        - Accepts either util signature: (report, lang) OR (pk, lang)
        - Returns FileResponse/HttpResponse directly, or wraps bytes in HttpResponse
        """
        lang = (request.query_params.get('lang') or 'en').lower().strip()
        if lang not in {'en', 'ur'}:
            return Response({"error": "Invalid 'lang' (use 'en' or 'ur')."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure report exists (and respect ViewSet permissions/filters)
        try:
            report = self.get_object()  # raises 404 automatically if not found in queryset
        except Exception as e:
            logger.exception("Report fetch failed for pk=%s", pk)
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        # Call your PDF generator with strong guards
        try:
            # Prefer (report, lang) signature
            try:
                result = generate_report_pdf(report, lang)
            except TypeError:
                # Fallback to older (pk, lang) signature if present
                result = generate_report_pdf(pk, lang)
        except Exception as e:
            logger.exception("PDF generation failed for report=%s lang=%s", pk, lang)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Accept multiple return types to be flexible with your utils:
        if isinstance(result, (HttpResponse, FileResponse)):
            return result

        if isinstance(result, (bytes, bytearray)):
            resp = HttpResponse(result, content_type='application/pdf')
            resp['Content-Disposition'] = f'attachment; filename="report_{pk}_{lang}.pdf"'
            resp['Cache-Control'] = 'no-store'
            return resp

        # Anything else is unexpected
        logger.error("generate_report_pdf returned unexpected type: %s", type(result))
        return Response(
            {"error": "PDF generator returned unexpected type (expected bytes or HttpResponse)."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=False, methods=['get'], url_path=r'student_progress/(?P<student_id>[^/.]+)')
    def student_progress(self, request, student_id=None):
        """
        API endpoint to get subject-wise performance of a student across all exams.
        Returns Chart.js-friendly structure.

        GET /api/reports/student_progress/<student_id>/
        """
        entries = PerformanceEntry.objects.filter(report__student__id=student_id)
        data = {}
        for entry in entries:
            subject = entry.subject.name
            if subject not in data:
                data[subject] = []
            data[subject].append({
                'exam': entry.report.exam.name,
                'marks_obtained': entry.marks_obtained,
                'total_marks': entry.total_marks,
                'percentage': entry.percentage
            })
        return Response(data)

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        """
        Download the *stored* PDF file for a specific report (if you persist it).
        GET /api/reports/<pk>/pdf/
        """
        report = self.get_object()
        if not getattr(report, "pdf_file", None):
            return Response({'detail': 'PDF not generated for this report.'}, status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(report.pdf_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=report_{report.id}.pdf'
        return response

    @action(detail=True, methods=['post'])
    def send_report(self, request, pk=None):
        """
        Send report to student/parent via selected method (WhatsApp/SMS/Email).
        POST body: { "method": "whatsapp" | "sms" | "email" }
        """
        method = request.data.get("method")
        _ = self.get_object()  # ensure report exists (you can use it below)

        # TODO: Implement actual sending logic (Twilio, SMTP, etc.)
        if method == "whatsapp":
            return Response({"status": "sent via WhatsApp"})
        elif method == "sms":
            return Response({"status": "sent via SMS"})
        elif method == "email":
            return Response({"status": "sent via Email"})
        else:
            return Response({"error": "Invalid method"}, status=status.HTTP_400_BAD_REQUEST)


class PerformanceEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on PerformanceEntry.
    """
    queryset = PerformanceEntry.objects.all()
    serializer_class = PerformanceEntrySerializer
    # permission_classes = [IsAuthenticated]


class MessageLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on MessageLog.
    """
    queryset = MessageLog.objects.all()
    serializer_class = MessageLogSerializer
    # permission_classes = [IsAuthenticated]


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer