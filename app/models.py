from django.db import models
from django.contrib.auth.models import User

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Author Model
class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Book Model
class Book(models.Model):
    book_code = models.IntegerField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    isbn = models.CharField(max_length=50, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)


    def __str__(self):
        return self.title
    
    def is_available(self):
        return self.available_copies > 0
    is_available.boolean = True

# Member Profile (optional extension of User)
class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    joined_on = models.DateField(auto_now_add=True)

    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# Issued Book Model
class IssuedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} → {self.user.username}"

def status_display(self, obj):
    return "Returned" if obj.return_date else "Issued"
status_display.short_description = 'Status'

