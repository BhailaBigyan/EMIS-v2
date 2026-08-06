from django.shortcuts import render

# Create your views here.
def fee_structure_list(request):
    # This view will handle the logic for displaying a list of fee structures.
    # You can fetch the fee structures from the database and pass them to the template.
    return render(request, 'admin\\finances_management\\list_fee_structures.html')