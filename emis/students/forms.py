from django import forms
from .models import Students
from academics.models import Program


class StudentForm(forms.ModelForm):
    """Form for adding/editing a single student."""
    class Meta:
        model = Students
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address',
            'program', 'batch', 'current_semester', 'section',
            'status', 'guardian_name', 'guardian_phone',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Address'
            }),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 2081'
            }),
            'current_semester': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. A'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Guardian name'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Guardian phone'
            }),
        }


class BulkStudentUploadForm(forms.Form):
    """Form for bulk student upload via CSV/Excel."""
    file = forms.FileField(
        label='Upload CSV or Excel File',
        help_text='Accepted formats: .csv, .xlsx',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx',
        })
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Program to assign all uploaded students to'
    )
    batch = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. 2081'
        }),
        help_text='Batch year for all uploaded students'
    )
