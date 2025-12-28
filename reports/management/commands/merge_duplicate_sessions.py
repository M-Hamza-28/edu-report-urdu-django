# reports/management/commands/merge_duplicate_sessions.py
# =============================================================================
# Usage:
#   python manage.py merge_duplicate_sessions --dry-run
#   python manage.py merge_duplicate_sessions
#
# Groups ExamSessions by: YEAR:<year> when year exists, else NAME:<normalized>.
# Keeps the highest id (usually the most recent) as canonical, repoints FKs
# (Exam, StudentSession, StudentExamMark, Enrollment) from duplicates.
# Safe to run multiple times (idempotent once normalized).
# =============================================================================

from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from reports.models import ExamSession, Exam, StudentSession, StudentExamMark
try:
    from reports.models import Enrollment
except Exception:
    Enrollment = None  # if migration not applied yet

def norm_key(session: ExamSession) -> str:
    if session.year:
        return f"YEAR:{session.year}"
    name = (session.name or "").strip().casefold()
    name = " ".join(name.split())
    return f"NAME:{name}" if name else f"ID:{session.id}"

class Command(BaseCommand):
    help = "Merge duplicate ExamSession rows and repoint related objects."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Preview changes only.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        sessions = list(ExamSession.objects.all())
        groups = defaultdict(list)
        for s in sessions:
            groups[norm_key(s)].append(s)

        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        if not dup_groups:
            self.stdout.write(self.style.SUCCESS("No duplicate sessions found."))
            return

        total_deleted = 0

        for key, group in dup_groups.items():
            # Keep the HIGHEST id as canonical (tends to be the latest "good" row)
            group.sort(key=lambda s: s.id, reverse=True)
            canonical = group[0]
            duplicates = group[1:]
            self.stdout.write(f"\nGroup {key}: keeping #{canonical.id} ({canonical}) and merging {len(duplicates)} duplicate(s).")

            for dup in duplicates:
                if dry:
                    e_cnt = Exam.objects.filter(session_id=dup.id).count()
                    ss_cnt = StudentSession.objects.filter(session_id=dup.id).count()
                    m_cnt = StudentExamMark.objects.filter(session_id=dup.id).count()
                    en_cnt = Enrollment.objects.filter(academic_year_id=dup.id).count() if Enrollment else 0
                    self.stdout.write(f"  - would repoint Exam:{e_cnt}, StudentSession:{ss_cnt}, StudentExamMark:{m_cnt}, Enrollment:{en_cnt} from session #{dup.id} → #{canonical.id}")
                    total_deleted += 1
                    continue

                with transaction.atomic():
                    Exam.objects.filter(session_id=dup.id).update(session_id=canonical.id)
                    StudentSession.objects.filter(session_id=dup.id).update(session_id=canonical.id)
                    StudentExamMark.objects.filter(session_id=dup.id).update(session_id=canonical.id)
                    if Enrollment:
                        Enrollment.objects.filter(academic_year_id=dup.id).update(academic_year_id=canonical.id)
                    dup.delete()
                self.stdout.write(self.style.SUCCESS(f"  - merged session #{dup.id} → #{canonical.id}"))
                total_deleted += 1

        if dry:
            self.stdout.write(self.style.WARNING(f"\n[DRY RUN] Would delete {total_deleted} duplicate session rows."))
        else:
            self.stdout.write(self.style.SUCCESS("\nDone merging duplicate sessions."))
