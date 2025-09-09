from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Tutor, Student, Subject, Exam, Report,
    PerformanceEntry, MessageLog, Feedback, ExamSession, StudentSession,
)

# ---------------- Users / Tutors / Students ----------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TutorSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = Tutor
        fields = ["id", "full_name", "phone", "email", "location", "user"]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_phone(self, value):
        if value:
            qs = Tutor.objects.filter(phone=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A tutor with this phone already exists.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop("user", None)
        base = (validated_data.get("full_name") or "tutor").lower().replace(" ", "")
        suffix = User.objects.count() + 1

        email = validated_data.get("email") or f"{base}{suffix}@example.com"
        validated_data.setdefault("email", email)
        validated_data.setdefault("location", "Unknown")

        if user_data:
            username = user_data.get("username") or f"{base}{suffix}"
            user_email = user_data.get("email") or email
        else:
            username = f"{base}{suffix}"
            user_email = email

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": user_email, "is_active": True},
        )
        tutor = Tutor.objects.create(user=user, **validated_data)
        return tutor


class StudentSerializer(serializers.ModelSerializer):
    gender = serializers.CharField()

    class Meta:
        model = Student
        fields = '__all__'

    def validate_gender(self, value):
        mapping = {"M": "Male", "F": "Female", "male": "Male", "female": "Female"}
        value = mapping.get(value, value)
        if value not in ("Male", "Female"):
            raise serializers.ValidationError("Gender must be Male or Female.")
        return value


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


# ---------------- Sessions ----------------

class ExamSessionSerializer(serializers.ModelSerializer):
    """
    Adds a computed 'label' like 'Session 2025-2026'.
    Uses (start_date → end_date) if available; else uses 'year' (year → year+1);
    else falls back to 'name' or 'Session <id>'.
    """
    label = serializers.SerializerMethodField()

    class Meta:
        model = ExamSession
        fields = ['id', 'name', 'year', 'start_date', 'end_date', 'label']

    def get_label(self, obj):
        # Prefer explicit dates if present
        if obj.start_date:
            y1 = obj.start_date.year
            y2 = obj.end_date.year if obj.end_date else (y1 + 1)
            return f"Session {y1}-{y2}"
        # Fall back to year range
        if obj.year:
            return f"Session {obj.year}-{obj.year + 1}"
        # Otherwise try name; prefix if needed
        if obj.name:
            nm = obj.name.strip()
            return nm if nm.lower().startswith("session") else f"Session {nm}"
        # Final fallback
        return f"Session {obj.id}"


class StudentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSession
        fields = '__all__'


# ---------------- Exams (Term-based) ----------------

class ExamSerializer(serializers.ModelSerializer):
    """
    Expose 'term' instead of the DB field 'name'.
    Include both:
      - 'session' (write with id)
      - 'session_info' (read with full object incl. label)
    """
    term = serializers.CharField(source='name', required=True)
    date = serializers.DateField(required=False, allow_null=True)
    session = serializers.PrimaryKeyRelatedField(queryset=ExamSession.objects.all())
    session_info = ExamSessionSerializer(source='session', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'term', 'exam_type', 'session', 'session_info', 'date']

    def validate_term(self, value):
        raw = (value or "").strip()
        normalized = {
            "term 1": "1st Term",
            "1st term": "1st Term",
            "first term": "1st Term",
            "term 2": "2nd Term",
            "2nd term": "2nd Term",
            "second term": "2nd Term",
        }.get(raw.lower(), raw)
        if normalized not in {"1st Term", "2nd Term"}:
            raise serializers.ValidationError("Term must be '1st Term' or '2nd Term'.")
        return normalized

    def to_internal_value(self, data):
        # Back-compat if someone posts {"name": "..."} instead of {"term": "..."}
        if 'term' not in data and 'name' in data:
            data = dict(data)
            data['term'] = data['name']
        return super().to_internal_value(data)


# ---------------- Performance / Reports / Logs ----------------

class PerformanceEntrySerializer(serializers.ModelSerializer):
    percentage = serializers.ReadOnlyField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = PerformanceEntry
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    entries = PerformanceEntrySerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    tutor_name = serializers.CharField(source='tutor.full_name', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    exam_type = serializers.CharField(source='exam.exam_type', read_only=True)
    exam_date = serializers.DateField(source='exam.date', read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = '__all__'


class MessageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageLog
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"
