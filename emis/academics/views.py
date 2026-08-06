from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required



# Classes Management Views
def classes_list(request):
    if not request.session.get("general_logged_in"):
        return redirect("general_login")
    # Fetch classes data from the database (replace with actual model query)
    classes = []  # Replace with actual query to fetch classes
    return render(request, "admin/classes_management/list_classes.html", {"classes": classes})