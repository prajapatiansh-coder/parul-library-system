"""
Admin configuration for library_app.
Parul University - Library Management System

This file registers our models (Book, Student) with the Django admin panel
so we can manage them from http://127.0.0.1:8000/admin/
"""

from django.contrib import admin
from .models import Book, Student, IssueRecord


# ============================================================
# Book Admin - Customize how Books appear in the admin panel
# ============================================================

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Columns to display in the book list
    list_display = ('title', 'author', 'isbn', 'quantity')

    # Fields you can search by in the admin panel
    search_fields = ('title', 'author', 'isbn')

    # Filter sidebar options
    list_filter = ('author',)


# ============================================================
# Student Admin - Customize how Students appear in the admin panel
# ============================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Columns to display in the student list
    list_display = ('name', 'enrollment_no', 'email')

    # Fields you can search by in the admin panel
    search_fields = ('name', 'enrollment_no', 'email')


# ============================================================
# IssueRecord Admin - Manage book issue/return records
# ============================================================

@admin.register(IssueRecord)
class IssueRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issue_date', 'due_date', 'return_date')
    search_fields = ('book__title', 'student__name', 'student__enrollment_no')
    list_filter = ('issue_date', 'due_date', 'return_date')

