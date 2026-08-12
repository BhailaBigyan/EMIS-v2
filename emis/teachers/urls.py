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
]

