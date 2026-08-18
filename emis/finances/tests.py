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


from academics.models import Department, Program, AcademicYear
from students.models import Students
from finances.models import FeeStructure, FeePayment, StudentFeeAccount, Salary


class FinanceSetupMixin(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Management", code="MGMT")
        self.program = Program.objects.create(
            name="BIM", code="BIM", department=self.dept, duration_years=4, total_semesters=8, is_active=True
        )
        self.year = AcademicYear.objects.create(name="2081/2082", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        self.fee_structure = FeeStructure.objects.create(
            name="BIM Sem 1 Fee", program=self.program, semester=1, academic_year=self.year,
            tuition_fee=50000, lab_fee=10000, library_fee=2000, exam_fee=3000, other_fee=0
        )
        self.student = Students.objects.create(
            roll_number="BIM-2081-001", first_name="Ram", last_name="Sharma",
            gender="M", program=self.program, batch="2081", current_semester=1, status="active"
        )


class FinanceModelTest(FinanceSetupMixin):
    def test_fee_structure_total(self):
        self.assertEqual(self.fee_structure.total_fee, 65000)

    def test_payment_receipt_auto_generated(self):
        payment = FeePayment.objects.create(
            student=self.student, fee_structure=self.fee_structure,
            amount_paid=65000, payment_date=date(2025, 2, 1)
        )
        self.assertTrue(payment.receipt_number.startswith("RCP-"))

    def test_fee_account_balance(self):
        account = StudentFeeAccount.objects.create(
            student=self.student, fee_structure=self.fee_structure,
            total_due=65000, total_paid=30000
        )
        self.assertEqual(account.balance, 35000)
        self.assertFalse(account.is_fully_paid)

        account.total_paid = 65000
        account.save()
        self.assertTrue(account.is_fully_paid)

    def test_salary_net(self):
        from teachers.models import Teacher
        teacher = Teacher.objects.create(employee_id="TCH-001", first_name="A", last_name="B")
        salary = Salary.objects.create(
            teacher=teacher,
            month="August 2026", base_salary=50000, allowances=5000, deductions=2000
        )
        self.assertEqual(salary.net_salary, 53000)


class FinanceViewTest(FinanceSetupMixin):
    def setUp(self):
        super().setUp()
        self.client = Client()
        session = self.client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

    def test_fee_structure_list_requires_login(self):
        anon = Client()
        response = anon.get(reverse("finances:fee_structure_list"))
        self.assertEqual(response.status_code, 302)

    def test_fee_structure_list(self):
        response = self.client.get(reverse("finances:fee_structure_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BIM Sem 1 Fee")

    def test_fee_structure_add(self):
        response = self.client.post(reverse("finances:fee_structure_add"), {
            "name": "BIM Sem 2 Fee", "program": self.program.id, "semester": 2,
            "academic_year": self.year.id, "tuition_fee": 55000, "lab_fee": 10000,
            "library_fee": 2000, "exam_fee": 3000, "other_fee": 0,
        })
        self.assertRedirects(response, reverse("finances:fee_structure_list"))
        self.assertTrue(FeeStructure.objects.filter(name="BIM Sem 2 Fee").exists())

    def test_record_payment_updates_account(self):
        response = self.client.post(reverse("finances:record_payment"), {
            "student": self.student.student_id,
            "fee_structure": self.fee_structure.id,
            "amount_paid": 65000,
            "payment_date": "2025-02-01",
            "payment_method": "cash",
            "status": "paid",
            "transaction_id": "",
            "remarks": "",
        })
        payment = FeePayment.objects.get(student=self.student)
        self.assertRedirects(response, reverse("finances:payment_receipt", args=[payment.id]))
        account = StudentFeeAccount.objects.get(student=self.student)
        self.assertEqual(account.total_paid, 65000)
        self.assertTrue(account.is_fully_paid)

    def test_payment_receipt_page(self):
        payment = FeePayment.objects.create(
            student=self.student, fee_structure=self.fee_structure,
            amount_paid=10000, payment_date=date(2025, 2, 1)
        )
        response = self.client.get(reverse("finances:payment_receipt", args=[payment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, payment.receipt_number)

    def test_finance_dashboard(self):
        response = self.client.get(reverse("finances:finance_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_student_fee_status_search(self):
        response = self.client.get(reverse("finances:student_fee_status"), {"q": "BIM-2081-001"})
        self.assertEqual(response.status_code, 200)