# from django.db import models
# from django.db.models import Q
# from django.contrib.auth.models import User
# from django.conf import settings as dj_settings
# from django.contrib.auth import get_user_model
# from django.db import models
# from django.utils import timezone

# try:
#     # Django 3.1+ has native JSONField
#     from django.db.models import JSONField  # type: ignore
# except Exception:  # Django 3.0 fallback (remove if you already use native)
#     from django.contrib.postgres.fields import JSONField  # type: ignore

# User = get_user_model()
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone  # optional; safe to keep

try:
    # Django 3.1+
    from django.db.models import JSONField
except Exception:  # Django < 3.1
    from django.contrib.postgres.fields import JSONField

User = get_user_model()


# ============================================================
# Core: Organization (multi-tenant ready) – optional for now
# ============================================================
class Organization(models.Model):
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=200, unique=True, blank=True, null=True)
    locale = models.CharField(max_length=10, default="en-PK")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

# ============================================================
# People: Tutor / Student / Subject (existing kept)
# ============================================================
class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    full_name_ur = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='tutor_profiles/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    @property
    def full_name_en(self):
        return self.full_name

    @full_name_en.setter
    def full_name_en(self, v):
        self.full_name = v

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                name="uniq_tutor_phone_nonnull",
                condition=Q(phone__isnull=False) & ~Q(phone=""),
            )
        ]
    def __str__(self) -> str:
        return self.full_name

class Subject(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    name_urdu = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    is_elective = models.BooleanField(default=False)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="uniq_subject_code_per_org",
                condition=Q(code__isnull=False) & ~Q(code=""),
            )
        ]
    def __str__(self) -> str:
        return self.name

class Student(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='students')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    full_name_urdu = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    grade_level = models.CharField(max_length=50)
    registration_date = models.DateField(auto_now_add=True)
    subjects = models.ManyToManyField('Subject', related_name='students', blank=True)

    @property
    def full_name_ur(self):
        return self.full_name_urdu
    @property
    def full_name_en(self):
        return self.full_name

    @full_name_en.setter
    def full_name_en(self, v):
        self.full_name = v
        
    def __str__(self) -> str:
        return self.full_name

# ============================================================
# Academics: Session/Year (existing), Grade, Section, Enrollment (new)
# ============================================================
class ExamSession(models.Model):
    """
    Academic session bucket, e.g. "2025-2026". (Existing)
    """
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)  # start year, e.g. 2025
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "year"],
                name="uniq_session_year_per_org_nonnull",
                condition=Q(year__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_session_name_per_org_nonnull_nonblank",
                condition=Q(name__isnull=False) & ~Q(name=""),
            ),
        ]

    # --- Back-compat: expose a `code` attribute commonly used by callers ---
    @property
    def code(self) -> str:
        # Prefer explicit name; then derive from year; else stable token
        return self.name or (str(self.year) if self.year else f"S-{self.pk}")

    @code.setter
    def code(self, value: str):
        # Allow assigning `code` to set `name` if not set explicitly
        if value and not self.name:
            self.name = value

    def __str__(self) -> str:
        if self.name:
            return self.name
        if self.year:
            return f"{self.year}-{self.year + 1}"
        return f"Session #{self.pk}"


# --- Back-compat proxy: Session -> ExamSession (no schema change) ---
class Session(ExamSession):
    """
    Proxy alias so legacy code/tests that import `Session` continue to work.
    Uses the same DB table as ExamSession (proxy=True).
    """
    class Meta:
        proxy = True
        verbose_name = "Session"
        verbose_name_plural = "Sessions"

    @classmethod
    def get_current(cls):
        """Convenience: return the current session if one is flagged."""
        return cls.objects.filter(is_current=True).first()

class Grade(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)  # e.g., "Grade-8"
    name_urdu = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self): return self.name

class Section(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="sections")
    name = models.CharField(max_length=20)   # e.g., "A"
    def __str__(self): return f"{self.grade.name}-{self.name}"

class Enrollment(models.Model):
    """
    New: canonical enrollment for a session (optionally grade/section).
    Keeps old StudentSession working side-by-side during transition.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments2")
    academic_year = models.ForeignKey(ExamSession, on_delete=models.PROTECT, related_name="enrollments2")
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        unique_together = (("student", "academic_year"),)
        indexes = [models.Index(fields=["student", "academic_year"])]
    def __str__(self): return f"{self.student} @ {self.academic_year}"

# ---- Existing Enrollment kept (compat) ----
class StudentSession(models.Model):
    """(Existing) Enrollment of a student into a session."""
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey('ExamSession', on_delete=models.CASCADE, related_name='enrollments', related_query_name='enrollment')
    class Meta:
        unique_together = ('student', 'session')
        indexes = [models.Index(fields=['student', 'session'])]
    def __str__(self) -> str:
        return f"{self.student} @ {self.session}"

# ============================================================
# Assessment: ExamType (optional), Exam (existing), ExamEvent (new)
# ============================================================
EXAM_TYPE_CHOICES = [
    ("Mid-Term", "Mid-Term"),
    ("Final", "Final"),
    ("Tests Week", "Tests Week"),
    ("Monthly Test", "Monthly Test"),
    ("Quiz", "Quiz"),
]

class ExamType(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=80, unique=True)
    weight_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    def __str__(self): return self.name

class Exam(models.Model):
    """
    Term/Exam under a session. DB field is `name`; API exposes it as `term` (existing).
    """
    name = models.CharField(max_length=100, verbose_name="term")
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES)
    session = models.ForeignKey('ExamSession', on_delete=models.CASCADE, related_name='exams', related_query_name='exam')
    date = models.DateField(blank=True, null=True)
    def __str__(self) -> str:
        return f"{self.name} — {self.exam_type}"

class ExamEvent(models.Model):
    """
    New: schedules a paper for a specific section & subject within an exam.
    Unique per (exam, section, subject).
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="events")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="exam_events")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="exam_events")
    date = models.DateField(blank=True, null=True)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)
    class Meta:
        unique_together = (("exam", "section", "subject"),)
        indexes = [models.Index(fields=["exam", "section"])]
    def __str__(self): return f"{self.exam} • {self.section} • {self.subject}"

# ============================================================
# Marks (existing kept) + bridge to ExamEvent (new FK optional)
# ============================================================
class StudentExamMark(models.Model):
    """
    Existing canonical marks table, now with an OPTIONAL link to ExamEvent.
    This allows a smooth migration without breaking current UI.
    """
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    session = models.ForeignKey('ExamSession', on_delete=models.CASCADE)
    term = models.CharField(max_length=100)       # e.g., "Term 1"
    exam_type = models.CharField(max_length=50)   # e.g., "Mid-Term"
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    total_marks = models.FloatField()
    # NEW (nullable during migration)
    exam_event = models.ForeignKey(ExamEvent, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "session", "term", "exam_type", "subject"],
                name="uniq_mark_per_student_session_term_type_subject",
            )
        ]
        indexes = [
            models.Index(fields=["student", "session"]),
            models.Index(fields=["student", "session", "term", "exam_type"]),
        ]
    def __str__(self) -> str:
        return f"{self.student} • {self.session} • {self.term}/{self.exam_type} • {self.subject}"

# ============================================================
# Grade Scales (for letters/GPA) – optional use in UI/PDF
# ============================================================
class GradeScale(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    label = models.CharField(max_length=100, default="Default")
    is_default = models.BooleanField(default=False)
    def __str__(self): return f"{self.label} ({'default' if self.is_default else 'custom'})"

class GradeBoundary(models.Model):
    grade_scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name="boundaries")
    min_pct = models.DecimalField(max_digits=5, decimal_places=2)
    max_pct = models.DecimalField(max_digits=5, decimal_places=2)
    letter = models.CharField(max_length=3)  # A+, A, A- ...
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    class Meta:
        ordering = ["-min_pct"]

# ============================================================
# Reporting (Report + PerformanceEntry + ReportTemplate)
# ============================================================
class ReportTemplate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=120)
    engine = models.CharField(max_length=20, default="reportlab")  # or "pdfkit" / "weasyprint"
    rtl_font = models.CharField(max_length=200, blank=True, null=True)  # e.g., Noto/Jameel paths
    file_url = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=120, default="", blank=True)
    is_default = models.BooleanField(default=False)
    def __str__(self): return self.title

class Report(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    tutor = models.ForeignKey('Tutor', on_delete=models.CASCADE)
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE)
    report_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    # NEW (optional for now)
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default="draft")  # draft|ready|sent
    pdf_url = models.URLField(blank=True, null=True)
    summary_json = models.JSONField(default=dict, blank=True)
    def __str__(self) -> str:
        return f"Report #{self.pk} — {self.student}"

class PerformanceEntry(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    total_marks = models.FloatField()
    def __str__(self) -> str:
        return f"{self.report_id} • {self.subject}"

# ============================================================
# Messaging / Feedback (existing)
# ============================================================
class MessageLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    contact_type = models.CharField(max_length=50, choices=[('SMS', 'SMS'), ('WhatsApp', 'WhatsApp')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return f"{self.contact_type} to {self.student.full_name} at {self.timestamp}"

class Feedback(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return f"Feedback by {self.tutor.full_name} at {self.created_at}"


class Setting(models.Model):
    GROUP_CHOICES = [
        ("organization", "Organization"),
        ("academic", "Academic"),
        ("reporting", "Reporting"),
        ("notifications", "Notifications"),
        ("security", "Security"),
    ]
    group = models.CharField(max_length=32, choices=GROUP_CHOICES, unique=True, db_index=True)
    payload = JSONField(default=dict, blank=True)

    # Files (used by organization group; harmlessly null for others)
    logo = models.FileField(upload_to="branding/", null=True, blank=True)
    favicon = models.FileField(upload_to="branding/", null=True, blank=True)
    principal_signature = models.FileField(upload_to="branding/", null=True, blank=True)

    version = models.PositiveIntegerField(default=1)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.group} settings v{self.version}"


class MessageTemplate(models.Model):
    LANGUAGE_CHOICES = [("en", "English"), ("ur", "Urdu"), ("bi", "Bilingual")]
    name = models.CharField(max_length=120)
    language_mode = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    body_en = models.TextField(blank=True, default="")
    body_ur = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class MessageThread(models.Model):
    FOLDER_CHOICES = [
        ("inbox", "Inbox"),
        ("sent", "Sent"),
        ("drafts", "Drafts"),
        ("scheduled", "Scheduled"),
        ("archived", "Archived"),
    ]
    subject = models.CharField(max_length=255, blank=True, default="")
    is_announcement = models.BooleanField(default=False)
    session = models.ForeignKey("ExamSession", null=True, blank=True, on_delete=models.SET_NULL)

    # per-owner mailbox semantics; simple and FE-compatible
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_threads")
    folder = models.CharField(max_length=16, choices=FOLDER_CHOICES, default="inbox", db_index=True)

    tags = JSONField(default=list, blank=True)  # e.g. ["important", "parent-comm"]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # used by FE ordering=-updated_at

    def __str__(self) -> str:
        return f"[{self.folder}] {self.subject or 'No subject'}"


class Message(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("scheduled", "Scheduled"), ("sent", "Sent"), ("failed", "Failed")]
    LANGUAGE_CHOICES = [("en", "English"), ("ur", "Urdu"), ("bi", "Bilingual")]

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_messages")

    language_mode = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    body_en = models.TextField(blank=True, default="")
    body_ur = models.TextField(blank=True, default="")
    attachment = models.FileField(upload_to="attachments/", null=True, blank=True)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft", db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Msg#{self.pk} in Thread#{self.thread_id} - {self.status}"


class MessageDelivery(models.Model):
    """
    Placeholder deliveries record (for future SMS/email). Safe to keep minimal.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="deliveries")
    recipient = models.CharField(max_length=255)  # phone/email/etc.
    channel = models.CharField(max_length=32, default="internal")
    status = models.CharField(max_length=16, default="queued")
    meta = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("message", "recipient")]

class Guardian(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    student = models.ForeignKey("Student", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.full_name


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=64)
    entity = models.CharField(max_length=64)
    entity_id = models.IntegerField()
    meta = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# --- Stable back-compat symbol for legacy imports ---
# Old code/tests may import AcademicYear; keep it mapped to Session.
AcademicYear = Session
