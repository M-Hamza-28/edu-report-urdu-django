from django.db import migrations

operations = [
    # 1) Drop any leftover constraint or index with this name (no-op if absent)
    migrations.RunSQL(
        sql=(
            "DO $$ BEGIN "
            "  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_tutor_phone_when_present') THEN "
            "    ALTER TABLE reports_tutor DROP CONSTRAINT uniq_tutor_phone_when_present; "
            "  END IF; "
            "  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'uniq_tutor_phone_when_present') THEN "
            "    DROP INDEX IF EXISTS uniq_tutor_phone_when_present; "
            "  END IF; "
            "END $$;"
        ),
        reverse_sql="",
    ),

    # 2) Now add your constraint normally
    migrations.AddConstraint(
        model_name='tutor',
        constraint=models.UniqueConstraint(
            fields=('phone',),
            name='uniq_tutor_phone_when_present',
            condition=Q(phone__isnull=False) & ~Q(phone='')
        ),
    ),

    # ... rest of the existing operations in 0005 ...
]
