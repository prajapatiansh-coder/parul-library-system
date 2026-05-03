"""
URL configuration for library_app.
Parul University - Library Management System

This file defines the URL patterns for:
- Authentication: Login, Dashboard, Logout
- Book CRUD:      List, Add, Edit, Delete
- Student CRUD:   List, Add, Edit, Delete
- Issue/Return:   Issue Book, Return Book, Issued Records
"""

from django.urls import path
from . import views  # Import views from current app

urlpatterns = [
    # ---- Authentication URLs ----
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # ---- Book CRUD URLs ----
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/edit/<int:book_id>/', views.book_edit, name='book_edit'),
    path('books/delete/<int:book_id>/', views.book_delete, name='book_delete'),

    # ---- Student CRUD URLs ----
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<int:student_id>/', views.student_edit, name='student_edit'),
    path('students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('students/id/<int:student_id>/', views.student_id_card, name='student_id_card'),

    # ---- Issue / Return URLs ----
    path('issue/', views.issue_book, name='issue_book'),                         # Issue a book
    path('return/<int:record_id>/', views.return_book, name='return_book'),       # Return a book
    path('issued/', views.issued_list, name='issued_list'),                       # View all records

    # Dashboard & Reports
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('report/pdf/', views.generate_pdf_report, name='generate_pdf_report'),
]
