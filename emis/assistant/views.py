import json
import time
import urllib.request
import urllib.error

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from emis.decorators import admin_login_required

COLLEGE_NAME = "Khwopa Engineering College"


def _build_system_prompt():
    """Ground the assistant with live EMIS data so answers are real, not generic."""
    from academics.models import Department, Program
    from finances.models import FeeStructure
    from library.models import Book, Borrowing
    from notices.models import Notice
    from students.models import Students
    from teachers.models import Teacher

    lines = [
        f"You are the AI Assistant of {COLLEGE_NAME}, Bhaktapur, Nepal. "
        "Answer students, teachers, and staff questions about the college. "
        "Be concise, friendly, and use Markdown (headings, bullet lists, bold) when helpful. "
        "If you do not know something, say so and suggest whom to contact instead of guessing.",
        "",
        "## Live college context (from the EMIS database)",
        f"- Departments: {', '.join(d.code for d in Department.objects.all()[:10]) or 'none'}",
        "- Programs: " + (
            ", ".join(f"{p.code} ({p.department.code if p.department else 'N/A'})"
                      for p in Program.objects.all()[:12]) or "none"
        ),
        f"- Students: {Students.objects.count()} total "
        f"({Students.objects.filter(status='active').count()} active)",
        f"- Teachers: {Teacher.objects.filter(is_active=True).count()} active",
        f"- Library: {Book.objects.count()} titles, "
        f"{sum(b.available_copies for b in Book.objects.all())} copies available, "
        f"{Borrowing.objects.filter(status='borrowed').count()} books on loan",
    ]

    fees = FeeStructure.objects.all()[:5]
    if fees:
        lines.append("- Fee structures: " + ", ".join(
            f"{f.name} (Rs. {f.tuition_fee + f.lab_fee + f.library_fee + f.exam_fee + f.other_fee})"
            for f in fees
        ))

    notices = Notice.objects.all()[:5]
    if notices:
        lines.append("- Latest notices: " + "; ".join(
            f"{n.title} ({n.published_date})" for n in notices
        ))

    lines.append(
        "Portal logins: students use their roll number (default password emis@<roll>), "
        "teachers use employee ID (default tch@<employee_id>), librarians use their username "
        "(default library@<username>), admins use the admin account."
    )
    return "\n".join(lines)


def _demo_answer(prompt):
    """Keyword-driven canned answer built from live DB data (used when no AI key is configured)."""
    from academics.models import Department, Program
    from finances.models import FeeStructure
    from library.models import Book, BookCategory
    from notices.models import Notice
    from students.models import Students
    from teachers.models import Teacher
    from datetime import date

    text = prompt.lower()

    if any(k in text for k in ["notice", "announcement", "news"]):
        notices = Notice.objects.all()[:6]
        if not notices:
            return "There are no published notices right now.\n\nCheck back later, or ask the administration office at admin@emis.edu.np."
        lines = ["## Latest Notices", ""]
        for n in notices:
            lines.append(f"- **[{n.get_category_display()}]** {n.title} — *{n.published_date}*")
            if n.is_important:
                lines[-1] += " ⚠️ Important"
        return "\n".join(lines)

    if any(k in text for k in ["program", "course", "faculty", "department"]):
        lines = ["## Programs Offered", ""]
        for p in Program.objects.all():
            lines.append(
                f"- **{p.name}** ({p.code}) — {p.department.name if p.department else 'General'}, "
                f"{p.duration_years} years, {p.total_semesters} semesters"
            )
        return "\n".join(lines) if len(lines) > 2 else "No programs are configured in the system yet."

    if any(k in text for k in ["fee", "payment", "cost", "tuition", "admission fee"]):
        fees = FeeStructure.objects.all()[:6]
        if not fees:
            return "No fee structures are published yet. Please contact the accounts office (accounts@emis.edu.np) for fee details."
        lines = ["## Fee Structures", ""]
        for f in fees:
            total = f.tuition_fee + f.lab_fee + f.library_fee + f.exam_fee + f.other_fee
            lines.append(f"- **{f.name}**: Rs. {total} "
                         f"(tuition {f.tuition_fee}, lab {f.lab_fee}, library {f.library_fee}, "
                         f"exam {f.exam_fee}, other {f.other_fee})")
        lines.append("")
        lines.append("You can view your own fee statement in the **Fees** section of the student portal.")
        return "\n".join(lines)

    if any(k in text for k in ["book", "library", "borrow"]):
        cats = BookCategory.objects.all()
        lines = ["## Library at a Glance", ""]
        for c in cats:
            count = c.books.count()
            lines.append(f"- **{c.name}**: {count} title(s)")
        lines.append("")
        lines.append(f"- Total titles: {Book.objects.count()}")
        lines.append("- Books are issued by the **librarian** at the circulation desk (loan period 14 days, fine Rs. 5/day overdue).")
        lines.append("- Students can see their issued books, due dates, and fines under **My Books**.")
        return "\n".join(lines)

    if any(k in text for k in ["attendance"]):
        active = Students.objects.filter(status='active').count()
        return (f"## Attendance\n\n- Teachers mark attendance per class in the **teacher portal** "
                f"(Mark Attendance).\n- Students can view their monthly records and attendance rate "
                f"in the **Attendance** section of the student portal.\n"
                f"- There are currently **{active} active students** in the system.\n"
                f"- A rate below **75%** is flagged as a risk on the student portal.")

    if any(k in text for k in ["exam", "result", "grade"]):
        return ("## Exams & Results\n\n- Published exam schedules appear under **Exams** in the student portal "
                "(dates, rooms, and invigilators per course).\n- Semester results with GPA, percentage, and rank "
                "are shown under **Results**.\n- The examination office publishes results; check back after the exam window.")

    if any(k in text for k in ["timetable", "routine", "class schedule"]):
        return ("## Class Timetable\n\n- Students: **Timetable** section in the student portal "
                "(weekly grid by day, room, and teacher).\n- Teachers: **My Routines** in the teacher portal "
                "(assigned courses + weekly teaching schedule).\n- Timetables are published by the academics office.")

    if any(k in text for k in ["teacher", "staff", "faculty count"]):
        total = Teacher.objects.count()
        active = Teacher.objects.filter(is_active=True).count()
        return (f"## Faculty\n\n- **{total}** teacher(s) on record, **{active}** active.\n"
                f"- Teachers log in with their **employee ID** (e.g. TCH-001) at the Teacher Portal "
                f"to mark attendance, view routines, and request leave.")

    if any(k in text for k in ["login", "password", "sign in", "account"]):
        return ("## Portal Access\n\n- **Students**: roll number + password (default `emis@<roll_number>`)\n"
                "- **Teachers**: employee ID + password (default `tch@<employee_id>`)\n"
                "- **Librarians**: username + password (default `library@<username>`)\n"
                "- **Admin**: admin account credentials\n\n"
                "Contact the administration office if you have forgotten your password.")

    if any(k in text for k in ["leave"]):
        return ("## Leave Requests\n\n- Teachers can apply for leave (casual, sick, annual, unpaid) "
                "from the **Leave** section of the teacher portal.\n- Requests are reviewed by the "
                "administration under **Faculty & Staff → Leave Requests** in the admin dashboard.\n"
                "- You can track the status of each request (pending / approved / rejected) in the same section.")

    if any(k in text for k in ["hello", "hi ", "hey", "namaste"]):
        return (f"Namaste! 👋 I'm the AI Assistant of {COLLEGE_NAME}.\n\n"
                "I can help you with:\n\n- **Notices** — the latest announcements\n"
                "- **Programs & fees** — what we offer and how much it costs\n"
                "- **Exams, results & timetable** — schedules and scores\n"
                "- **Library** — borrowing, due dates, and fines\n"
                "- **Portals** — how to log in as student, teacher, or staff\n\n"
                "Try asking: *\"What are the latest notices?\"* or *\"How much are the fees?\"*")

    total_students = Students.objects.count()
    return (f"Here's a snapshot of {COLLEGE_NAME} right now:\n\n"
            f"- **Students:** {total_students} on record "
            f"({Students.objects.filter(status='active').count()} active)\n"
            f"- **Teachers:** {Teacher.objects.filter(is_active=True).count()} active\n"
            f"- **Library:** {Book.objects.count()} titles available\n"
            f"- **Date:** {date.today().strftime('%B %d, %Y')}\n\n"
            "Try asking me about *notices*, *programs*, *fees*, *exams*, *attendance*, "
            "or *library books* — I'll pull the latest data from the college database.")


def _stream_openai(messages):
    """Stream tokens from an OpenAI-compatible chat/completions endpoint."""
    url = settings.AI_BASE_URL.rstrip('/') + '/chat/completions'
    body = json.dumps({
        "model": settings.AI_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
    }).encode('utf-8')
    req = urllib.request.Request(
        url, data=body, method='POST',
        headers={
            'Authorization': f'Bearer {settings.AI_API_KEY}',
            'Content-Type': 'application/json',
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        for raw in resp:
            line = raw.decode('utf-8', errors='replace').strip()
            if not line.startswith('data:'):
                continue
            payload = line[len('data:'):].strip()
            if payload == '[DONE]':
                break
            try:
                delta = json.loads(payload)['choices'][0]['delta'].get('content', '')
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                continue
            if delta:
                yield delta


def _event(e):
    return f"data: {json.dumps(e)}\n\n"


@require_POST
def chat_api(request):
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request body.'}, status=400)

    messages = payload.get('messages', [])
    valid = [m for m in messages if isinstance(m, dict) and m.get('role') in ('user', 'assistant') and m.get('content')]
    if not valid:
        return JsonResponse({'error': 'No messages provided.'}, status=400)

    conversation = [{'role': 'system', 'content': _build_system_prompt()}] + valid[-20:]

    def stream():
        try:
            yield _event({'type': 'tool', 'label': 'Consulting EMIS records'})
            time.sleep(0.5)

            if settings.AI_API_KEY:
                try:
                    for token in _stream_openai(conversation):
                        yield _event({'type': 'token', 'text': token})
                except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
                    friendly = (
                        "I couldn't reach the AI service right now. "
                        "Please try again in a moment, or check the AI configuration with the system administrator."
                    )
                    yield _event({'type': 'error', 'message': friendly, 'detail': str(exc)})
                    return
            else:
                last_user = next((m['content'] for m in reversed(valid) if m['role'] == 'user'), '')
                answer = _demo_answer(last_user)
                for word in answer.split(' '):
                    yield _event({'type': 'token', 'text': word + ' '})
                    time.sleep(0.04)

            yield _event({'type': 'done'})
        except Exception as exc:  # pragma: no cover - safety net
            yield _event({'type': 'error', 'message': 'Something unexpected went wrong. Please try again.'})

    return StreamingHttpResponse(stream(), content_type='text/event-stream')


# ---------------------------------------------------------
# Portal page views
# ---------------------------------------------------------

def _assistant_context(request, name, initials):
    return {
        'api_url': '/assistant/api/chat/',
        'assistant_name': name,
        'assistant_initials': initials,
    }


@admin_login_required
def admin_assistant(request):
    ctx = _assistant_context(request, request.session.get('general_username', 'Admin'), 'AD')
    return render(request, 'assistant/admin_chat.html', ctx)


def student_assistant(request):
    if not request.session.get('student_logged_in'):
        return redirect('students:student_login')
    student_id = request.session.get('student_id')
    from students.models import Students
    from django.shortcuts import get_object_or_404
    student = get_object_or_404(Students, student_id=student_id)
    ctx = _assistant_context(
        request, student.full_name,
        f"{student.first_name[:1]}{student.last_name[:1]}".upper() or 'ST',
    )
    ctx['student'] = student
    return render(request, 'assistant/student_chat.html', ctx)


def teacher_assistant(request):
    if not request.session.get('teacher_logged_in'):
        return redirect('teachers:teacher_login')
    teacher_id = request.session.get('teacher_id')
    from django.shortcuts import get_object_or_404
    from teachers.models import Teacher
    teacher = get_object_or_404(Teacher, id=teacher_id)
    ctx = _assistant_context(
        request, teacher.full_name,
        f"{teacher.first_name[:1]}{teacher.last_name[:1]}".upper() or 'TCH',
    )
    ctx['teacher'] = teacher
    return render(request, 'assistant/teacher_chat.html', ctx)