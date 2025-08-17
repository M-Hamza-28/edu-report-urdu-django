from django.contrib import admin
from .models import (
    Tutor, Student, Subject, Exam,
    Report, PerformanceEntry, MessageLog
)

# ----------------------------
# Inlines
# ----------------------------
class PerformanceEntryInline(admin.TabularInline):
    model = PerformanceEntry
    extra = 1  # one empty row by default
    fields = ("subject", "marks_obtained", "total_marks")
    autocomplete_fields = ("subject",)
    # If your model has a computed 'percentage' property, you can show it read-only:
    # readonly_fields = ("percentage",)

# ----------------------------
# Tutor
# ----------------------------
@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'full_name_urdu', 'email', 'phone', 'location', 'created_at')
    search_fields = ('full_name', 'full_name_urdu', 'email', 'location', 'phone')
    ordering = ('-created_at',)

# ----------------------------
# Student
# ----------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'full_name_urdu', 'tutor', 'gender', 'grade_level', 'registration_date')
    search_fields = ('full_name', 'full_name_urdu', 'grade_level', 'tutor__full_name')
    list_filter = ('gender', 'grade_level')
    date_hierarchy = 'registration_date'
    list_select_related = ('tutor',)

    # ✅ SHOW SUBJECTS PICKER IN ADMIN
    filter_horizontal = ('subjects',)  # dual-list widget
    # For very large data sets, also enable autocompletes:
    # autocomplete_fields = ('tutor', 'subjects')

# ----------------------------
# Subject
# ----------------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_urdu', 'category')
    search_fields = ('name', 'name_urdu', 'category')
    ordering = ('name',)

# ----------------------------
# Exam
# ----------------------------
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'date')
    search_fields = ('name', 'exam_type')
    list_filter = ('exam_type', 'date')
    date_hierarchy = 'date'
    ordering = ('-date',)

# ----------------------------
# Report
# ----------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'exam', 'report_date')
    search_fields = ('student__full_name', 'exam__name', 'tutor__full_name')
    list_filter = ('report_date', 'exam__exam_type')
    date_hierarchy = 'report_date'
    list_select_related = ('student', 'tutor', 'exam')
    autocomplete_fields = ('student', 'tutor', 'exam')

    # ✅ Manage entries directly on the report page
    inlines = [PerformanceEntryInline]

    # Small perf boost when listing reports:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'tutor', 'exam')

# ----------------------------
# PerformanceEntry
# ----------------------------
@admin.register(PerformanceEntry)
class PerformanceEntryAdmin(admin.ModelAdmin):
    # Use a safe display for percentage (works even if model lacks a direct field)
    def percentage_display(self, obj):
        try:
            if getattr(obj, 'percentage', None) is not None:
                return round(obj.percentage, 2)
            # Fallback compute
            if obj.total_marks:
                return round((obj.marks_obtained / obj.total_marks) * 100, 2)
        except Exception:
            return "-"
        return "-"
    percentage_display.short_description = 'Percentage'

    list_display = ('report', 'subject', 'marks_obtained', 'total_marks', 'percentage_display')
    search_fields = ('subject__name', 'report__student__full_name', 'report__exam__name')
    list_filter = ('subject', 'report__exam__exam_type', 'report__report_date')
    list_select_related = ('report', 'subject', 'report__student', 'report__exam')
    autocomplete_fields = ('report', 'subject')

# ----------------------------
# MessageLog
# ----------------------------
@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'contact_type', 'status', 'timestamp')
    list_filter = ('contact_type', 'status', 'timestamp')
    search_fields = ('student__full_name', 'message')
    date_hierarchy = 'timestamp'
    list_select_related = ('student',)
