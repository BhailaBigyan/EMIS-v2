from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    # Legacy / Classes overview
    path('classes/', views.classes_list, name='classes_list'),

    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:dept_id>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:dept_id>/delete/', views.department_delete, name='department_delete'),

    # Programs
    path('programs/', views.program_list, name='program_list'),
    path('programs/add/', views.program_add, name='program_add'),
    path('programs/<int:prog_id>/edit/', views.program_edit, name='program_edit'),
    path('programs/<int:prog_id>/delete/', views.program_delete, name='program_delete'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),

    # Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/add/', views.batch_add, name='batch_add'),
    path('batches/<int:batch_id>/edit/', views.batch_edit, name='batch_edit'),
    path('batches/<int:batch_id>/delete/', views.batch_delete, name='batch_delete'),

    # Academic Years & Semesters
    path('academic-years/', views.academic_year_list, name='academic_year_list'),
    path('academic-years/add/', views.academic_year_add, name='academic_year_add'),
    path('academic-years/<int:year_id>/edit/', views.academic_year_edit, name='academic_year_edit'),
    path('academic-years/<int:year_id>/delete/', views.academic_year_delete, name='academic_year_delete'),
    path('semesters/add/', views.semester_add, name='semester_add'),
    path('semesters/<int:sem_id>/edit/', views.semester_edit, name='semester_edit'),
    path('semesters/<int:sem_id>/delete/', views.semester_delete, name='semester_delete'),

    # Course Assignments (Teacher Allocation)
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_add, name='assignment_add'),
    path('assignments/<int:assign_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:assign_id>/delete/', views.assignment_delete, name='assignment_delete'),

    # Timetable
    path('timetable/', views.timetable_view, name='timetable_view'),
    path('timetable/add/', views.timetable_add, name='timetable_add'),
    path('timetable/<int:slot_id>/edit/', views.timetable_edit, name='timetable_edit'),
    path('timetable/<int:slot_id>/delete/', views.timetable_delete, name='timetable_delete'),
]