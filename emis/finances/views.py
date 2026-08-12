from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from emis.decorators import admin_login_required
from .models import FeeStructure, FeePayment, StudentFeeAccount, Salary
from .forms import FeeStructureForm, FeePaymentForm, SalaryForm
from students.models import Students


@admin_login_required
def fee_structure_list(request):
    fee_structures = FeeStructure.objects.select_related('program', 'academic_year').all()
    return render(request, "admin/finances_management/list_fee_structures.html", {"fee_structures": fee_structures})


@admin_login_required
def fee_structure_add(request):
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fs = form.save()
            messages.success(request, f"Fee structure '{fs.name}' created.")
            return redirect("finances:fee_structure_list")
    else:
        form = FeeStructureForm()

    return render(request, "admin/finances_management/fee_structure_form.html", {"form": form, "title": "Add Fee Structure"})


@admin_login_required
def fee_structure_edit(request, fs_id):
    fs = get_object_or_404(FeeStructure, id=fs_id)
    if request.method == "POST":
        form = FeeStructureForm(request.POST, instance=fs)
        if form.is_valid():
            form.save()
            messages.success(request, f"Fee structure '{fs.name}' updated.")
            return redirect("finances:fee_structure_list")
    else:
        form = FeeStructureForm(instance=fs)

    return render(request, "admin/finances_management/fee_structure_form.html", {"form": form, "title": "Edit Fee Structure"})


@admin_login_required
def fee_structure_delete(request, fs_id):
    fs = get_object_or_404(FeeStructure, id=fs_id)
    if request.method == "POST":
        name = fs.name
        fs.delete()
        messages.success(request, f"Fee structure '{name}' deleted.")
        return redirect("finances:fee_structure_list")
    return render(request, "admin/finances_management/fee_structure_delete.html", {"fee_structure": fs})


@admin_login_required
def payment_list(request):
    payments = FeePayment.objects.select_related('student', 'fee_structure').all()
    total_collected = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    context = {
        'payments': payments,
        'total_collected': total_collected,
    }
    return render(request, "admin/finances_management/payment_list.html", context)


@admin_login_required
def record_payment(request):
    if request.method == "POST":
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()

            # Update or create student fee account
            account, created = StudentFeeAccount.objects.get_or_create(
                student=payment.student,
                fee_structure=payment.fee_structure,
                defaults={'total_due': payment.fee_structure.total_fee}
            )
            account.total_paid += payment.amount_paid
            account.save()

            messages.success(
                request,
                f"Payment recorded! Receipt No: {payment.receipt_number} for student {payment.student.roll_number}."
            )
            return redirect("finances:payment_receipt", payment_id=payment.id)
    else:
        initial_student = request.GET.get('student_id')
        form = FeePaymentForm(initial={'student': initial_student} if initial_student else None)

    return render(request, "admin/finances_management/record_payment.html", {"form": form})


@admin_login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(FeePayment.objects.select_related('student', 'fee_structure__program'), id=payment_id)
    return render(request, "admin/finances_management/payment_receipt.html", {"payment": payment})


@admin_login_required
def student_fee_status(request):
    query = request.GET.get('q', '').strip()
    accounts = StudentFeeAccount.objects.select_related('student__program', 'fee_structure').all()

    if query:
        accounts = accounts.filter(
            Q(student__roll_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )

    context = {
        'accounts': accounts,
        'query': query,
    }
    return render(request, "admin/finances_management/student_fee_status.html", context)


@admin_login_required
def finance_dashboard(request):
    total_collections = FeePayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_due_agg = StudentFeeAccount.objects.aggregate(total_due=Sum('total_due'), total_paid=Sum('total_paid'))
    
    total_due = total_due_agg['total_due'] or 0
    total_paid = total_due_agg['total_paid'] or 0
    total_pending_dues = max(0, total_due - total_paid)
    
    recent_payments = FeePayment.objects.select_related('student', 'fee_structure').all()[:10]
    total_payments_count = FeePayment.objects.count()

    context = {
        'total_collections': total_collections,
        'total_pending_dues': total_pending_dues,
        'total_due': total_due,
        'total_paid': total_paid,
        'recent_payments': recent_payments,
        'total_payments_count': total_payments_count,
    }
    return render(request, "admin/finances_management/finance_dashboard.html", context)


@admin_login_required
def salary_list(request):
    salaries = Salary.objects.select_related('teacher').all()
    total_disbursed = salaries.filter(payment_status='paid').aggregate(Sum('base_salary'))['base_salary__sum'] or 0
    
    context = {
        'salaries': salaries,
        'total_disbursed': total_disbursed,
    }
    return render(request, "admin/finances_management/salary_list.html", context)


@admin_login_required
def record_salary(request):
    if request.method == "POST":
        form = SalaryForm(request.POST)
        if form.is_valid():
            sal = form.save()
            messages.success(request, f"Salary record saved for {sal.teacher.full_name} ({sal.month}).")
            return redirect("finances:salary_list")
    else:
        form = SalaryForm()

    return render(request, "admin/finances_management/record_salary.html", {"form": form})