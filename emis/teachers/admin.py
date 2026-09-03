from django.contrib import admin
from .models import LeaveRequest, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'designation', 'is_active', 'has_portal_access')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'leave_type', 'from_date', 'to_date', 'days', 'status', 'applied_at')
    list_filter = ('status', 'leave_type')
    search_fields = ('teacher__employee_id', 'teacher__first_name', 'teacher__last_name')
