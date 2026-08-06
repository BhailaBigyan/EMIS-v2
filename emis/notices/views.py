from django.shortcuts import render

# Create your views here.
def notice_list(request):
    # This view will handle the logic for displaying a list of notices.
    # You can fetch the notices from the database and pass them to the template.
    return render(request, 'admin\\notices_management\\list_notices.html')