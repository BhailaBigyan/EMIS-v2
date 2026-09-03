import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from emis.decorators import admin_login_required
from academics.models import CourseAssignment, Department
from students.models import Attendance
from .models import LeaveRequest, Teacher
from .forms import LeaveRequestForm, TeacherForm, TeacherProfileForm


def generate_employee_id():
    count = Teacher.objects.count() + 1
    return f"TCH-{count:03d}"


@admin_login_required
def teacher_list(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')
    designation = request.GET.get('designation', '')
    status = request.GET.get('status', '')

    teachers = Teacher.objects.select_related('department').all()

    if query:
        teachers = teachers.filter(
            Q(employee_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(qualification__icontains=query) |
            Q(specialization__icontains=query)
        )

    if dept_id:
        teachers = teachers.filter(department_id=dept_id)

    if designation:
        teachers = teachers.filter(designation=designation)

    if status == 'active':
        teachers = teachers.filter(is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(is_active=False)

    paginator = Paginator(teachers, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all()

    # Metrics
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(is_active=True).count()
    professors_count = Teacher.objects.filter(designation__in=['professor', 'associate_professor']).count()
    departments_count = Department.objects.filter(teachers__isnull=False).distinct().count()

    context = {
        "teachers": page_obj,
        "departments": departments,
        "designation_choices": Teacher.DESIGNATION_CHOICES,
        "query": query,
        "selected_dept": dept_id,
        "selected_designation": designation,
        "selected_status": status,
        "total_teachers": total_teachers,
        "active_teachers": active_teachers,
        "professors_count": professors_count,
        "departments_count": departments_count,
    }
    return render(request, "admin/teachers_management/list_teachers.html", context)


@admin_login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher.objects.select_related('department'), id=teacher_id)
    
    assigned_courses = teacher.course_assignments.select_related('course', 'semester__academic_year').all() if hasattr(teacher, 'assignments') else []
    invigilations = teacher.invigilated_exams.select_related('exam', 'course').all() if hasattr(teacher, 'invigilated_exams') else []
    salaries = teacher.salaries.all().order_by('-payment_date') if hasattr(teacher, 'salaries') else []

    context = {
        "teacher": teacher,
        "assigned_courses": assigned_courses,
        "invigilations": invigilations,
        "salaries": salaries,
    }
    return render(request, "admin/teachers_management/teacher_detail.html", context)


@admin_login_required
def teacher_add(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            if not teacher.employee_id:
                teacher.employee_id = generate_employee_id()
            if not teacher.password:
                teacher.set_default_password()
            teacher.save()
            messages.success(request, f"Teacher '{teacher.full_name}' added successfully with Employee ID: {teacher.employee_id}")
            return redirect("teachers:teacher_list")
    else:
        form = TeacherForm(initial={'employee_id': generate_employee_id()})

    return render(request, "admin/teachers_management/teacher_form.html", {"form": form, "title": "Add New Teacher"})


@admin_login_required
def teacher_edit(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == "POST":
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f"Teacher '{teacher.full_name}' updated successfully.")
            return redirect("teachers:teacher_list")
    else:
        form = TeacherForm(instance=teacher)

    return render(request, "admin/teachers_management/teacher_form.html", {"form": form, "teacher": teacher, "title": "Edit Teacher Details"})


@admin_login_required
def teacher_delete(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == "POST":
        name = teacher.full_name
        teacher.delete()
        messages.success(request, f"Teacher '{name}' has been deleted.")
        return redirect("teachers:teacher_list")

    return render(request, "admin/teachers_management/teacher_delete.html", {"teacher": teacher})


@admin_login_required
def teacher_export_csv(request):
    teachers = Teacher.objects.select_related('department').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teachers_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'Full Name', 'Gender', 'Email', 'Phone', 'Department', 'Designation', 'Qualification', 'Specialization', 'Status', 'Date Joined'])

    for t in teachers:
        writer.writerow([
            t.employee_id, t.full_name, t.get_gender_display(), t.email, t.phone,
            t.department.name if t.department else '',
            t.get_designation_display(), t.qualification, t.specialization,
            'Active' if t.is_active else 'Inactive', t.date_joined
        ])

    return response


# =========================================================
# Teacher Portal
# =========================================================

def _portal_teacher(request):
    if not request.session.get("teacher_logged_in"):
        return None
    teacher_id = request.session.get("teacher_id")
    return get_object_or_404(Teacher, id=teacher_id)


def teacher_login(request):
    if request.method == "POST":
        employee_id = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            teacher = Teacher.objects.get(employee_id=employee_id)
            if teacher.is_active and check_password(password, teacher.password):
                request.session["teacher_logged_in"] = True
                request.session["teacher_id"] = teacher.id
                request.session["teacher_name"] = teacher.full_name
                messages.success(request, f"Welcome back, {teacher.full_name}!")
                return redirect("teachers:teacher_dashboard")
            return render(request, "teachers/login.html", {"error": "Invalid employee ID or password"})
        except Teacher.DoesNotExist:
            return render(request, "teachers/login.html", {"error": "Teacher account not found"})

    if request.session.get("teacher_logged_in"):
        return redirect("teachers:teacher_dashboard")
    return render(request, "teachers/login.html")


def teacher_logout(request):
    request.session.flush()
    return redirect("teachers:teacher_login")


def teacher_dashboard(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    from academics.models import Timetable
    from students.models import Students

    assignments = teacher.course_assignments.select_related('course', 'semester__academic_year')
    today = timezone.localdate()
    today_slots = []
    if today.weekday() < 6:
        day_codes = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SUN']
        today_slots = (
            Timetable.objects.filter(
                course_assignment__teacher=teacher,
                day_of_week=day_codes[today.weekday()],
            )
            .select_related('course_assignment__course', 'course_assignment__semester')
            .order_by('start_time')
        )

    pending_leaves = teacher.leave_requests.filter(status='pending').count()
    recent_leaves = teacher.leave_requests.all()[:5]

    week_start = today - timezone.timedelta(days=today.weekday())
    marked_days = (
        Attendance.objects.filter(course_assignment__teacher=teacher, date__gte=week_start)
        .values('date').distinct().count()
    )

    student_ids = Students.objects.filter(
        program__in=assignments.values('course__program'),
        current_semester__in=assignments.values('semester__number'),
    ).distinct().count()

    context = {
        "teacher": teacher,
        "assignments": assignments,
        "assignments_count": assignments.count(),
        "today_slots": today_slots,
        "pending_leaves": pending_leaves,
        "recent_leaves": recent_leaves,
        "marked_days": marked_days,
        "students_count": student_ids,
        "today_display": today.strftime("%A, %b %d, %Y"),
    }
    return render(request, "teachers/dashboard.html", context)


def teacher_attendance(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    assignments = teacher.course_assignments.select_related('course', 'semester__academic_year')

    if request.method == "POST":
        assignment_id = request.POST.get("course_assignment")
        date_str = request.POST.get("date", "")
        if not assignment_id or not date_str:
            messages.error(request, "Please select a class and date.")
        else:
            assignment = get_object_or_404(CourseAssignment, id=assignment_id, teacher=teacher)
            from datetime import date as date_cls
            mark_date = date_cls.fromisoformat(date_str)
            students = _assignment_students(assignment)
            saved = updated = 0
            for s in students:
                status = request.POST.get(f"attendance_{s.student_id}", "").strip()
                if status not in dict(Attendance.STATUS_CHOICES):
                    continue
                remarks = request.POST.get(f"remarks_{s.student_id}", "").strip()
                record, created = Attendance.objects.update_or_create(
                    student=s, course_assignment=assignment, date=mark_date,
                    defaults={"status": status, "remarks": remarks},
                )
                if created:
                    saved += 1
                else:
                    updated += 1
            messages.success(request, f"Attendance saved for {students.count()} students ({saved} new, {updated} updated).")
            return redirect(f"{request.path}?course_assignment={assignment_id}&date={date_str}")

    assignment_id = request.GET.get("course_assignment", "")
    date_str = request.GET.get("date", "")
    students = existing = None
    selected_assignment = None
    if assignment_id:
        selected_assignment = get_object_or_404(CourseAssignment, id=assignment_id, teacher=teacher)
        students = _assignment_students(selected_assignment)
        if date_str:
            from datetime import date as date_cls
            mark_date = date_cls.fromisoformat(date_str)
            existing = {
                r.student_id: r
                for r in Attendance.objects.filter(
                    student__in=students, course_assignment=selected_assignment, date=mark_date
                )
            }

    context = {
        "teacher": teacher,
        "assignments": assignments,
        "selected_assignment": selected_assignment,
        "students": students,
        "existing": existing or {},
        "default_date": date_str or timezone.localdate().isoformat(),
        "status_choices": Attendance.STATUS_CHOICES,
    }
    return render(request, "teachers/attendance.html", context)


def _assignment_students(assignment):
    """Students enrolled in a course assignment by program/semester/section."""
    from students.models import Students
    return (
        Students.objects.filter(
            program=assignment.course.program,
            current_semester=assignment.semester.number,
            section=assignment.section or 'A',
        )
        .select_related('program')
        .order_by('roll_number')
    )


def teacher_attendance_records(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    assignments = teacher.course_assignments.select_related('course', 'semester__academic_year')
    assignment_id = request.GET.get("course_assignment", "")
    month = request.GET.get("month", "")

    summary = None
    records = None
    selected_assignment = None
    if assignment_id:
        selected_assignment = get_object_or_404(CourseAssignment, id=assignment_id, teacher=teacher)
        qs = Attendance.objects.filter(
            course_assignment=selected_assignment
        ).select_related('student')
        today = timezone.localdate()
        if month:
            try:
                year, m = (int(x) for x in month.split("-"))
                qs = qs.filter(date__year=year, date__month=m)
            except ValueError:
                month = ""
        if not month:
            qs = qs.filter(date__year=today.year, date__month=today.month)
        records = qs.order_by('date')
        summary = qs.values('student__roll_number', 'student__first_name', 'student__last_name') \
                   .annotate(
                       present=Count('status', filter=Q(status='present')),
                       late=Count('status', filter=Q(status='late')),
                       leave=Count('status', filter=Q(status='leave')),
                       absent=Count('status', filter=Q(status='absent')),
                   ).order_by('student__roll_number')

    context = {
        "teacher": teacher,
        "assignments": assignments,
        "selected_assignment": selected_assignment,
        "records": records,
        "summary": summary,
        "month": month or timezone.localdate().strftime("%Y-%m"),
        "default_date": timezone.localdate().isoformat(),
    }
    return render(request, "teachers/attendance_records.html", context)


def teacher_routines(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    from academics.models import Timetable

    assignments = teacher.course_assignments.select_related('course', 'semester__academic_year')
    slots = (
        Timetable.objects.filter(course_assignment__teacher=teacher)
        .select_related('course_assignment__course', 'course_assignment__semester')
        .order_by('day_of_week', 'start_time')
    )

    days = [('SUN', 'Sunday'), ('MON', 'Monday'), ('TUE', 'Tuesday'),
            ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday')]
    by_day = {code: [] for code, _ in days}
    for s in slots:
        by_day[s.day_of_week].append(s)
    grid = [(code, label, by_day[code]) for code, label in days]

    context = {
        "teacher": teacher,
        "assignments": assignments,
        "grid": grid,
        "any_slots": bool(slots),
    }
    return render(request, "teachers/routines.html", context)


def teacher_leave(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    leave_requests = teacher.leave_requests.all()
    context = {
        "teacher": teacher,
        "leave_requests": leave_requests,
        "pending_count": leave_requests.filter(status='pending').count(),
        "approved_count": leave_requests.filter(status='approved').count(),
        "rejected_count": leave_requests.filter(status='rejected').count(),
    }
    return render(request, "teachers/leave.html", context)


def teacher_leave_new(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.teacher = teacher
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect("teachers:teacher_leave")
    else:
        form = LeaveRequestForm()

    return render(request, "teachers/leave_form.html", {"teacher": teacher, "form": form})


def teacher_profile(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    context = {
        "teacher": teacher,
        "assignment_count": teacher.course_assignments.count(),
    }
    return render(request, "teachers/profile.html", context)


def teacher_profile_edit(request):
    teacher = _portal_teacher(request)
    if not teacher:
        return redirect("teachers:teacher_login")

    if request.method == "POST":
        form = TeacherProfileForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("teachers:teacher_profile")
    else:
        form = TeacherProfileForm(instance=teacher)

    return render(request, "teachers/profile_edit.html", {"teacher": teacher, "form": form})


# =========================================================
# Admin: Leave Request Management
# =========================================================

@admin_login_required
def teacher_leave_admin(request):
    status = request.GET.get('status', '')
    leaves = LeaveRequest.objects.select_related('teacher').all()
    if status:
        leaves = leaves.filter(status=status)

    counts = {
        'pending': LeaveRequest.objects.filter(status='pending').count(),
        'approved': LeaveRequest.objects.filter(status='approved').count(),
        'rejected': LeaveRequest.objects.filter(status='rejected').count(),
    }

    context = {
        "leaves": leaves,
        "counts": counts,
        "status": status,
    }
    return render(request, "admin/teachers_management/leave_requests.html", context)


@admin_login_required
def teacher_leave_decision(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if request.method == "POST":
        action = request.POST.get("action")
        remarks = request.POST.get("admin_remarks", "").strip()
        if action == "approve":
            leave.status = "approved"
            messages.success(request, f"Leave request approved for {leave.teacher.full_name}.")
        elif action == "reject":
            leave.status = "rejected"
            messages.info(request, f"Leave request rejected for {leave.teacher.full_name}.")
        leave.admin_remarks = remarks
        leave.decided_at = timezone.now()
        leave.save()

    return redirect("teachers:teacher_leave_admin")
