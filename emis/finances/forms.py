from django import forms
from .models import FeeStructure, FeePayment, StudentFeeAccount, Salary


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            'name', 'program', 'semester', 'academic_year',
            'tuition_fee', 'lab_fee', 'library_fee', 'exam_fee', 'other_fee', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BCA 1st Semester Fee'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'tuition_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lab_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'library_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'exam_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = [
            'student', 'fee_structure', 'amount_paid', 'payment_date',
            'payment_method', 'transaction_id', 'status', 'remarks'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional transaction ref/cheque no'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = [
            'teacher', 'month', 'base_salary', 'allowances',
            'deductions', 'payment_date', 'payment_status'
        ]
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. August 2026'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'allowances': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

