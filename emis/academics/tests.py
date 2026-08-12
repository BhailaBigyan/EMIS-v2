from django.test import TestCase, Client
from django.urls import reverse
from teachers.models import Teacher
from academics.models import Department, Program, Course, AcademicYear, Semester, CourseAssignment, Timetable, Batch


class AcademicsModelsTestCase(TestCase):
    def setUp(self):
        self.teacher = Teacher.objects.create(
            employee_id="T101",
            first_name="Dr. John",
            last_name="Doe",
            email="john@example.com",
            designation="professor"
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            head=self.teacher
        )
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.department,
            duration_years=4,
            total_semesters=8
        )
        self.course = Course.objects.create(
            name="Data Structures",
            code="CACS151",
            program=self.program,
            credit_hours=3,
            semester=2
        )
        self.batch = Batch.objects.create(
            name="2081",
            program=self.program,
            start_year=2024
        )
        self.year = AcademicYear.objects.create(
            name="2081/2082",
            start_date="2024-01-01",
            end_date="2024-12-31",
            is_current=True
        )
        self.semester = Semester.objects.create(
            academic_year=self.year,
            name="Spring 2026",
            number=1,
            start_date="2024-01-01",
            end_date="2024-06-30",
            is_current=True
        )
        self.assignment = CourseAssignment.objects.create(
            course=self.course,
            teacher=self.teacher,
            semester=self.semester,
            section="A"
        )
        self.timetable = Timetable.objects.create(
            course_assignment=self.assignment,
            day_of_week="MON",
            start_time="09:00:00",
            end_time="10:00:00",
            room="Room 101"
        )

    def test_string_representations(self):
        self.assertEqual(str(self.department), "CS - Computer Science")
        self.assertEqual(str(self.program), "BCA - Bachelor in Computer Application")
        self.assertEqual(str(self.course), "CACS151 - Data Structures")
        self.assertEqual(str(self.batch), "2081 (BCA)")
        self.assertEqual(str(self.year), "2081/2082")
        self.assertEqual(str(self.semester), "Spring 2026 (2081/2082)")
        self.assertEqual(str(self.assignment), "CACS151 - Dr. John Doe (Sec A)")
        self.assertIn("CACS151", str(self.timetable))

    def test_academic_year_current_toggle(self):
        year2 = AcademicYear.objects.create(
            name="2082/2083",
            start_date="2025-01-01",
            end_date="2025-12-31",
            is_current=True
        )
        self.year.refresh_from_db()
        self.assertFalse(self.year.is_current)
        self.assertTrue(year2.is_current)


class AcademicsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Session for admin login decorator
        session = self.client.session
        session['admin_logged_in'] = True
        session.save()

        self.teacher = Teacher.objects.create(
            employee_id="T102",
            first_name="Jane",
            last_name="Smith"
        )
        self.department = Department.objects.create(
            name="Information Technology",
            code="IT"
        )
        self.program = Program.objects.create(
            name="BSc CSIT",
            code="BSCCSIT",
            department=self.department
        )
        self.course = Course.objects.create(
            name="Discrete Structures",
            code="CSC109",
            program=self.program,
            credit_hours=3,
            semester=1
        )
        self.year = AcademicYear.objects.create(
            name="2080/2081",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        self.semester = Semester.objects.create(
            academic_year=self.year,
            name="Fall 2025",
            number=1,
            start_date="2023-01-01",
            end_date="2023-06-30"
        )

    def test_department_crud(self):
        # List
        res = self.client.get(reverse('academics:department_list'))
        self.assertEqual(res.status_code, 200)

        # Add
        res = self.client.post(reverse('academics:department_add'), {
            'name': 'Management',
            'code': 'MGMT',
            'description': 'Management dept'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Department.objects.filter(code='MGMT').exists())

        # Edit
        res = self.client.post(reverse('academics:department_edit', args=[self.department.id]), {
            'name': 'IT & CS Department',
            'code': 'IT',
            'description': 'Updated'
        })
        self.assertEqual(res.status_code, 302)
        self.department.refresh_from_db()
        self.assertEqual(self.department.name, 'IT & CS Department')

        # Delete
        res = self.client.post(reverse('academics:department_delete', args=[self.department.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Department.objects.filter(id=self.department.id).exists())

    def test_program_crud(self):
        res = self.client.get(reverse('academics:program_list'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('academics:program_add'), {
            'name': 'Bachelor of Business Information',
            'code': 'BIT',
            'department': self.department.id,
            'duration_years': 4,
            'total_semesters': 8,
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Program.objects.filter(code='BIT').exists())

    def test_course_crud(self):
        res = self.client.get(reverse('academics:course_list'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('academics:course_add'), {
            'name': 'Object Oriented Programming',
            'code': 'CACS152',
            'program': self.program.id,
            'credit_hours': 3,
            'semester': 2,
            'is_elective': False
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Course.objects.filter(code='CACS152').exists())

    def test_batch_crud(self):
        res = self.client.get(reverse('academics:batch_list'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('academics:batch_add'), {
            'name': '2082',
            'program': self.program.id,
            'start_year': 2025,
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Batch.objects.filter(name='2082').exists())

    def test_assignment_crud(self):
        res = self.client.get(reverse('academics:assignment_list'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('academics:assignment_add'), {
            'course': self.course.id,
            'teacher': self.teacher.id,
            'semester': self.semester.id,
            'section': 'B',
            'max_students': 50
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(CourseAssignment.objects.filter(section='B').exists())

    def test_unauthenticated_access(self):
        client = Client()  # No session login
        res = client.get(reverse('academics:department_list'))
        self.assertEqual(res.status_code, 302)  # Redirects to login
