from django.shortcuts import render, redirect
from django.contrib import messages


def library_home(request):
    if request.session.get("library_logged_in"):
        return redirect('library:library_dashboard')
    return redirect('library:library_login')


def library_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if username and password:
            request.session["library_logged_in"] = True
            request.session["library_username"] = username
            messages.success(request, f"Welcome to Library Portal, {username}!")
            return redirect("library:library_dashboard")
        
        return render(request, "library/library_login.html", {"error": "Please enter a valid username and password."})

    if request.session.get("library_logged_in"):
        return redirect("library:library_dashboard")

    return render(request, 'library/library_login.html')


def library_dashboard(request):
    if not request.session.get("library_logged_in"):
        return redirect("library:library_login")

    username = request.session.get("library_username", "Member")
    context = {
        "username": username,
    }
    return render(request, 'library/library_dashboard.html', context)


def library_logout(request):
    request.session.pop("library_logged_in", None)
    request.session.pop("library_username", None)
    messages.info(request, "Logged out from Library Portal.")
    return redirect("library:library_login")