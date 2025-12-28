# reports/utils.py
import os
from typing import Iterable, List, Optional, Tuple, Dict, Any, TYPE_CHECKING

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

try:
    # Prefer WeasyPrint if available
    from weasyprint import HTML, CSS  # type: ignore
    _HAS_WEASY = True
except Exception:
    HTML = None  # type: ignore[assignment]
    _HAS_WEASY = False

# Provide a type-only import so Pylance knows CSS is a type, even if not installed
if TYPE_CHECKING:
    from weasyprint import CSS  # noqa: F401
from .models import (
    Report, PerformanceEntry, ReportTemplate,
)

# ------------------------------------------------------------
# Static helpers
# ------------------------------------------------------------

def _static_path(rel_path: str) -> Optional[str]:
    """
    Resolve a STATIC file to an absolute path using Django's staticfiles finders.
    Returns None if the file does not exist (safe: no exception).
    """
    fs_path = finders.find(rel_path)
    if fs_path and os.path.exists(fs_path):
        return fs_path
    return None


def _css_from_paths(paths: Iterable[str]) -> List["CSS"]:
    """
    Build WeasyPrint CSS objects only for files that exist.
    If WeasyPrint isn't installed, returns an empty list.
    """
    css_objs: List["CSS"] = []
    if not _HAS_WEASY:
        return css_objs
    for p in paths:
        abs_path = _static_path(p)
        if abs_path:
            try:
                css_objs.append(CSS(filename=abs_path))  # type: ignore
            except Exception:
                # Ignore a bad CSS path and continue – never crash PDF rendering pipeline
                pass
    return css_objs


def _rtl_font_css() -> List["CSS"]:
    """
    Tries to include Urdu/RTL font face if available under static.
    We look for commonly used font paths and include whichever are found.
    """
    candidates = [
        # Typical locations used in this project
        "reports/fonts/NotoNastaliqUrdu-Regular.ttf",
        "reports/fonts/NotoNastaliqUrdu-Regular.woff2",
        "reports/fonts/NotoNastaliqUrdu-Regular.woff",
    ]
    found = [p for p in candidates if _static_path(p)]
    if not (_HAS_WEASY and found):
        return []

    # Build a small @font-face CSS on the fly and feed to WeasyPrint
    css_text = "@font-face { font-family: 'NotoNastaliqUrdu'; src: " + \
               ", ".join([f"url('file://{_static_path(p)}')" for p in found]) + \
               "; font-weight: normal; font-style: normal; }\n" \
               "body { font-family: 'NotoNastaliqUrdu', sans-serif; }"
    try:
        return [CSS(string=css_text)]  # type: ignore
    except Exception:
        return []


# ------------------------------------------------------------
# Template selection
# ------------------------------------------------------------

def pick_report_template(report: "Report") -> Optional["ReportTemplate"]:
    """
    Decide which ReportTemplate to use. Current strategy:
    1) If report.template is set (if your model has it), return it (safe getattr).
    2) Else return the latest global template (first() by -id).
    Non-fatal: returns None if no template exists – caller can still render the
    default HTML template.
    """
    tmpl = getattr(report, "template", None)
    if tmpl:
        return tmpl
    try:
        return ReportTemplate.objects.order_by("-id").first()
    except Exception:
        return None


# ------------------------------------------------------------
# Public API: render report → html/pdf bytes
# ------------------------------------------------------------

def build_report_context(report: "Report", lang: str = "en") -> Dict[str, Any]:
    """
    Assemble a serializable context dictionary used by report templates.
    """
    is_ur = (str(lang).lower() in ("ur", "urdu", "bi", "bilingual"))
    entries = list(report.entries.select_related("subject").all())  # type: ignore[attr-defined]
    # Allow template to decide on RTL specifics
    ctx = {
        "report": report,
        "entries": entries,
        "lang": "ur" if is_ur else "en",
        "is_ur": is_ur,
    }
    return ctx


def render_report_html(report: "Report", lang: str = "en", template_name: str = "report_template.html",
                       extra_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Return rendered HTML string for a given report using Django templates.
    """
    ctx = build_report_context(report, lang)
    if extra_context:
        ctx.update(extra_context)
    return render_to_string(template_name, ctx)


def render_report_pdf_bytes(report: "Report", lang: str = "en",
                            base_css: str = "reports/css/report_style.css",
                            urdu_css: str = "reports/css/report_style_ur.css",
                            template_name: str = "report_template.html",
                            include_rtl_font: bool = True) -> bytes:
    """
    Render report to PDF bytes using WeasyPrint.
    - Silently falls back to returning an encoded HTML if WeasyPrint is unavailable.
    - Only includes CSS files that exist to avoid MissingFileError during collectstatic.
    """
    html = render_report_html(report, lang=lang, template_name=template_name)

    if not _HAS_WEASY:
        # No WeasyPrint installed – return HTML bytes so caller can still respond
        return html.encode("utf-8")

    css_paths = [base_css]
    if str(lang).lower() in ("ur", "urdu", "bi", "bilingual"):
        css_paths.append(urdu_css)

    styles = _css_from_paths(css_paths)
    if include_rtl_font:
        styles.extend(_rtl_font_css())

    base_url = getattr(settings, "STATIC_ROOT", None) or getattr(settings, "BASE_DIR", None) or "/"
    pdf = HTML(string=html, base_url=base_url).write_pdf(stylesheets=styles)  # type: ignore
    return pdf


# ------------------------------------------------------------
# Utilities: filenames, simple audit hook (DB model can be added later)
# ------------------------------------------------------------

def safe_filename(name: str, suffix: str = ".pdf") -> str:
    """
    Make a safe filename (very light normalizer; keeps Urdu/Unicode intact).
    """
    bad = {'/', '\\', ':', '*', '?', '"', '<', '>', '|'}
    cleaned = "".join(ch for ch in name if ch not in bad).strip()
    return f"{cleaned or 'report'}{suffix}"


def log_action(user, action: str, entity: str, entity_id: int, meta: Optional[Dict[str, Any]] = None) -> None:
    """
    Audit hook:
    - Always write to Python logger.
    - If the AuditLog model exists and DB is ready, persist a row (best-effort).
    """
    try:
        username = getattr(user, "username", "anonymous") if user else "anonymous"
        logging_line = f"[AUDIT] {username} {action} {entity}#{entity_id}"
        if meta:
            logging_line += f" meta={meta}"
        import logging
        logger = logging.getLogger(__name__)
        logger.info(logging_line)
    except Exception:
        pass

    # Try to write a DB row (never raise)
    try:
        from django.db import connection
        if not connection.introspection.table_names():
            return  # migrations not applied yet
        # local import to avoid circulars
        from .models import AuditLog
        AuditLog.objects.create(
            actor=user if getattr(user, "is_authenticated", False) else None,
            action=action,
            entity=entity,
            entity_id=int(entity_id),
            meta=meta or {},
        )
    except Exception:
        pass
