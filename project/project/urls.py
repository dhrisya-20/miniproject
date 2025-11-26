"""
URL configuration for project project.
"""

from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 🏠 Home Page
    path('', views.home, name='home'),

    # 👨‍💼 Admin Module
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_books/', views.manage_books, name='manage_books'),
    path('manage_authors/', views.manage_authors, name='manage_authors'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
    path('manage_members/', views.manage_members, name='manage_members'),
    path('admin_issues/', views.track_issues, name='admin_issues'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('add_book/', views.add_book, name='add_book'),

    # 👩‍💻 User Module
    path('user_register/', views.user_register, name='user_register'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user_browse/', views.browse_books, name='user_browse'),
    path('user_issue/', views.user_issue, name='user_issue'),
    path('user_logout/', views.user_logout, name='user_logout'),
]

# MEDIA handling (needed to show uploaded images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
