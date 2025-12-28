# reports/management/commands/dedupe_sessions.py
# -----------------------------------------------------------------------------
# Deduplicate ExamSession rows by a computed label (year or normalized name).
# Keeps the lowest id as canonical, repoints FKs (StudentSession, Exam,
# StudentExamMark, Enrollment) and deletes extras. Idempotent.
#
# USAGE:
#   python manage.py dedupe_sessions
# -----------------------------------------------------------------------------
from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from reports.models import ExamSession, StudentSession, Exam, StudentExamMark
try:
    from reports.models import Enrollment
except Exception:
    Enrollment = None  # if migration not applied yet

def session_key(s: ExamSession) -> str:
    if getattr(s, "year", None):
        return f"{s.year}-{s.year+1}"
    name = (s.name or "").strip().casefold()
    name = " ".join(name.split())
    return name or f"session-{s.id}"

class Command(BaseCommand):
    help = "Deduplicate ExamSession rows by (year or normalized name). Keeps smallest id, repoints FKs, deletes extras."

    def handle(self, *args, **opts):
        self.stdout.write("Scanning sessions by computed label...")
        by_key = defaultdict(list)
        for s in ExamSession.objects.all().only('id', 'name', 'year'):
            by_key[session_key(s)].append(s.id)

        total_dupes = 0
        with transaction.atomic():
            for key, ids in by_key.items():
                ids.sort()
                keep, dupes = ids[0], ids[1:]
                if not dupes:
                    continue
                total_dupes += len(dupes)
                self.stdout.write(f"{key}: keep {keep}, dedupe {dupes}")

                # Repoint FKs on related tables
                updates = [
                    (StudentSession, 'session_id'),
                    (Exam, 'session_id'),
                    (StudentExamMark, 'session_id'),
                ]
                if Enrollment:
                    updates.append((Enrollment, 'academic_year_id'))

                for model, field in updates:
                    updated = model.objects.filter(**{f"{field}__in": dupes}).update(**{field: keep})
                    self.stdout.write(f"  -> updated {updated} {model.__name__} rows")

                # Finally delete duplicate sessions
                ExamSession.objects.filter(id__in=dupes).delete()

        self.stdout.write(self.style.SUCCESS(f"Done. Duplicate session rows removed: {total_dupes}"))
