from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    # Exams CRUD
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:exam_id>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),

    # Exam Schedule
    path('exams/<int:exam_id>/schedule/', views.schedule_list, name='schedule_list'),
    path('exams/<int:exam_id>/schedule/add/', views.schedule_add, name='schedule_add'),

    # Grade Entry
    path('grades/<int:exam_id>/<int:course_id>/', views.grade_entry, name='grade_entry'),

    # Results & Report Cards
    path('results/', views.result_list, name='result_list'),
    path('results/generate/', views.result_generate, name='result_generate'),
    path('report-card/<int:student_id>/<int:semester_id>/', views.report_card_view, name='report_card_view'),
]