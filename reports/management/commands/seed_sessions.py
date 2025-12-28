# reports/management/commands/seed_sessions.py
# -----------------------------------------------------------------------------
# Idempotently seed ExamSession rows from --from-year up to next academic year.
# Creates rows with:
#   year = Y
#   name = f"Session {Y}-{Y+1}"
#   (start_date/end_date left null; feel free to extend)
# Sets is_current=True only on the most recent year inserted (others False).
#
# USAGE:
#   python manage.py seed_sessions --from-year 2020
# -----------------------------------------------------------------------------
from django.core.management.base import BaseCommand, CommandError
from datetime import date
from reports.models import ExamSession

class Command(BaseCommand):
    help = "Seed ExamSession rows with years from --from-year up to current+1. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument('--from-year', type=int, required=True, help='Starting year, e.g. 2020')

    def handle(self, *args, **opts):
        from_year = opts['from_year']
        if from_year < 2000:
            raise CommandError("from-year must be >= 2000")

        cur = date.today().year
        # up to next academic year; adjust if your policy differs
        end_year = cur + 1

        created = 0
        last_id = None
        for y in range(from_year, end_year + 1):
            name = f"Session {y}-{y+1}"
            obj, was_created = ExamSession.objects.get_or_create(
                year=y,
                defaults={"name": name}
            )
            # If a row exists without year but with matching name, you can normalize here:
            if not was_created and not obj.name:
                obj.name = name
                obj.save(update_fields=["name"])
            if was_created:
                created += 1
            last_id = obj.id

        # Mark only the latest as current; unset others
        if last_id is not None:
            ExamSession.objects.exclude(id=last_id).update(is_current=False)
            ExamSession.objects.filter(id=last_id).update(is_current=True)

        self.stdout.write(self.style.SUCCESS(f"Seeding complete. Created {created} sessions (others already existed)."))
