from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_important', 'published_date', 'created_at')
    list_filter = ('category', 'is_important')
    search_fields = ('title', 'content')
    list_editable = ('is_important',)
    date_hierarchy = 'published_date'