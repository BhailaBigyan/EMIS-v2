from django.urls import path, include
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.library_home, name='library_home'),
    path('login/', views.library_login, name='library_login'),
    path('dashboard/', views.library_dashboard, name='library_dashboard'),
]