from django.contrib import admin
from .models import Book, BookCategory, Librarian, Borrowing


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'rack_location')
    list_filter = ('category', 'published_year')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    list_editable = ('available_copies',)


@admin.register(Librarian)
class LibrarianAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('username', 'full_name', 'email')


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'borrowed_date', 'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('status', 'borrowed_date')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name', 'book__title')