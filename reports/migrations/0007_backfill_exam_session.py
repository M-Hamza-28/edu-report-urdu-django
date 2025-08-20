from django.db import migrations

def backfill_exam_session(apps, schema_editor):
    """
    Attach all legacy Exam rows that have session=NULL to a default ExamSession.
    Uses `name` (no `code` field exists on ExamSession).
    """
    Exam = apps.get_model('reports', 'Exam')
    ExamSession = apps.get_model('reports', 'ExamSession')

    # Keep ASCII hyphen to avoid “en-dash” oddities in logs
    default_session, _ = ExamSession.objects.get_or_create(
        name="Session 2025-2026",
        defaults={"year": 2025}  # optional; remove if you prefer
    )

    Exam.objects.filter(session__isnull=True).update(session=default_session)

class Migration(migrations.Migration):
    # ⬇️ CHANGE THIS to the migration that created ExamSession and made Exam.session nullable
    dependencies = [
        ('reports', '0006_examsession_exam_session_studentsession'),
    ]

    operations = [
        migrations.RunPython(backfill_exam_session, migrations.RunPython.noop),
    ]
