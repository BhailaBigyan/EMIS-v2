from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.template.context import Context

# Fix Python 3.14 + Django Context.__copy__ compatibility for test client
def _fixed_copy(self):
    duplicate = Context()
    duplicate.dicts = self.dicts[:]
    return duplicate

Context.__copy__ = _fixed_copy


from academics.models import Department, Program, Course, AcademicYear, Semester
from students.models import Students
from examinations.models import Exam, ExamSchedule, Grade, Result


class ExamSetupMixin(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="BCA", code="BCA", department=self.dept, duration_years=4, total_semesters=8, is_active=True
        )
        self.course = Course.objects.create(name="Programming", code="CSC101", program=self.program, semester=1)
        self.year = AcademicYear.objects.create(name="2081/2082", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        self.semester = Semester.objects.create(
            academic_year=self.year, name="First Semester", number=1,
            start_date=date(2025, 1, 1), end_date=date(2025, 6, 30), is_current=True
        )
        self.exam = Exam.objects.create(
            name="Final", exam_type="final", semester=self.semester,
            start_date=date(2025, 3, 1), end_date=date(2025, 3, 15),
            total_marks=100, pass_marks=40
        )
        self.student = Students.objects.create(
            roll_number="BCA-2081-001", first_name="Ram", last_name="Sharma",
            gender="M", program=self.program, batch="2081", current_semester=1, status="active"
        )
        self.student.set_default_password()
        self.student.save()


class ExamModelTest(ExamSetupMixin):
    def test_grade_letter_computed(self):
        grade = Grade.objects.create(
            student=self.student, exam=self.exam, course=self.course, marks_obtained=92
        )
        self.assertEqual(grade.grade_letter, "A+")

    def test_grade_letter_fail(self):
        grade = Grade.objects.create(
            student=self.student, exam=self.exam, course=self.course, marks_obtained=25
        )
        self.assertEqual(grade.grade_letter, "F")

    def test_grade_unique_constraint(self):
        Grade.objects.create(student=self.student, exam=self.exam, course=self.course, marks_obtained=60)
        with self.assertRaises(Exception):
            Grade.objects.create(student=self.student, exam=self.exam, course=self.course, marks_obtained=70)


class ExamViewTest(ExamSetupMixin):
    def setUp(self):
        super().setUp()
        self.client = Client()
        session = self.client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

    def test_exam_list_requires_login(self):
        anon = Client()
        response = anon.get(reverse("examinations:exam_list"))
        self.assertEqual(response.status_code, 302)

    def test_exam_list(self):
        response = self.client.get(reverse("examinations:exam_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Final")

    def test_exam_create(self):
        response = self.client.post(reverse("examinations:exam_create"), {
            "name": "Mid Term", "exam_type": "first_assessment",
            "semester": self.semester.id,
            "start_date": "2025-02-01", "end_date": "2025-02-10",
            "total_marks": 50, "pass_marks": 20,
        })
        self.assertRedirects(response, reverse("examinations:exam_list"))
        self.assertTrue(Exam.objects.filter(name="Mid Term").exists())

    def test_schedule_add(self):
        response = self.client.post(reverse("examinations:schedule_add", args=[self.exam.id]), {
            "exam": self.exam.id,
            "course": self.course.id,
            "date": "2025-03-02", "start_time": "10:00", "end_time": "13:00",
            "room": "Hall A",
        })
        self.assertRedirects(response, reverse("examinations:schedule_list", args=[self.exam.id]))
        self.assertTrue(ExamSchedule.objects.filter(exam=self.exam).exists())

    def test_grade_entry(self):
        response = self.client.post(reverse("examinations:grade_entry", args=[self.exam.id, self.course.id]), {
            f"marks_{self.student.student_id}": "85",
        })
        self.assertRedirects(response, reverse("examinations:exam_list"))
        grade = Grade.objects.get(student=self.student, exam=self.exam, course=self.course)
        self.assertEqual(float(grade.marks_obtained), 85.0)
        self.assertEqual(grade.grade_letter, "A")

    def test_grade_entry_ignores_invalid_marks(self):
        response = self.client.post(reverse("examinations:grade_entry", args=[self.exam.id, self.course.id]), {
            f"marks_{self.student.student_id}": "not-a-number",
        })
        self.assertRedirects(response, reverse("examinations:exam_list"))
        self.assertFalse(Grade.objects.filter(student=self.student).exists())

    def test_result_generate(self):
        Grade.objects.create(student=self.student, exam=self.exam, course=self.course, marks_obtained=75)
        response = self.client.post(reverse("examinations:result_generate"), {"semester": self.semester.id})
        self.assertRedirects(response, reverse("examinations:result_list"))
        result = Result.objects.get(student=self.student, semester=self.semester)
        self.assertEqual(float(result.percentage), 75.0)
        self.assertTrue(result.published)
        self.assertEqual(result.status, "pass")

    def test_report_card(self):
        Grade.objects.create(student=self.student, exam=self.exam, course=self.course, marks_obtained=75)
        response = self.client.get(reverse("examinations:report_card_view", args=[self.student.student_id, self.semester.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programming")