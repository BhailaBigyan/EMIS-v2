import json

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
from notices.models import Notice
from students.models import Students
from teachers.models import Teacher


class AssistantPagesTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(
            name="Bachelor in Computer Application", code="BCA",
            department=self.dept, is_active=True, total_semesters=8,
        )
        self.student = Students.objects.create(
            roll_number="BCA-2081-001", first_name="Ram", last_name="Sharma",
            gender="M", program=self.program, batch="2081",
        )
        self.student.set_default_password()
        self.student.save()

        self.teacher = Teacher.objects.create(
            employee_id="TCH-001", first_name="Demo", last_name="Teacher",
            department=self.dept, designation="lecturer", is_active=True,
        )
        self.teacher.set_default_password()
        self.teacher.save()

    def test_admin_page_requires_login(self):
        response = Client().get(reverse("assistant"))
        self.assertEqual(response.status_code, 302)

    def test_admin_page_renders(self):
        client = Client()
        session = client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()
        response = client.get(reverse("assistant"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMIS AI Assistant")
        self.assertContains(response, "aiShell")

    def test_student_page_requires_login(self):
        response = Client().get(reverse("students:assistant"))
        self.assertRedirects(response, reverse("students:student_login"))

    def test_student_page_renders(self):
        client = Client()
        response = client.post(reverse("students:student_login"), {
            "username": "BCA-2081-001", "password": "emis@BCA-2081-001",
        })
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse("students:assistant"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMIS AI Assistant")
        self.assertContains(response, "Ram Sharma")

    def test_teacher_page_requires_login(self):
        response = Client().get(reverse("teachers:assistant"))
        self.assertRedirects(response, reverse("teachers:teacher_login"))

    def test_teacher_page_renders(self):
        client = Client()
        response = client.post(reverse("teachers:teacher_login"), {
            "username": "TCH-001", "password": "tch@TCH-001",
        })
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse("teachers:assistant"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMIS AI Assistant")
        self.assertContains(response, "Demo Teacher")


def _full_text(response):
    """Collect streamed token texts into a single string."""
    body = "".join(chunk.decode() for chunk in response.streaming_content)
    text = []
    for line in body.splitlines():
        if not line.startswith("data:"):
            continue
        payload = json.loads(line[len("data:"):].strip())
        if payload.get("type") == "token":
            text.append(payload["text"])
    return body, "".join(text)


class AssistantApiTest(TestCase):
    def test_api_requires_post(self):
        client = Client()
        response = client.get(reverse("assistant:chat_api"))
        self.assertEqual(response.status_code, 405)

    def test_api_empty_messages_rejected(self):
        client = Client()
        response = client.post(
            reverse("assistant:chat_api"),
            data=json.dumps({"messages": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_invalid_json_rejected(self):
        client = Client()
        response = client.post(
            reverse("assistant:chat_api"),
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_streams_demo_answer(self):
        Notice.objects.create(
            title="Exam Schedule Published", content="Mid-term exams start Monday.",
            category="exam", is_important=True,
        )
        client = Client()
        response = client.post(
            reverse("assistant:chat_api"),
            data=json.dumps({"messages": [{"role": "user", "content": "What are the latest notices?"}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])

        body, text = _full_text(response)
        self.assertIn('"type": "tool"', body)
        self.assertIn("Consulting EMIS records", body)
        self.assertIn("Exam Schedule Published", text)
        self.assertIn('"type": "done"', body)

    def test_api_grounds_context_from_db(self):
        client = Client()
        response = client.post(
            reverse("assistant:chat_api"),
            data=json.dumps({"messages": [{"role": "user", "content": "hello"}]}),
            content_type="application/json",
        )
        _, text = _full_text(response)
        self.assertIn("Khwopa Engineering College", text)