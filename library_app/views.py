from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Book, Student, IssueRecord


# =========================
# LOGIN VIEW (WORKING)
# =========================

def login_view(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == "admin" and password == "Admin@123":
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'library_app/login.html')


# =========================
# DASHBOARD
# =========================

def dashboard_view(request):

    today = timezone.now().date()
    two_days_later = today + timedelta(days=2)

    total_books = Book.objects.count()
    total_students = Student.objects.count()
    books_issued = IssueRecord.objects.filter(return_date__isnull=True).count()
    overdue_count = IssueRecord.objects.filter(return_date__isnull=True, due_date__lt=today).count()
    returned_records = IssueRecord.objects.filter(return_date__isnull=False)
    total_fines_collected = sum(record.fine_amount for record in returned_records)

    due_soon_list = IssueRecord.objects.filter(return_date__isnull=True, due_date__gte=today, due_date__lte=two_days_later)
    overdue_list = IssueRecord.objects.filter(return_date__isnull=True, due_date__lt=today)

    return render(request, 'library_app/dashboard.html', {
        'total_books': total_books,
        'total_students': total_students,
        'books_issued': books_issued,
        'overdue_count': overdue_count,
        'total_fines_collected': total_fines_collected,
        'due_soon_list': due_soon_list,
        'overdue_list': overdue_list,
    })


# =========================
# BOOK VIEWS
# =========================

def book_list(request):
    query = request.GET.get('q')
    books_list = Book.objects.filter(title__icontains=query) if query else Book.objects.all()

    paginator = Paginator(books_list, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'library_app/book_list.html', {
        'books': page_obj,
        'search_query': query,
    })


def book_add(request):
    if request.method == 'POST':
        Book.objects.create(
            title=request.POST.get('title'),
            author=request.POST.get('author'),
            isbn=request.POST.get('isbn'),
            quantity=int(request.POST.get('quantity') or 1),
        )
        messages.success(request, 'Book added successfully!')
        return redirect('book_list')

    return render(request, 'library_app/book_form.html')


def book_edit(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.isbn = request.POST.get('isbn')
        book.quantity = int(request.POST.get('quantity') or 1)
        book.save()
        return redirect('book_list')

    return render(request, 'library_app/book_form.html', {'book': book})


def book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    return redirect('book_list')


# =========================
# STUDENT VIEWS
# =========================

def student_list(request):
    query = request.GET.get('q')
    students = Student.objects.filter(
        Q(name__icontains=query) | Q(enrollment_no__icontains=query)
    ) if query else Student.objects.all()

    paginator = Paginator(students, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'library_app/student_list.html', {
        'students': page_obj,
        'search_query': query
    })


def student_add(request):
    if request.method == 'POST':
        Student.objects.create(
            name=request.POST.get('name'),
            enrollment_no=request.POST.get('enrollment_no'),
            email=request.POST.get('email'),
        )
        return redirect('student_list')

    return render(request, 'library_app/student_form.html')


def student_edit(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        student.name = request.POST.get('name')
        student.enrollment_no = request.POST.get('enrollment_no')
        student.email = request.POST.get('email')
        student.save()
        return redirect('student_list')

    return render(request, 'library_app/student_form.html', {'student': student})


def student_delete(request, student_id):
    get_object_or_404(Student, id=student_id).delete()
    return redirect('student_list')


# =========================
# ISSUE / RETURN
# =========================

def issue_book(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=request.POST.get('student'))
        book = get_object_or_404(Book, id=request.POST.get('book'))

        if book.quantity <= 0:
            messages.error(request, 'Book out of stock')
            return redirect('issue_book')

        IssueRecord.objects.create(
            student=student,
            book=book,
            due_date=request.POST.get('due_date')
        )

        book.quantity -= 1
        book.save()

        return redirect('issued_list')

    return render(request, 'library_app/issue_book.html', {
        'students': Student.objects.all(),
        'books': Book.objects.filter(quantity__gt=0),
    })


def return_book(request, record_id):
    record = get_object_or_404(IssueRecord, id=record_id)

    record.return_date = timezone.now().date()
    record.save()

    record.book.quantity += 1
    record.book.save()

    return redirect('issued_list')


def issued_list(request):
    records = IssueRecord.objects.select_related('student', 'book')
    return render(request, 'library_app/issued_list.html', {'records': records}) 
def student_id_card(request, student_id):
    return render(request, 'library_app/id_card.html')    