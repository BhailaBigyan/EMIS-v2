from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.general_login, name='general_login'),
    path('dashboard/', views.general_dashboard, name='general_dashboard'),
    path('logout/', views.general_logout, name='general_logout'),

    # Student portal
    path('students/', include(('students.urls', 'students'), namespace='students')),

    # Admin Student Management URLs
    path('dashboard/students/', views.student_list, name='student_list'),
    path('dashboard/students/add/', views.student_add, name='student_add'),
    path('dashboard/students/bulk-upload/', views.student_bulk_upload, name='student_bulk_upload'),
    path('dashboard/students/bulk-summary/', views.student_bulk_summary, name='student_bulk_summary'),
    path('dashboard/students/<int:student_id>/', views.student_profile, name='student_profile'),
    path('dashboard/students/<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('dashboard/students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('dashboard/students/export/', views.student_export_csv, name='student_export_csv'),
    path('dashboard/students/sample-csv/', views.download_sample_csv_view, name='download_sample_csv'),
    path('dashboard/students/sample-excel/', views.download_sample_excel_view, name='download_sample_excel'),

    # Academics management URLs
    path('dashboard/academics/', include(('academics.urls', 'academics'), namespace='academics')),

    # Examinations management URLs
    path('dashboard/examinations/', include(('examinations.urls', 'examinations'), namespace='examinations')),

    # Finances management URLs
    path('dashboard/finances/', include(('finances.urls', 'finances'), namespace='finances')),

    # Notices management URLs
    path('dashboard/notices/', include(('notices.urls', 'notices'), namespace='notices')),

    # Teachers management URLs
    path('dashboard/teachers/', include(('teachers.urls', 'teachers'), namespace='teachers')),

    # Library Portal URLs
    path('library/', include(('library.urls', 'library'), namespace='library')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
