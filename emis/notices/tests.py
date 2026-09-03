from django.test import TestCase, Client
from django.urls import reverse
from django.template.context import Context

# Fix Python 3.14 + Django Context.__copy__ compatibility for test client
def _fixed_copy(self):
    duplicate = Context()
    duplicate.dicts = self.dicts[:]
    return duplicate

Context.__copy__ = _fixed_copy


from notices.models import Notice
from notices.forms import NoticeForm


class NoticeModelTest(TestCase):
    def test_create_notice(self):
        notice = Notice.objects.create(
            title="Final Exam Schedule",
            content="All exams start next week.",
            category="exam",
            is_important=True
        )
        self.assertEqual(notice.published_date, notice.created_at.date())
        self.assertIn("Examination", str(notice))

    def test_ordering_newest_first(self):
        n1 = Notice.objects.create(title="Old", content="a")
        n2 = Notice.objects.create(title="New", content="b")
        self.assertEqual(list(Notice.objects.all()), [n2, n1])


class NoticeFormTest(TestCase):
    def test_valid_form(self):
        form = NoticeForm(data={
            "title": "Holiday Notice",
            "content": "College closed tomorrow.",
            "category": "general",
            "is_important": False,
        })
        self.assertTrue(form.is_valid())

    def test_requires_title_and_content(self):
        form = NoticeForm(data={"category": "general"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("content", form.errors)


class NoticeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["general_logged_in"] = True
        session["general_username"] = "admin"
        session.save()

    def test_notice_list_shows_notices(self):
        Notice.objects.create(title="Admission Open", content="Apply now.", category="academic")
        response = self.client.get(reverse("notices:notice_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admission Open")

    def test_notice_list_requires_login(self):
        anon = Client()
        response = anon.get(reverse("notices:notice_list"))
        self.assertEqual(response.status_code, 302)

    def test_notice_add(self):
        response = self.client.post(reverse("notices:notice_add"), {
            "title": "New Notice",
            "content": "Body text",
            "category": "event",
            "is_important": True,
        })
        self.assertRedirects(response, reverse("notices:notice_list"))
        self.assertTrue(Notice.objects.filter(title="New Notice").exists())

    def test_notice_edit(self):
        notice = Notice.objects.create(title="Before", content="x")
        response = self.client.post(reverse("notices:notice_edit", args=[notice.id]), {
            "title": "After",
            "content": "y",
            "category": "general",
            "is_important": False,
        })
        self.assertRedirects(response, reverse("notices:notice_list"))
        notice.refresh_from_db()
        self.assertEqual(notice.title, "After")

    def test_notice_delete(self):
        notice = Notice.objects.create(title="Temp", content="z")
        response = self.client.post(reverse("notices:notice_delete", args=[notice.id]))
        self.assertRedirects(response, reverse("notices:notice_list"))
        self.assertFalse(Notice.objects.filter(id=notice.id).exists())