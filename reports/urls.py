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
router.register(r'tutors', TutorViewSet)
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'exams', ExamViewSet)
router.register(r'exam-sessions', ExamSessionViewSet)
router.register(r'student-sessions', StudentSessionViewSet)
router.register(r'reports', ReportViewSet)  # <--- This enables /api/reports/
router.register(r'entries', PerformanceEntryViewSet)
router.register(r'messages', MessageLogViewSet)
router.register(r'feedback', FeedbackViewSet)


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
