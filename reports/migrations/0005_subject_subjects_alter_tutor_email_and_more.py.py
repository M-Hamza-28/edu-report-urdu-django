# reports/migrations/0005_subject_subjects_alter_tutor_email_and_more.py
from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):
    """
    Idempotent fix for Tutor.phone uniqueness:
      - Ensure Tutor.phone is NOT unique at the field level.
      - DB: create a partial UNIQUE INDEX only if it doesn't exist.
      - Django state: record the UniqueConstraint so future migrations see it,
        without trying to create it again on the database.
    """

    dependencies = [
        ("reports", "0004_feedback"),
    ]

    operations = [
        # 1) Make sure the field itself is not unique (uniqueness handled by partial index/constraint)
        migrations.AlterField(
            model_name="tutor",
            name="phone",
            field=models.CharField(max_length=15, null=True, blank=True),
        ),

        # If your original 0005 altered these tutor fields, keep them (harmless if already matching)
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

        # 2) DB op: create the partial unique index IF NOT EXISTS (won't fail if it already exists)
        #    STATE op: add the UniqueConstraint to Django's model state ONLY (no DB action),
        #    so future migrations remain consistent.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uniq_tutor_phone_when_present "
                        "ON reports_tutor (phone) "
                        "WHERE phone IS NOT NULL AND phone <> '';"
                    ),
                    reverse_sql="DROP INDEX IF EXISTS uniq_tutor_phone_when_present;",
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="tutor",
                    constraint=models.UniqueConstraint(
                        fields=("phone",),
                        name="uniq_tutor_phone_when_present",
                        condition=Q(phone__isnull=False) & ~Q(phone=""),
                    ),
                ),
            ],
        ),

        # If your original 0005 also added other fields (e.g., Student.subjects M2M), add them here.
        # Example (uncomment & adjust if you actually intended this in 0005):
        migrations.AddField(
            model_name="student",
            name="subjects",
            field=models.ManyToManyField(blank=True, related_name="students", to="reports.subject"),
        ),
    ]
