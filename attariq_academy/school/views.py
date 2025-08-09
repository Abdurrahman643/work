from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test

# Role-checking decorators
def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'TEACHER'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'STUDENT'

def is_parent(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'PARENT'

@login_required
def home_view(request):
    """
    Redirects users to their respective dashboards based on their role.
    """
    if hasattr(request.user, 'role'):
        if request.user.role == 'TEACHER':
            return redirect('school:teacher_dashboard')
        elif request.user.role == 'STUDENT':
            return redirect('school:student_dashboard')
        elif request.user.role == 'PARENT':
            return redirect('school:parent_dashboard')
        elif request.user.role == 'ADMIN':
            return redirect('admin:index')

    # Fallback for users with no role or for debugging
    return render(request, 'home.html', {'user': request.user})

from django.utils import timezone
from datetime import date
from django.forms import modelformset_factory
from .forms import SubjectForm, GradeForm, AttendanceForm, AnnouncementForm, AssignmentForm, DocumentForm, MessageForm, CourseFilterForm
from .models import Subject, Teacher, Course, Grade, Student, Parent, Attendance, Announcement, Assignment, Document, Message

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def teacher_dashboard(request):
    """
    The main dashboard for teachers.
    """
    announcements = Announcement.objects.all()[:5]
    context = {
        'user': request.user,
        'announcements': announcements,
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def manage_subjects(request):
    """
    Allows teachers to see a list of subjects and add new ones.
    """
    teacher = Teacher.objects.get(user=request.user)
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.created_by = teacher
            subject.save()
            return redirect('school:manage_subjects')
    else:
        form = SubjectForm()

    subjects = Subject.objects.all()
    context = {
        'form': form,
        'subjects': subjects
    }
    return render(request, 'teacher_features/manage_subjects.html', context)

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def view_my_courses(request):
    """
    Lists all courses taught by the currently logged-in teacher.
    """
    teacher = Teacher.objects.get(user=request.user)
    courses = Course.objects.filter(teacher=teacher)
    context = {
        'courses': courses
    }
    return render(request, 'teacher_features/my_courses.html', context)

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def course_detail(request, course_id):
    """
    Shows course details and handles management of grades, assignments, and documents.
    """
    course = get_object_or_404(Course, pk=course_id)
    if course.teacher.user != request.user:
        return redirect('school:teacher_dashboard')

    if request.method == 'POST':
        # Differentiate between the three forms
        if 'add_grade' in request.POST:
            grade_form = GradeForm(request.POST, course=course)
            if grade_form.is_valid():
                grade = grade_form.save(commit=False)
                grade.course = course
                grade.save()
                return redirect('school:course_detail', course_id=course_id)
        elif 'add_assignment' in request.POST:
            assignment_form = AssignmentForm(request.POST, request.FILES)
            if assignment_form.is_valid():
                assignment = assignment_form.save(commit=False)
                assignment.course = course
                assignment.save()
                return redirect('school:course_detail', course_id=course_id)
        elif 'add_document' in request.POST:
            document_form = DocumentForm(request.POST, request.FILES)
            if document_form.is_valid():
                document = document_form.save(commit=False)
                document.course = course
                document.save()
                return redirect('school:course_detail', course_id=course_id)

    # If not a POST request or if forms were invalid, create fresh forms
    grade_form = GradeForm(course=course)
    assignment_form = AssignmentForm()
    document_form = DocumentForm()

    # Fetch existing data
    students = course.students.all()
    grades = Grade.objects.filter(course=course).order_by('student__user__username', '-date')
    assignments = Assignment.objects.filter(course=course).order_by('-due_date')
    documents = Document.objects.filter(course=course).order_by('-uploaded_at')

    student_grades = {student: [] for student in students}
    for grade in grades:
        student_grades[grade.student].append(grade)

    context = {
        'course': course,
        'student_grades': student_grades,
        'assignments': assignments,
        'documents': documents,
        'grade_form': grade_form,
        'assignment_form': assignment_form,
        'document_form': document_form,
    }
    return render(request, 'teacher_features/course_detail.html', context)


# --- Student and Parent Features ---

@login_required
@user_passes_test(is_student, login_url='school:home')
def student_dashboard(request):
    """
    Displays the dashboard for a student, with filtering for grades and attendance.
    """
    student = Student.objects.get(user=request.user)

    # Base querysets
    grades = Grade.objects.filter(student=student)
    attendance_records = Attendance.objects.filter(student=student)

    # Filter logic
    filter_form = CourseFilterForm(request.GET, user=request.user)
    if filter_form.is_valid():
        course_id = filter_form.cleaned_data.get('course')
        if course_id:
            grades = grades.filter(course=course_id)
            attendance_records = attendance_records.filter(course=course_id)

    # Other data
    courses = student.enrolled_courses.all()
    assignments = Assignment.objects.filter(course__in=courses).order_by('-due_date')
    documents = Document.objects.filter(course__in=courses).order_by('-uploaded_at')
    announcements = Announcement.objects.all()[:5]

    context = {
        'filter_form': filter_form,
        'courses': courses,
        'assignments': assignments,
        'documents': documents,
        'grades': grades.order_by('-date'),
        'attendance_records': attendance_records.order_by('-date')[:10],
        'announcements': announcements,
    }
    return render(request, 'dashboards/student_dashboard.html', context)

@login_required
@user_passes_test(is_parent, login_url='school:home')
def parent_dashboard(request):
    """
    Displays the dashboard for a parent, showing their children.
    """
    parent = Parent.objects.get(user=request.user)
    children = parent.students.all()
    announcements = Announcement.objects.all()[:5]

    context = {
        'children': children,
        'announcements': announcements,
    }
    return render(request, 'dashboards/parent_dashboard.html', context)

@login_required
@user_passes_test(is_parent, login_url='school:home')
def child_detail(request, student_id):
    """
    Displays a detailed view of a specific child's courses, grades, and attendance for a parent.
    """
    parent = Parent.objects.get(user=request.user)
    child = get_object_or_404(Student, pk=student_id)

    if child not in parent.students.all():
        return redirect('school:parent_dashboard')

    # Base querysets
    grades = Grade.objects.filter(student=child)
    attendance_records = Attendance.objects.filter(student=child)

    # Filter logic
    filter_form = CourseFilterForm(request.GET, user=request.user, child=child)
    if filter_form.is_valid():
        course_id = filter_form.cleaned_data.get('course')
        if course_id:
            grades = grades.filter(course=course_id)
            attendance_records = attendance_records.filter(course=course_id)

    # Other data
    courses = child.enrolled_courses.all()
    assignments = Assignment.objects.filter(course__in=courses).order_by('-due_date')
    documents = Document.objects.filter(course__in=courses).order_by('-uploaded_at')

    context = {
        'child': child,
        'filter_form': filter_form,
        'courses': courses,
        'assignments': assignments,
        'documents': documents,
        'grades': grades.order_by('-date'),
        'attendance_records': attendance_records.order_by('-date')[:10],
    }
    return render(request, 'dashboards/child_detail.html', context)


# --- Attendance Features ---

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def select_attendance_course(request):
    """
    Lets a teacher select which course they want to take attendance for.
    """
    teacher = Teacher.objects.get(user=request.user)
    courses = Course.objects.filter(teacher=teacher)
    context = {
        'courses': courses
    }
    return render(request, 'teacher_features/select_attendance_course.html', context)

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def take_attendance(request, course_id):
    """
    Handles the main attendance taking logic for a given course.
    """
    course = get_object_or_404(Course, pk=course_id)
    # Security check: ensure the logged-in teacher is assigned to this course
    if course.teacher.user != request.user:
        return redirect('school:teacher_dashboard')

    AttendanceFormSet = modelformset_factory(Attendance, form=AttendanceForm, extra=0)

    # Get or create attendance records for all students in the course for today
    today = date.today()
    students = course.students.all()
    for student in students:
        Attendance.objects.get_or_create(student=student, course=course, date=today)

    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=Attendance.objects.filter(course=course, date=today))
        if formset.is_valid():
            formset.save()
            return redirect('school:teacher_dashboard') # Or a success page
    else:
        formset = AttendanceFormSet(queryset=Attendance.objects.filter(course=course, date=today))

    # Combine the formset with the student data for rendering
    student_forms = zip(students, formset)

    context = {
        'course': course,
        'formset': formset, # Pass the formset itself for management form
        'student_forms': student_forms,
        'date': today,
    }
    return render(request, 'teacher_features/take_attendance.html', context)


# --- Announcement Features ---

@login_required
@user_passes_test(is_teacher, login_url='school:home')
def post_announcement(request):
    """
    Allows teachers to post a new announcement.
    """
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            return redirect('school:teacher_dashboard')
    else:
        form = AnnouncementForm()

    context = {
        'form': form
    }
    return render(request, 'teacher_features/post_announcement.html', context)


# --- Messaging Features ---

@login_required
def inbox(request):
    """
    Displays a list of received messages for the logged-in user.
    """
    messages = Message.objects.filter(recipient=request.user)
    context = {
        'messages': messages
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def view_message(request, message_id):
    """
    Displays a single message and marks it as read.
    """
    message = get_object_or_404(Message, pk=message_id, recipient=request.user)
    if not message.read_at:
        message.read_at = timezone.now()
        message.save()

    context = {
        'message': message
    }
    return render(request, 'messaging/view_message.html', context)

@login_required
def compose_message(request):
    """
    Handles composing and sending a new message.
    """
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('school:inbox')
    else:
        form = MessageForm()

    context = {
        'form': form
    }
    return render(request, 'messaging/compose_message.html', context)
