from django.contrib import admin
from .models import CampusEvent

@admin.register(CampusEvent)
class CampusEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'location', 'organizer')
    list_filter = ('category', 'date')
    search_fields = ('title', 'description', 'organizer')
