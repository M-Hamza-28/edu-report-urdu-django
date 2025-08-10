# -*- coding: utf-8 -*-
"""
Management command to wipe ALL app data.

Usage:
  python manage.py reset_data --yes-i-am-sure
  python manage.py reset_data --yes-i-am-sure --truncate

Flags:
  --yes-i-am-sure : required confirmation flag (prevents accidents)
  --truncate      : use TRUNCATE ... RESTART IDENTITY CASCADE (PostgreSQL),
                    resets auto-increment IDs. If DB doesn't support this,
                    auto-falls back to .delete().

Notes:
- This targets the core reporting models only. Add/remove models as needed.
- Wraps in a transaction for safety.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.utils import ProgrammingError
from reports.models import Tutor, Student, Subject, Exam, Report, PerformanceEntry  # adjust if you renamed

TABLES = [
    # Order matters only if you use .delete() and there are FK constraints
    # Using TRUNCATE with CASCADE will handle order automatically.
    # These are the concrete DB table names (not model names).
    Tutor._meta.db_table,
    Student._meta.db_table,
    Subject._meta.db_table,
    Exam._meta.db_table,
    PerformanceEntry._meta.db_table,
    Report._meta.db_table,
]

class Command(BaseCommand):
    help = "Wipes ALL data from reporting tables. Use with caution."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes-i-am-sure",
            action="store_true",
            help="Required confirmation flag. Acknowledges irreversible data wipe.",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Use TRUNCATE ... RESTART IDENTITY CASCADE (PostgreSQL only).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["yes_i_am_sure"]:
            raise CommandError(
                "Refusing to run without --yes-i-am-sure. This command wipes ALL data."
            )

        use_truncate = options["truncate"]

        if use_truncate:
            self.stdout.write(self.style.WARNING("Attempting TRUNCATE (PostgreSQL)…"))
            try:
                with connection.cursor() as cursor:
                    # Build a single TRUNCATE statement with all tables + RESTART IDENTITY + CASCADE
                    joined = ", ".join(connection.ops.quote_name(t) for t in TABLES)
                    sql = f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE;"
                    cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS("TRUNCATE completed (IDs reset)."))
                return
            except ProgrammingError as e:
                self.stdout.write(self.style.WARNING(
                    f"TRUNCATE failed or unsupported on this DB ({e}). Falling back to .delete()."
                ))

        # Fallback delete (or chosen path if --truncate not provided)
        self.stdout.write(self.style.WARNING("Deleting via ORM… (IDs not reset)"))
        # Delete children first if you don't use CASCADE TRUNCATE
        # Adjust order if your FK graph differs
        Report.objects.all().delete()
        PerformanceEntry.objects.all().delete()
        Exam.objects.all().delete()
        Student.objects.all().delete()
        Subject.objects.all().delete()
        Tutor.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Delete completed."))
