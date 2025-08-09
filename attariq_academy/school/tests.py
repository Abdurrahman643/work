from django.test import TestCase
from django.urls import reverse
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import User, Student, Teacher, Parent, Subject, Course, Grade, Attendance, Announcement, Assignment, Document, Message

class SchoolModelTest(TestCase):

    def setUp(self):
        self.teacher_user = User.objects.create_user(username='teacher_test', password='password123', role='TEACHER', first_name='Tess', last_name='Teacher')
        self.teacher_profile = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(username='student_test', password='password123', role='STUDENT', first_name='Sam', last_name='Student')
        self.student_profile = Student.objects.create(user=self.student_user)

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.teacher_user.role, 'TEACHER')
        self.assertEqual(self.student_user.role, 'STUDENT')
        self.assertEqual(self.student_user.first_name, 'Sam')

    def test_profile_creation(self):
        self.assertTrue(hasattr(self.teacher_user, 'teacher_profile'))
        self.assertTrue(hasattr(self.student_user, 'student_profile'))
        self.assertEqual(str(self.teacher_profile), 'teacher_test')
        self.assertEqual(str(self.student_profile), 'student_test')

class SchoolViewTest(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin_test', password='password123', email='admin@test.com')

        self.teacher_user = User.objects.create_user(username='teacher_test', password='password123', role='TEACHER', first_name='Tess', last_name='Teacher')
        self.teacher_profile = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(username='student_test', password='password123', role='STUDENT', first_name='Sam', last_name='Student')
        self.student_profile = Student.objects.create(user=self.student_user)

    def test_login_required_for_dashboards(self):
        response = self.client.get(reverse('school:teacher_dashboard'))
        self.assertRedirects(response, reverse('school:login') + '?next=' + reverse('school:teacher_dashboard'))

        response = self.client.get(reverse('school:student_dashboard'))
        self.assertRedirects(response, reverse('school:login') + '?next=' + reverse('school:student_dashboard'))

    def test_role_based_access(self):
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('school:teacher_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('school:home'), response.url)
        self.client.logout()

        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboards/teacher_dashboard.html')

    def test_home_view_redirects(self):
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:home'))
        self.assertRedirects(response, reverse('school:teacher_dashboard'))
        self.client.logout()

        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('school:home'))
        self.assertRedirects(response, reverse('school:student_dashboard'))
        self.client.logout()

    def test_manage_subjects_view(self):
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:manage_subjects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Subject')

        response = self.client.post(reverse('school:manage_subjects'), {'name': 'Test Subject'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subject.objects.filter(name='Test Subject').exists())
        new_subject = Subject.objects.get(name='Test Subject')
        self.assertEqual(new_subject.created_by, self.teacher_profile)

    def test_parent_can_only_view_own_child_detail(self):
        other_student_user = User.objects.create_user(username='other_student', password='password123', role='STUDENT', first_name='Other', last_name='Kid')
        other_student_profile = Student.objects.create(user=other_student_user)

        parent_user = User.objects.create_user(username='parent_test', password='password123', role='PARENT', first_name='Pam', last_name='Parent')
        parent_profile = Parent.objects.create(user=parent_user)
        parent_profile.students.add(self.student_profile)

        self.client.login(username='parent_test', password='password123')

        response = self.client.get(reverse('school:child_detail', kwargs={'student_id': self.student_profile.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_profile.user.first_name)

        response = self.client.get(reverse('school:child_detail', kwargs={'student_id': other_student_profile.user.id}))
        self.assertRedirects(response, reverse('school:parent_dashboard'))

    def test_take_and_view_attendance(self):
        subject = Subject.objects.create(name='Math')
        course = Course.objects.create(name='Algebra 1', subject=subject, teacher=self.teacher_profile)
        course.students.add(self.student_profile)

        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:take_attendance', kwargs={'course_id': course.id}))
        self.assertEqual(response.status_code, 200)

        attendance_obj = Attendance.objects.get(student=self.student_profile, course=course, date=date.today())
        self.assertTrue(attendance_obj.is_present)

        formset_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            f'form-0-id': str(attendance_obj.id),
        }
        response = self.client.post(reverse('school:take_attendance', kwargs={'course_id': course.id}), data=formset_data)
        self.assertRedirects(response, reverse('school:teacher_dashboard'))

        attendance_obj.refresh_from_db()
        self.assertFalse(attendance_obj.is_present)

        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('school:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Absent')

    def test_post_and_view_announcement(self):
        self.client.login(username='teacher_test', password='password123')
        announcement_data = {
            'title': 'Test Announcement',
            'content': 'This is a test.'
        }
        response = self.client.post(reverse('school:post_announcement'), data=announcement_data)
        self.assertRedirects(response, reverse('school:teacher_dashboard'))

        self.assertTrue(Announcement.objects.filter(title='Test Announcement').exists())

        self.client.logout()
        self.client.login(username='student_test', password='password123')

        response = self.client.get(reverse('school:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Announcement')
        self.assertContains(response, 'This is a test.')

    def test_teacher_can_upload_document(self):
        subject = Subject.objects.create(name='Science')
        course = Course.objects.create(name='Biology', subject=subject, teacher=self.teacher_profile)
        course.students.add(self.student_profile)

        self.client.login(username='teacher_test', password='password123')

        dummy_file = SimpleUploadedFile("syllabus.txt", b"Course syllabus content.", content_type="text/plain")

        document_data = {
            'title': 'Biology Syllabus',
            'description': 'Syllabus for the year.',
            'file': dummy_file
        }

        response = self.client.post(reverse('school:course_detail', kwargs={'course_id': course.id}), data={**document_data, 'add_document': ''})
        self.assertRedirects(response, reverse('school:course_detail', kwargs={'course_id': course.id}))

        self.assertTrue(Document.objects.filter(course=course, title='Biology Syllabus').exists())

        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('school:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biology Syllabus')

    def test_messaging_system(self):
        self.client.login(username='student_test', password='password123')
        message_data = {
            'recipient': self.teacher_user.id,
            'subject': 'Question about homework',
            'body': 'When is the homework due?'
        }
        response = self.client.post(reverse('school:compose_message'), data=message_data)
        self.assertRedirects(response, reverse('school:inbox'))

        self.assertTrue(Message.objects.filter(subject='Question about homework').exists())
        message = Message.objects.get(subject='Question about homework')
        self.assertEqual(message.sender, self.student_user)
        self.assertEqual(message.recipient, self.teacher_user)
        self.assertIsNone(message.read_at)

        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Question about homework')

        response = self.client.get(reverse('school:view_message', kwargs={'message_id': message.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'When is the homework due?')

        message.refresh_from_db()
        self.assertTrue(message.read_at)
        self.assertTrue(message.read_at <= timezone.now())

    def test_unread_message_notification(self):
        message = Message.objects.create(
            sender=self.student_user,
            recipient=self.teacher_user,
            subject='Unread Test',
            body='This is a test message.'
        )

        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('school:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="badge bg-danger">1</span>')

        self.client.get(reverse('school:view_message', kwargs={'message_id': message.id}))

        response = self.client.get(reverse('school:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<span class="badge bg-danger">1</span>')

    def test_student_sees_only_own_data(self):
        student2_user = User.objects.create_user(username='student2', password='password123', role='STUDENT', first_name='Sue', last_name='Smith')
        student2_profile = Student.objects.create(user=student2_user)
        subject = Subject.objects.create(name='English')
        course = Course.objects.create(name='Literature', subject=subject, teacher=self.teacher_profile)
        course.students.add(self.student_profile)
        course.students.add(student2_profile)

        grade1 = Grade.objects.create(student=self.student_profile, course=course, title='Essay 1', grade=90)
        grade2 = Grade.objects.create(student=student2_profile, course=course, title='Essay 1', grade=85)

        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('school:student_dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '90.00')
        self.assertNotContains(response, '85.00')
