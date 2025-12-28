from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0014_examsession_uniq_session_year_nonnull_and_more"),
    ]

    operations = [
        # -------------------------
        # 1) New tables
        # -------------------------
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("domain", models.CharField(max_length=200, blank=True, null=True, unique=True)),
                ("locale", models.CharField(max_length=10, default="en-PK")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),

        migrations.CreateModel(
            name="Grade",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("name_urdu", models.CharField(max_length=100, blank=True, null=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True)),
            ],
        ),

        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("name", models.CharField(max_length=20)),
                ("grade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.grade", related_name="sections")),
            ],
        ),

        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("active", models.BooleanField(default=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.examsession", related_name="enrollments2")),
                ("grade", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.grade", null=True, blank=True)),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.section", null=True, blank=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reports.student", related_name="enrollments2")),
            ],
            options={
                "indexes": [models.Index(fields=["student", "academic_year"], name="reports_enr_student_ay_idx")],
                "unique_together": {("student", "academic_year")},
            },
        ),

        migrations.CreateModel(
            name="ExamEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("date", models.DateField(blank=True, null=True)),
                ("max_marks", models.DecimalField(max_digits=6, decimal_places=2)),
                ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reports.exam", related_name="events")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.section", related_name="exam_events")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="reports.subject", related_name="exam_events")),
            ],
            options={
                "unique_together": {("exam", "section", "subject")},
                "indexes": [models.Index(fields=["exam", "section"], name="reports_exe_exam_section_idx")],
            },
        ),

        migrations.CreateModel(
            name="GradeScale",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("label", models.CharField(max_length=100, default="Default")),
                ("is_default", models.BooleanField(default=False)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True)),
            ],
        ),

        migrations.CreateModel(
            name="GradeBoundary",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("min_pct", models.DecimalField(max_digits=5, decimal_places=2)),
                ("max_pct", models.DecimalField(max_digits=5, decimal_places=2)),
                ("letter", models.CharField(max_length=3)),
                ("gpa", models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)),
                ("grade_scale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reports.gradescale", related_name="boundaries")),
            ],
        ),

        migrations.CreateModel(
            name="ReportTemplate",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("engine", models.CharField(max_length=20, default="reportlab")),
                ("rtl_font", models.CharField(max_length=200, blank=True, null=True)),
                ("file_url", models.URLField(blank=True, null=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True)),
            ],
        ),

        # -------------------------
        # 2) Extend existing models (add nullable fields; no breakage)
        # -------------------------
        migrations.AddField(
            model_name="report",
            name="template",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.reporttemplate", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="report",
            name="status",
            field=models.CharField(max_length=20, default="draft"),
        ),
        migrations.AddField(
            model_name="report",
            name="pdf_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="summary_json",
            field=models.JSONField(default=dict, blank=True),
        ),

        migrations.AddField(
            model_name="studentexammark",
            name="exam_event",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.examevent", null=True, blank=True),
        ),

        # Optional multi-tenant hooks (all nullable; harmless if unused now)
        migrations.AddField(
            model_name="tutor",
            name="organization",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="student",
            name="organization",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="subject",
            name="organization",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="subject",
            name="code",
            field=models.CharField(max_length=40, blank=True, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name="subject",
            name="is_elective",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="examsession",
            name="organization",
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to="reports.organization", null=True, blank=True),
        ),
        migrations.AddField(
            model_name="examsession",
            name="is_current",
            field=models.BooleanField(default=False),
        ),

        # -------------------------
        # 3) Subject (org,code) conditional uniqueness
        # -------------------------
        migrations.AddConstraint(
            model_name="subject",
            constraint=models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_subject_code_per_org",
                condition=Q(code__isnull=False) & ~Q(code=""),
            ),
        ),
    ]
