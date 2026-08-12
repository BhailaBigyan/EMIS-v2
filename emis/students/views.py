from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Students


def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            student = Students.objects.get(roll_number=username)
            if check_password(password, student.password) or password == student.password:
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


def student_index(request):
    if not request.session.get("student_logged_in"):
        return redirect("students:student_login")
    
    student_id = request.session.get("student_id")
    student = get_object_or_404(Students.objects.select_related('program'), student_id=student_id)
    
    context = {
        "student": student,
        "username": student.full_name,
    }
    return render(request, "students/student_dashboard.html", context)


def student_logout(request):
    request.session.flush()
    return redirect("students:student_login")


def student_profile(request):
    if not request.session.get("student_logged_in"):
        return redirect("students:student_login")
    
    student_id = request.session.get("student_id")
    student = get_object_or_404(Students.objects.select_related('program'), student_id=student_id)
    
    return render(request, "students/student_profile.html", {"student": student, "username": student.full_name})