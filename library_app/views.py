"""
Views for library_app.
Parul University - Library Management System

This file contains the view functions for:

Authentication:
- login_view, dashboard_view, logout_view

Book CRUD:
- book_list, book_add, book_edit, book_delete

Student CRUD:
- student_list, student_add, student_edit, student_delete

Issue / Return:
- issue_book:    Issue a book to a student (reduces quantity)
- return_book:   Return a book (sets return_date, increases quantity)
- issued_list:   View all issued book records with overdue status
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Book, Student, IssueRecord


# ============================================================
# Authentication Views (Login / Dashboard / Logout)
# ============================================================

def login_view(request):
    from django.contrib.auth.models import User

    # AUTO CREATE ADMIN USER
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@gmail.com", "Admin@123")

   print("USERS:", User.objects.all())

    # If user already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Login logic
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'library_app/login.html')

    """
    Handles the login page.

    GET  -> Displays the login form
    POST -> Validates username/password and logs in the user

    If the user is already logged in, redirect them to dashboard.
    """

    # If user is already logged in, send them to dashboard directly
    if request.user.is_authenticated:
        return redirect('dashboard')

    # When the form is submitted (POST request)
    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user using Django's built-in authentication
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If credentials are correct, log in the user
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')  # Redirect to dashboard
        else:
            # If credentials are wrong, show error message
            messages.error(request, 'Invalid username or password. Please try again.')

    # Render the login page (for GET request or failed login)
    return render(request, 'library_app/login.html')


@login_required
def dashboard_view(request):
    """
    Main dashboard controller.
    Staff -> Show admin statistics
    Student -> Redirect to student_dashboard
    """
    if not request.user.is_staff:
        return redirect('student_dashboard')

    today = timezone.now().date()
    two_days_later = today + timedelta(days=2)

    # Admin Statistics
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    books_issued = IssueRecord.objects.filter(return_date__isnull=True).count()
    overdue_count = IssueRecord.objects.filter(return_date__isnull=True, due_date__lt=today).count()
    returned_records = IssueRecord.objects.filter(return_date__isnull=False)
    total_fines_collected = sum(record.fine_amount for record in returned_records)

    # Reminders
    due_soon_list = IssueRecord.objects.filter(return_date__isnull=True, due_date__gte=today, due_date__lte=two_days_later).select_related('student', 'book')
    overdue_list = IssueRecord.objects.filter(return_date__isnull=True, due_date__lt=today).select_related('student', 'book')

    context = {
        'total_books': total_books,
        'total_students': total_students,
        'books_issued': books_issued,
        'overdue_count': overdue_count,
        'total_fines_collected': total_fines_collected,
        'due_soon_list': due_soon_list,
        'overdue_list': overdue_list,
    }
    return render(request, 'library_app/dashboard.html', context)


@login_required
def student_dashboard(request):
    """
    Dashboard for students to view their own issued books and fines.
    """
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.warning(request, "You are logged in as a student but don't have a library profile.")
        return render(request, 'library_app/student_dashboard.html', {'records': []})

    records = IssueRecord.objects.filter(student=student).select_related('book').order_by('-issue_date')
    return render(request, 'library_app/student_dashboard.html', {
        'student': student,
        'records': records
    })


def logout_view(request):
    """
    Logs out the user and redirects to the login page.
    """
    logout(request)  # Django's built-in logout function
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')  # Redirect to login page


# ============================================================
# Book CRUD Views
# ============================================================

@login_required
def book_list(request):
    """
    Display a list of all books in the library with pagination.
    Includes search functionality by title.
    """
    # Note: Book list is visible to everyone, but actions are hidden in template.
    query = request.GET.get('q')
    if query:
        books_list = Book.objects.filter(title__icontains=query)
    else:
        books_list = Book.objects.all()
    
    # Pagination: 5 books per page
    paginator = Paginator(books_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library_app/book_list.html', {
        'books': page_obj,  # Passing the page object as 'books'
        'search_query': query,
    })


@login_required
def book_add(request):
    """
    Add a new book. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        quantity = request.POST.get('quantity')

        # Check if ISBN already exists
        if Book.objects.filter(isbn=isbn).exists():
            messages.error(request, f'A book with ISBN "{isbn}" already exists.')
            return render(request, 'library_app/book_form.html', {
                'form_title': 'Add New Book',
                'form_data': request.POST,  # Pass back the entered data
            })

        # Create and save the new book
        Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            quantity=int(quantity) if quantity else 1,
        )
        messages.success(request, f'Book "{title}" has been added successfully!')
        return redirect('book_list')

    # GET request - show empty form
    return render(request, 'library_app/book_form.html', {
        'form_title': 'Add New Book',
    })


@login_required
def book_edit(request, book_id):
    """
    Edit an existing book. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    # Get the book or return 404 if not found
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        # Update the book fields
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.isbn = request.POST.get('isbn')
        quantity = request.POST.get('quantity')
        book.quantity = int(quantity) if quantity else 1
        book.save()  # Save changes to database

        messages.success(request, f'Book "{book.title}" has been updated successfully!')
        return redirect('book_list')

    # GET request - show form with current book data
    return render(request, 'library_app/book_form.html', {
        'form_title': 'Edit Book',
        'book': book,
    })


@login_required
def book_delete(request, book_id):
    """
    Delete a book from the library.
    Security: Staff only, POST only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        book_title = book.title
        book.delete()
        messages.success(request, f'Book "{book_title}" has been deleted successfully!')
    else:
        messages.warning(request, "Delete operation must be via POST.")
        
    return redirect('book_list')


# ============================================================
# Student CRUD Views
# ============================================================

@login_required
def student_list(request):
    """
    Display a list of all registered students with pagination.
    Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    query = request.GET.get('q')
    if query:
        students_list = Student.objects.filter(
            Q(name__icontains=query) | Q(enrollment_no__icontains=query)
        )
    else:
        students_list = Student.objects.all()
    
    # Pagination: 5 students per page
    paginator = Paginator(students_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library_app/student_list.html', {
        'students': page_obj, 
        'search_query': query
    })


@login_required
def student_add(request):
    """
    Add a new student. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        enrollment_no = request.POST.get('enrollment_no')
        email = request.POST.get('email')
        photo = request.FILES.get('photo')

        # Check if enrollment number already exists
        if Student.objects.filter(enrollment_no=enrollment_no).exists():
            messages.error(request, f'A student with enrollment no. "{enrollment_no}" already exists.')
            return render(request, 'library_app/student_form.html', {
                'form_title': 'Add New Student',
                'form_data': request.POST,
            })

        # Create and save the new student
        Student.objects.create(
            name=name,
            enrollment_no=enrollment_no,
            email=email,
            photo=photo,
        )
        messages.success(request, f'Student "{name}" has been added successfully!')
        return redirect('student_list')

    # GET request - show empty form
    return render(request, 'library_app/student_form.html', {
        'form_title': 'Add New Student',
    })


@login_required
def student_edit(request, student_id):
    """
    Edit an existing student. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        student.name = request.POST.get('name')
        student.enrollment_no = request.POST.get('enrollment_no')
        student.email = request.POST.get('email')
        if request.FILES.get('photo'):
            student.photo = request.FILES.get('photo')
        student.save()

        messages.success(request, f'Student "{student.name}" has been updated successfully!')
        return redirect('student_list')

    return render(request, 'library_app/student_form.html', {
        'form_title': 'Edit Student',
        'student': student,
    })


@login_required
def student_delete(request, student_id):
    """
    Delete a student record.
    Security: Staff only, POST only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        student_name = student.name
        student.delete()
        messages.success(request, f'Student "{student_name}" has been deleted successfully!')
    else:
        messages.warning(request, "Delete operation must be via POST.")

    return redirect('student_list')


# ============================================================
# Issue / Return Book Views
# ============================================================

@login_required
def issue_book(request):
    """
    Issue a book to a student. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        book_id = request.POST.get('book')
        due_date = request.POST.get('due_date')

        # Get the student and book objects
        student = get_object_or_404(Student, id=student_id)
        book = get_object_or_404(Book, id=book_id)

        # 1. PREVENT DUPLICATE ISSUE
        # Check if this student already has this book issued and not returned
        already_issued = IssueRecord.objects.filter(
            student=student, 
            book=book, 
            return_date__isnull=True
        ).exists()

        if already_issued:
            messages.error(request, f'This student already has "{book.title}" issued and not returned.')
            return redirect('issue_book')

        # 2. VALIDATION: Check if the book has available copies
        if book.quantity <= 0:
            messages.error(request, f'Sorry, "{book.title}" is out of stock! No copies available.')
            return redirect('issue_book')

        # 3. TRANSACTION SAFETY: Use atomic transaction to ensure data integrity
        try:
            with transaction.atomic():
                # Create the issue record
                IssueRecord.objects.create(
                    student=student,
                    book=book,
                    due_date=due_date,
                )

                # Reduce book quantity by 1
                book.quantity -= 1
                book.save()

            messages.success(request, f'"{book.title}" has been issued to {student.name} successfully!')
            return redirect('issued_list')
        except Exception as e:
            messages.error(request, f'An error occurred during transaction: {str(e)}')
            return redirect('issue_book')

    # GET request - show the issue form
    students = Student.objects.all()
    books = Book.objects.filter(quantity__gt=0)  # Only show books with available copies
    # Default due date: 14 days from today
    default_due_date = (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d')

    return render(request, 'library_app/issue_book.html', {
        'students': students,
        'books': books,
        'default_due_date': default_due_date,
    })


@login_required
def return_book(request, record_id):
    """
    Return a previously issued book. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    record = get_object_or_404(IssueRecord, id=record_id)

    # 1. IMPROVE RETURN LOGIC: Check if already returned
    if record.is_returned:
        messages.warning(request, 'This book has already been returned.')
        return redirect('issued_list')

    # 2. TRANSACTION SAFETY: Mark as returned and increase quantity safely
    try:
        with transaction.atomic():
            # Set return date to today
            record.return_date = timezone.now().date()
            record.save()

            # Increase book quantity by 1 (book is back in library)
            record.book.quantity += 1
            record.book.save()

        messages.success(request, f'"{record.book.title}" has been returned by {record.student.name} successfully!')
    except Exception as e:
        messages.error(request, f'An error occurred while returning the book: {str(e)}')
    
    return redirect('issued_list')


@login_required
def issued_list(request):
    """
    Display a list of all issued book records. Staff only.
    """
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    records = IssueRecord.objects.select_related('student', 'book').all()
    return render(request, 'library_app/issued_list.html', {'records': records})


# ============================================================
# Student ID Card System
# ============================================================

@login_required
def student_id_card(request, student_id):
    """
    Generates and displays a digital ID card for a student.
    Staff can see anyone's card; Students can only see their own.
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Security: If not staff, must be the student owner
    if not request.user.is_staff:
        try:
            if request.user.student_profile.id != student.id:
                messages.error(request, "You can only view your own ID card.")
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            return redirect('login')

    # Generate QR Code
    import qrcode
    from io import BytesIO
    import base64
    
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(f"Parul University\nName: {student.name}\nEnroll: {student.enrollment_no}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'library_app/id_card.html', {
        'student': student,
        'qr_code': qr_base64,
    })


# ============================================================
# PDF Report Generation
# ============================================================

@login_required
def generate_pdf_report(request):
    """
    Generates a PDF report of library issued records.
    Admin gets all records, Student gets their own records.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    from django.http import HttpResponse

    # Determine records to include
    if request.user.is_staff:
        records = IssueRecord.objects.select_related('student', 'book').all()
        title_text = "Full Library Issued Records"
    else:
        try:
            student = request.user.student_profile
            records = IssueRecord.objects.filter(student=student).select_related('book')
            title_text = f"Library Records: {student.name}"
        except Student.DoesNotExist:
            return HttpResponse("Student profile not found.")

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph(f"<b>Parul University Library</b>", styles['Title']))
    elements.append(Paragraph(title_text, styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Table Data
    data = [['Student', 'Book', 'Issue Date', 'Due Date', 'Fine']]
    for r in records:
        data.append([
            r.student.name if request.user.is_staff else "Self",
            r.book.title,
            r.issue_date.strftime('%d-%m-%Y'),
            r.due_date.strftime('%d-%m-%Y'),
            f"Rs. {r.fine_amount}"
        ])

    # Styling Table
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)

    # Build PDF
    doc.build(elements)
    
    # Return response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="library_report.pdf"'
    return response
