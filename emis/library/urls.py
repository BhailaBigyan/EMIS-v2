from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Librarian portal (circulation desk)
    path('', views.library_home, name='library_home'),
    path('login/', views.library_login, name='library_login'),
    path('dashboard/', views.library_dashboard, name='library_dashboard'),
    path('catalog/', views.library_catalog, name='library_catalog'),
    path('issue/', views.issue_book, name='issue_book'),
    path('loans/', views.library_loans, name='library_loans'),
    path('return/<int:borrowing_id>/', views.return_book, name='return_book'),
    path('logout/', views.library_logout, name='library_logout'),

    # Admin: books
    path('admin/books/', views.admin_book_list, name='admin_book_list'),
    path('admin/books/add/', views.admin_book_add, name='admin_book_add'),
    path('admin/books/<int:book_id>/edit/', views.admin_book_edit, name='admin_book_edit'),
    path('admin/books/<int:book_id>/delete/', views.admin_book_delete, name='admin_book_delete'),

    # Admin: categories
    path('admin/categories/', views.admin_category_list, name='admin_category_list'),
    path('admin/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('admin/categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),

    # Admin: librarian accounts
    path('admin/librarians/', views.admin_librarian_list, name='admin_librarian_list'),
    path('admin/librarians/add/', views.admin_librarian_add, name='admin_librarian_add'),
    path('admin/librarians/<int:librarian_id>/edit/', views.admin_librarian_edit, name='admin_librarian_edit'),

    # Admin: circulation oversight
    path('admin/borrowings/', views.admin_borrowing_list, name='admin_borrowing_list'),
    path('admin/borrowings/<int:borrowing_id>/return/', views.admin_return_book, name='admin_return_book'),
]