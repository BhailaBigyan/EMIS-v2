import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from emis.decorators import admin_login_required
from academics.models import Department
from .models import Teacher
from .forms import TeacherForm


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
    
    assigned_courses = teacher.assignments.select_related('course', 'semester', 'academic_year').all() if hasattr(teacher, 'assignments') else []
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
