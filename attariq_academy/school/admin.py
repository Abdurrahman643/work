from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Teacher, Parent, Subject, Course, Attendance, Grade, Announcement

# Custom User Admin to display and manage roles
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        # Add the custom 'role' field to be editable in the admin
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Custom Course Admin for better management of student enrollment
class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('students',)
    list_display = ('name', 'subject', 'teacher')
    list_filter = ('subject', 'teacher')

# Custom Grade Admin for better filtering and display
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'title', 'grade')
    list_filter = ('course',)
    search_fields = ('student__user__username', 'course__name', 'title')

# Custom Attendance Admin for better filtering and display
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'is_present')
    list_filter = ('course', 'date', 'is_present')
    search_fields = ('student__user__username', 'course__name')

# Register models with their custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Attendance, AttendanceAdmin)

# Register the remaining models with the default admin interface
# These will be managed by the admin, but require less custom functionality for now
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Parent)
admin.site.register(Subject)

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'content')

admin.site.register(Announcement, AnnouncementAdmin)
