from django.shortcuts import redirect, render
from students.models import Students

def home(request):
    if request.session.get("general_logged_in"):
        return redirect("general_dashboard")
    return render(request, 'index.html')


def general_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username == "admin" and password == "admin123":
            request.session["general_logged_in"] = True
            request.session["general_username"] = username
            return redirect("general_dashboard")
        return render(request, "index.html", {"error": "Invalid username or password"})

    if request.session.get("general_logged_in"):
        return redirect("general_dashboard")
    return render(request, "index.html")


def general_dashboard(request):
    if not request.session.get("general_logged_in"):
        return redirect("general_login")
    return render(request, "general_dashboard.html", {"username": request.session.get("general_username", "Admin")})


def general_logout(request):
    request.session.flush()
    return redirect("home")

# Student Management Views
def student_list(request):
    if not request.session.get("general_logged_in"):
        return redirect("general_login")
    # Fetch student data from the database (replace with actual model query)
    students = Students.objects.all()
    return render(request, "admin/students_management/list_students.html", {"students": students})

