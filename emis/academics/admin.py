from django.contrib import admin
from .models import (
    Department, Program, Course, AcademicYear, Semester,
    CourseAssignment, Timetable, Batch
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head')
    search_fields = ('code', 'name')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'duration_years', 'total_semesters', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'program', 'semester', 'credit_hours')
    list_filter = ('program', 'semester')
    search_fields = ('code', 'name')


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'is_current')
    list_filter = ('academic_year', 'is_current')


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'semester', 'section')
    list_filter = ('semester',)
    search_fields = ('course__code', 'course__name', 'teacher__first_name', 'teacher__last_name')


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('course_assignment', 'day_of_week', 'start_time', 'end_time', 'room')
    list_filter = ('day_of_week',)
    ordering = ('day_of_week', 'start_time')


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'program')
    list_filter = ('program',)