from django import forms
from .models import Exam, ExamSchedule, Grade, Result


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'name', 'exam_type', 'semester', 'start_date', 'end_date',
            'total_marks', 'pass_marks', 'description', 'is_published'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. First Assessment 2081'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'pass_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['exam', 'course', 'date', 'start_time', 'end_time', 'room', 'invigilator']
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hall A'}),
            'invigilator': forms.Select(attrs={'class': 'form-select'}),
        }


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'exam', 'course', 'marks_obtained', 'remarks', 'graded_by']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Remarks'}),
            'graded_by': forms.Select(attrs={'class': 'form-select'}),
        }
