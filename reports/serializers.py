from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Tutor, Student, Subject, Exam, Report,
    PerformanceEntry, MessageLog, Feedback, ExamSession
)

class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TutorSerializer(serializers.ModelSerializer):
    """
    Serializer for Tutor.
    - Accepts optional nested "user" (dict) to create/link a User.
    - Ensures phone is unique if provided.
    """
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
        # Optional phone; if provided, enforce uniqueness (excluding self on update)
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

        # default email/location if missing
        email = validated_data.get("email") or f"{base}{suffix}@example.com"
        validated_data.setdefault("email", email)
        validated_data.setdefault("location", "Unknown")

        # derive username/email from nested user (if present) or defaults
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
    # accept "M/F/male/female" and normalize to "Male"/"Female"
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


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'

class ExamSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSession
        fields = '__all__'

class StudentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSession
        fields = '__all__'


class PerformanceEntrySerializer(serializers.ModelSerializer):
    percentage = serializers.ReadOnlyField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = PerformanceEntry
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    """
    Report:
    - Includes read-only 'entries'
    - Convenience read-only fields for student/exam/tutor names and exam_type
    """
    entries = PerformanceEntrySerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    tutor_name = serializers.CharField(source='tutor.full_name', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    exam_type = serializers.CharField(source='exam.exam_type', read_only=True)
    exam_date = serializers.DateField(source='exam.date', read_only=True)

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
