# reports/migrations/0005_fix_tutor_phone_unique.py
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    """
    Fix deploy failure:
    psycopg2.errors.DuplicateTable: relation "uniq_tutor_phone_when_present" already exists

    Root cause: a previous deploy left a constraint/index with that name in the DB.
    This migration first *drops if exists* the legacy object, then adds the
    intended conditional UniqueConstraint exactly once.
    """

    dependencies = [
        ("reports", "0004_feedback"),  # <- your last successful migration
    ]

    operations = [
        # ------------------------------------------------------------------
        # 0) Defensive cleanup: drop any leftover constraint/index if present
        # ------------------------------------------------------------------
        migrations.RunSQL(
            sql=(
                "DO $$ BEGIN "
                "  -- Drop constraint (if it exists) on reports_tutor(phone)\n"
                "  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_tutor_phone_when_present') THEN "
                "    ALTER TABLE reports_tutor DROP CONSTRAINT uniq_tutor_phone_when_present; "
                "  END IF; "
                "  -- Drop index with the same name (if it exists)\n"
                "  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'uniq_tutor_phone_when_present') THEN "
                "    DROP INDEX IF EXISTS uniq_tutor_phone_when_present; "
                "  END IF; "
                "END $$;"
            ),
            reverse_sql="",
        ),

        # ------------------------------------------------------------------
        # 1) Make sure the Tutor.phone field itself is NOT unique at field level
        #    (uniqueness will be enforced ONLY by the conditional constraint)
        #    Adjust null/blank to your model (these are common settings).
        # ------------------------------------------------------------------
        migrations.AlterField(
            model_name="tutor",
            name="phone",
            field=models.CharField(max_length=15, null=True, blank=True),
        ),

        # (Optional) If you had altered these in your previous 0005, keep them here.
        # Remove if not applicable in your project.
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

        # ------------------------------------------------------------------
        # 2) Re-add the intended single source of truth for uniqueness:
        #    Unique only when phone is present (not NULL/empty string).
        # ------------------------------------------------------------------
        migrations.AddConstraint(
            model_name="tutor",
            constraint=models.UniqueConstraint(
                fields=("phone",),
                name="uniq_tutor_phone_when_present",
                condition=Q(phone__isnull=False) & ~Q(phone=""),
            ),
        ),
    ]
