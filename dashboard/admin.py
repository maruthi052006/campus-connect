from django.contrib import admin
from .models import ProfileViewTracker

@admin.register(ProfileViewTracker)
class ProfileViewTrackerAdmin(admin.ModelAdmin):
    list_display = ('user', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)
