import os
from typing import List
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS
from .models import Report, PerformanceEntry

# Optional: digit conversion for Urdu numerals
def convert_to_urdu_digits(value):
    english = "0123456789."
    urdu    = "۰۱۲۳۴۵۶۷۸۹٫"
    return ''.join(urdu[english.index(c)] if c in english else c for c in str(value))

def _resolve_static_paths(paths: List[str]) -> List[CSS]:
    """Resolve a list of static file paths to WeasyPrint CSS objects, skipping missing ones."""
    css_objs = []
    for p in paths:
        fs_path = finders.find(p)  # e.g. "reports/css/report_style.css"
        if fs_path and os.path.exists(fs_path):
            css_objs.append(CSS(filename=fs_path))
    return css_objs

def generate_report_pdf(report_id, lang='en'):
    """
    Build a PDF for the given report id.
    - For Urdu, we include an RTL stylesheet with @font-face for Noto Nastaliq Urdu.
    - Returns raw PDF bytes (let the view set headers/filename).
    """
    # 1) Fetch data
    report = Report.objects.select_related("student", "tutor", "exam").get(id=report_id)
    entries = PerformanceEntry.objects.filter(report=report).select_related("subject")

    is_ur = (str(lang or "en").lower() in {"ur", "urdu"})
    chosen_lang = "ur" if is_ur else "en"

    # Choose what to print in the header as “Exam: …”
    # Prefer type (Mid Term / Final) and fall back to exam.name if type missing.
    exam_type = getattr(report.exam, "exam_type", "") or ""
    exam_name = getattr(report.exam, "name", "") or ""
    exam_display = exam_type or exam_name  # <- key fix to avoid showing a subject name

    # 2) Template & context
    # If you create a dedicated Urdu template, set template_ur = "reports/report_template_ur.html"
    template = "report_template.html"
    context = {
        "report": report,
        "entries": entries,
        "lang": chosen_lang,
        "is_ur": is_ur,
        "convert_to_urdu_digits": convert_to_urdu_digits,
        "exam_display": exam_display,  # <- use this in template instead of report.exam.name
    }

    html_string = render_to_string(template, context)

    # 3) Stylesheets
    base_css = "reports/css/report_style.css"
    urdu_css = "reports/css/report_style_ur.css"
    css_files = [base_css] + ([urdu_css] if is_ur else [])
    css_objs = _resolve_static_paths(css_files)

    # 4) Base URL for resolving <img src="...">, etc.
    base_url = settings.STATIC_ROOT if getattr(settings, "STATIC_ROOT", None) else settings.BASE_DIR

    # 5) Render to PDF bytes
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf(stylesheets=css_objs)
    return pdf_bytes
