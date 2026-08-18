from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Avg, Q
from emis.decorators import admin_login_required
from .models import Exam, ExamSchedule, Grade, Result
from .forms import ExamForm, ExamScheduleForm, GradeForm
from academics.models import Course, Semester
from students.models import Students


@admin_login_required
def exam_list(request):
    exams = Exam.objects.select_related('semester').all()
    return render(request, 'admin/examinations_management/list_examinations.html', {'exams': exams})


@admin_login_required
def exam_create(request):
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f"Exam '{exam.name}' created.")
            return redirect('examinations:exam_list')
    else:
        form = ExamForm()

    return render(request, 'admin/examinations_management/exam_form.html', {'form': form, 'title': 'Create New Exam'})


@admin_login_required
def exam_edit(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f"Exam '{exam.name}' updated.")
            return redirect('examinations:exam_list')
    else:
        form = ExamForm(instance=exam)

    return render(request, 'admin/examinations_management/exam_form.html', {'form': form, 'title': 'Edit Exam'})


@admin_login_required
def exam_delete(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        name = exam.name
        exam.delete()
        messages.success(request, f"Exam '{name}' deleted.")
        return redirect('examinations:exam_list')
    return render(request, 'admin/examinations_management/exam_delete.html', {'exam': exam})


# ==================== Exam Schedules ====================

@admin_login_required
def schedule_list(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('semester'), id=exam_id)
    schedules = ExamSchedule.objects.filter(exam=exam).select_related('course', 'invigilator')
    
    context = {
        'exam': exam,
        'schedules': schedules,
    }
    return render(request, 'admin/examinations_management/exam_schedule.html', context)


@admin_login_required
def schedule_add(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        form = ExamScheduleForm(request.POST)
        if form.is_valid():
            sched = form.save(commit=False)
            sched.exam = exam
            sched.save()
            messages.success(request, f"Schedule slot added for {sched.course.code}.")
            return redirect('examinations:schedule_list', exam_id=exam.id)
    else:
        form = ExamScheduleForm(initial={'exam': exam})

    return render(request, 'admin/examinations_management/schedule_form.html', {'form': form, 'exam': exam})


# ==================== Grade Entry Grid ====================

@admin_login_required
def grade_entry(request, exam_id, course_id):
    exam = get_object_or_404(Exam, id=exam_id)
    course = get_object_or_404(Course, id=course_id)

    # Fetch students enrolled in the course's program & semester
    students = Students.objects.filter(
        program=course.program,
        current_semester=course.semester,
        status='active'
    )

    if request.method == "POST":
        # Bulk save marks
        updated_count = 0
        error_count = 0
        for student in students:
            input_name = f"marks_{student.student_id}"
            remarks_name = f"remarks_{student.student_id}"
            marks_val = request.POST.get(input_name, '').strip()
            remarks_val = request.POST.get(remarks_name, '').strip()

            if marks_val != '':
                try:
                    marks_num = float(marks_val)
                except ValueError:
                    error_count += 1
                    continue
                grade_obj, created = Grade.objects.get_or_create(
                    student=student,
                    exam=exam,
                    course=course,
                    defaults={'marks_obtained': marks_num, 'remarks': remarks_val}
                )
                if not created:
                    grade_obj.marks_obtained = marks_num
                    grade_obj.remarks = remarks_val
                    grade_obj.save()
                updated_count += 1

        messages.success(request, f"Successfully recorded grades for {updated_count} students.")
        if error_count:
            messages.warning(request, f"Skipped {error_count} invalid mark entr{'y' if error_count == 1 else 'ies'} (non-numeric values).")
        return redirect('examinations:exam_list')

    # Fetch existing grades
    existing_grades = {
        g.student_id: g
        for g in Grade.objects.filter(exam=exam, course=course)
    }

    students_with_grades = [
        {'student': s, 'grade': existing_grades.get(s.student_id)}
        for s in students
    ]

    context = {
        'exam': exam,
        'course': course,
        'students_with_grades': students_with_grades,
    }
    return render(request, 'admin/examinations_management/grade_entry.html', context)



# ==================== Results & Report Cards ====================

@admin_login_required
def result_list(request):
    results = Result.objects.select_related('student__program', 'semester').all()
    semesters = Semester.objects.all()

    selected_sem = request.GET.get('semester', '')
    if selected_sem:
        results = results.filter(semester_id=selected_sem)

    context = {
        'results': results,
        'semesters': semesters,
        'selected_sem': selected_sem,
    }
    return render(request, 'admin/examinations_management/result_list.html', context)


@admin_login_required
@transaction.atomic
def result_generate(request):
    """Auto-generate semester results from entered grades."""
    if request.method == "POST":
        semester_id = request.POST.get('semester')
        semester = get_object_or_404(Semester, id=semester_id)

        # Get all students with grades in exams of this semester
        students = Students.objects.filter(
            grades__exam__semester=semester
        ).distinct()

        generated_count = 0
        for student in students:
            student_grades = Grade.objects.filter(
                student=student,
                exam__semester=semester
            )

            if not student_grades.exists():
                continue

            total_obtained = sum(float(g.marks_obtained) for g in student_grades)
            total_possible = sum(float(g.exam.total_marks) for g in student_grades)

            percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
            
            # Simple GPA calculation
            if percentage >= 90: gpa = 4.0
            elif percentage >= 80: gpa = 3.6
            elif percentage >= 70: gpa = 3.2
            elif percentage >= 60: gpa = 2.8
            elif percentage >= 50: gpa = 2.4
            elif percentage >= 40: gpa = 2.0
            else: gpa = 0.0

            has_failed = any(g.grade_letter == 'F' for g in student_grades)
            status_val = 'fail' if has_failed else 'pass'

            res_obj, created = Result.objects.get_or_create(
                student=student,
                semester=semester,
                defaults={
                    'total_marks': total_possible,
                    'obtained_marks': total_obtained,
                    'percentage': percentage,
                    'gpa': gpa,
                    'status': status_val,
                    'published': True,
                }
            )

            if not created:
                res_obj.total_marks = total_possible
                res_obj.obtained_marks = total_obtained
                res_obj.percentage = percentage
                res_obj.gpa = gpa
                res_obj.status = status_val
                res_obj.published = True
                res_obj.save()

            generated_count += 1

        messages.success(request, f"Generated and published semester results for {generated_count} students.")
        return redirect('examinations:result_list')

    semesters = Semester.objects.all()
    return render(request, 'admin/examinations_management/result_generate.html', {'semesters': semesters})


@admin_login_required
def report_card_view(request, student_id, semester_id):
    student = get_object_or_404(Students.objects.select_related('program'), student_id=student_id)
    semester = get_object_or_404(Semester.objects.select_related('academic_year'), id=semester_id)
    
    grades = Grade.objects.filter(
        student=student,
        exam__semester=semester
    ).select_related('course', 'exam')

    result = Result.objects.filter(student=student, semester=semester).first()

    context = {
        'student': student,
        'semester': semester,
        'grades': grades,
        'result': result,
    }
    return render(request, 'admin/examinations_management/report_card.html', context)