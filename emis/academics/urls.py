


from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path('classes/', views.classes_list, name='classes_list'),
]