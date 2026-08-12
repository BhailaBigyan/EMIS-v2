import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings

from emis.decorators import admin_login_required
from students.models import Students
from students.forms import StudentForm, BulkStudentUploadForm
from students.utils import (
    parse_csv_file, parse_excel_file, bulk_create_students,
    generate_roll_number, generate_sample_csv, generate_sample_excel
)
from academics.models import Program, Department, Course


def home(request):
    if request.session.get("general_logged_in"):
        return redirect("general_dashboard")
    from notices.models import Notice
    from academics.models import Program
    notices = Notice.objects.all()[:5]
    programs = Program.objects.filter(is_active=True)
    return render(request, 'index.html', {'notices': notices, 'programs': programs})


def general_login(request):
    from notices.models import Notice
    from academics.models import Program
    notices = Notice.objects.all()[:5]
    programs = Program.objects.filter(is_active=True)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        admin_user = getattr(settings, 'ADMIN_USERNAME', 'admin')
        admin_pass = getattr(settings, 'ADMIN_PASSWORD', 'admin123')
        
        if username == admin_user and password == admin_pass:
            request.session["general_logged_in"] = True
            request.session["general_username"] = username
            messages.success(request, "Welcome to EMIS Admin Console.")
            return redirect("general_dashboard")
        
        return render(request, "index.html", {"error": "Invalid username or password", "notices": notices, "programs": programs})

    if request.session.get("general_logged_in"):
        return redirect("general_dashboard")
    return render(request, "index.html", {"notices": notices, "programs": programs})


@admin_login_required
def general_dashboard(request):
    from finances.models import FeePayment
    from examinations.models import Exam
    from teachers.models import Teacher
    from django.db.models import Sum

    total_students = Students.objects.count()
    active_students = Students.objects.filter(status='active').count()
    total_programs = Program.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    recent_students = Students.objects.select_related('program').order_by('-created_at')[:5]

    recent_payments = FeePayment.objects.select_related('student', 'fee_structure').order_by('-created_at')[:5]
    upcoming_exams = Exam.objects.select_related('semester').order_by('-start_date')[:5]
    total_collections = FeePayment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    context = {
        "username": request.session.get("general_username", "Admin"),
        "total_students": total_students,
        "active_students": active_students,
        "total_programs": total_programs,
        "total_departments": total_departments,
        "total_teachers": total_teachers,
        "recent_students": recent_students,
        "recent_payments": recent_payments,
        "upcoming_exams": upcoming_exams,
        "total_collections": total_collections,
    }
    return render(request, "general_dashboard.html", context)



def general_logout(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ==========================================
# Student Management Views (Admin)
# ==========================================

@admin_login_required
def student_list(request):
    query = request.GET.get('q', '').strip()
    program_id = request.GET.get('program', '')
    status_filter = request.GET.get('status', '')
    batch_filter = request.GET.get('batch', '')

    students = Students.objects.select_related('program').all()

    if query:
        students = students.filter(
            Q(roll_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    if program_id:
        students = students.filter(program_id=program_id)

    if status_filter:
        students = students.filter(status=status_filter)

    if batch_filter:
        students = students.filter(batch=batch_filter)

    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    programs = Program.objects.filter(is_active=True)
    batches = Students.objects.values_list('batch', flat=True).distinct().order_by('-batch')

    context = {
        'students': page_obj,
        'programs': programs,
        'batches': [b for b in batches if b],
        'query': query,
        'selected_program': program_id,
        'selected_status': status_filter,
        'selected_batch': batch_filter,
        'total_count': paginator.count,
    }
    return render(request, "admin/students_management/list_students.html", context)


@admin_login_required
def student_add(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            if student.program and student.batch:
                student.roll_number = generate_roll_number(student.program, student.batch)
            else:
                student.roll_number = f"STU-{Students.objects.count() + 1:04d}"
            
            raw_password = student.set_default_password()
            student.save()
            messages.success(
                request, 
                f"Student '{student.full_name}' created successfully! "
                f"Roll No / Username: {student.roll_number}, Password: {raw_password}"
            )
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, "admin/students_management/add_student.html", {"form": form})


@admin_login_required
def student_bulk_upload(request):
    if request.method == "POST":
        form = BulkStudentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            program = form.cleaned_data['program']
            batch = form.cleaned_data['batch']

            filename = uploaded_file.name.lower()
            if filename.endswith('.csv'):
                data, parse_errors = parse_csv_file(uploaded_file)
            elif filename.endswith('.xlsx'):
                data, parse_errors = parse_excel_file(uploaded_file)
            else:
                messages.error(request, "Unsupported file format. Please upload a .csv or .xlsx file.")
                return render(request, "admin/students_management/bulk_upload.html", {"form": form})

            if parse_errors:
                for err in parse_errors:
                    messages.error(request, err)
                return render(request, "admin/students_management/bulk_upload.html", {"form": form})

            if not data:
                messages.warning(request, "No valid student data found in the uploaded file.")
                return render(request, "admin/students_management/bulk_upload.html", {"form": form})

            created, create_errors = bulk_create_students(data, program, batch)

            if create_errors:
                for err in create_errors:
                    messages.error(request, err)

            if created:
                messages.success(
                    request,
                    f"Successfully imported {len(created)} students for {program.code} (Batch {batch}). "
                    f"Default passwords set as 'emis@<roll_number>'."
                )
                # Store created summary in session to display credentials summary
                request.session['bulk_upload_summary'] = [
                    {'roll': item['roll_number'], 'name': item['student'].full_name, 'pass': item['default_password']}
                    for item in created
                ]
                return redirect('student_bulk_summary')

    else:
        form = BulkStudentUploadForm()

    return render(request, "admin/students_management/bulk_upload.html", {"form": form})


@admin_login_required
def student_bulk_summary(request):
    summary = request.session.pop('bulk_upload_summary', None)
    if not summary:
        return redirect('student_list')
    return render(request, "admin/students_management/bulk_summary.html", {"summary": summary})


@admin_login_required
def student_edit(request, student_id):
    student = get_object_or_404(Students, student_id=student_id)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.full_name}' updated successfully.")
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)

    return render(request, "admin/students_management/edit_student.html", {"form": form, "student": student})


@admin_login_required
def student_delete(request, student_id):
    student = get_object_or_404(Students, student_id=student_id)
    if request.method == "POST":
        name = student.full_name
        student.delete()
        messages.success(request, f"Student '{name}' has been deleted.")
        return redirect('student_list')

    return render(request, "admin/students_management/delete_student.html", {"student": student})


@admin_login_required
def student_profile(request, student_id):
    student = get_object_or_404(Students.objects.select_related('program'), student_id=student_id)
    fee_accounts = student.fee_accounts.select_related('fee_structure').all() if hasattr(student, 'fee_accounts') else []
    fee_payments = student.fee_payments.select_related('fee_structure').all() if hasattr(student, 'fee_payments') else []
    grades = student.grades.select_related('exam', 'course').all() if hasattr(student, 'grades') else []

    context = {
        "student": student,
        "fee_accounts": fee_accounts,
        "fee_payments": fee_payments,
        "grades": grades,
    }
    return render(request, "admin/students_management/student_profile.html", context)


@admin_login_required
def student_export_csv(request):
    students = Students.objects.select_related('program').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'First Name', 'Last Name', 'Email', 'Phone', 'Gender', 'Program', 'Batch', 'Semester', 'Status'])

    for s in students:
        writer.writerow([
            s.roll_number, s.first_name, s.last_name, s.email, s.phone,
            s.get_gender_display(), s.program.code if s.program else '',
            s.batch, s.current_semester, s.get_status_display()
        ])

    return response


@admin_login_required
def download_sample_csv_view(request):
    content = generate_sample_csv()
    response = HttpResponse(content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_student_upload.csv"'
    return response


@admin_login_required
def download_sample_excel_view(request):
    output = generate_sample_excel()
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="sample_student_upload.xlsx"'
    return response
