from django import forms
from .models import Book, BookCategory, Librarian, Borrowing
from students.models import Students


class BookCategoryForm(forms.ModelForm):
    class Meta:
        model = BookCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'category', 'publisher',
            'published_year', 'total_copies', 'available_copies',
            'rack_location', 'description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'published_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2100}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'rack_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rack 3-B'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LibrarianForm(forms.ModelForm):
    class Meta:
        model = Librarian
        fields = ['username', 'full_name', 'email', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. librarian1'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IssueBookForm(forms.ModelForm):
    class Meta:
        model = Borrowing
        fields = ['student', 'book']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'book': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Students.objects.select_related('program').order_by('roll_number')
        self.fields['student'].label_from_instance = (
            lambda s: f"{s.roll_number} - {s.full_name}"
        )
        self.fields['book'].queryset = Book.objects.select_related('category').order_by('title')

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        book = cleaned.get('book')
        if not student or not book:
            return cleaned

        if student.status != 'active':
            raise forms.ValidationError(
                f"Student {student.roll_number} ({student.full_name}) is not active and cannot borrow books."
            )

        if student.borrowings.filter(status='borrowed').count() >= 3:
            raise forms.ValidationError(
                f"Student {student.roll_number} already has 3 active loans (maximum allowed)."
            )

        if book.available_copies < 1:
            raise forms.ValidationError(f"No copies of '{book.title}' are currently available.")

        if Borrowing.objects.filter(student=student, book=book, status='borrowed').exists():
            raise forms.ValidationError(
                f"Student {student.roll_number} already has '{book.title}' on loan."
            )

        return cleaned