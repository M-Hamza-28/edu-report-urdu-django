# reports/admin.py
from django.contrib import admin
from django.db import models as dj_models
from .models import Setting, MessageTemplate, MessageThread, Message, MessageDelivery, Guardian, AuditLog

from . import models as m


# --------------------------------------------------------------------
# Smart admin helpers
# --------------------------------------------------------------------
class SmartAdmin(admin.ModelAdmin):
    """
    A resilient ModelAdmin that only shows fields that actually exist,
    so we don't break if a field is renamed or missing in this repo snapshot.
    """
    suggested_list: tuple = ()
    suggested_search: tuple = ()
    suggested_filters: tuple = ()
    autocomplete: tuple = ()

    def get_list_display(self, request):
        # Always include id; try to include suggested fields that exist.
        base = ["id"]
        for name in self.suggested_list:
            if hasattr(self.model, name):
                base.append(name)
                continue
            try:
                self.model._meta.get_field(name)
                base.append(name)
            except Exception:
                continue
        # Fallback to __str__ if no other fields
        if len(base) == 1:
            base.append("__str__")
        return tuple(dict.fromkeys(base))  # dedupe while preserving order

    def get_search_fields(self, request):
        fields = []
        for name in self.suggested_search:
            try:
                f = self.model._meta.get_field(name)
                if isinstance(f, (dj_models.CharField, dj_models.TextField, dj_models.EmailField)):
                    fields.append(name)
            except Exception:
                continue
        return tuple(dict.fromkeys(fields))

    def get_list_filter(self, request):
        fields = []
        for name in self.suggested_filters:
            try:
                self.model._meta.get_field(name)
                fields.append(name)
            except Exception:
                continue
        return tuple(dict.fromkeys(fields))

    def get_autocomplete_fields(self, request):
        fields = []
        for name in self.autocomplete:
            try:
                f = self.model._meta.get_field(name)
                if isinstance(f, (dj_models.ForeignKey, dj_models.OneToOneField)):
                    fields.append(name)
            except Exception:
                continue
        return tuple(dict.fromkeys(fields))


def _register(model, **hints):
    """
    Register a model using SmartAdmin with gentle hints.
    """
    attrs = dict(
        suggested_list=hints.get("list", ()),
        suggested_search=hints.get("search", ()),
        suggested_filters=hints.get("filters", ()),
        autocomplete=hints.get("autocomplete", ()),
    )
    # Create a dynamic subclass to attach model-specific hints
    admin_cls = type(f"{model.__name__}Admin", (SmartAdmin,), attrs)
    admin.site.register(model, admin_cls)


# --------------------------------------------------------------------
# Register models – hints reflect the FE flows (lists & lookups)
# --------------------------------------------------------------------

# Core / organization
if hasattr(m, "Organization"):
    _register(m.Organization,
              list=("name", "domain", "locale", "created_at"),
              search=("name", "domain"),
              filters=("locale",))

# People
for mdl, hints in (
    ("Tutor", dict(list=("full_name", "phone", "email", "location"),
                   search=("full_name", "phone", "email", "location"))),
    ("Student", dict(list=("full_name", "roll_no", "phone", "tutor"),
                     search=("full_name", "roll_no", "phone"),
                     autocomplete=("tutor",))),
    ("Subject", dict(list=("name",), search=("name",))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

# Academics
for mdl, hints in (
    ("Grade", dict(list=("name",), search=("name",))),
    ("Section", dict(list=("name", "grade"), search=("name", "grade__name"), autocomplete=("grade",))),
    ("Enrollment", dict(list=("student", "academic_year", "grade", "section", "active"),
                        search=("student__full_name", "academic_year__name", "section__name"),
                        filters=("active",),
                        autocomplete=("student", "academic_year", "grade", "section"))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

# Sessions & exams
for mdl, hints in (
    ("ExamSession", dict(list=("name", "year", "start_date", "end_date"),
                         search=("name", "year"),
                         filters=("year",))),
    ("ExamType", dict(list=("name",), search=("name",))),
    ("Exam", dict(list=("name", "exam_type", "session", "date"),
                  search=("name", "exam_type", "session__name"),
                  filters=("exam_type", "session"),
                  autocomplete=("session",))),
    ("ExamEvent", dict(list=("exam", "section", "subject"),
                       search=("exam__name", "section__name", "subject__name"),
                       autocomplete=("exam", "section", "subject"))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

# Marks
if hasattr(m, "StudentExamMark"):
    _register(m.StudentExamMark,
              list=("student", "session", "term", "exam_type", "subject", "marks_obtained", "total_marks"),
              search=("student__full_name", "session__name", "subject__name", "term", "exam_type"),
              autocomplete=("student", "session", "subject"))

# Grading
for mdl, hints in (
    ("GradeScale", dict(list=("label", "is_default", "organization"),
                        search=("label", "organization__name"),
                        filters=("is_default", "organization"),
                        autocomplete=("organization",))),
    ("GradeBoundary", dict(list=("scale", "grade", "min_score", "max_score"),
                           search=("grade",), autocomplete=("scale",))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

# Reports
for mdl, hints in (
    ("ReportTemplate", dict(list=("title", "engine", "rtl_font", "file_url", "organization"),
                            search=("title", "engine", "organization__name"),
                            filters=("engine", "organization"),
                            autocomplete=("organization",))),
    ("Report", dict(list=("student", "tutor", "exam", "created_at"),
                    search=("student__full_name", "tutor__full_name", "exam__name"),
                    autocomplete=("student", "tutor", "exam"))),
    ("PerformanceEntry", dict(list=("report", "subject", "marks", "remarks"),
                              search=("report__id", "subject__name"),
                              autocomplete=("report", "subject"))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

# Logging / feedback
for mdl, hints in (
    ("MessageLog", dict(list=("student", "contact_type", "phone_number", "timestamp"),
                        search=("student__full_name", "phone_number", "contact_type"),
                        filters=("contact_type",),
                        autocomplete=("student",))),
    ("Feedback", dict(list=("tutor", "created_at"),
                      search=("tutor__full_name", "message"),
                      autocomplete=("tutor",))),
):
    if hasattr(m, mdl):
        _register(getattr(m, mdl), **hints)

