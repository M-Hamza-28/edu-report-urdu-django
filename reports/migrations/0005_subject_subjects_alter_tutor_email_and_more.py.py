# reports/migrations/0005_subject_subjects_alter_tutor_email_and_more.py
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    """
    Make Tutor.phone unique only when present, without clashing on deploy.

    Strategy:
      - Ensure Tutor.phone is NOT unique at field level.
      - In DB: CREATE UNIQUE INDEX IF NOT EXISTS ... WHERE phone IS NOT NULL AND phone <> ''.
      - In Django state: Add the UniqueConstraint with the same condition, so future
        migrations see the correct schema without trying to re-create it.
    """

    dependencies = [
        ("reports", "0004_feedback"),
    ]

    operations = [
        # 1) Make sure the phone field itself is not unique (uniqueness handled by conditional index/constraint)
        migrations.AlterField(
            model_name="tutor",
            name="phone",
            field=models.CharField(max_length=15, null=True, blank=True),
        ),

        # (Optional) Keep these if your original 0005 altered these tutor fields.
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

        # 2) Database-side: create the partial unique index ONLY IF it doesn't exist.
        #    This avoids the "relation already exists" error on environments where it was created earlier.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uniq_tutor_phone_when_present "
                        "ON reports_tutor (phone) "
                        "WHERE phone IS NOT NULL AND phone <> '';"
                    ),
                    reverse_sql=(
                        "DROP INDEX IF EXISTS uniq_tutor_phone_when_present;"
                    ),
                ),
            ],
            state_operations=[
                # 3) Django state: record the intended UniqueConstraint so the model state stays correct.
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

        # 4) If your original 0005 also added other fields (e.g., M2M subjects on Student),
        #    add those operations here (uncomment and adjust as needed).
        # migrations.AddField(
        #     model_name="student",
        #     name="subjects",
        #     field=models.ManyToManyField(blank=True, related_name="students", to="reports.subject"),
        # ),
    ]
