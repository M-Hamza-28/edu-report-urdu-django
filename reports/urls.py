# reports/urls.py
from django.urls import path, include, re_path
from django.conf import settings
import os
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import the module, then reference everything via views.X
from . import views

# Router (keeps your trailing-slash flexibility)
router = DefaultRouter(trailing_slash='/?')

# ---- Core entities ----
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'tutors', views.TutorViewSet, basename='tutor')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'exam-sessions', views.ExamSessionViewSet, basename='exam-session')
router.register(r'student-sessions', views.StudentSessionViewSet, basename='student-session')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'sections', views.SectionViewSet, basename='section')
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'student-subjects', views.StudentSubjectViewSet, basename='student-subject')

# ---- Exams & marks ----
router.register(r'exams', views.ExamViewSet, basename='exam')
router.register(r'exam-events', views.ExamEventViewSet, basename='exam-event')
router.register(r'student-marks', views.StudentExamMarkViewSet, basename='student-mark')
router.register(r'exam-types', views.ExamTypeViewSet, basename='exam-type')
router.register(r'grade-scales', views.GradeScaleViewSet, basename='grade-scale')
router.register(r'grade-boundaries', views.GradeBoundaryViewSet, basename='grade-boundary')

# Back-compat routes
router.register(r'sessions', views.ExamSessionViewSet, basename='session')
router.register(r'marks', views.StudentExamMarkViewSet, basename='mark')

# ---- Reports ----
router.register(r'report-templates', views.ReportTemplateViewSet, basename='report-template')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'performance-entries', views.PerformanceEntryViewSet, basename='performance-entry')

# ---- Analytics root ----
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')

# Helper for binding viewset actions
analytics_view = views.AnalyticsViewSet.as_view

urlpatterns = [
    # ---- Auth (JWT) ----
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---- Profile ----
    path('users/me', views.MeView.as_view(), name='users-me'),

    # ---- Settings groups ----
    path('settings/organization',  views.OrganizationSettingsView.as_view(),  name='settings-organization'),
    path('settings/academic',      views.AcademicSettingsView.as_view(),      name='settings-academic'),
    path('settings/reporting',     views.ReportingSettingsView.as_view(),     name='settings-reporting'),
    path('settings/notifications', views.NotificationsSettingsView.as_view(), name='settings-notifications'),
    path('settings/security',      views.SecuritySettingsView.as_view(),      name='settings-security'),
    path('settings/branding',      views.BrandingUploadView.as_view(),        name='settings-branding'),

    # ---- Audit log ----
    path('audit-logs', views.AuditLogList.as_view(), name='audit-logs'),

    # ---- Messages ----
    path('messages/templates/',               views.MessageTemplatesList.as_view(),  name='messages-templates'),
    path('messages/threads/',                 views.MessageThreadsList.as_view(),    name='messages-threads'),
    path('messages/threads/<int:thread_id>/', views.MessageThreadDetail.as_view(),   name='messages-thread-detail'),
    path('messages/threads/<int:thread_id>/messages/', views.ThreadMessagesList.as_view(), name='thread-messages'),

    # ---- Guardians ----
    path('guardians/', views.GuardiansList.as_view(), name='guardians-list'),

    # ---- Helper endpoints ----
    path('prefill-marks', views.prefill_marks, name='prefill-marks'),

    # ---- Dev/E2E SAFE READ ALIASES ----
    path("templates/",                           views.TemplateListAlias.as_view(),        name='templates-alias'),
    path("templates/<str:template_id>/preview/pdf", views.TemplatePreviewPdfAlias.as_view(), name='template-preview-pdf-alias'),
    path("reports/",                             views.ReportListAlias.as_view(),          name='reports-alias'),
    path("reports/<str:report_id>/preview/pdf",  views.ReportPreviewPdfAlias.as_view(),    name='report-preview-pdf-alias'),

    # ---- Dev/E2E SAFE WRITE ALIASES (SEED) — optional trailing slash ----
    re_path(r'^sessions/?$',  views.SessionsAliasAPI.as_view(), name='sessions-alias'),
    re_path(r'^tutors/?$',    views.TutorsAliasAPI.as_view(),   name='tutors-alias'),
    re_path(r'^students/?$',  views.StudentsAliasAPI.as_view(), name='students-alias'),
    re_path(r'^subjects/?$',  views.SubjectsAliasAPI.as_view(), name='subjects-alias'),
    re_path(r'^marks/?$',     views.MarksAliasAPI.as_view(),    name='marks-alias'),

    # ---- Analytics (explicit routes used by FE/tests) ----
    path('analytics/session/<int:session_id>/overview',           analytics_view({'get': 'session_overview'}),       name='analytics-overview'),
    path('analytics/session/<int:session_id>/trends',             analytics_view({'get': 'session_trends'}),         name='analytics-trends'),
    # Distribution → call our alias that returns the pluralized payload
    path('analytics/session/<int:session_id>/distribution',       analytics_view({'get': 'session_distribution_alias'}),   name='analytics-distribution'),

    # Subject difficulty → correct method name is session-scoped
    path('analytics/session/<int:session_id>/subject-difficulty', analytics_view({'get': 'session_subject_difficulty'}),   name='analytics-subject-difficulty'),

    path('analytics/session/<int:session_id>/class-compare',      analytics_view({'get': 'session_class_compare'}),  name='analytics-class-compare'),

    path('analytics/missing-marks',                                analytics_view({'get': 'missing_marks'}),          name='analytics-missing-marks'),
    path('analytics/section/<int:section_id>/coverage',           analytics_view({'get': 'section_coverage'}),       name='analytics-section-coverage'),

    # Student/Tutor analytics contracts
    path('analytics/student/<int:student_id>/trends',             analytics_view({'get': 'student_trends'}),         name='analytics-student-trends'),
    path('analytics/student/<int:student_id>/mastery',            analytics_view({'get': 'student_mastery'}),        name='analytics-student-mastery'),
    path('analytics/student/<int:student_id>/flags',              analytics_view({'get': 'student_flags'}),          name='analytics-student-flags'),
    path('analytics/tutor/<int:tutor_id>/',                       analytics_view({'get': 'tutor_dashboard'}),        name='analytics-tutor-dashboard'),

    # Exports
    path('analytics/export/csv',                                   analytics_view({'get': 'export_csv'}),            name='analytics-export-csv'),
    path('analytics/export/pdf',                                   analytics_view({'get': 'export_pdf'}),            name='analytics-export-pdf'),

    # Report generation
    re_path(r'^reports/generate/?$', views.ReportGenerateView.as_view(), name='reports-generate'),
    path('reports/generate',          views.ReportGenerateView.as_view(), name='reports-generate-plain'),

    # ---- Router-driven endpoints (last) ----
    path('', include(router.urls)),
]

# ---- DEBUG/E2E-only helpers (mounted only in dev/test contexts) ----
if getattr(settings, "DEBUG", False) or os.environ.get("E2E_ONLY") == "1":
    urlpatterns += [
        path('test/reset',        views.test_reset,        name='test-reset'),
        path('test/notify-send',  views.notify_test_send,  name='test-notify-send'),
    ]
