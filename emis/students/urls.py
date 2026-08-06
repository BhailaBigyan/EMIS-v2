from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path('', views.student_login, name='student_login'),
    path('index/', views.student_index, name='student_index'),
    path('logout/', views.student_logout, name='student_logout'),
]