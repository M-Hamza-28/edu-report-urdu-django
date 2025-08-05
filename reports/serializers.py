from rest_framework import serializers
from .models import Tutor, Student, Subject, Exam, Report, PerformanceEntry, MessageLog
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TutorSerializer(serializers.ModelSerializer):
    """
    Serializer for Tutor model.
    Allows nested User creation and update.
    """
    user = UserSerializer()

    class Meta:
        model = Tutor
        fields = '__all__'

    def create(self, validated_data):
        """
        Allows creation of Tutor along with nested User data in one API call.
        """
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        tutor = Tutor.objects.create(user=user, **validated_data)
        return tutor

    def update(self, instance, validated_data):
        """
        Allows updating Tutor and nested User.
        """
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model.
    """
    class Meta:
        model = Student
        fields = '__all__'

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
