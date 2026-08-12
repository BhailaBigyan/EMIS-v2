from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from emis.decorators import admin_login_required
from .models import Department, Program, Course, AcademicYear, Semester, CourseAssignment, Timetable, Batch
from .forms import (
    DepartmentForm, ProgramForm, CourseForm,
    AcademicYearForm, SemesterForm, CourseAssignmentForm, TimetableForm, BatchForm
)


# Legacy / Overview view for classes list
@admin_login_required
def classes_list(request):
    departments = Department.objects.prefetch_related('programs').all()
    programs = Program.objects.select_related('department').all()
    courses = Course.objects.select_related('program').all()
    assignments = CourseAssignment.objects.select_related('course', 'teacher', 'semester').all()
    batches = Batch.objects.select_related('program').all()
    
    context = {
        'departments': departments,
        'programs': programs,
        'courses': courses,
        'assignments': assignments,
        'batches': batches,
    }
    return render(request, "admin/classes_management/list_classes.html", context)


# ==================== Department Views ====================

@admin_login_required
def department_list(request):
    departments = Department.objects.select_related('head').all()
    return render(request, "admin/academics_management/department_list.html", {"departments": departments})


@admin_login_required
def department_add(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect("academics:department_list")
    else:
        form = DepartmentForm()

    return render(request, "admin/academics_management/department_form.html", {"form": form, "title": "Add Department"})


@admin_login_required
def department_edit(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect("academics:department_list")
    else:
        form = DepartmentForm(instance=dept)

    return render(request, "admin/academics_management/department_form.html", {"form": form, "title": "Edit Department"})


@admin_login_required
def department_delete(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == "POST":
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' deleted.")
        return redirect("academics:department_list")
    return render(request, "admin/academics_management/department_delete.html", {"department": dept})


# ==================== Program Views ====================

@admin_login_required
def program_list(request):
    programs = Program.objects.select_related('department').all()
    return render(request, "admin/academics_management/program_list.html", {"programs": programs})


@admin_login_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            prog = form.save()
            messages.success(request, f"Program '{prog.name}' created.")
            return redirect("academics:program_list")
    else:
        form = ProgramForm()

    return render(request, "admin/academics_management/program_form.html", {"form": form, "title": "Add Program"})


@admin_login_required
def program_edit(request, prog_id):
    prog = get_object_or_404(Program, id=prog_id)
    if request.method == "POST":
        form = ProgramForm(request.POST, instance=prog)
        if form.is_valid():
            form.save()
            messages.success(request, f"Program '{prog.name}' updated.")
            return redirect("academics:program_list")
    else:
        form = ProgramForm(instance=prog)

    return render(request, "admin/academics_management/program_form.html", {"form": form, "title": "Edit Program"})


@admin_login_required
def program_delete(request, prog_id):
    prog = get_object_or_404(Program, id=prog_id)
    if request.method == "POST":
        name = prog.name
        prog.delete()
        messages.success(request, f"Program '{name}' deleted.")
        return redirect("academics:program_list")
    return render(request, "admin/academics_management/program_delete.html", {"program": prog})


# ==================== Course Views ====================

@admin_login_required
def course_list(request):
    courses = Course.objects.select_related('program').all()
    return render(request, "admin/academics_management/course_list.html", {"courses": courses})


@admin_login_required
def course_add(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.name}' created.")
            return redirect("academics:course_list")
    else:
        form = CourseForm()

    return render(request, "admin/academics_management/course_form.html", {"form": form, "title": "Add Course"})


@admin_login_required
def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.name}' updated.")
            return redirect("academics:course_list")
    else:
        form = CourseForm(instance=course)

    return render(request, "admin/academics_management/course_form.html", {"form": form, "title": "Edit Course"})


@admin_login_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        name = course.name
        course.delete()
        messages.success(request, f"Course '{name}' deleted.")
        return redirect("academics:course_list")
    return render(request, "admin/academics_management/course_delete.html", {"course": course})


# ==================== Academic Year & Semester Views ====================

@admin_login_required
def academic_year_list(request):
    years = AcademicYear.objects.prefetch_related('semesters').all()
    return render(request, "admin/academics_management/academic_year_list.html", {"years": years})


@admin_login_required
def academic_year_add(request):
    if request.method == "POST":
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            year = form.save()
            messages.success(request, f"Academic Year '{year.name}' added.")
            return redirect("academics:academic_year_list")
    else:
        form = AcademicYearForm()

    return render(request, "admin/academics_management/academic_year_form.html", {"form": form, "title": "Add Academic Year"})


@admin_login_required
def academic_year_edit(request, year_id):
    year = get_object_or_404(AcademicYear, id=year_id)
    if request.method == "POST":
        form = AcademicYearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, f"Academic Year '{year.name}' updated.")
            return redirect("academics:academic_year_list")
    else:
        form = AcademicYearForm(instance=year)

    return render(request, "admin/academics_management/academic_year_form.html", {"form": form, "title": "Edit Academic Year"})


@admin_login_required
def academic_year_delete(request, year_id):
    year = get_object_or_404(AcademicYear, id=year_id)
    if request.method == "POST":
        name = year.name
        year.delete()
        messages.success(request, f"Academic Year '{name}' deleted.")
        return redirect("academics:academic_year_list")
    return render(request, "admin/academics_management/academic_year_delete.html", {"year": year})


@admin_login_required
def semester_add(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            sem = form.save()
            messages.success(request, f"Semester '{sem.name}' added.")
            return redirect("academics:academic_year_list")
    else:
        form = SemesterForm()

    return render(request, "admin/academics_management/semester_form.html", {"form": form, "title": "Add Semester"})


@admin_login_required
def semester_edit(request, sem_id):
    sem = get_object_or_404(Semester, id=sem_id)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=sem)
        if form.is_valid():
            form.save()
            messages.success(request, f"Semester '{sem.name}' updated.")
            return redirect("academics:academic_year_list")
    else:
        form = SemesterForm(instance=sem)

    return render(request, "admin/academics_management/semester_form.html", {"form": form, "title": "Edit Semester"})


@admin_login_required
def semester_delete(request, sem_id):
    sem = get_object_or_404(Semester, id=sem_id)
    if request.method == "POST":
        name = sem.name
        sem.delete()
        messages.success(request, f"Semester '{name}' deleted.")
        return redirect("academics:academic_year_list")
    return render(request, "admin/academics_management/semester_delete.html", {"semester": sem})


# ==================== Course Assignment Views (Assign Teacher) ====================

@admin_login_required
def assignment_list(request):
    assignments = CourseAssignment.objects.select_related('course', 'teacher', 'semester').all()
    return render(request, "admin/academics_management/assignment_list.html", {"assignments": assignments})


@admin_login_required
def assignment_add(request):
    if request.method == "POST":
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            ca = form.save()
            messages.success(request, f"Assigned teacher '{ca.teacher.full_name}' to course '{ca.course.code}'.")
            return redirect("academics:assignment_list")
    else:
        form = CourseAssignmentForm()

    return render(request, "admin/academics_management/assignment_form.html", {"form": form, "title": "Assign Teacher to Course"})


@admin_login_required
def assignment_edit(request, assign_id):
    ca = get_object_or_404(CourseAssignment, id=assign_id)
    if request.method == "POST":
        form = CourseAssignmentForm(request.POST, instance=ca)
        if form.is_valid():
            form.save()
            messages.success(request, f"Assignment for '{ca.course.code}' updated.")
            return redirect("academics:assignment_list")
    else:
        form = CourseAssignmentForm(instance=ca)

    return render(request, "admin/academics_management/assignment_form.html", {"form": form, "title": "Edit Course Assignment"})


@admin_login_required
def assignment_delete(request, assign_id):
    ca = get_object_or_404(CourseAssignment, id=assign_id)
    if request.method == "POST":
        ca.delete()
        messages.success(request, "Course assignment removed.")
        return redirect("academics:assignment_list")
    return render(request, "admin/academics_management/assignment_delete.html", {"assignment": ca})


# ==================== Timetable Views ====================

@admin_login_required
def timetable_view(request):
    timetable_slots = Timetable.objects.select_related(
        'course_assignment__course',
        'course_assignment__teacher',
        'course_assignment__semester'
    ).all()

    # Group by day
    days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI']
    timetable_grid = {day: [] for day in days}

    for slot in timetable_slots:
        if slot.day_of_week in timetable_grid:
            timetable_grid[slot.day_of_week].append(slot)

    context = {
        'timetable_grid': timetable_grid,
        'slots': timetable_slots,
    }
    return render(request, "admin/academics_management/timetable.html", context)


@admin_login_required
def timetable_add(request):
    if request.method == "POST":
        form = TimetableForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f"Timetable slot added for {slot.course_assignment.course.code}.")
            return redirect("academics:timetable_view")
    else:
        form = TimetableForm()

    return render(request, "admin/academics_management/timetable_form.html", {"form": form, "title": "Add Timetable Slot"})


@admin_login_required
def timetable_edit(request, slot_id):
    slot = get_object_or_404(Timetable, id=slot_id)
    if request.method == "POST":
        form = TimetableForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, f"Timetable slot updated for {slot.course_assignment.course.code}.")
            return redirect("academics:timetable_view")
    else:
        form = TimetableForm(instance=slot)

    return render(request, "admin/academics_management/timetable_form.html", {"form": form, "title": "Edit Timetable Slot"})


@admin_login_required
def timetable_delete(request, slot_id):
    slot = get_object_or_404(Timetable, id=slot_id)
    if request.method == "POST":
        slot.delete()
        messages.success(request, "Timetable slot deleted.")
        return redirect("academics:timetable_view")
    return render(request, "admin/academics_management/timetable_delete.html", {"slot": slot})


# ==================== Batch Views ====================

@admin_login_required
def batch_list(request):
    batches = Batch.objects.select_related('program').all()
    return render(request, "admin/academics_management/batch_list.html", {"batches": batches})


@admin_login_required
def batch_add(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.name}' created.")
            return redirect("academics:batch_list")
    else:
        form = BatchForm()

    return render(request, "admin/academics_management/batch_form.html", {"form": form, "title": "Add Batch"})


@admin_login_required
def batch_edit(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if request.method == "POST":
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f"Batch '{batch.name}' updated.")
            return redirect("academics:batch_list")
    else:
        form = BatchForm(instance=batch)

    return render(request, "admin/academics_management/batch_form.html", {"form": form, "title": "Edit Batch"})


@admin_login_required
def batch_delete(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if request.method == "POST":
        name = batch.name
        batch.delete()
        messages.success(request, f"Batch '{name}' deleted.")
        return redirect("academics:batch_list")
    return render(request, "admin/academics_management/batch_delete.html", {"batch": batch})