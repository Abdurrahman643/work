from django import forms
from .models import Subject, Grade, Student, Attendance, Announcement, Assignment, Document, Message, User, Course

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']

class GradeForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=Student.objects.none(), label="Student")

    class Meta:
        model = Grade
        fields = ['student', 'title', 'grade']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Mid-term Exam'}),
            'grade': forms.NumberInput(attrs={'placeholder': 'e.g., 85.5'}),
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        if course:
            self.fields['student'].queryset = course.students.all()

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['is_present']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'file']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file']

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="Select Recipient")

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']

class CourseFilterForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=False, empty_label="All Courses", label="Filter by Course")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        child = kwargs.pop('child', None)
        super().__init__(*args, **kwargs)
        if user:
            if hasattr(user, 'student_profile'):
                self.fields['course'].queryset = user.student_profile.enrolled_courses.all()
            elif hasattr(user, 'parent_profile'):
                if child:
                    self.fields['course'].queryset = child.enrolled_courses.all()
