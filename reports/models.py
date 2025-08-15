from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    full_name_urdu = models.CharField(max_length=100, blank=True, null=True)  # ✅ New
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='tutor_profiles/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        constraints = [
            # enforce unique phone only when phone is not NULL
            models.UniqueConstraint(
                fields=['phone'],
                name='uniq_tutor_phone_when_present',
                condition=Q(phone__isnull=False),
            )
        ]


class Student(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='students')
    full_name = models.CharField(max_length=100)
    full_name_urdu = models.CharField(max_length=100, blank=True, null=True)  # ✅ New
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    grade_level = models.CharField(max_length=50)
    registration_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    name_urdu = models.CharField(max_length=100, blank=True, null=True)  # ✅ New
    category = models.CharField(max_length=50, blank=True, null=True)
    subjects = models.ManyToManyField('Subject', related_name='students', blank=True)

    def __str__(self):
        return self.name


class Exam(models.Model):
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.exam_type})"


class Report(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reports')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)
    report_date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)

    def __str__(self):
        return f"Report for {self.student.full_name} - {self.exam.name}"


class PerformanceEntry(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    total_marks = models.FloatField()

    class Meta:
        unique_together = ('report', 'subject')

    @property
    def percentage(self):
        return (self.marks_obtained / self.total_marks) * 100 if self.total_marks else 0

    def __str__(self):
        return f"{self.subject.name} - {self.marks_obtained}/{self.total_marks}"


class MessageLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    contact_type = models.CharField(max_length=10, choices=[('WhatsApp', 'WhatsApp'), ('SMS', 'SMS'), ('Email', 'Email')])
    status = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contact_type} to {self.student.full_name} at {self.timestamp}"

class Feedback(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # add any other fields you want

    def __str__(self):
        return f"Feedback by {self.tutor.full_name} at {self.created_at}"

