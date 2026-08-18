from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from emis.decorators import admin_login_required
from .models import Notice
from .forms import NoticeForm


@admin_login_required
def notice_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    important = request.GET.get('important', '')

    notices = Notice.objects.all()

    if query:
        notices = notices.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    if category:
        notices = notices.filter(category=category)

    if important:
        notices = notices.filter(is_important=True)

    context = {
        'notices': notices,
        'query': query,
        'selected_category': category,
        'important_only': important,
    }
    return render(request, 'admin/notices_management/list_notices.html', context)


@admin_login_required
def notice_add(request):
    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f"Notice '{notice.title}' published.")
            return redirect('notices:notice_list')
    else:
        form = NoticeForm()

    return render(request, 'admin/notices_management/notice_form.html', {'form': form, 'title': 'Add Notice'})


@admin_login_required
def notice_edit(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    if request.method == "POST":
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, f"Notice '{notice.title}' updated.")
            return redirect('notices:notice_list')
    else:
        form = NoticeForm(instance=notice)

    return render(request, 'admin/notices_management/notice_form.html', {'form': form, 'title': 'Edit Notice'})


@admin_login_required
def notice_delete(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    if request.method == "POST":
        title = notice.title
        notice.delete()
        messages.success(request, f"Notice '{title}' deleted.")
        return redirect('notices:notice_list')

    return render(request, 'admin/notices_management/notice_delete.html', {'notice': notice})
