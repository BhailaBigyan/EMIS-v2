from django.shortcuts import render, redirect
from emis.decorators import admin_login_required


@admin_login_required
def notice_list(request):
    # Notices module — future implementation
    return render(request, 'admin/notices_management/list_notices.html')