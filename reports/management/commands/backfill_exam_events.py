from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from statistics import median
from reports.models import Exam, ExamEvent, StudentExamMark, Enrollment

class Command(BaseCommand):
    help = (
        "Create ExamEvent rows inferred from existing StudentExamMark + Enrollment. "
        "We find matching Exam by (session==SEM.session AND term==Exam.name AND exam_type==Exam.exam_type). "
        "Section comes from Enrollment(student, same session). "
        "max_marks is median(total_marks) per (exam, section, subject). Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without writing.")
        parser.add_argument("--only-session", type=int, help="Limit to a specific ExamSession id.")
        parser.add_argument("--only-exam", type=int, help="Limit to a specific Exam id.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        only_session = opts.get("only_session")
        only_exam = opts.get("only_exam")

        # 1) Map (session, term, exam_type) -> Exam.id
        exam_map = defaultdict(list)
        exams = Exam.objects.all().values("id", "session_id", "name", "exam_type")
        if only_session:
            exams = [e for e in exams if e["session_id"] == only_session]
        if only_exam:
            exams = [e for e in exams if e["id"] == only_exam]
        for e in exams:
            exam_map[(e["session_id"], e["name"], e["exam_type"])].append(e["id"])

        # 2) Build per (exam_id, section_id, subject_id) → list(total_marks)
        buckets = defaultdict(list)
        sem_qs = StudentExamMark.objects.select_related("session", "subject", "student")
        if only_session:
            sem_qs = sem_qs.filter(session_id=only_session)
        if only_exam:
            # restrict SEM to only that exam's session/term/type
            try:
                ex = Exam.objects.get(pk=only_exam)
                sem_qs = sem_qs.filter(session=ex.session, term=ex.name, exam_type=ex.exam_type)
            except Exam.DoesNotExist:
                self.stdout.write(self.style.ERROR("Specified --only-exam not found."))
                return

        # Resolve student's section via Enrollment (active row for that session)
        enroll_lookup = {}
        for en in Enrollment.objects.select_related("section").filter(active=True).values("student_id", "academic_year_id", "section_id"):
            enroll_lookup[(en["student_id"], en["academic_year_id"])] = en["section_id"]

        for m in sem_qs.values("student_id", "session_id", "term", "exam_type", "subject_id", "total_marks"):
            exam_ids = exam_map.get((m["session_id"], m["term"], m["exam_type"]), [])
            if not exam_ids:
                continue
            section_id = enroll_lookup.get((m["student_id"], m["session_id"]))
            if not section_id:
                continue
            for ex_id in exam_ids:
                buckets[(ex_id, section_id, m["subject_id"])].append(float(m["total_marks"]))

        # 3) Create ExamEvent rows
        created = 0
        for (ex_id, sec_id, sub_id), totals in buckets.items():
            max_marks = median(totals) if totals else 100.0
            if dry:
                self.stdout.write(f"[DRY] ExamEvent(exam={ex_id}, section={sec_id}, subject={sub_id}, max_marks={max_marks})")
                continue
            with transaction.atomic():
                _, was_created = ExamEvent.objects.get_or_create(
                    exam_id=ex_id, section_id=sec_id, subject_id=sub_id,
                    defaults={"max_marks": max_marks, "date": None},
                )
                created += int(was_created)

        if dry:
            self.stdout.write(self.style.WARNING("Dry run complete. No rows written."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Created {created} ExamEvent row(s)."))
