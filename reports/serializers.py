# reports/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from decimal import Decimal
import secrets

from .models import (
    Organization,
    Tutor, Student, Subject,
    ExamSession, StudentSession, Enrollment,
    Grade, Section,
    ExamType, Exam, ExamEvent,
    StudentExamMark,
    GradeScale, GradeBoundary,
    ReportTemplate, Report, PerformanceEntry,
    MessageLog, Feedback,
    Setting,
    MessageTemplate, MessageThread, Message, MessageDelivery,
    Guardian, AuditLog, EXAM_TYPE_CHOICES
)


def _safe_file_url(file_field):
    try:
        return file_field.url if file_field and getattr(file_field, "name", None) else ""
    except Exception:
        return ""

def _validate_image_file(value, max_size_bytes, field_name):
    ct = getattr(value, "content_type", "") or ""
    if not ct.startswith("image/"):
        raise serializers.ValidationError(f"{field_name}: only image/* files are allowed.")
    size = getattr(value, "size", 0) or 0
    if size > max_size_bytes:
        raise serializers.ValidationError(f"{field_name}: file too large.")
    return value


# ---------------- Organization ----------------
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"

# ---------------- Users / Tutors / Students ----------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email']

class TutorSerializer(serializers.ModelSerializer):
    full_name_ur = serializers.CharField(source='full_name_urdu', allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Tutor
        fields = "__all__"
        read_only_fields = ("user",)

    def _resolve_by_payload(self, payload):
        if not isinstance(payload, dict):
            return None
        User = get_user_model()
        uid = payload.get("id")
        if uid:
            try: return User.objects.get(pk=uid)
            except User.DoesNotExist:
                raise serializers.ValidationError({"user": f"User id={uid} not found."})
        uname = payload.get("username")
        if uname:
            user, _ = User.objects.get_or_create(username=uname, defaults={"email": payload.get("email", "")})
            return user
        uemail = payload.get("email")
        if uemail:
            user = User.objects.filter(email=uemail).first()
            if user: return user
            base = (uemail.split("@")[0] or "tutor")[:30]
            username = base if not User.objects.filter(username=base).exists() else f"{base[:24]}-{secrets.token_hex(3)}"
            user = User.objects.create(username=username, email=uemail)
            user.set_unusable_password(); user.save()
            return user
        return None

    def _ensure_user(self, name, email):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            return request.user
        payload_user = self.initial_data.get("user") if hasattr(self, "initial_data") else None
        resolved = self._resolve_by_payload(payload_user)
        if resolved: return resolved
        User = get_user_model()
        safe_name = (name or "Tutor").strip() or "Tutor"
        base = (email.split("@")[0] if email else slugify(safe_name) or "tutor")[:30]
        username = base if not User.objects.filter(username=base).exists() else f"{base[:24]}-{secrets.token_hex(3)}"
        user = User.objects.create(username=username, email=email or "")
        user.set_unusable_password(); user.save()
        return user

    def create(self, validated_data):
        name = validated_data.get("full_name") or validated_data.get("full_name_ur") or "Tutor"
        email = validated_data.get("email") or ""
        validated_data["user"] = self._ensure_user(name, email)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)

class StudentSerializer(serializers.ModelSerializer):
    full_name_ur = serializers.CharField(source='full_name_urdu', allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = Student
        fields = "__all__"

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


# Expose the implicit Student<->Subject through model for REST linking
StudentSubjectThrough = Student._meta.get_field('subjects').remote_field.through

class StudentSubjectSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for the implicit Student<->Subject through table.
    Enables the StudentSubjectViewSet to create/delete links.
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = StudentSubjectThrough
        fields = ['id', 'student', 'student_name', 'subject', 'subject_name']

        
# ---------------- Grades / Sections / Enrollment ----------------
class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"

class SectionSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    class Meta:
        model = Section
        fields = ["id", "grade", "grade_name", "name"]

# ---------------- Grade Scales / Boundaries ----------------
class GradeBoundarySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for a single boundary row.
    (Kept generic with __all__ to match your current model without assumptions.)
    """
    class Meta:
        model = GradeBoundary
        fields = "__all__"

class GradeScaleSerializer(serializers.ModelSerializer):
    """
    Serializer for a grading scale. If your GradeBoundary FK uses a related_name
    (e.g. 'boundaries'), you can uncomment the read-only nested list below.
    """
    # boundaries = GradeBoundarySerializer(many=True, read_only=True)  # <-- enable if related_name exists

    class Meta:
        model = GradeScale
        fields = "__all__"  # or: fields = ["id", "name", "description", "boundaries"]


# ---------------- Enrollment ----------------
class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    # FE-friendly read-only mirror so legacy UIs using `row.session` still work
    session = serializers.IntegerField(source='academic_year_id', read_only=True)
    session_label = serializers.SerializerMethodField()

    # 👉 NEW: write-only alias accepted by FE (`session_id` → academic_year)
    session_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student", "student_name",
            "academic_year",  # canonical FK
            "session", "session_label",  # read-only conveniences
            "session_id",  # write-only alias
            "grade", "section", "active",
        ]
        # keep grade/section optional to avoid 400 on simple enroll
        extra_kwargs = {
            "grade": {"required": False, "allow_null": True},
            "section": {"required": False, "allow_null": True},
            "academic_year": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        """
        Accept either 'academic_year' or 'session_id' (common FE alias).
        """
        # Map alias if provided and canonical missing
        if not attrs.get("academic_year") and "session_id" in attrs and attrs["session_id"]:
            try:
                sess = ExamSession.objects.get(pk=attrs["session_id"])
            except ExamSession.DoesNotExist:
                raise serializers.ValidationError({"session_id": "Invalid session id."})
            attrs["academic_year"] = sess
            attrs.pop("session_id", None)
        else:
            # remove alias if present (won't reach model field)
            attrs.pop("session_id", None)

        # Basic sanity: student + academic_year must exist for create
        if self.instance is None:
            if not attrs.get("student"):
                raise serializers.ValidationError({"student": "Student is required."})
            if not attrs.get("academic_year"):
                raise serializers.ValidationError({"academic_year": "Session is required."})

        return attrs

    def get_session_label(self, obj):
        s = obj.academic_year
        if getattr(s, "start_date", None):
            y1 = s.start_date.year
            y2 = s.end_date.year if getattr(s, "end_date", None) else (y1 + 1)
            return f"Session {y1}-{y2}"
        if getattr(s, "year", None):
            return f"Session {s.year}-{s.year + 1}"
        if getattr(s, "name", None):
            nm = (s.name or "").strip()
            return nm if nm.lower().startswith("session") else f"Session {nm}"
        return f"Session {s.pk}"


# ---------------- Sessions (existing) ----------------
class ExamSessionSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    class Meta:
        model = ExamSession
        fields = ['id', 'name', 'year', 'start_date', 'end_date', 'is_current', 'label']
    def get_label(self, obj):
        if getattr(obj, "start_date", None):
            y1 = obj.start_date.year
            y2 = obj.end_date.year if getattr(obj, "end_date", None) else (y1 + 1)
            return f"Session {y1}-{y2}"
        if getattr(obj, "year", None):
            return f"Session {obj.year}-{obj.year + 1}"
        if getattr(obj, "name", None):
            nm = (obj.name or "").strip()
            return nm if nm.lower().startswith("session") else f"Session {nm}"
        return f"Session {obj.pk}"

class StudentSessionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_grade = serializers.CharField(source='student.grade_level', read_only=True)
    tutor_id = serializers.IntegerField(source='student.tutor.id', read_only=True)
    tutor_name = serializers.CharField(source='student.tutor.full_name', read_only=True)
    session_label = serializers.CharField(source='session.name', read_only=True)
    class Meta:
        model = StudentSession
        fields = [
            'id', 'student', 'session',
            'student_name', 'student_grade',
            'tutor_id', 'tutor_name', 'session_label'
        ]

# ---------------- Exams / ExamEvents ----------------

class ExamTypeSerializer(serializers.ModelSerializer):
    """Basic serializer for exam type definitions (e.g., Mid-Term, Final)."""
    class Meta:
        model = ExamType
        fields = "__all__"

class ExamSerializer(serializers.ModelSerializer):
    term = serializers.CharField(source='name', required=True)
    date = serializers.DateField(required=False, allow_null=True)
    session = serializers.PrimaryKeyRelatedField(queryset=ExamSession.objects.all())
    session_info = ExamSessionSerializer(source='session', read_only=True)
    class Meta:
        model = Exam
        fields = ['id', 'term', 'exam_type', 'session', 'session_info', 'date']

class ExamEventSerializer(serializers.ModelSerializer):
    """
    Serializer for scheduling an exam event (paper) for a section/subject within an exam.
    Accepts either:
      A) canonical FKs:   exam, section, subject, date, max_marks
      B) FE-friendly keys: session_id + term + exam_type (+ exam_date), section_id, subject_id
         → we will resolve/create Exam and map ids to canonical fields.

    Read-only conveniences:
      - exam_term, section_name, subject_name
    """

    # ---- read-only convenience labels ----
    exam_term    = serializers.CharField(source="exam.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    # ---- FE-friendly write-only aliases (optional) ----
    session_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    section_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subject_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    exam_date  = serializers.DateField(write_only=True, required=False, allow_null=True)

    # Write-only helpers; if present we’ll create/resolve an Exam row.
    session   = serializers.PrimaryKeyRelatedField(queryset=ExamSession.objects.all(), write_only=True, required=False)
    term      = serializers.CharField(write_only=True, required=False, allow_blank=False)
    exam_type = serializers.CharField(write_only=True, required=False, allow_blank=False)

    # Accept & ignore (write-only) so UI/tests can send them without 400s.
    components = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    status     = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = ExamEvent
        fields = [
            "id",
            # canonical, persisted fields (writeable)
            "exam", "section", "subject", "date", "max_marks",

            # read-only labels for FE
            "exam_term", "section_name", "subject_name",

            # write-only helpers / aliases
            "session", "term", "exam_type",
            "session_id", "section_id", "subject_id", "exam_date",
            "components", "status",
        ]
        extra_kwargs = {
            "exam":     {"required": False, "allow_null": True},
            "section":  {"required": False, "allow_null": True},
            "subject":  {"required": False, "allow_null": True},
            "date":     {"required": False, "allow_null": True},
            "max_marks":{"required": False},
        }
        validators = []  # we enforce uniqueness manually in create()

    # -------- helpers --------
    def _normalize_exam_type(self, val: str | None) -> str | None:
        if not val: return None
        v = str(val).strip().lower()
        mapping = {
            "mid": "Mid-Term", "midterm": "Mid-Term", "mid-term": "Mid-Term",
            "final": "Final", "quiz": "Quiz", "monthly": "Monthly Test",
            "tests": "Tests Week", "tests week": "Tests Week", "test week": "Tests Week",
        }
        return mapping.get(v, val)

    def to_internal_value(self, data):
        """
        Be forgiving to FE:
        - accept numeric strings for *_id + max_marks
        - map exam_date -> date if date not supplied
        """
        data = dict(data) if isinstance(data, dict) else data

        def _to_int(k):
            v = data.get(k)
            if isinstance(v, str) and v.isdigit():
                data[k] = int(v)

        for k in ("exam", "session", "session_id", "section", "section_id", "subject", "subject_id", "max_marks"):
            _to_int(k)

        if "date" not in data and "exam_date" in data:
            data["date"] = data.get("exam_date")

        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        Map FE aliases to canonical fields and perform basic FK validation.
        Raise clean 400s instead of 500s for bad ids.
        """
        # session_id -> session
        if not attrs.get("session") and attrs.get("session_id"):
            try:
                attrs["session"] = ExamSession.objects.get(pk=attrs.pop("session_id"))
            except ExamSession.DoesNotExist:
                raise serializers.ValidationError({"session_id": "Invalid session id."})
        else:
            attrs.pop("session_id", None)

        # section_id -> section (optional)
        if not attrs.get("section") and attrs.get("section_id"):
            try:
                attrs["section"] = Section.objects.get(pk=attrs.pop("section_id"))
            except Section.DoesNotExist:
                raise serializers.ValidationError({"section_id": "Invalid section id."})
        else:
            attrs.pop("section_id", None)

        # subject_id -> subject
        if not attrs.get("subject") and attrs.get("subject_id"):
            try:
                attrs["subject"] = Subject.objects.get(pk=attrs.pop("subject_id"))
            except Subject.DoesNotExist:
                raise serializers.ValidationError({"subject_id": "Invalid subject id."})
        else:
            attrs.pop("subject_id", None)

        # exam_date -> date
        if not attrs.get("date") and "exam_date" in attrs:
            attrs["date"] = attrs.pop("exam_date")

        # normalize exam_type if provided
        if attrs.get("exam_type"):
            attrs["exam_type"] = self._normalize_exam_type(attrs["exam_type"])

        # For create, ensure we have enough to resolve an ExamEvent
        if self.instance is None:
            if not (attrs.get("exam") or (attrs.get("session") and attrs.get("term"))):
                raise serializers.ValidationError({"exam": "Provide exam id OR (session + term)."})
            if not attrs.get("subject"):
                raise serializers.ValidationError({"subject": "Subject is required."})
            # Section can be optional in your flow; require it only if you need class-level scheduling.
            # If you want it mandatory, uncomment the next two lines:
            # if not attrs.get("section"):
            #     raise serializers.ValidationError({"section": "Section is required."})

        return attrs

    def create(self, validated_data):
        """
        Resolve/ensure Exam, then upsert ExamEvent (unique on exam+section+subject).
        """
        session   = validated_data.pop("session", None)
        term      = validated_data.pop("term", None)
        exam_type = validated_data.pop("exam_type", None)
        validated_data.pop("components", None)  # ignore for now
        validated_data.pop("status", None)      # handled at view level if needed

        # Resolve or create Exam if not provided explicitly
        exam = validated_data.get("exam")
        if not exam:
            if not (session and term):
                raise serializers.ValidationError({"exam": "Missing exam or (session + term)."})
            exam, created = Exam.objects.get_or_create(
                session=session,
                name=term,
                defaults={"exam_type": exam_type or "Written"},
            )
            # If existing exam has a different type and client sent one, sync it.
            if not created and exam_type and exam.exam_type != exam_type:
                exam.exam_type = exam_type
                exam.save(update_fields=["exam_type"])
            validated_data["exam"] = exam

        # Defaults
        if "max_marks" not in validated_data or validated_data["max_marks"] in (None, ""):
            validated_data["max_marks"] = Decimal("100")

        # Idempotent upsert by (exam, section, subject)
        ev, created = ExamEvent.objects.get_or_create(
            exam   = validated_data["exam"],
            section= validated_data.get("section"),
            subject= validated_data["subject"],
            defaults={
                "date":      validated_data.get("date"),
                "max_marks": validated_data.get("max_marks"),
            },
        )
        if not created:
            changed = False
            if validated_data.get("date") is not None and ev.date != validated_data["date"]:
                ev.date = validated_data["date"]; changed = True
            if validated_data.get("max_marks") is not None and ev.max_marks != validated_data["max_marks"]:
                ev.max_marks = validated_data["max_marks"]; changed = True
            if changed:
                ev.save(update_fields=["date", "max_marks"])
        return ev





# ---------------- Canonical Marks ----------------
class StudentExamMarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    session_label = serializers.SerializerMethodField()
    exam_event_info = ExamEventSerializer(source="exam_event", read_only=True)

    class Meta:
        model = StudentExamMark
        fields = [
            'id', 'student', 'student_name',
            'session', 'session_label',
            'term', 'exam_type',
            'subject', 'subject_name',
            'marks_obtained', 'total_marks',
            'exam_event', 'exam_event_info'
        ]

    def get_session_label(self, obj):
        s = obj.session
        if getattr(s, "start_date", None):
            y1 = s.start_date.year
            y2 = s.end_date.year if getattr(s, "end_date", None) else (y1 + 1)
            return f"Session {y1}-{y2}"
        if getattr(s, "year", None):
            return f"Session {s.year}-{s.year + 1}"
        if getattr(s, "name", None):
            nm = (s.name or "").strip()
            return nm if nm.lower().startswith("session") else f"Session {nm}"
        return f"Session {s.pk}"

    def validate(self, attrs):
        mo = attrs.get('marks_obtained', getattr(self.instance, 'marks_obtained', None))
        tm = attrs.get('total_marks', getattr(self.instance, 'total_marks', None))
        if mo is not None and tm is not None:
            try:
                mo_f = float(mo); tm_f = float(tm)
            except Exception:
                raise serializers.ValidationError("marks_obtained and total_marks must be numbers.")
            if tm_f < 0 or mo_f < 0 or mo_f > tm_f:
                raise serializers.ValidationError("0 ≤ marks_obtained ≤ total_marks, and total_marks ≥ 0.")
        return attrs

# ---------------- Reporting ----------------
class PerformanceEntrySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class Meta:
        model = PerformanceEntry
        fields = "__all__"

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"

class ReportSerializer(serializers.ModelSerializer):
    entries = PerformanceEntrySerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    tutor_name = serializers.CharField(source='tutor.full_name', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    exam_type = serializers.CharField(source='exam.exam_type', read_only=True)
    exam_date = serializers.DateField(source='exam.date', read_only=True, allow_null=True)
    template_info = ReportTemplateSerializer(source="template", read_only=True)
    class Meta:
        model = Report
        fields = "__all__"

# ---------------- Logs & feedback ----------------
class MessageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageLog
        fields = "__all__"

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = "__all__"

class OrganizationSettingsSerializer(serializers.ModelSerializer):
    """
    Accepts JSON or multipart (logo, favicon, principal_signature).
    Returns URLs in *_url fields as the FE expects.
    """
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    principal_signature_url = serializers.SerializerMethodField()

    class Meta:
        model = Setting
        fields = ["id", "group", "payload", "logo_url", "favicon_url", "principal_signature_url", "version"]

    def get_logo_url(self, obj):
        return _safe_file_url(getattr(obj, "logo", None))

    def get_favicon_url(self, obj):
        return _safe_file_url(getattr(obj, "favicon", None))

    def get_principal_signature_url(self, obj):
        return _safe_file_url(getattr(obj, "principal_signature", None))
    
    def validate_logo(self, value):
        if value is None: 
            return value
        return _validate_image_file(value, 2 * 1024 * 1024, "logo")  # 2MB

    def validate_favicon(self, value):
        if value is None:
            return value
        return _validate_image_file(value, 256 * 1024, "favicon")   # 256KB

    def validate_principal_signature(self, value):
        if value is None:
            return value
        return _validate_image_file(value, 2 * 1024 * 1024, "principal_signature")  # 2MB

    
class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTemplate
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id", "thread", "sender", "sender_username",
            "language_mode", "body_en", "body_ur",
            "attachment", "attachment_url",
            "scheduled_at", "sent_at", "status",
            "created_at",
        ]
        read_only_fields = ("sender", "sent_at", "created_at")

    def get_attachment_url(self, obj):
        return _safe_file_url(getattr(obj, "attachment", None))

class MessageDeliverySerializer(serializers.ModelSerializer):
    """
    Records per-recipient delivery (channel/status/timestamps). Kept generic
    to align with your current model without making field assumptions.
    """
    class Meta:
        model = MessageDelivery
        fields = "__all__"


class MessageThreadSerializer(serializers.ModelSerializer):
    last_message_preview = serializers.SerializerMethodField()
    messages_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model = MessageThread
        fields = [
            "id", "subject", "is_announcement", "session",
            "owner", "folder", "tags",
            "created_at", "updated_at",
            "messages_count", "last_message_preview",
        ]
        read_only_fields = ("owner", "created_at", "updated_at", "messages_count", "last_message_preview")

    def get_last_message_preview(self, obj):
        m = obj.messages.order_by("-created_at").first()
        if not m:
            return ""
        text = (m.body_en or m.body_ur or "").strip()
        return (text[:120] + "…") if len(text) > 120 else text
    
    
class GuardianSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    class Meta:
        model = Guardian
        fields = ["id", "full_name", "email", "phone", "student", "student_name"]

class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    class Meta:
        model = AuditLog
        fields = ["id", "created_at", "actor", "actor_username", "action", "entity", "entity_id", "meta"]
