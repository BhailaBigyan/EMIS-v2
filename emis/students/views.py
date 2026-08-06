from django.shortcuts import redirect, render


def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username == "student" and password == "password":
            request.session["student_logged_in"] = True
            request.session["student_username"] = username
            return redirect("students:student_index")
        return render(request, "students/login.html", {"error": "Invalid username or password"})

    if request.session.get("student_logged_in"):
        return redirect("students:student_index")
    return render(request, "students/login.html")


def student_index(request):
    if not request.session.get("student_logged_in"):
        return redirect("students:student_login")
    return render(request, "students/student_dashboard.html", {"username": request.session.get("student_username", "Student")})


def student_logout(request):
    request.session.flush()
    return redirect("students:student_login")