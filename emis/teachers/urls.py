from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('<int:teacher_id>/edit/', views.teacher_edit, name='teacher_edit'),
    path('<int:teacher_id>/delete/', views.teacher_delete, name='teacher_delete'),
    path('export/', views.teacher_export_csv, name='teacher_export_csv'),

    # Teacher portal
    path('login/', views.teacher_login, name='teacher_login'),
    path('logout/', views.teacher_logout, name='teacher_logout'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('attendance/records/', views.teacher_attendance_records, name='teacher_attendance_records'),
    path('routines/', views.teacher_routines, name='teacher_routines'),
    path('leave/', views.teacher_leave, name='teacher_leave'),
    path('leave/new/', views.teacher_leave_new, name='teacher_leave_new'),
    path('profile/', views.teacher_profile, name='teacher_profile'),
    path('profile/edit/', views.teacher_profile_edit, name='teacher_profile_edit'),

    # Admin: leave management
    path('leave-requests/', views.teacher_leave_admin, name='teacher_leave_admin'),
    path('leave-requests/<int:leave_id>/decision/', views.teacher_leave_decision, name='teacher_leave_decision'),
]

