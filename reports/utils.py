import os
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML, CSS
from .models import Tutor, Student, Subject, Exam, Report, PerformanceEntry, MessageLog, Feedback

def generate_report_pdf(report_id, lang='en'):
    try:
        report = Report.objects.get(id=report_id)
        entries = PerformanceEntry.objects.filter(report=report)

        # Prepare data context
        context = {
            'report': report,
            'entries': entries,
            'lang': lang,
        }

        # Render HTML from template
        html_string = render_to_string('report_template.html', context)

        # CSS (font + RTL support)
        css_path = os.path.join(settings.BASE_DIR, 'reports', 'static', 'fonts', 'report_style.css')

        # Generate PDF
        pdf_file = HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(stylesheets=[CSS(css_path)])

        return HttpResponse(pdf_file, content_type='application/pdf')

    except Report.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    
def convert_to_urdu_digits(value):
    english = "0123456789."
    urdu    = "۰۱۲۳۴۵۶۷۸۹٫"
    return ''.join(urdu[english.index(c)] if c in english else c for c in str(value))
