from django.shortcuts import render

# Create your views here.
def library_home(request):
    return render(request, 'library/library_home.html')

def library_login(request):
    return render(request, 'library/library_login.html')

def library_dashboard(request):
    return render(request, 'library/library_dashboard.html')