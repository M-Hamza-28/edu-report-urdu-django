# project urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from reports.views import ReportGenerateView


def api_status(request):
    return JsonResponse({'status': 'API Running'})

urlpatterns = [
    path('', api_status, name='root-ping'),
    path('api/status', api_status, name='api-status'),

    # accepts /api/reports/generate (no trailing slash)
    path('api/reports/generate', ReportGenerateView.as_view(), name='reports-generate-nonslash'),


    # All app endpoints
    path('api/', include('reports.urls')),

    # Admin
    path('admin/', admin.site.urls),
]

# Serve media (uploads) in development: org logos, favicons, signatures, message attachments
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
