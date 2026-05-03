"""
Models for library_app.
Parul University - Library Management System

This file defines the database tables (models) for:
- Book:    Stores information about each book in the library
- Student: Stores information about each registered student
"""

from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    """
    Book Model - Represents a book in the library.
    
    Fields:
        title    - Name of the book
        author   - Author of the book
        isbn     - International Standard Book Number (unique identifier)
        quantity - Number of copies available in the library
    """
    title = models.CharField(max_length=200, help_text="Enter the book title")
    author = models.CharField(max_length=200, help_text="Enter the author name")
    isbn = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="ISBN",
        help_text="Enter 13-digit ISBN number"
    )
    quantity = models.PositiveIntegerField(default=1, help_text="Number of copies available")

    class Meta:
        ordering = ['title']  # Books will be listed alphabetically by title
        verbose_name = "Book"
        verbose_name_plural = "Books"

    def __str__(self):
        """This is what will be displayed when we print a Book object"""
        return f"{self.title} by {self.author}"


class Student(models.Model):
    """
    Student Model - Represents a registered student/member.
    
    Fields:
        name          - Full name of the student
        enrollment_no - Unique enrollment/roll number
        email         - Student's email address
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile'
    )
    name = models.CharField(max_length=200, help_text="Enter the student's full name")
    enrollment_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Enrollment No.",
        help_text="Enter unique enrollment number"
    )
    email = models.EmailField(help_text="Enter the student's email address")
    photo = models.ImageField(
        upload_to='students/',
        null=True,
        blank=True,
        help_text="Upload student photo"
    )

    class Meta:
        ordering = ['name']  # Students will be listed alphabetically by name
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        """This is what will be displayed when we print a Student object"""
        return f"{self.name} ({self.enrollment_no})"


class IssueRecord(models.Model):
    """
    IssueRecord Model - Tracks which book was issued to which student.

    Fields:
        student     - The student who borrowed the book (ForeignKey to Student)
        book        - The book that was borrowed (ForeignKey to Book)
        issue_date  - Date when the book was issued (auto-set on creation)
        due_date    - Date by which the book should be returned
        return_date - Date when the book was actually returned (null if not returned yet)
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='issued_books',
        help_text="Select the student"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='issue_records',
        help_text="Select the book"
    )
    issue_date = models.DateField(auto_now_add=True, help_text="Date of issue (auto-filled)")
    due_date = models.DateField(help_text="Date by which book must be returned")
    return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when book was returned (empty if not returned)"
    )

    class Meta:
        ordering = ['-issue_date']  # Most recent issues first
        verbose_name = "Issue Record"
        verbose_name_plural = "Issue Records"

    def __str__(self):
        return f"{self.book.title} → {self.student.name}"

    @property
    def is_returned(self):
        """Check if the book has been returned"""
        return self.return_date is not None

    @property
    def is_overdue(self):
        """
        Check if the book is overdue.
        A book is overdue if:
        - It has NOT been returned yet AND
        - Today's date is PAST the due date
        """
        if self.is_returned:
            return False  # Already returned, not overdue
        from django.utils import timezone
        return timezone.now().date() > self.due_date

    @property
    def fine_amount(self):
        """
        Calculate the fine amount for returned books.
        Rate: ₹5 per day late.
        """
        if self.return_date and self.return_date > self.due_date:
            days_late = (self.return_date - self.due_date).days
            return days_late * 5
        return 0

    @property
    def overdue_days(self):
        """
        Calculate number of days late for books not yet returned.
        """
        from django.utils import timezone
        if not self.return_date and self.due_date < timezone.now().date():
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def estimated_fine(self):
        """
        Calculate estimated fine for overdue books that are NOT yet returned.
        """
        return self.overdue_days * 5
