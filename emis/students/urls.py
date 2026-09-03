from django.urls import path
from . import views
from assistant import views as assistant_views

app_name = "students"

urlpatterns = [
    path('', views.student_login, name='student_login'),
    path('index/', views.student_index, name='student_index'),
    path('logout/', views.student_logout, name='student_logout'),
    path('profile/', views.student_profile, name='student_profile'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('exams/', views.student_exams, name='student_exams'),
    path('results/', views.student_results, name='student_results'),
    path('timetable/', views.student_timetable, name='student_timetable'),
    path('notices/', views.student_notices, name='student_notices'),
    path('fees/', views.student_fees, name='student_fees'),
    path('books/', views.student_books, name='student_books'),
    path('help/', views.student_help, name='student_help'),
    path('assistant/', assistant_views.student_assistant, name='assistant'),
]