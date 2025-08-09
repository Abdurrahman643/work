from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

def course_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/course_<id>/<filename>
    return f'course_{instance.course.id}/{filename}'

# 1. User Model
class User(AbstractUser):
    """
    Custom User model to include roles.
    This will be the model used for authentication.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

# Profile models for different user types
# These models are linked one-to-one with the User model to store additional information.

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    # Add any other student-specific fields here, like date of birth, etc.
    def __str__(self):
        return self.user.username

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    # Add any other teacher-specific fields here, like qualifications.
    def __str__(self):
        return self.user.username

class Parent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='parent_profile')
    students = models.ManyToManyField('school.Student', related_name='parents') # A parent can have multiple children in the school
    def __str__(self):
        return self.user.username

# 2. Subject and Course Models

class Subject(models.Model):
    """
    Represents a subject, like 'Mathematics' or 'History'.
    """
    name = models.CharField(max_length=100, unique=True)
    # As requested, teachers can add subjects. This field can track who created it.
    created_by = models.ForeignKey('school.Teacher', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    """
    Represents a specific course or class, e.g., 'Grade 10 Algebra'.
    It's taught by a teacher and has a subject.
    """
    name = models.CharField(max_length=200)
    subject = models.ForeignKey('school.Subject', on_delete=models.CASCADE, related_name='courses')
    teacher = models.ForeignKey('school.Teacher', on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField('school.Student', related_name='enrolled_courses', blank=True)

    def __str__(self):
        return self.name

# 3. Attendance and Grade Models

class Attendance(models.Model):
    """
    Tracks attendance for a student in a specific course on a given date.
    """
    student = models.ForeignKey('school.Student', on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey('school.Course', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'course', 'date') # Prevents duplicate attendance records

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name} on {self.date}"

class Grade(models.Model):
    """
    Represents a grade given to a student for a particular assignment or exam in a course.
    """
    student = models.ForeignKey('school.Student', on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey('school.Course', on_delete=models.CASCADE, related_name='grades')
    grade = models.DecimalField(max_digits=5, decimal_places=2) # e.g., 85.50
    title = models.CharField(max_length=100) # e.g., 'Mid-term Exam'
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username}'s grade in {self.course.name} for {self.title}"


# 4. Announcements Model

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# 6. Messaging System

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"

    class Meta:
        ordering = ['-sent_at']


# 5. Assignments and Documents

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    file = models.FileField(upload_to=course_directory_path, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Document(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=course_directory_path)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
