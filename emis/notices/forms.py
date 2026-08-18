from django import forms
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'category', 'is_important']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Semester End Examination Schedule'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Write the full notice content here...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
