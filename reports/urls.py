from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TutorViewSet,
    StudentViewSet,
    SubjectViewSet,
    ExamViewSet,
    ReportViewSet,
    PerformanceEntryViewSet,
    MessageLogViewSet,
    FeedbackViewSet,
    ExamSessionViewSet,
    StudentSessionViewSet
)

# DRF router to auto-generate standard CRUD endpoints
router = DefaultRouter()
router.register(r'tutors', TutorViewSet, basename= 'tutor')
router.register(r'students', StudentViewSet, basename= 'student')
router.register(r'subjects', SubjectViewSet, basename= 'subject')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-sessions', ExamSessionViewSet, basename='exam-session')
router.register(r'student-sessions', StudentSessionViewSet, 'student-session')
router.register(r'reports', ReportViewSet, 'report')  # <--- This enables /api/reports/
router.register(r'entries', PerformanceEntryViewSet, 'entries')
router.register(r'messages', MessageLogViewSet, 'messages')
router.register(r'feedback', FeedbackViewSet, 'feedback')


# Main urlpatterns - expose all endpoints under this app
urlpatterns = [
    path('', include(router.urls)),  # All /api/<model>/ routes auto-included
]

# --- Usage Guide ---
# With this config, the following endpoints are available:
# /api/tutors/
# /api/students/
# /api/subjects/
# /api/exams/
# /api/reports/
# /api/entries/
# /api/messages/
