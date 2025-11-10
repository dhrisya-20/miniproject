from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Book, Author, Category, Member, IssuedBook
from django.utils import timezone


# ---------------- Home ----------------
def home(request):
    return render(request, 'home.html')


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('user_dashboard')  # change this to your user homepage
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'user_login.html')

    return render(request, 'user_login.html')
# ---------------- Logout ----------------
def user_logout(request):
    logout(request)
    return render(request, 'logout.html')

def admin_logout(request):
    logout(request)
    return render(request, 'admin_logout.html')

# ---------------- Admin Views ----------------
def admin_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid admin credentials.')
    return render(request, 'admin_login.html')

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def manage_books(request):
    if request.method == 'POST':
        title = request.POST['title']
        author_name = request.POST['author']
        category_name = request.POST['category']
        author, _ = Author.objects.get_or_create(name=author_name)
        category, _ = Category.objects.get_or_create(name=category_name)
        Book.objects.create(title=title, author=author, category=category)
    books = Book.objects.all()
    return render(request, 'manage_books.html', {'books': books})

def manage_authors(request):
    if request.method == 'POST':
        Author.objects.create(
            name=request.POST['author_name'],
            bio=request.POST.get('author_bio', '')
        )
    authors = Author.objects.all()
    return render(request, 'manage_authors.html', {'authors': authors})

def manage_categories(request):
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST['category_name'],
            description=request.POST.get('category_description', '')
        )
    categories = Category.objects.all()
    return render(request, 'manage_categories.html', {'categories': categories})

def manage_members(request):
    members = User.objects.filter(is_staff=False)
    return render(request, 'manage_members.html', {'members': members})

def track_issues(request):
    issues = IssuedBook.objects.select_related('book', 'user').all()
    return render(request, 'track_issues.html', {'issues': issues})

# ---------------- User Views ----------------
def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Simple validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('user_register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('user_register')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, "Registration successful! You can now log in.")
        return redirect('user_login')

    return render(request, 'user_register.html')

def user_dashboard(request):
    return render(request, 'user_dashboard.html')

def browse_books(request):
    books = Book.objects.filter(is_available=True)
    return render(request, 'browse_books.html', {'books': books})

def search_books(request):
    query = request.GET.get('q', '')
    books = Book.objects.filter(title__icontains=query) | Book.objects.filter(author__name__icontains=query)
    return render(request, 'search_books.html', {'books': books, 'query': query})

def issue_book(request):
    if request.method == 'POST':
        book_id = request.POST['book_id']
        book = get_object_or_404(Book, id=book_id)
        if book.is_available:
            IssuedBook.objects.create(user=request.user, book=book)
            book.is_available = False
            book.save()
            messages.success(request, 'Book issued successfully.')
        else:
            messages.error(request, 'Book is not available.')
    issued_books = Book.objects.filter(is_available=True)
    return render(request, 'issue_book.html', {'books': issued_books})

def return_book(request):
    if request.method == 'POST':
        issue_id = request.POST['issue_id']
        issue = get_object_or_404(IssuedBook, id=issue_id, user=request.user)
        issue.return_date = timezone.now().date()
        issue.book.is_available = True
        issue.book.save()
        issue.save()
        messages.success(request, 'Book returned successfully.')
    issued = IssuedBook.objects.filter(user=request.user, return_date__isnull=True)
    return render(request, 'return_book.html', {'issued_books': issued})

def admin_books(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        is_available = request.POST.get('is_available') == 'True'

        author = get_object_or_404(Author, id=author_id)
        category = Category.objects.filter(id=category_id).first()

        Book.objects.create(
            title=title,
            author=author,
            category=category,
            is_available=is_available
        )
        messages.success(request, f'Book "{title}" added successfully!')
        return redirect('admin_books')

    books = Book.objects.all()
    authors = Author.objects.all()
    categories = Category.objects.all()
    return render(request, 'admin_books.html', {
        'books': books,
        'authors': authors,
        'categories': categories,
    })


def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    authors = Author.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.author_id = request.POST.get('author')
        book.category_id = request.POST.get('category')
        book.is_available = request.POST.get('is_available') == 'True'
        book.save()
        messages.success(request, f'Book "{book.title}" updated successfully!')
        return redirect('admin_books')

    return render(request, 'edit_book.html', {
        'book': book,
        'authors': authors,
        'categories': categories
    })


def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    messages.success(request, f'Book "{book.title}" deleted successfully!')
    return redirect('admin_books')