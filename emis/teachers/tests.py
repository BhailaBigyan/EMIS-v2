from django.test import TestCase, Client
from django.urls import reverse
from django.template.context import Context

# Fix Python 3.14 + Django Context.__copy__ compatibility for test client
def _fixed_copy(self):
    duplicate = Context()
    duplicate.dicts = self.dicts[:]
    return duplicate

Context.__copy__ = _fixed_copy


from academics.models import AcademicYear, Course, CourseAssignment, Department, Program, Semester, Timetable
from students.models import Attendance, Students
from teachers.models import LeaveRequest, Teacher
from teachers.views import generate_employee_id


class TeacherModelTest(TestCase):
    def test_employee_id_generation(self):
        self.assertEqual(generate_employee_id(), "TCH-001")
        Teacher.objects.create(employee_id="TCH-001", first_name="Alan", last_name="Turing")
        self.assertEqual(generate_employee_id(), "TCH-002")

    def test_full_name(self):
        teacher = Teacher.objects.create(employee_id="TCH-002", first_name="Grace", last_name="Hopper")
        self.assertEqual(teacher.full_name, "Grace Hopper")


class TeacherViewTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.teacher = Teacher.objects.create(
            employee_id="TCH-001", first_name="Alan", last_name="Turing",
            department=self.dept, designation="professor", is_active=True
        )
        self.client = Client()
        session = self.client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

    def test_list_requires_login(self):
        anon = Client()
        response = anon.get(reverse("teachers:teacher_list"))
        self.assertEqual(response.status_code, 302)

    def test_teacher_list(self):
        response = self.client.get(reverse("teachers:teacher_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alan")

    def test_teacher_add(self):
        response = self.client.post(reverse("teachers:teacher_add"), {
            "employee_id": "TCH-002",
            "first_name": "Ada", "last_name": "Lovelace",
            "gender": "F",
            "department": self.dept.id, "designation": "lecturer",
            "qualification": "MSc", "is_active": "on",
        })
        self.assertRedirects(response, reverse("teachers:teacher_list"))
        self.assertTrue(Teacher.objects.filter(employee_id="TCH-002").exists())

    def test_teacher_edit(self):
        response = self.client.post(reverse("teachers:teacher_edit", args=[self.teacher.id]), {
            "employee_id": "TCH-001",
            "first_name": "Alan", "last_name": "Turing Jr",
            "gender": "M",
            "department": self.dept.id, "designation": "associate_professor",
            "qualification": "PhD", "is_active": "on",
        })
        self.assertRedirects(response, reverse("teachers:teacher_list"))
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.last_name, "Turing Jr")

    def test_teacher_delete(self):
        response = self.client.post(reverse("teachers:teacher_delete", args=[self.teacher.id]))
        self.assertRedirects(response, reverse("teachers:teacher_list"))
        self.assertFalse(Teacher.objects.filter(id=self.teacher.id).exists())

    def test_teacher_detail(self):
        response = self.client.get(reverse("teachers:teacher_detail", args=[self.teacher.id]))
        self.assertEqual(response.status_code, 200)

    def test_teacher_export_csv(self):
        response = self.client.get(reverse("teachers:teacher_export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])


class TeacherPortalTest(TestCase):
    """Tests for the teacher-facing portal."""

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application",
            code="BCA",
            department=self.dept,
            is_active=True,
            total_semesters=8,
        )
        self.year = AcademicYear.objects.create(
            name="2081/082", start_date="2024-08-01", end_date="2025-07-30"
        )
        self.semester = Semester.objects.create(
            academic_year=self.year, name="Semester I", number=1,
            start_date="2024-08-01", end_date="2025-01-30",
        )
        self.course = Course.objects.create(
            name="Programming Fundamentals", code="CMP101",
            program=self.program, semester=1, credit_hours=3,
        )
        self.teacher = Teacher.objects.create(
            employee_id="TCH-001", first_name="Demo", last_name="Teacher",
            department=self.dept, designation="lecturer", is_active=True,
        )
        self.teacher.set_default_password()
        self.teacher.save()
        self.assignment = CourseAssignment.objects.create(
            course=self.course, teacher=self.teacher, semester=self.semester,
            section="A", max_students=60,
        )
        self.student = Students.objects.create(
            roll_number="BCA-2081-001", first_name="Ram", last_name="Sharma",
            gender="M", program=self.program, batch="2081",
            current_semester=1, section="A",
        )

    def login(self):
        return self.client.post(reverse("teachers:teacher_login"), {
            "username": "TCH-001",
            "password": "tch@TCH-001",
        })

    def test_login_success(self):
        response = self.login()
        self.assertRedirects(response, reverse("teachers:teacher_dashboard"))

    def test_login_bad_password(self):
        response = self.client.post(reverse("teachers:teacher_login"), {
            "username": "TCH-001", "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid employee ID or password")

    def test_pages_require_login(self):
        for name in ["teacher_dashboard", "teacher_attendance", "teacher_attendance_records",
                     "teacher_routines", "teacher_leave", "teacher_leave_new",
                     "teacher_profile", "teacher_profile_edit"]:
            response = Client().get(reverse(f"teachers:{name}"))
            self.assertRedirects(response, reverse("teachers:teacher_login"))

    def test_dashboard(self):
        self.login()
        response = self.client.get(reverse("teachers:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Teacher")
        self.assertContains(response, "Assigned Courses")

    def test_mark_attendance(self):
        self.login()
        response = self.client.post(reverse("teachers:teacher_attendance"), {
            "course_assignment": self.assignment.id,
            "date": "2025-09-01",
            f"attendance_{self.student.student_id}": "present",
        })
        self.assertRedirects(response, reverse("teachers:teacher_attendance") + "?course_assignment=1&date=2025-09-01")
        record = Attendance.objects.get(student=self.student, course_assignment=self.assignment, date="2025-09-01")
        self.assertEqual(record.status, "present")

    def test_attendance_page_shows_students(self):
        self.login()
        response = self.client.get(
            reverse("teachers:teacher_attendance"),
            {"course_assignment": self.assignment.id, "date": "2025-09-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ram Sharma")
        self.assertContains(response, "BCA-2081-001")

    def test_attendance_records(self):
        self.login()
        Attendance.objects.create(
            student=self.student, course_assignment=self.assignment,
            date="2025-09-01", status="present",
        )
        response = self.client.get(
            reverse("teachers:teacher_attendance_records"),
            {"course_assignment": self.assignment.id, "month": "2025-09"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ram Sharma")
        self.assertContains(response, "100%")

    def test_leave_request_flow(self):
        self.login()
        response = self.client.post(reverse("teachers:teacher_leave_new"), {
            "leave_type": "sick", "from_date": "2025-10-01",
            "to_date": "2025-10-03", "reason": "Fever",
        })
        self.assertRedirects(response, reverse("teachers:teacher_leave"))
        leave = LeaveRequest.objects.get(teacher=self.teacher)
        self.assertEqual(leave.status, "pending")
        self.assertEqual(leave.days, 3)

        response = self.client.get(reverse("teachers:teacher_leave"))
        self.assertContains(response, "Sick Leave")
        self.assertContains(response, "Pending")

    def test_leave_form_validation(self):
        self.login()
        response = self.client.post(reverse("teachers:teacher_leave_new"), {
            "leave_type": "casual", "from_date": "2025-10-10",
            "to_date": "2025-10-01", "reason": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be before")

    def test_admin_leave_decision(self):
        leave = LeaveRequest.objects.create(
            teacher=self.teacher, leave_type="casual",
            from_date="2025-10-01", to_date="2025-10-01", reason="Personal",
        )
        admin = Client()
        session = admin.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

        response = admin.post(
            reverse("teachers:teacher_leave_decision", args=[leave.id]),
            {"action": "approve", "admin_remarks": "Granted"},
        )
        self.assertRedirects(response, reverse("teachers:teacher_leave_admin"))
        leave.refresh_from_db()
        self.assertEqual(leave.status, "approved")
        self.assertEqual(leave.admin_remarks, "Granted")

        response = admin.get(reverse("teachers:teacher_leave_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Teacher")

    def test_profile_edit(self):
        self.login()
        response = self.client.post(reverse("teachers:teacher_profile_edit"), {
            "first_name": "Demo", "last_name": "Updated",
            "gender": "M", "email": "demo@example.com", "phone": "9800000111",
            "qualification": "PhD", "specialization": "AI",
        })
        self.assertRedirects(response, reverse("teachers:teacher_profile"))
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.last_name, "Updated")
        self.assertEqual(self.teacher.specialization, "AI")

    def test_routines_page(self):
        self.login()
        Timetable.objects.create(
            course_assignment=self.assignment, day_of_week="MON",
            start_time="09:00", end_time="10:30", room="Lab 2",
        )
        response = self.client.get(reverse("teachers:teacher_routines"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programming Fundamentals")
        self.assertContains(response, "Lab 2")

    def test_dashboard_today_slots(self):
        self.login()
        from django.utils import timezone
        day_codes = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SUN']
        Timetable.objects.create(
            course_assignment=self.assignment,
            day_of_week=day_codes[timezone.localdate().weekday()],
            start_time="09:00", end_time="10:30", room="Lab 2",
        )
        response = self.client.get(reverse("teachers:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programming Fundamentals")