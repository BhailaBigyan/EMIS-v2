from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    # Dashboard & Reports
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),

    # Fee Structures
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/add/', views.fee_structure_add, name='fee_structure_add'),
    path('fee-structures/<int:fs_id>/edit/', views.fee_structure_edit, name='fee_structure_edit'),
    path('fee-structures/<int:fs_id>/delete/', views.fee_structure_delete, name='fee_structure_delete'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/record/', views.record_payment, name='record_payment'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),

    # Student Fee Status
    path('student-fees/', views.student_fee_status, name='student_fee_status'),

    # Faculty Salaries
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/record/', views.record_salary, name='record_salary'),
]

