from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'school'

from . import views

urlpatterns = [
    # General URLs
    path('', views.home_view, name='home'),

    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='school:home'), name='logout'),

    # Teacher URLs
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/subjects/', views.manage_subjects, name='manage_subjects'),
    path('teacher/courses/', views.view_my_courses, name='view_my_courses'),
    path('teacher/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('teacher/attendance/', views.select_attendance_course, name='select_attendance_course'),
    path('teacher/attendance/<int:course_id>/', views.take_attendance, name='take_attendance'),
    path('teacher/announcements/post/', views.post_announcement, name='post_announcement'),

    # Student URLs
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    # Parent URLs
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/child/<int:student_id>/', views.child_detail, name='child_detail'),

    # Messaging URLs
    path('messages/inbox/', views.inbox, name='inbox'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/view/<int:message_id>/', views.view_message, name='view_message'),
]
