from django.contrib import admin
from .models import Category, Author, Book, Member, IssuedBook

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)

# Author Admin
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bio')
    search_fields = ('name',)

# Book Admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'author',
        'category',
        'isbn',
        'publisher',
        'publication_date',
        'is_available'
    )
    list_filter = ('category',)
    search_fields = ('title', 'author__name', 'isbn', 'publisher')

# Member Admin
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'joined_on')
    search_fields = ('user__username', 'user__first_name')

# IssuedBook Admin
@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'user', 'issue_date', 'return_date', 'status_display')
    list_filter = ('issue_date', 'return_date')
    search_fields = ('book__title', 'user__username')

    def status_display(self, obj):
        return "Returned" if obj.return_date else "Issued"
    status_display.short_description = 'Status'