from django.contrib import admin
from .models import Exam, ExamSchedule, Grade, Result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'semester', 'start_date', 'end_date', 'is_published')
    list_filter = ('exam_type', 'semester')
    search_fields = ('name',)


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam', 'course', 'date', 'start_time', 'end_time', 'room', 'invigilator')
    list_filter = ('exam',)
    search_fields = ('course__code', 'course__name')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'course', 'marks_obtained', 'grade_letter', 'remarks')
    list_filter = ('exam', 'course')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'percentage', 'gpa', 'status', 'published')
    list_filter = ('semester', 'status', 'published')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')