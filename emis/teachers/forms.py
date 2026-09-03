from django import forms
from .models import LeaveRequest, Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'first_name', 'last_name', 'gender', 'email', 'phone',
            'department', 'designation', 'qualification', 'specialization', 'is_active', 'date_joined'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TCH-001'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.Sc. Computer Science'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Artificial Intelligence, Data Science'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date_joined': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TeacherProfileForm(forms.ModelForm):
    """Self-service profile editing for teachers in the teacher portal."""

    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'gender', 'email', 'phone',
                  'qualification', 'specialization']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'from_date', 'to_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Reason for leave (optional)'}),
        }

    def clean(self):
        cleaned = super().clean()
        from_date = cleaned.get('from_date')
        to_date = cleaned.get('to_date')
        if from_date and to_date and to_date < from_date:
            self.add_error('to_date', 'To date cannot be before from date.')
        return cleaned

