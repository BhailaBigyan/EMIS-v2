from django.shortcuts import render

# from emis.examinations.models import Exam

# Create your views here.
def exam_list(request):
    # This view will handle the logic for displaying a list of exams.
    # You can fetch the exams from the database and pass them to the template.
    # exams = Exam.objects.all()  # Assuming you have an Exam model defined in models.py
    return render(request, 'admin\\examinations_management\\list_examinations.html')