"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.urls import path
from app import views

urlpatterns = [
    # 🏠 Home Page
    path('', views.home, name='home'),

    # 👨‍💼 Admin Module
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_books/', views.manage_books, name='manage_books'),
    path('manage_authors/', views.manage_authors, name='manage_authors'),
    path('admin_categories/', views.manage_categories, name='manage_categories'),
    path('admin_members/', views.manage_members, name='manage_members'),
    path('admin_issues/', views.track_issues, name='track_issues'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('admin_books/', views.admin_books, name='admin_books'),
    path('edit_book/<int:book_id>/', views.edit_book, name='edit_book'),
    path('delete_book/<int:book_id>/', views.delete_book, name='delete_book'),

    # 👩‍💻 User Module
    path('user_register/', views.user_register, name='user_register'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user_browse/', views.browse_books, name='browse_books'),
    path('search_books/', views.search_books, name='search_books'),
    path('user_issue/', views.issue_book, name='user_issue'),
    path('user_return/', views.return_book, name='return_book'),
    path('user_logout/', views.user_logout, name='user_logout'),

]


