from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('exams/', views.exam_list, name='exam_list'),
]