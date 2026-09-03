from django.contrib import admin
from .models import FeeStructure, FeePayment, StudentFeeAccount, Salary


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'semester', 'academic_year', 'total_fee')
    list_filter = ('program', 'semester', 'academic_year')
    search_fields = ('name',)


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'fee_structure', 'amount_paid', 'payment_date', 'status')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('receipt_number', 'student__roll_number', 'student__first_name', 'student__last_name')
    readonly_fields = ('receipt_number',)


@admin.register(StudentFeeAccount)
class StudentFeeAccountAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'total_due', 'total_paid', 'balance', 'is_fully_paid')
    list_filter = ('fee_structure',)
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'month', 'base_salary', 'allowances', 'deductions', 'net_salary', 'payment_status')
    list_filter = ('payment_status',)
    search_fields = ('teacher__first_name', 'teacher__last_name', 'month')