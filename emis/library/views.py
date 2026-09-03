from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db.models import Q, Sum
from emis.decorators import admin_login_required
from .models import Book, BookCategory, Librarian, Borrowing
from .forms import BookForm, BookCategoryForm, LibrarianForm, IssueBookForm


# ==========================================
# Librarian Portal (Circulation Desk)
# ==========================================

def library_home(request):
    if request.session.get("library_logged_in"):
        return redirect('library:library_dashboard')
    return redirect('library:library_login')


def library_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            librarian = Librarian.objects.get(username=username)
            if check_password(password, librarian.password):
                if not librarian.is_active:
                    return render(request, "library/library_login.html", {
                        "error": "This librarian account is inactive. Contact the administrator."
                    })
                request.session["library_logged_in"] = True
                request.session["library_librarian_id"] = librarian.id
                request.session["library_username"] = librarian.full_name
                messages.success(request, f"Welcome, {librarian.full_name}!")
                return redirect("library:library_dashboard")
            return render(request, "library/library_login.html", {"error": "Invalid username or password."})
        except Librarian.DoesNotExist:
            return render(request, "library/library_login.html", {"error": "Librarian account not found."})

    if request.session.get("library_logged_in"):
        return redirect("library:library_dashboard")

    return render(request, 'library/library_login.html')


def _get_librarian(request):
    librarian_id = request.session.get("library_librarian_id")
    if not librarian_id:
        return None
    return Librarian.objects.filter(id=librarian_id).first()


def library_dashboard(request):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    librarian = _get_librarian(request)
    if not librarian:
        request.session.pop("library_logged_in", None)
        return redirect("library:library_login")

    active_loans = Borrowing.objects.filter(status='borrowed').select_related('student', 'book', 'issued_by')
    overdue_loans = [b for b in active_loans if b.is_overdue]

    context = {
        "librarian": librarian,
        "username": librarian.full_name,
        "total_books": Book.objects.aggregate(Sum('total_copies'))['total_copies__sum'] or 0,
        "available_books": Book.objects.aggregate(Sum('available_copies'))['available_copies__sum'] or 0,
        "active_loan_count": active_loans.count(),
        "overdue_count": len(overdue_loans),
        "recent_loans": Borrowing.objects.select_related('student', 'book').order_by('-created_at')[:8],
    }
    return render(request, 'library/library_dashboard.html', context)


def library_catalog(request):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    available_only = request.GET.get('available', '')

    books = Book.objects.select_related('category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(publisher__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    if available_only:
        books = books.filter(available_copies__gt=0)

    context = {
        "books": books,
        "categories": BookCategory.objects.all(),
        "query": query,
        "selected_category": category_id,
        "available_only": available_only,
    }
    return render(request, 'library/library_catalog.html', context)


def issue_book(request):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    librarian = _get_librarian(request)
    if request.method == "POST":
        form = IssueBookForm(request.POST)
        if form.is_valid():
            borrowing = form.save(commit=False)
            borrowing.issued_by = librarian
            borrowing.book.available_copies -= 1
            borrowing.book.save(update_fields=['available_copies'])
            borrowing.save()
            messages.success(
                request,
                f"'{borrowing.book.title}' issued to {borrowing.student.roll_number} "
                f"({borrowing.student.full_name}). Due: {borrowing.due_date}."
            )
            return redirect("library:library_loans")
    else:
        initial_student = request.GET.get('student_id', '')
        form = IssueBookForm(initial={'student': initial_student} if initial_student else None)

    return render(request, 'library/issue_book.html', {'form': form})


def library_loans(request):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    active_loans = Borrowing.objects.filter(status='borrowed').select_related('student', 'book', 'issued_by')
    history = Borrowing.objects.filter(status='returned').select_related('student', 'book')[:50]

    context = {
        "active_loans": active_loans,
        "history": history,
    }
    return render(request, 'library/library_loans.html', context)


def return_book(request, borrowing_id):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    borrowing = get_object_or_404(
        Borrowing.objects.select_related('student', 'book'),
        id=borrowing_id, status='borrowed'
    )
    if request.method == "POST":
        fine = borrowing.return_book()
        if fine:
            messages.warning(
                request,
                f"'{borrowing.book.title}' returned late by {borrowing.student.roll_number}. Fine: Rs. {fine}"
            )
        else:
            messages.success(request, f"'{borrowing.book.title}' returned by {borrowing.student.roll_number}.")
        return redirect("library:library_loans")

    return render(request, 'library/return_book.html', {'borrowing': borrowing})


def library_logout(request):
    request.session.pop("library_logged_in", None)
    request.session.pop("library_librarian_id", None)
    request.session.pop("library_username", None)
    messages.info(request, "Logged out from Library Portal.")
    return redirect("library:library_login")


# ==========================================
# Admin — Book Management
# ==========================================

@admin_login_required
def admin_book_list(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.select_related('category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    total_books = Book.objects.aggregate(Sum('total_copies'))['total_copies__sum'] or 0
    total_available = Book.objects.aggregate(Sum('available_copies'))['available_copies__sum'] or 0
    active_borrowings = Borrowing.objects.filter(status='borrowed').count()

    context = {
        'books': books,
        'query': query,
        'total_books': total_books,
        'total_available': total_available,
        'active_borrowings': active_borrowings,
    }
    return render(request, 'admin/library_management/book_list.html', context)


@admin_login_required
def admin_book_add(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' added to catalog.")
            return redirect('library:admin_book_list')
    else:
        form = BookForm()

    return render(request, 'admin/library_management/book_form.html', {'form': form, 'title': 'Add Book'})


@admin_login_required
def admin_book_edit(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"Book '{book.title}' updated.")
            return redirect('library:admin_book_list')
    else:
        form = BookForm(instance=book)

    return render(request, 'admin/library_management/book_form.html', {'form': form, 'title': 'Edit Book'})


@admin_login_required
def admin_book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == "POST":
        title = book.title
        book.delete()
        messages.success(request, f"Book '{title}' removed from catalog.")
        return redirect('library:admin_book_list')

    return render(request, 'admin/library_management/book_delete.html', {'book': book})


# ==========================================
# Admin — Categories
# ==========================================

@admin_login_required
def admin_category_list(request):
    categories = BookCategory.objects.annotate(book_count=Sum('books__total_copies'))
    return render(request, 'admin/library_management/category_list.html', {'categories': categories})


@admin_login_required
def admin_category_add(request):
    if request.method == "POST":
        form = BookCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            return redirect('library:admin_category_list')
    else:
        form = BookCategoryForm()

    return render(request, 'admin/library_management/category_form.html', {'form': form, 'title': 'Add Category'})


@admin_login_required
def admin_category_delete(request, category_id):
    category = get_object_or_404(BookCategory, id=category_id)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
        return redirect('library:admin_category_list')

    return render(request, 'admin/library_management/category_delete.html', {'category': category})


# ==========================================
# Admin — Librarian Accounts
# ==========================================

@admin_login_required
def admin_librarian_list(request):
    librarians = Librarian.objects.all()
    return render(request, 'admin/library_management/librarian_list.html', {'librarians': librarians})


@admin_login_required
def admin_librarian_add(request):
    if request.method == "POST":
        form = LibrarianForm(request.POST)
        if form.is_valid():
            librarian = form.save(commit=False)
            raw_password = librarian.set_default_password()
            librarian.save()
            messages.success(
                request,
                f"Librarian '{librarian.full_name}' created. Username: {librarian.username}, Password: {raw_password}"
            )
            return redirect('library:admin_librarian_list')
    else:
        form = LibrarianForm()

    return render(request, 'admin/library_management/librarian_form.html', {'form': form, 'title': 'Add Librarian'})


@admin_login_required
def admin_librarian_edit(request, librarian_id):
    librarian = get_object_or_404(Librarian, id=librarian_id)
    if request.method == "POST":
        form = LibrarianForm(request.POST, instance=librarian)
        if form.is_valid():
            form.save()
            messages.success(request, f"Librarian '{librarian.full_name}' updated.")
            return redirect('library:admin_librarian_list')
    else:
        form = LibrarianForm(instance=librarian)

    return render(request, 'admin/library_management/librarian_form.html', {'form': form, 'title': 'Edit Librarian'})


# ==========================================
# Admin — Circulation Oversight
# ==========================================

@admin_login_required
def admin_borrowing_list(request):
    status_filter = request.GET.get('status', '')
    borrowings = Borrowing.objects.select_related('student', 'book', 'issued_by').all()

    if status_filter:
        borrowings = borrowings.filter(status=status_filter)

    overdue = [b for b in borrowings if b.is_overdue]

    context = {
        'borrowings': borrowings,
        'selected_status': status_filter,
        'overdue': overdue,
    }
    return render(request, 'admin/library_management/borrowing_list.html', context)


@admin_login_required
def admin_return_book(request, borrowing_id):
    borrowing = get_object_or_404(
        Borrowing.objects.select_related('student', 'book'), id=borrowing_id, status='borrowed'
    )
    if request.method == "POST":
        fine = borrowing.return_book()
        if fine:
            messages.warning(request, f"Book returned late. Fine: Rs. {fine}")
        else:
            messages.success(request, f"'{borrowing.book.title}' marked as returned.")
        return redirect('library:admin_borrowing_list')

    return render(request, 'admin/library_management/return_book.html', {'borrowing': borrowing})