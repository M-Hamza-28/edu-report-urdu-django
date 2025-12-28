from django.core.management.base import BaseCommand
from django.db import transaction
from reports.models import StudentSession, Enrollment

class Command(BaseCommand):
    help = (
        "Copy legacy StudentSession rows into canonical Enrollment. "
        "Idempotent: will not duplicate existing (student, academic_year)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--inactive", action="store_true", help="Create rows as inactive instead of active.")

    def handle(self, *args, **opts):
        active = not opts["inactive"]
        created = 0
        skipped = 0

        self.stdout.write("Backfilling Enrollment from StudentSession...")
        with transaction.atomic():
            qs = StudentSession.objects.all().values("student_id", "session_id")
            for row in qs:
                obj, was_created = Enrollment.objects.get_or_create(
                    student_id=row["student_id"],
                    academic_year_id=row["session_id"],
                    defaults={"active": active, "grade_id": None, "section_id": None},
                )
                created += int(was_created)
                skipped += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created} enrollment(s), skipped {skipped} existing."
        ))
