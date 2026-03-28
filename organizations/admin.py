from django.contrib import admin
from .models import Organization, OrganizationMember, JoinRequest, Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'date', 'location')
    list_filter = ('date', 'organization')
    search_fields = ('title', 'description')
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'created_by', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('type', 'created_at')

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')

@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')

admin.site.register(Organization)