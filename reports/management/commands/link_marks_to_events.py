from django.core.management.base import BaseCommand
from django.db import transaction
from reports.models import Exam, ExamEvent, StudentExamMark, Enrollment

class Command(BaseCommand):
    help = (
        "Populate StudentExamMark.exam_event by matching (Exam via session/term/type) "
        "and student's Section (via Enrollment), and the same Subject."
    )

    def add_arguments(self, parser):
        parser.add_argument("--only-session", type=int, help="Limit to a specific ExamSession id.")
        parser.add_argument("--only-exam", type=int, help="Limit to a specific Exam id.")
        parser.add_argument("--dry-run", action="store_true", help="Preview changes only.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        only_session = opts.get("only_session")
        only_exam = opts.get("only_exam")

        # Map (session, term, exam_type) -> Exam.id (if multiple, pick first deterministically)
        exam_key_to_id = {}
        exams = Exam.objects.all().values("id", "session_id", "name", "exam_type").order_by("id")
        if only_session:
            exams = [e for e in exams if e["session_id"] == only_session]
        if only_exam:
            exams = [e for e in exams if e["id"] == only_exam]
        for e in exams:
            exam_key_to_id.setdefault((e["session_id"], e["name"], e["exam_type"]), e["id"])

        # Enrollment lookup: (student, session) -> section
        enroll_lookup = {}
        for en in Enrollment.objects.filter(active=True).values("student_id", "academic_year_id", "section_id"):
            enroll_lookup[(en["student_id"], en["academic_year_id"])] = en["section_id"]

        # For fast lookup of ExamEvent: (exam_id, section_id, subject_id) -> id
        event_lookup = {}
        for ev in ExamEvent.objects.all().values("id", "exam_id", "section_id", "subject_id"):
            event_lookup[(ev["exam_id"], ev["section_id"], ev["subject_id"])] = ev["id"]

        qs = StudentExamMark.objects.filter(exam_event__isnull=True).select_related("session", "subject", "student")
        if only_session:
            qs = qs.filter(session_id=only_session)
        if only_exam:
            try:
                ex = Exam.objects.get(pk=only_exam)
                qs = qs.filter(session=ex.session, term=ex.name, exam_type=ex.exam_type)
            except Exam.DoesNotExist:
                self.stdout.write(self.style.ERROR("Specified --only-exam not found."))
                return

        updated = 0
        skipped = 0

        for m in qs:
            exam_id = exam_key_to_id.get((m.session_id, m.term, m.exam_type))
            if not exam_id:
                skipped += 1
                continue
            section_id = enroll_lookup.get((m.student_id, m.session_id))
            if not section_id:
                skipped += 1
                continue
            ev_id = event_lookup.get((exam_id, section_id, m.subject_id))
            if not ev_id:
                skipped += 1
                continue

            if dry:
                self.stdout.write(f"[DRY] Link SEM#{m.id} -> ExamEvent#{ev_id}")
                updated += 1
                continue

            with transaction.atomic():
                StudentExamMark.objects.filter(pk=m.id).update(exam_event_id=ev_id)
                updated += 1

        if dry:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Would update {updated} StudentExamMark rows; skipped {skipped}."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} StudentExamMark rows; skipped {skipped}."))
