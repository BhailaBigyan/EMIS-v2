from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    path('notices/', views.notice_list, name='notice_list'),
]