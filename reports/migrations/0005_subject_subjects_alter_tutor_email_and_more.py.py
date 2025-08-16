# reports/migrations/0005_subject_subjects_alter_tutor_email_and_more.py
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    """
    Fix deploy error:
      psycopg2.errors.DuplicateTable: relation "uniq_tutor_phone_when_present" already exists

    Strategy:
      1) DROP the leftover constraint/index if they exist (no-op if absent)
      2) Ensure Tutor.phone is NOT unique at field level
      3) Re-add a single conditional UniqueConstraint on phone (when not null/empty)
      4) (Keep any other field alterations you previously intended here)
    """

    dependencies = [
        ("reports", "0004_feedback"),
    ]

    operations = [
        # --- 0) Defensive cleanup: drop any leftover objects with this name ---
        migrations.RunSQL(
            # Drop constraint if present
            "ALTER TABLE reports_tutor DROP CONSTRAINT IF EXISTS uniq_tutor_phone_when_present;",
            reverse_sql="",
        ),
        migrations.RunSQL(
            # Drop index with the same name if present (some earlier attempts may have created it directly)
            "DROP INDEX IF EXISTS uniq_tutor_phone_when_present;",
            reverse_sql="",
        ),

        # --- 1) Make sure the Tutor.phone field itself is NOT unique at field level ---
        migrations.AlterField(
            model_name="tutor",
            name="phone",
            field=models.CharField(max_length=15, null=True, blank=True),
        ),

        # If your original 0005 altered these fields, keep them here (safe no-ops if already matching)
        migrations.AlterField(
            model_name="tutor",
            name="email",
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="tutor",
            name="location",
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        # --- 2) Re-add the intended conditional unique constraint (single source of truth) ---
        migrations.AddConstraint(
            model_name="tutor",
            constraint=models.UniqueConstraint(
                fields=("phone",),
                name="uniq_tutor_phone_when_present",
                condition=Q(phone__isnull=False) & ~Q(phone=""),
            ),
        ),

        # --- 3) (Optional) If your original 0005 added other fields, put them below ---
        # Example for adding a ManyToMany (adjust to your actual intent; remove if not needed):
        migrations.AddField(
            model_name="student",
            name="subjects",
            field=models.ManyToManyField(blank=True, related_name="students", to="reports.subject"),
        ),
    ]
