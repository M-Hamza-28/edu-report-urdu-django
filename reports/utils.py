# reports/utils.py
import io
import os
from django.conf import settings
from django.http import FileResponse, HttpResponse  # keep HttpResponse for 404s
from django.template.loader import render_to_string, select_template
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS

from .models import Report, PerformanceEntry

def generate_report_pdf(report_id, lang: str = "en"):
    """
    Generate a report PDF in the requested language.
    Returns a FileResponse with a language-specific filename.

    lang: "en" | "ur"
    """
    lang = (lang or "en").lower()
    if lang not in ("en", "ur"):
        lang = "en"

    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return HttpResponse("Report not found", status=404)

    entries = PerformanceEntry.objects.filter(report=report)

    # Context passed to the template (templates can branch on `lang`)
    context = {
        "report": report,
        "entries": entries,
        "lang": lang,
        "is_urdu": lang == "ur",
    }

    # Pick the first existing template (Urdu -> English -> generic fallback)
    # Create these if you don’t already have them:
    #   templates/reports/report_ur.html
    #   templates/reports/report_en.html
    #   templates/report_template.html (fallback)
    template = select_template([
        "reports/report_ur.html" if lang == "ur" else "___dummy___",  # only try when needed
        "reports/report_en.html" if lang == "en" else "___dummy___",
        "report_template.html",  # your existing fallback
    ])

    html_string = render_to_string(template.template.name, context)

    # Resolve CSS path via staticfiles finders (works in dev + collectstatic)
    # Place your stylesheet at:  static/fonts/report_style.css
    css_rel_path = "fonts/report_style.css"
    css_abs_path = finders.find(css_rel_path)

    # Base URL for resolving relative asset paths in HTML/CSS (fonts, images)
    # Prefer the directory containing the CSS; fallback to STATIC_ROOT or BASE_DIR.
    base_url = os.path.dirname(css_abs_path) if css_abs_path else (
        settings.STATIC_ROOT if getattr(settings, "STATIC_ROOT", None) else settings.BASE_DIR
    )

    # Build the PDF bytes
    stylesheets = [CSS(css_abs_path)] if css_abs_path else None
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf(stylesheets=stylesheets)

    # Return a downloadable response with language in the filename
    filename = f"report_{report_id}_{lang}.pdf"
    return FileResponse(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )


def convert_to_urdu_digits(value):
    english = "0123456789."
    urdu = "۰۱۲۳۴۵۶۷۸۹٫"
    return "".join(urdu[english.index(c)] if c in english else c for c in str(value))
