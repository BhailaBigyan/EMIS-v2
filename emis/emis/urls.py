
from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.general_login, name='general_login'),
    path('dashboard/', views.general_dashboard, name='general_dashboard'),
    path('logout/', views.general_logout, name='general_logout'),
    
    # Student portal
    path('students/', include(('students.urls', 'students'), namespace='students')),
    
    # student management URLs
    path('dashboard/students/', views.student_list, name='student_list'),
    
    # Academics management URLs
    path('dashboard/academics/', include(('academics.urls', 'academics'), namespace='academics')),
    
    # Examinations management URLs
    path('dashboard/examinations/', include(('examinations.urls', 'examinations'), namespace='examinations')),
    
    # Finances management URLs
    path('dashboard/finances/', include(('finances.urls', 'finances'), namespace='finances')),
    
    # Notices management URLs
    path('dashboard/notices/', include(('notices.urls', 'notices'), namespace='notices')),
    
    # Library Portal URLs
    path('library/', include(('library.urls', 'library'), namespace='library')),
]
