from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from .models import Book, Author, Category, Member, IssuedBook
from django.utils import timezone
from datetime import datetime
from django.db import transaction,IntegrityError
from django.core.paginator import Paginator
from datetime import timedelta
from .models import IssuedBook as Issue
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme






# ---------------- Home ----------------
def home(request):
    return render(request, 'home.html')


# ---------------- Authentication ----------------
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user_dashboard')  # change to the desired user homepage
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'user_login.html')

    return render(request, 'user_login.html')


def user_logout(request):
    logout(request)
    return render(request, 'user_logout.html')


def admin_logout(request):
    logout(request)
    return render(request, 'admin_logout.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid admin credentials.')
    return render(request, 'admin_login.html')


def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


def manage_books(request):

    def parse_int(value, default=1):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    # Common context pieces (will be overwritten/extended where needed)
    authors_qs = Author.objects.all().order_by('name')
    categories_qs = Category.objects.all().order_by('name')
    books_qs = Book.objects.select_related('author', 'category').all().order_by('-id')

    if request.method == 'POST':
        action = request.POST.get('action', 'add')
        title = request.POST.get('title', '').strip()
        author_name = request.POST.get('author', '').strip()
        category_name = request.POST.get('category', '').strip()
        cover = request.FILES.get('cover_image')

        # ------------- EDIT -------------
        if action == 'edit':
            book_id = request.POST.get('book_id')
            if not book_id:
                messages.error(request, 'Missing book id for edit.')
                return redirect('manage_books')

            book = get_object_or_404(Book, id=book_id)

            # Basic required fields check
            if not (title and author_name and category_name):
                messages.error(request, 'Title, author and category are required.')
                # Render with submitted values and disable_submit True
                temp = Book()  # temp, not saved
                temp.id = book.id
                temp.title = title
                temp.author = Author.objects.filter(name__iexact=author_name).first() or None
                temp.category = Category.objects.filter(name__iexact=category_name).first() or None
                temp.isbn = request.POST.get('isbn', '').strip()
                temp.publisher = request.POST.get('publisher', '').strip()
                # keep publication_date from incoming if parseable
                try:
                    temp.publication_date = datetime.strptime(request.POST.get('publication_date', ''), '%Y-%m-%d').date()
                except Exception:
                    temp.publication_date = None
                temp.description = request.POST.get('description', '').strip()
                temp.total_copies = parse_int(request.POST.get('total_copies'), default=1)
                temp.available_copies = parse_int(request.POST.get('available_copies', default=1))

                context = {
                    'books': books_qs,
                    'edit_book': temp,
                    'authors': authors_qs,
                    'categories': categories_qs,
                    'disable_submit': True,
                }
                return render(request, 'manage_books.html', context)

            # find or create author/category
            author = Author.objects.filter(name__iexact=author_name).first()
            if not author:
                author = Author.objects.create(name=author_name)

            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                category = Category.objects.create(name=category_name)

            # parse publication_date
            date_str = request.POST.get('publication_date')
            try:
                pub_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            except (ValueError, TypeError):
                pub_date = None

            # <<< ADDED: check publication date not in future (edit)
            if pub_date:
                today = datetime.today().date()
                if pub_date > today:
                    messages.error(request, "Publication date cannot be in the future.", extra_tags="publication")
                    # create temp object to re-populate the form (so user doesn't lose input)
                    temp = Book()  # not saved
                    temp.id = book.id
                    temp.title = title
                    temp.author = author
                    temp.category = category
                    temp.isbn = request.POST.get('isbn', '').strip()
                    temp.publisher = request.POST.get('publisher', '').strip()
                    temp.description = request.POST.get('description', '').strip()
                    temp.publication_date = pub_date
                    temp.total_copies = parse_int(request.POST.get('total_copies'), default=1)
                    temp.available_copies = parse_int(request.POST.get('available_copies'), default=1)

                    context = {
                        'books': books_qs,
                        'edit_book': temp,
                        'authors': authors_qs,
                        'categories': categories_qs,
                        'disable_submit': True,
                    }
                    return render(request, 'manage_books.html', context)
            # <<< END ADDED

            # update model fields
            book.title = title
            book.author = author
            book.category = category
            book.isbn = request.POST.get('isbn', '').strip()
            book.publisher = request.POST.get('publisher', '').strip()
            book.description = request.POST.get('description', '').strip()
            book.publication_date = pub_date

            book.total_copies = parse_int(request.POST.get('total_copies'), default=1)
            book.available_copies = parse_int(request.POST.get('available_copies'), default=1)

            # validation: available must not exceed total
            if book.available_copies > book.total_copies:
                messages.error(request, "Available copies cannot be greater than total copies.", extra_tags="available")

                # create temp object to re-populate the form (so user doesn't lose input)
                temp = Book()  # not saved
                temp.id = book.id
                temp.title = book.title
                temp.author = book.author
                temp.category = book.category
                temp.isbn = book.isbn
                temp.publisher = book.publisher
                temp.description = book.description
                temp.publication_date = book.publication_date
                # show the submitted values so they can correct them
                temp.total_copies = book.total_copies
                temp.available_copies = book.available_copies

                context = {
                    'books': books_qs,
                    'edit_book': temp,
                    'authors': authors_qs,
                    'categories': categories_qs,
                    'disable_submit': True,
                }
                return render(request, 'manage_books.html', context)

            # save cover if provided
            if cover:
                book.cover_image = cover

            book.save()
            messages.success(request, f'Book "{book.title}" updated.')
            return redirect('manage_books')

        # ------------- ADD -------------
        elif action == 'add':
            if not (title and author_name and category_name):
                messages.error(request, 'Title, author and category are required to add a book.')
                return redirect('manage_books')

            author = Author.objects.filter(name__iexact=author_name).first()
            if not author:
                author = Author.objects.create(name=author_name)

            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                category = Category.objects.create(name=category_name)

            date_str = request.POST.get('publication_date')
            try:
                pub_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            except (ValueError, TypeError):
                pub_date = None

            total_copies = parse_int(request.POST.get('total_copies'), default=1)
            available_copies = parse_int(request.POST.get('available_copies'), default=1)

            # <<< ADDED: check publication date not in future (add)
            if pub_date:
                today = datetime.today().date()
                if pub_date > today:
                    messages.error(request, "Publication date cannot be in the future.", extra_tags="publication")
                    return redirect('manage_books')
            # <<< END ADDED

            if available_copies > total_copies:
                messages.error(request, "Available copies cannot be greater than total copies.", extra_tags="available")
                # Render the page so the user can see values (optional) — here we redirect to keep behavior consistent
                return redirect('manage_books')

            book = Book.objects.create(
                title=title,
                author=author,
                category=category,
                isbn=request.POST.get('isbn', '').strip(),
                publisher=request.POST.get('publisher', '').strip(),
                publication_date=pub_date,
                description=request.POST.get('description', '').strip(),
                total_copies=total_copies,
                available_copies=available_copies,
            )

            if cover:
                book.cover_image = cover
                book.save()

            messages.success(request, f'Book "{title}" added.')
            return redirect('manage_books')

        # ------------- DELETE -------------
        elif action == 'delete':
            book_id = request.POST.get('book_id')
            if not book_id:
                messages.error(request, 'Missing book id for delete.')
                return redirect('manage_books')
            book = get_object_or_404(Book, id=book_id)
            book.delete()
            messages.success(request, f'Book "{book.title}" deleted.')
            return redirect('manage_books')

        else:
            messages.error(request, 'Unknown action.')
            return redirect('manage_books')

    # ---------------- GET ------------
    # show books and optionally edit record
    books = books_qs
    edit_book = None
    edit_id = request.GET.get('edit')
    disable_submit = False

    if edit_id:
        try:
            edit_book = Book.objects.select_related('author', 'category').get(id=edit_id)
            # compute disable_submit from DB values
            try:
                if (edit_book.available_copies is not None and edit_book.total_copies is not None
                        and edit_book.available_copies > edit_book.total_copies):
                    disable_submit = True
                    # add a message so template shows the reason (field highlight)
                    messages.error(request,
                                   "Available copies cannot be greater than total copies for this record.",
                                   extra_tags="available")
            except Exception:
                disable_submit = False

            # <<< ADDED: if stored publication_date is future, disable submit and show message
            try:
                if edit_book.publication_date:
                    today = datetime.today().date()
                    if edit_book.publication_date > today:
                        disable_submit = True
                        messages.error(request,
                                       "Publication date for this record is in the future.",
                                       extra_tags="publication")
            except Exception:
                # swallow parsing/comparison errors (keep existing disable_submit)
                pass
            # <<< END ADDED

        except Book.DoesNotExist:
            messages.error(request, 'Requested book to edit was not found.')
            edit_book = None

    context = {
        'books': books,
        'edit_book': edit_book,
        'authors': authors_qs,
        'categories': categories_qs,
        'disable_submit': disable_submit,
    }
    return render(request, 'manage_books.html', context)




def manage_authors(request):

    # -------------------- POST: Add / Edit / Delete --------------------
    if request.method == 'POST':
        action = request.POST.get('action')

        # Add Author
        if action == 'add':
            name = request.POST.get('author_name', '').strip()
            bio = request.POST.get('author_bio', '').strip()
            if name:
                Author.objects.create(name=name, bio=bio)

        # Edit Author
        elif action == 'edit':
            pk = request.POST.get('edit_pk')
            if pk:
                author = get_object_or_404(Author, pk=pk)
                name = request.POST.get('author_name', '').strip()
                bio = request.POST.get('author_bio', '').strip()
                if name:
                    author.name = name
                    author.bio = bio
                    author.save()

        # Delete Author
        elif action == 'delete':
            pk = request.POST.get('delete_pk')
            if pk:
                author = get_object_or_404(Author, pk=pk)
                author.delete()

        # Always redirect after POST
        return redirect('manage_authors')

    # -------------------- GET: Show authors + Edit mode --------------------
    authors = Author.objects.all().order_by('name')

    edit_author = None
    edit_pk = request.GET.get('edit')

    if edit_pk:
        try:
            edit_author = Author.objects.get(pk=edit_pk)
        except Author.DoesNotExist:
            edit_author = None

    # Render page
    return render(request, 'manage_authors.html', {
        'authors': authors,
        'edit_author': edit_author,
    })

def user_issue(request):
    """
    If user not authenticated -> redirect to register with ?next=<current_path_with_query>
    If authenticated -> perform issue logic (GET shows confirm page, POST issues book).
    Expects book_id as GET or POST parameter.
    """
    book_id = request.GET.get('book_id') or request.POST.get('book_id')
    if not book_id:
        messages.error(request, "No book specified to issue.")
        return redirect('user_browse')

    # safe numeric check
    try:
        book_id = int(book_id)
    except (TypeError, ValueError):
        messages.error(request, "Invalid book id.")
        return redirect('user_browse')

    book = get_object_or_404(Book, id=book_id)

    # If user is not authenticated, redirect to register with next
    if not request.user.is_authenticated:
        return redirect(f"{reverse('user_register')}?next={request.get_full_path()}")


    # From here user is authenticated — continue issue flow.
    # Example: show confirm page on GET; handle issue on POST.
    if request.method == 'POST':
        # TODO: add checks (availability, existing loan, etc.)
        # Example placeholder action:
        # create an Issue/Loan record, reduce available_copies, etc.
        # For demonstration:
        if book.available_copies <= 0:
            messages.error(request, f"'{book.title}' is currently not available.")
            return redirect('browse_books')

        # Example: reduce available copies and pretend to issue
        book.available_copies -= 1
        book.save()
        messages.success(request, f'You have successfully issued "{book.title}".')
        return redirect('user_dashboard')

    # GET -> render confirmation page
    return render(request, 'confirm_issue.html', {'book': book})

def manage_categories(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'add')

        if action == 'add':
            name = request.POST.get('category_name', '').strip()
            desc = request.POST.get('category_description', '').strip()
            if not name:
                messages.error(request, "Category name is required.")
                return redirect('manage_categories')

            Category.objects.create(name=name, description=desc)
            messages.success(request, f'Category \"{name}\" added successfully.')
            return redirect('manage_categories')

        if action == 'edit':
            cid = request.POST.get('category_id')
            if not cid:
                messages.error(request, "Category id missing for edit.")
                return redirect('manage_categories')

            category = get_object_or_404(Category, id=cid)
            category.name = request.POST.get('category_name', category.name).strip()
            category.description = request.POST.get('category_description', category.description).strip()
            category.save()
            messages.success(request, f'Category \"{category.name}\" updated.')
            return redirect('manage_categories')

        if action == 'delete':
            cid = request.POST.get('category_id')
            if not cid:
                messages.error(request, "Category id missing for delete.")
                return redirect('manage_categories')

            category = get_object_or_404(Category, id=cid)
            name = category.name
            category.delete()
            messages.success(request, f'Category \"{name}\" deleted.')
            return redirect('manage_categories')

        # unknown action
        messages.error(request, "Unknown action.")
        return redirect('manage_categories')

    # GET: show categories
    categories = Category.objects.all().order_by('id')
    return render(request, 'manage_categories.html', {'categories': categories})


def manage_members(request):
    # consume any leftover messages so category/book messages don't appear here

    if request.method == 'POST':
        print("manage_members POST data:", dict(request.POST))

        action = request.POST.get('action')
        member_id = request.POST.get('member_id')

        if not action:
            messages.error(request, "No action provided in the form.")
            return redirect('manage_members')

        if not member_id:
            messages.error(request, "Missing member_id in the submitted form.")
            return redirect('manage_members')

        try:
            member_id = int(member_id)
        except:
            messages.error(request, "Invalid member_id value.")
            return redirect('manage_members')

        # Only operate on non-staff users
        try:
            member = User.objects.get(id=member_id, is_staff=False)
        except User.DoesNotExist:
            messages.error(request, "Member not found.")
            return redirect('manage_members')
# ----- EDIT -----
        if action == 'edit':
            email = request.POST.get('email', '').strip()
            is_active = request.POST.get('is_active') in ('on', 'true', 'True', '1')

            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            username = request.POST.get('username', '').strip()

            # basic required checks
            if not username:
                messages.error(request, "Username is required.")
                return redirect('manage_members')

            if not email:
                messages.error(request, "Email is required.")
                return redirect('manage_members')

            # don't allow editing a superuser
            if member.is_superuser:
                messages.error(request, "Cannot edit superuser.")
                return redirect('manage_members')

            # UNIQUE CHECK: prevent duplicate username
            if User.objects.exclude(id=member.id).filter(username=username).exists():
                messages.error(request, "Username already taken. Choose another.")
                return redirect(f"{request.path}?page={request.GET.get('page','1')}")  # keep pagination if used

            # Update User fields
            member.username = username
            member.email = email
            member.is_active = is_active
            member.save()

            # Save phone and address
            try:
                from .models import Member
                profile, created = Member.objects.get_or_create(user=member)
                profile.phone = phone
                profile.address = address
                profile.save()
            except Exception as e:
                print("Error saving phone/address:", e)
                messages.warning(request, "Email/username updated, but phone/address not saved.")
                return redirect('manage_members')

            messages.success(request, f"Member '{member.username}' updated successfully.")
            return redirect('manage_members')

        # ----- DELETE -----
        elif action == 'delete':
            if request.user.id == member.id:
                messages.error(request, "You can't delete yourself.")
                return redirect('manage_members')

            if member.is_superuser:
                messages.error(request, "Cannot delete superuser.")
                return redirect('manage_members')

            uname = member.username
            member.delete()
            messages.success(request, f"Member '{uname}' deleted successfully.")
            return redirect('manage_members')

        else:
            messages.error(request, f"Unknown action: {action}")
            return redirect('manage_members')

    # ---------------- GET ----------------
    # fetch all non-staff users (we'll ensure each has a Member profile)
    qs = User.objects.filter(is_staff=False).order_by('id')

    # Ensure every user has a Member profile so template access like `member.member.phone`
    # won't raise a DoesNotExist in templates. This is idempotent and cheap for modest user counts.
    try:
        from .models import Member
        missing_users = []
        for u in qs:
            # get_or_create will create profile if missing, otherwise do nothing
            Member.objects.get_or_create(user=u)
    except Exception as e:
        # if Member model not present or any unexpected error, log and continue
        print("manage_members: error ensuring Member profiles:", e)

    # paginate and render (keep same behaviour as before)
    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'manage_members.html', {
        'members': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })


def track_issues(request):
    issues = Issue.objects.select_related('book', 'user').order_by('id')
    return render(request, 'track_issues.html', {'issues': issues})



# ---------------- User Views ----------------
def user_register(request):
    # Accept next from either GET or POST
    next_param = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()          # NEW
        address = request.POST.get('address', '').strip()      # NEW

        # Simple validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(f"{request.path}?next={next_param}" if next_param else 'user_register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect(f"{request.path}?next={next_param}" if next_param else 'user_register')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Create Member profile (NEW)
        from .models import Member
        Member.objects.create(
            user=user,
            phone=phone,
            address=address
        )

        # Log the user in immediately
        login(request, user)

        # Validate 'next' to avoid open-redirect attacks.
        # Only allow relative paths or safe host+scheme.
        if next_param and url_has_allowed_host_and_scheme(
            url=next_param,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
        ):
            return redirect(next_param)

        messages.success(request, "Registration successful! You are now logged in.")
        return redirect('user_dashboard')

    # GET -> render register form. Pass next so template can include it in POST.
    return render(request, 'user_register.html', {'next': next_param})

def user_dashboard(request):
    user = request.user
    overdue_warnings = []

    # 6 months ago
    six_months_date = (timezone.now() - timedelta(days=182)).date()

    # Get all issued books for this user
    issues = Issue.objects.filter(user=user)

    # Check each issue
    for issue in issues:
        issue_date = issue.issue_date

        # Convert datetime to date if needed
        if hasattr(issue_date, 'date'):
            issue_date = issue_date.date()

        # Compare dates
        if issue_date < six_months_date:
            overdue_warnings.append(
                f"Book '{issue.book.title}' was issued more than 6 months ago."
            )

    return render(request, "user_dashboard.html", {"overdue_warnings": overdue_warnings})


def browse_books(request):

    # Redirect unregistered / not logged-in users
    if not request.user.is_authenticated:
        return redirect('user_register')

    # Fetch all books
    books = Book.objects.select_related('author', 'category').all()

    # Get filter values
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    author_id = request.GET.get('author', '').strip()

    # Apply filters
    if search_query:
        books = books.filter(title__icontains=search_query)

    if category_id:
        books = books.filter(category_id=category_id)

    if author_id:
        books = books.filter(author_id=author_id)

    categories = Category.objects.all()
    authors = Author.objects.all()

    context = {
        'books': books,
        'categories': categories,
        'authors': authors,
        'request': request,
    }

    return render(request, 'browse_books.html', context)






def user_issue(request):
    """
    Handles:
    - GET: show available books OR confirm page if ?book_id=
    - POST with 'book_id': issue the book to request.user
    - POST with 'issue_id': return the issued book (mark return_date, increment copies)
    """

    # Redirect anonymous users to register/login with next
    if not request.user.is_authenticated:
        next_url = request.get_full_path()   # e.g. /user_issue/?book_id=3
        return redirect(f"{reverse('user_register')}?next={next_url}")

    # ---------------- POST ----------------
    if request.method == 'POST':
        # --- RETURN flow: form posts issue_id ---
        issue_id = request.POST.get('issue_id')
        if issue_id:
            # validate and fetch issued record belonging to current user
            issued = get_object_or_404(IssuedBook, id=issue_id, user=request.user)

            if issued.return_date:
                messages.info(request, "This book has already been returned.")
                return redirect('user_issue')

            # mark as returned
            issued.return_date = timezone.now().date()
            issued.save()

            # increment book available copies safely
            book = issued.book
            try:
                book.available_copies = int(book.available_copies or 0) + 1
            except (ValueError, TypeError):
                book.available_copies = 1
            book.save()

            messages.success(request, f'Book "{book.title}" returned successfully.')
            return redirect('user_issue')

        # --- ISSUE flow: form posts book_id ---
        book_id = request.POST.get('book_id')
        if book_id:
            # ensure book exists
            book = get_object_or_404(Book, id=book_id)

            # ensure copies available
            try:
                available = int(book.available_copies or 0)
            except (ValueError, TypeError):
                available = 0

            if available <= 0:
                messages.error(request, "Book is not available to issue.")
                return redirect('user_issue')

            # create issued record
            IssuedBook.objects.create(user=request.user, book=book, issue_date=timezone.now().date())

            # decrement available copies
            book.available_copies = max(0, available - 1)
            book.save()

            messages.success(request, f'Book "{book.title}" issued successfully.')
            return redirect('user_issue')

        # if neither, invalid POST
        messages.error(request, "Invalid request.")
        return redirect('user_issue')

    # ---------------- GET ----------------
    # If GET has ?book_id=xx, show confirm page for that book
    book_id = request.GET.get('book_id')
    if book_id:
        book = get_object_or_404(Book, id=book_id)
        # user's issued records (so confirm page can also show them if desired)
        my_issued = IssuedBook.objects.filter(user=request.user).select_related('book').order_by('-issue_date')
        return render(request, 'issue_book.html', {'book': book, 'my_issued': my_issued})

    # Otherwise list all available books + user's issued list
    available_books = Book.objects.filter(available_copies__gt=0).order_by("title")
    my_issued = IssuedBook.objects.filter(user=request.user).select_related('book').order_by('-issue_date')

    return render(request, 'issue_book.html', {
        'books': available_books,
        'my_issued': my_issued,
    })


# ---------------------------------------------------
# ADMIN: Add a new book
# (cover_image handling removed)
# ---------------------------------------------------
def add_book(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        published_date = request.POST.get('published_date', None)
        try:
            total_copies = int(request.POST.get('total_copies', 1))
        except (ValueError, TypeError):
            total_copies = 1
        try:
            available_copies = int(request.POST.get('available_copies', 1))
        except (ValueError, TypeError):
            available_copies = 1

        # Get category (if selected)
        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                category = None

        # Create the book
        Book.objects.create(
            title=title,
            category=category,
            description=description,
            isbn=isbn,
            publisher=publisher,
            published_date=published_date if published_date else None,
            total_copies=total_copies,
            available_copies=available_copies,
        )

        messages.success(request, f'Book "{title}" added successfully!')
        return redirect('admin_books')

    # If not POST, show empty add-book form
    categories = Category.objects.all()
    return render(request, 'admin_books.html', {'categories': categories})


# ---------------------------------------------------



