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
