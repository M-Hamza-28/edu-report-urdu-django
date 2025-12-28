from django.core.management.base import BaseCommand
from django.db import transaction
from reports.models import GradeScale, GradeBoundary

DEFAULT_BOUNDS = [
    ("A+", 90, 100, 4.0),
    ("A", 80, 89.99, 4.0),
    ("B+", 70, 79.99, 3.5),
    ("B", 60, 69.99, 3.0),
    ("C", 50, 59.99, 2.0),
    ("D", 40, 49.99, 1.0),
    ("F", 0, 39.99, 0.0),
]

class Command(BaseCommand):
    help = "Create a default GradeScale with common boundaries. Idempotent."

    def handle(self, *args, **opts):
        with transaction.atomic():
            scale, _ = GradeScale.objects.get_or_create(label="Default", is_default=True)
            for letter, minp, maxp, gpa in DEFAULT_BOUNDS:
                GradeBoundary.objects.get_or_create(
                    grade_scale=scale, letter=letter,
                    defaults={"min_pct": minp, "max_pct": maxp, "gpa": gpa},
                )
        self.stdout.write(self.style.SUCCESS("Default grade scale ready."))
