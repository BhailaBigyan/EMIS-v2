import io
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.context import Context

# Fix Python 3.14 + Django Context.__copy__ compatibility for test client
def _fixed_copy(self):
    duplicate = Context()
    duplicate.dicts = self.dicts[:]
    return duplicate

Context.__copy__ = _fixed_copy


from academics.models import Department, Program
from students.models import Students
from students.utils import (
    generate_roll_number, parse_csv_file, parse_excel_file,
    bulk_create_students, generate_sample_csv, generate_sample_excel
)


class StudentModelTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.dept,
            duration_years=4,
            total_semesters=8,
            is_active=True
        )

    def test_roll_number_generation(self):
        roll1 = generate_roll_number(self.program, "2081")
        self.assertEqual(roll1, "BCA-2081-001")

        student = Students.objects.create(
            roll_number=roll1,
            first_name="John",
            last_name="Doe",
            gender="M",
            program=self.program,
            batch="2081"
        )
        student.set_default_password()
        student.save()

        roll2 = generate_roll_number(self.program, "2081")
        self.assertEqual(roll2, "BCA-2081-002")

    def test_set_default_password(self):
        student = Students(roll_number="BCA-2081-001", first_name="Jane", last_name="Doe")
        raw_pass = student.set_default_password()
        self.assertEqual(raw_pass, "emis@BCA-2081-001")
        self.assertTrue(student.password.startswith("pbkdf2_sha256$") or len(student.password) > 20)


class StudentUtilsTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.dept,
            is_active=True
        )

    def test_parse_csv_valid(self):
        csv_content = (
            "first_name,last_name,email,phone,date_of_birth,gender,address,guardian_name,guardian_phone\n"
            "Ram,Sharma,ram@example.com,9841234567,2005-03-15,M,Kathmandu,Hari Sharma,9801234567\n"
            "Sita,Gurung,sita@example.com,9851234567,2005-06-20,F,Pokhara,Gita Gurung,9811234567\n"
        ).encode('utf-8')
        file_obj = io.BytesIO(csv_content)
        data, errors = parse_csv_file(file_obj)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['first_name'], 'Ram')
        self.assertEqual(data[1]['gender'], 'F')

    def test_bulk_create_students(self):
        data_list = [
            {
                'first_name': 'Ram',
                'last_name': 'Sharma',
                'email': 'ram@example.com',
                'gender': 'M',
            },
            {
                'first_name': 'Sita',
                'last_name': 'Gurung',
                'email': 'sita@example.com',
                'gender': 'F',
            }
        ]
        created, errors = bulk_create_students(data_list, self.program, "2081")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(created), 2)
        self.assertEqual(created[0]['roll_number'], 'BCA-2081-001')
        self.assertEqual(created[1]['roll_number'], 'BCA-2081-002')
        self.assertEqual(Students.objects.count(), 2)

    def test_generate_sample_files(self):
        csv_sample = generate_sample_csv()
        self.assertIn("first_name", csv_sample)
        self.assertIn("Ram", csv_sample)

        excel_sample = generate_sample_excel()
        self.assertIsNotNone(excel_sample.getvalue())


class StudentViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session['general_logged_in'] = True
        session['general_username'] = 'admin'
        session.save()

        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.dept,
            is_active=True
        )
        self.student = Students.objects.create(
            roll_number="BCA-2081-001",
            first_name="Test",
            last_name="Student",
            gender="M",
            program=self.program,
            batch="2081"
        )

    def test_student_list_view(self):
        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Student")
        self.assertContains(response, "BCA-2081-001")

    def test_student_add_view(self):
        post_data = {
            'first_name': 'New',
            'last_name': 'Student',
            'gender': 'F',
            'program': self.program.id,
            'batch': '2081',
            'current_semester': 1,
            'status': 'active',
        }
        response = self.client.post(reverse('student_add'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Students.objects.filter(first_name='New').exists())
        new_student = Students.objects.get(first_name='New')
        self.assertEqual(new_student.roll_number, 'BCA-2081-002')

    def test_student_edit_view(self):
        edit_url = reverse('student_edit', args=[self.student.student_id])
        response = self.client.post(edit_url, {
            'first_name': 'Updated',
            'last_name': 'Student',
            'gender': 'M',
            'program': self.program.id,
            'batch': '2081',
            'current_semester': 2,
            'status': 'active',
        })
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Updated')
        self.assertEqual(self.student.current_semester, 2)

    def test_student_delete_view(self):
        delete_url = reverse('student_delete', args=[self.student.student_id])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Students.objects.filter(student_id=self.student.student_id).exists())

    def test_student_bulk_upload_csv(self):
        csv_content = (
            "first_name,last_name,email,phone,date_of_birth,gender,address,guardian_name,guardian_phone\n"
            "Bulk1,Student,bulk1@example.com,9841000001,2005-01-01,M,Kathmandu,Guard1,9801000001\n"
            "Bulk2,Student,bulk2@example.com,9841000002,2005-01-02,F,Lalitpur,Guard2,9801000002\n"
        ).encode('utf-8')
        uploaded_file = SimpleUploadedFile("students.csv", csv_content, content_type="text/csv")

        response = self.client.post(reverse('student_bulk_upload'), {
            'file': uploaded_file,
            'program': self.program.id,
            'batch': '2081',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Students.objects.filter(first_name='Bulk1').exists())
        self.assertTrue(Students.objects.filter(first_name='Bulk2').exists())

    def test_student_export_csv(self):
        response = self.client.get(reverse('student_export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertContains(response, 'BCA-2081-001')


class StudentPortalTest(TestCase):
    """Tests for the student-facing portal pages."""

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.dept,
            is_active=True
        )
        self.student = Students.objects.create(
            roll_number="BCA-2081-001",
            first_name="Portal",
            last_name="Student",
            gender="M",
            program=self.program,
            batch="2081",
            email="portal@example.com",
        )
        self.student.set_default_password()
        self.student.save()

        self.notice = None
        from notices.models import Notice
        self.notice = Notice.objects.create(
            title="Holiday Notice",
            content="The college is closed on Friday.",
            category="general",
        )

    def login(self):
        return self.client.post(reverse("students:student_login"), {
            "username": self.student.roll_number,
            "password": "emis@BCA-2081-001",
        })

    def test_login_success(self):
        response = self.login()
        self.assertRedirects(response, reverse("students:student_index"))

    def test_pages_require_login(self):
        for name in ["student_profile", "student_attendance", "student_exams",
                     "student_results", "student_timetable", "student_notices",
                     "student_fees", "student_help"]:
            response = self.client.get(reverse(f"students:{name}"))
            self.assertRedirects(response, reverse("students:student_login"))

    def test_dashboard(self):
        self.login()
        response = self.client.get(reverse("students:student_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.full_name)
        self.assertContains(response, self.student.roll_number)

    def test_profile_page(self):
        self.login()
        response = self.client.get(reverse("students:student_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portal Student")
        self.assertContains(response, "portal@example.com")

    def test_attendance_page(self):
        self.login()
        from django.utils import timezone
        from students.models import Attendance
        Attendance.objects.create(student=self.student, date=timezone.localdate(), status="present")
        Attendance.objects.create(
            student=self.student,
            date=timezone.localdate() - timezone.timedelta(days=1),
            status="absent"
        )
        response = self.client.get(reverse("students:student_attendance"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Attendance Rate")
        self.assertContains(response, "50.0%")

    def test_exams_page(self):
        self.login()
        response = self.client.get(reverse("students:student_exams"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exam Schedule")

    def test_results_page(self):
        self.login()
        response = self.client.get(reverse("students:student_results"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Results")

    def test_timetable_page(self):
        self.login()
        response = self.client.get(reverse("students:student_timetable"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Class Timetable")

    def test_notices_page(self):
        self.login()
        response = self.client.get(reverse("students:student_notices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Holiday Notice")

    def test_fees_page(self):
        self.login()
        response = self.client.get(reverse("students:student_fees"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fee Statement")

    def test_help_page(self):
        self.login()
        response = self.client.get(reverse("students:student_help"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frequently Asked Questions")

    def test_books_page_empty(self):
        self.login()
        response = self.client.get(reverse("students:student_books"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Borrowed Books")

    def test_books_page_with_loans(self):
        from library.models import Book, BookCategory, Borrowing, Librarian
        from datetime import timedelta
        from django.utils import timezone

        category = BookCategory.objects.create(name="Programming")
        book = Book.objects.create(
            title="Django for Beginners", author="Will Vincent",
            category=category, total_copies=2, available_copies=1,
        )
        librarian = Librarian.objects.create(
            username="lib1", full_name="Librarian One"
        )
        active = Borrowing.objects.create(
            student=self.student, book=book, issued_by=librarian
        )
        active.due_date = timezone.localdate() - timedelta(days=3)
        active.save()
        returned = Borrowing.objects.create(
            student=self.student, book=book, issued_by=librarian
        )
        returned.return_date = timezone.localdate()
        returned.status = "returned"
        returned.fine_amount = 10
        returned.save()

        self.login()
        response = self.client.get(reverse("students:student_books"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django for Beginners")
        self.assertContains(response, "Overdue")
        self.assertContains(response, "days overdue")
        self.assertContains(response, "Rs. 15")  # 3 overdue days x Rs. 5
        self.assertContains(response, "Return History")

    def test_topbar_nav_links_present(self):
        self.login()
        response = self.client.get(reverse("students:student_index"))
        for name in ["student_profile", "student_attendance", "student_exams",
                     "student_results", "student_timetable", "student_notices",
                     "student_fees", "student_books", "student_help", "student_logout"]:
            self.assertContains(response, reverse(f"students:{name}"))
