from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.template.context import Context

# Fix Python 3.14 + Django Context.__copy__ compatibility for test client
def _fixed_copy(self):
    duplicate = Context()
    duplicate.dicts = self.dicts[:]
    return duplicate

Context.__copy__ = _fixed_copy


from academics.models import Department, Program
from students.models import Students
from library.models import Book, BookCategory, Librarian, Borrowing


class LibrarySetupMixin(TestCase):
    def setUp(self):
        self.category = BookCategory.objects.create(name="Computer Science")
        self.book = Book.objects.create(
            title="Django for Beginners",
            author="John Doe",
            isbn="978-0000000001",
            category=self.category,
            total_copies=2,
            available_copies=2,
        )
        self.librarian = Librarian.objects.create(
            username="librarian",
            full_name="Demo Librarian",
            is_active=True,
        )
        self.librarian.set_default_password()
        self.librarian.save()

        dept = Department.objects.create(name="Management", code="MGMT")
        self.program = Program.objects.create(
            name="BIM", code="BIM", department=dept, duration_years=4, total_semesters=8, is_active=True
        )
        self.student = Students.objects.create(
            roll_number="BIM-2083-001", first_name="Ram", last_name="Sharma",
            gender="M", program=self.program, batch="2083", current_semester=1, status="active"
        )


class LibraryModelTest(LibrarySetupMixin):
    def test_librarian_default_password_hashed(self):
        self.assertTrue(self.librarian.password.startswith("pbkdf2_sha256$"))

    def test_borrowing_creates_due_date(self):
        borrowing = Borrowing.objects.create(student=self.student, book=self.book)
        self.assertEqual(borrowing.due_date, borrowing.borrowed_date + timedelta(days=14))
        self.assertEqual(borrowing.status, "borrowed")
        self.assertFalse(borrowing.is_overdue)

    def test_return_book_increments_copies(self):
        self.book.available_copies = 1
        self.book.save()
        borrowing = Borrowing.objects.create(student=self.student, book=self.book)
        borrowing.return_book()
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        self.assertEqual(borrowing.status, "returned")
        self.assertEqual(borrowing.fine_amount, 0)

    def test_overdue_fine_calculation(self):
        borrowing = Borrowing.objects.create(
            student=self.student,
            book=self.book,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        self.assertTrue(borrowing.is_overdue)
        self.assertEqual(borrowing.overdue_days, 6)
        self.assertEqual(borrowing.calculate_fine(), 30)


class LibrarianPortalTest(LibrarySetupMixin):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.post(reverse("library:library_login"), {
            "username": "librarian",
            "password": "library@librarian",
        })

    def test_login_success(self):
        response = self.client.post(reverse("library:library_login"), {
            "username": "librarian",
            "password": "library@librarian",
        })
        self.assertRedirects(response, reverse("library:library_dashboard"))

    def test_login_rejects_wrong_password(self):
        response = self.client.post(reverse("library:library_login"), {
            "username": "librarian",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_dashboard_requires_login(self):
        anon = Client()
        response = anon.get(reverse("library:library_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_shows_stats(self):
        response = self.client.get(reverse("library:library_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Circulation Desk")

    def test_issue_book_to_student(self):
        response = self.client.post(reverse("library:issue_book"), {
            "student": self.student.student_id,
            "book": self.book.id,
        })
        self.assertRedirects(response, reverse("library:library_loans"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)
        borrowing = Borrowing.objects.get(student=self.student)
        self.assertEqual(borrowing.issued_by, self.librarian)

    def test_issue_duplicate_book_blocked(self):
        Borrowing.objects.create(student=self.student, book=self.book)
        response = self.client.post(reverse("library:issue_book"), {
            "student": self.student.student_id,
            "book": self.book.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already has")

    def test_issue_unavailable_book_blocked(self):
        self.book.available_copies = 0
        self.book.save()
        response = self.client.post(reverse("library:issue_book"), {
            "student": self.student.student_id,
            "book": self.book.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "currently available")
        self.assertFalse(Borrowing.objects.filter(student=self.student).exists())

    def test_issue_inactive_student_blocked(self):
        self.student.status = "suspended"
        self.student.save()
        response = self.client.post(reverse("library:issue_book"), {
            "student": self.student.student_id,
            "book": self.book.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not active")

    def test_issue_three_book_limit(self):
        for i in range(3):
            b = Book.objects.create(
                title=f"Book {i}", author="X", isbn=f"978-00000001{i}",
                total_copies=1, available_copies=1
            )
            Borrowing.objects.create(student=self.student, book=b)
        response = self.client.post(reverse("library:issue_book"), {
            "student": self.student.student_id,
            "book": self.book.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3 active loans")
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_return_book_flow(self):
        self.book.available_copies = 1
        self.book.save()
        borrowing = Borrowing.objects.create(student=self.student, book=self.book)
        response = self.client.post(reverse("library:return_book", args=[borrowing.id]))
        self.assertRedirects(response, reverse("library:library_loans"))
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.status, "returned")
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_loans_page_shows_active_and_history(self):
        Borrowing.objects.create(student=self.student, book=self.book)
        response = self.client.get(reverse("library:library_loans"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BIM-2083-001")


class LibraryAdminViewTest(LibrarySetupMixin):
    def setUp(self):
        super().setUp()
        self.client = Client()
        session = self.client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

    def test_book_list_requires_admin_login(self):
        anon = Client()
        response = anon.get(reverse("library:admin_book_list"))
        self.assertEqual(response.status_code, 302)

    def test_book_add(self):
        response = self.client.post(reverse("library:admin_book_add"), {
            "title": "New Book", "author": "Author",
            "isbn": "978-1234567890", "total_copies": 3, "available_copies": 3,
        })
        self.assertRedirects(response, reverse("library:admin_book_list"))
        self.assertTrue(Book.objects.filter(title="New Book").exists())

    def test_librarian_add(self):
        response = self.client.post(reverse("library:admin_librarian_add"), {
            "username": "librarian2", "full_name": "Second Librarian",
            "is_active": "on",
        })
        self.assertRedirects(response, reverse("library:admin_librarian_list"))
        lib = Librarian.objects.get(username="librarian2")
        self.assertTrue(lib.password.startswith("pbkdf2_sha256$"))

    def test_borrowing_list_shows_student(self):
        Borrowing.objects.create(student=self.student, book=self.book)
        response = self.client.get(reverse("library:admin_borrowing_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BIM-2083-001")

    def test_admin_return_book(self):
        self.book.available_copies = 1
        self.book.save()
        borrowing = Borrowing.objects.create(student=self.student, book=self.book)
        response = self.client.post(reverse("library:admin_return_book", args=[borrowing.id]))
        self.assertRedirects(response, reverse("library:admin_borrowing_list"))
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.status, "returned")
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)