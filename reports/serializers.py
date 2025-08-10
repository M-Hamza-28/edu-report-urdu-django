from rest_framework import serializers
from .models import Tutor, Student, Subject, Exam, Report, PerformanceEntry, MessageLog, Feedback
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TutorSerializer(serializers.ModelSerializer):
    # make nested user optional for writes
    user = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = Tutor
        fields = ["id", "full_name", "phone", "email", "location", "user"]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
        }
        def validate_phone(self, value):
            # allow blank/None (optional phone) — but if provided, must be unique
                if value:
                    qs = Tutor.objects.filter(phone=value)
                    # if updating, exclude self
                    if self.instance:
                        qs = qs.exclude(pk=self.instance.pk)
                    if qs.exists():
                        raise serializers.ValidationError("A tutor with this phone already exists.")
                return value

    def create(self, validated_data):
        user_data = validated_data.pop("user", None)

        # generate defaults if missing
        base = (validated_data.get("full_name") or "tutor").lower().replace(" ", "")
        suffix = User.objects.count() + 1
        if not validated_data.get("email"):
            validated_data["email"] = f"{base}{suffix}@example.com"
        if not validated_data.get("location"):
            validated_data["location"] = "Unknown"

        if user_data:
            username = user_data.get("username") or f"{base}{suffix}"
            email = user_data.get("email") or validated_data["email"]
        else:
            username = f"{base}{suffix}"
            
            email = validated_data["email"]

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_active": True},
            
        )

        tutor = Tutor.objects.create(user=user, **validated_data)
        return tutor


class StudentSerializer(serializers.ModelSerializer):
    
    gender = serializers.CharField()
    class Meta:
        model = Student
        fields = '__all__'

    def validate_gender(self, value):
    # Normalize short codes and common variants
    mapping = {
        "M": "Male",
        "F": "Female",
        "male": "Male",
        "female": "Female",
    }
    value = mapping.get(value, value)
    if value not in ("Male", "Female"):
        raise serializers.ValidationError("Gender must be Male or Female.")
    return value


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model.
    """
    class Meta:
        model = Subject
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    """
    Serializer for Exam model.
    """
    class Meta:
        model = Exam
        fields = '__all__'

class PerformanceEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for PerformanceEntry model.
    Includes percentage (read-only) and subject name.
    """
    percentage = serializers.ReadOnlyField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = PerformanceEntry
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Report model.
    Includes related PerformanceEntries (entries).
    """
    entries = PerformanceEntrySerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)

    class Meta:
        model = Report
        fields = '__all__'

class MessageLogSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageLog model.
    """
    class Meta:
        model = MessageLog
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"

