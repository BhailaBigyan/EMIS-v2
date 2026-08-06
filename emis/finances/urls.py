from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
]




