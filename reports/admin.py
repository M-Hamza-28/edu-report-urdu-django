from django.contrib import admin
from .models import (
    Tutor, Student, Subject, Exam,
    Report, PerformanceEntry, MessageLog
)

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'full_name_urdu', 'email', 'phone', 'location', 'created_at')  # ✅ Updated
    search_fields = ('full_name', 'full_name_urdu', 'email', 'location')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'full_name_urdu', 'tutor', 'gender', 'grade_level', 'registration_date')  # ✅ Updated
    search_fields = ('full_name', 'full_name_urdu', 'grade_level')
    list_filter = ('gender', 'grade_level')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_urdu', 'category')  # ✅ Updated
    search_fields = ('name', 'name_urdu', 'category')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'date')
    search_fields = ('name', 'exam_type')
    list_filter = ('exam_type', 'date')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'exam', 'report_date')
    search_fields = ('student__full_name', 'exam__name')
    list_filter = ('report_date',)


@admin.register(PerformanceEntry)
class PerformanceEntryAdmin(admin.ModelAdmin):
    list_display = ('report', 'subject', 'marks_obtained', 'total_marks', 'percentage')
    search_fields = ('subject__name',)


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'contact_type', 'status', 'timestamp')
    list_filter = ('contact_type', 'status')
    search_fields = ('student__full_name', 'message')
