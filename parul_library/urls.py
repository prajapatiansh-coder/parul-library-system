"""
URL configuration for parul_library project.
Parul University - Library Management System

This file connects the project-level URLs to our library_app URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin panel (accessible at /admin/)
    path('admin/', admin.site.urls),

    # Include all URLs from library_app
    path('', include('library_app.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
