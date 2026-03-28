"""
URL configuration for campusconnect project.

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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('connections/', include('connections.urls', namespace='connections')),
    path('skills/', include('skills.urls', namespace='skills')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('organizations/', include('organizations.urls', namespace='organizations')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('search/', include('search.urls', namespace='search')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('recruitment/', include('recruitment.urls', namespace='recruitment')),
    path('events/', include('campus_events.urls', namespace='campus_events')),
    path('', include('feed.urls', namespace='feed')),
    
    # Admin Panel (Root Level)
    path('admin-panel/add-user/', accounts_views.AddUserView.as_view(), name='admin_add_user'),
    path('admin-panel/bulk-upload/', accounts_views.BulkUploadView.as_view(), name='admin_bulk_upload'),
    path('admin-panel/sample-csv/', accounts_views.DownloadSampleCSVView.as_view(), name='admin_sample_csv'),
]

handler404 = 'campusconnect.views.error_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
