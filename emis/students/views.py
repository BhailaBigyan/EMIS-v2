from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Attendance, Students


def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            student = Students.objects.get(roll_number=username)
            if check_password(password, student.password):
                request.session["student_logged_in"] = True
                request.session["student_id"] = student.student_id
                request.session["student_roll"] = student.roll_number
                request.session["student_name"] = student.full_name
                messages.success(request, f"Welcome back, {student.full_name}!")
                return redirect("students:student_index")
            else:
                return render(request, "students/login.html", {"error": "Invalid roll number or password"})
        except Students.DoesNotExist:
            return render(request, "students/login.html", {"error": "Student account not found"})

    if request.session.get("student_logged_in"):
        return redirect("students:student_index")
    return render(request, "students/login.html")


def _portal_student(request):
    """Fetch the logged-in student for the portal, or None if not logged in."""
    if not request.session.get("student_logged_in"):
        return None
    student_id = request.session.get("student_id")
    return get_object_or_404(Students.objects.select_related('program'), student_id=student_id)


def _current_semester(student):
    """Best-effort lookup of the semester matching the student's current level."""
    from academics.models import Semester
    sem = Semester.objects.filter(
        number=student.current_semester,
        academic_year__end_date__gte=timezone.localdate(),
    ).order_by('-academic_year__start_date').first()
    if not sem:
        sem = Semester.objects.filter(number=student.current_semester).order_by('-id').first()
    return sem


def student_index(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from notices.models import Notice
    notices = Notice.objects.all()[:5]
    context = {
        "student": student,
        "username": student.full_name,
        "notices_count": notices.count(),
        "recent_notices": notices,
    }
    return render(request, "students/student_dashboard.html", context)


def student_logout(request):
    request.session.flush()
    return redirect("students:student_login")


def student_profile(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    grades = student.grades.select_related('exam', 'course').order_by('-exam__start_date')
    payments = student.fee_payments.select_related('fee_structure')[:10]

    return render(request, "students/student_profile.html", {
        "student": student,
        "username": student.full_name,
        "grades": grades,
        "fee_payments": payments,
    })


def student_attendance(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    month = request.GET.get("month", "")
    today = timezone.localdate()
    records = student.attendance_records.all()
    if month:
        try:
            year, m = (int(x) for x in month.split("-"))
            records = records.filter(date__year=year, date__month=m)
        except ValueError:
            month = ""
    if not month:
        records = records.filter(date__year=today.year, date__month=today.month)

    total = records.count()
    summary = {
        'present': records.filter(status='present').count(),
        'late': records.filter(status='late').count(),
        'leave': records.filter(status='leave').count(),
        'absent': records.filter(status='absent').count(),
    }
    present_days = summary['present'] + summary['late']
    percentage = round(present_days / total * 100, 1) if total else 0.0

    return render(request, "students/attendance.html", {
        "student": student,
        "username": student.full_name,
        "records": records,
        "summary": summary,
        "total": total,
        "percentage": percentage,
        "month": month or today.strftime("%Y-%m"),
    })


def student_exams(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from examinations.models import Exam
    semester = _current_semester(student)
    today = timezone.localdate()
    exams = []
    if semester:
        exams = Exam.objects.filter(semester=semester, is_published=True).prefetch_related('schedules__course')
    upcoming = [e for e in exams if e.start_date >= today]
    completed = [e for e in exams if e.end_date < today]

    return render(request, "students/exams.html", {
        "student": student,
        "username": student.full_name,
        "semester": semester,
        "upcoming": upcoming,
        "completed": completed,
        "today": today,
    })


def student_results(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from examinations.models import Result
    results = Result.objects.filter(student=student).select_related('semester').order_by('-semester__number')
    grades = student.grades.select_related('exam', 'course').order_by('-exam__start_date')

    return render(request, "students/results.html", {
        "student": student,
        "username": student.full_name,
        "results": results,
        "grades": grades,
    })


def student_timetable(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from academics.models import Timetable
    semester = _current_semester(student)
    slots = Timetable.objects.none()
    if semester:
        slots = (
            Timetable.objects
            .filter(course_assignment__semester=semester,
                    course_assignment__section=student.section or 'A')
            .select_related('course_assignment__course', 'course_assignment__teacher')
            .order_by('day_of_week', 'start_time')
        )

    days = [('SUN', 'Sunday'), ('MON', 'Monday'), ('TUE', 'Tuesday'),
            ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday')]
    by_day = {code: [] for code, _ in days}
    for s in slots:
        by_day[s.day_of_week].append(s)
    grid = [(code, label, by_day[code]) for code, label in days]
    any_slots = bool(slots)

    return render(request, "students/timetable.html", {
        "student": student,
        "username": student.full_name,
        "semester": semester,
        "grid": grid,
        "any_slots": any_slots,
    })


def student_notices(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from notices.models import Notice
    notices = Notice.objects.all()

    return render(request, "students/notices.html", {
        "student": student,
        "username": student.full_name,
        "notices": notices,
    })


def student_fees(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    accounts = student.fee_accounts.select_related('fee_structure')
    payments = student.fee_payments.select_related('fee_structure')[:15]

    total_due = sum(a.total_due for a in accounts)
    total_paid = sum(a.total_paid for a in accounts)

    return render(request, "students/fees.html", {
        "student": student,
        "username": student.full_name,
        "accounts": accounts,
        "payments": payments,
        "total_due": total_due,
        "total_paid": total_paid,
        "balance": total_due - total_paid,
    })


def student_help(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    return render(request, "students/help.html", {
        "student": student,
        "username": student.full_name,
    })


def student_books(request):
    student = _portal_student(request)
    if not student:
        return redirect("students:student_login")

    from library.models import Borrowing
    active = (
        student.borrowings.filter(status='borrowed')
        .select_related('book', 'issued_by')
    )
    history = (
        student.borrowings.filter(status='returned')
        .select_related('book', 'issued_by')
    )

    total_fine = sum(b.calculate_fine() for b in active)
    overdue_count = sum(1 for b in active if b.is_overdue)

    return render(request, "students/books.html", {
        "student": student,
        "username": student.full_name,
        "active_loans": active,
        "history": history,
        "total_fine": total_fine,
        "overdue_count": overdue_count,
        "loan_period_days": Borrowing.LOAN_PERIOD_DAYS,
        "fine_per_day": Borrowing.FINE_PER_DAY,
    })