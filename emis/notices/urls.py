from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    path('', views.notice_list, name='notice_list'),
    path('add/', views.notice_add, name='notice_add'),
    path('<int:notice_id>/edit/', views.notice_edit, name='notice_edit'),
    path('<int:notice_id>/delete/', views.notice_delete, name='notice_delete'),
]