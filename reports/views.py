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

    @action(detail=True, methods=["get"], url_path="generate_pdf")
    def generate_pdf(self, request, pk=None):

        # 1) Normalize/validate the query param
        lang = (request.query_params.get("lang") or "en").lower()
        if lang not in ("en", "ur"):
            lang = "en"

        # 2) Ensure the report exists (nice 404 if not)
        get_object_or_404(Report, pk=pk)

        # 3) Ask utils for the bytes for THIS language
        #    IMPORTANT: generate_report_pdf MUST actually switch template/fonts based on `lang`.
        try:
            pdf_bytes: bytes = generate_report_pdf(report_id=pk, lang=lang)
        except Exception as exc:
            # helpful error for the frontend
            return Response({"detail": f"PDF generation failed: {exc}"}, status=500)

        # 4) Return a proper FileResponse with language in filename
        filename = f"report_{pk}_{lang}.pdf"
        return FileResponse(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )

    @action(detail=False, methods=['get'], url_path='student_progress/(?P<student_id>[^/.]+)')
    def student_progress(self, request, student_id=None):
        """
        API endpoint to get subject-wise performance of a student across all exams.
        Returns Chart.js-friendly structure.
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
        Download the PDF for a specific report.
        """
        report = self.get_object()
        if not report.pdf_file:
            return Response({'detail': 'PDF not generated for this report.'}, status=404)
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
        report = self.get_object()

        # TODO: Implement actual sending logic (Twilio, SMTP, etc.)
        # For demo, just log or simulate:
        if method == "whatsapp":
            # call your WhatsApp sending function here
            return Response({"status": "sent via WhatsApp"})
        elif method == "sms":
            # call your SMS sending function here
            return Response({"status": "sent via SMS"})
        elif method == "email":
            # call your email sending function here
            return Response({"status": "sent via Email"})
        else:
            return Response({"error": "Invalid method"}, status=400)

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
