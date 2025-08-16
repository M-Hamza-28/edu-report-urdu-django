# e.g. reports/migrations/00XX_fix_tutor_phone_unique.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('reports', '00XX_previous'),
    ]

    operations = [
        # Best-effort drop of the old auto-generated unique index if it exists
        migrations.RunSQL(
            sql=(
                "DO $$ BEGIN "
                "IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'reports_tutor_phone_0558e282_uniq') THEN "
                "    -- Drop the index created by unique=True on the phone field (Postgres names auto-generate like this)\n"
                "    DROP INDEX IF EXISTS reports_tutor_phone_0558e282_uniq; "
                "END IF; "
                "END $$;"
            ),
            reverse_sql="",
        ),
    ]
