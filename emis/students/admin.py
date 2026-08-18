from django.contrib import admin

from .models import Attendance, Students


@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'full_name', 'program', 'current_semester', 'status')
    list_filter = ('status', 'program', 'batch')
    search_fields = ('roll_number', 'first_name', 'last_name', 'email')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')
    date_hierarchy = 'date'